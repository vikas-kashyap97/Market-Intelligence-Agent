import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from uuid import uuid4
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from cachetools import TTLCache

from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA

from config.settings import Settings
from core.state import MarketIntelligenceState
from core.db import DatabaseManager
from core.charts import IntelligentChartGenerator
from core.utils import sanitize_filename, ensure_dir_exists, safe_json_dumps

logger = logging.getLogger(__name__)

class MarketIntelligenceAgent:
    """Main agent class for market intelligence operations"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.search_cache = TTLCache(maxsize=Settings.SEARCH_CACHE_SIZE, ttl=Settings.SEARCH_CACHE_TTL)
        
        # Set USER_AGENT if not already set
        if not os.environ.get("USER_AGENT"):
            os.environ["USER_AGENT"] = Settings.USER_AGENT
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def search_with_tavily(self, query: str) -> List[str]:
        """Search using Tavily API with caching and retry logic"""
        cache_key = f"tavily_{query}"
        if cache_key in self.search_cache:
            logger.info(f"Tavily search: Cache hit for query: {query}")
            return self.search_cache[cache_key]

        if not Settings.TAVILY_API_KEY:
            raise ValueError("TAVILY_API_KEY not set")

        try:
            logger.info(f"Tavily search: Querying {query}")
            response = requests.post(
                "https://api.tavily.com/search",
                headers={"Content-Type": "application/json"},
                json={
                    "api_key": Settings.TAVILY_API_KEY,
                    "query": query,
                    "search_depth": "advanced",
                    "include_answer": False,
                    "max_results": 20
                }
            )
            response.raise_for_status()
            data = response.json()
            urls = [res["url"] for res in data.get("results", []) if "url" in res]
            self.search_cache[cache_key] = urls
            logger.info(f"Tavily search: Retrieved {len(urls)} URLs for query: {query}")
            return urls
        except requests.exceptions.RequestException as e:
            logger.error(f"Tavily search failed for query {query}: {str(e)}")
            raise

    def fetch_url_content(self, url: str) -> Dict[str, Any]:
        """Fetch content from URL using WebBaseLoader"""
        try:
            logger.info(f"Web loader: Fetching {url}")
            loader = WebBaseLoader(url)
            docs = loader.load()
            doc = docs[0] if docs else {}
            content = doc.page_content[:300] if doc else "No content"
            return {
                "source": url,
                "title": doc.metadata.get("title", "No title") if doc else "No title",
                "summary": content,
                "url": url
            }
        except Exception as e:
            logger.error(f"Failed to load URL {url}: {str(e)}")
            return {
                "source": url,
                "title": "Failed to load",
                "summary": str(e),
                "url": url
            }

    def market_data_collector(self, state: MarketIntelligenceState) -> Dict[str, Any]:
        """Collect market data from various sources"""
        logger.info(f"Market data collector: Starting for {state.market_domain}, query: {state.query}")
        
        # Create report directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        safe_query = sanitize_filename(state.query or "analysis")[:10]
        report_dir = os.path.join(Settings.REPORTS_DIR, f"{safe_query}_{timestamp}")
        
        if not ensure_dir_exists(report_dir):
            raise IOError(f"Cannot create report directory: {report_dir}")
        
        state.report_dir = report_dir
        logger.info(f"Market data collector: Set report_dir: {report_dir}")
        
        # Search for data
        try:
            news_urls = self.search_with_tavily(f"{state.query} {state.market_domain} news trends")
            competitor_urls = self.search_with_tavily(f"{state.query} {state.market_domain} competitors analysis")
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return {"raw_news_data": [], "competitor_data": [], "report_dir": report_dir}

        # Fetch content from URLs
        all_urls = list(set(news_urls + competitor_urls))
        logger.info(f"Market data collector: Found {len(all_urls)} unique URLs")
        
        raw_data = []
        for url in all_urls:
            data = self.fetch_url_content(url)
            raw_data.append(data)

        # Save data to files
        self._save_data_files(raw_data, report_dir, state.market_domain)
        
        state.raw_news_data = raw_data
        state.competitor_data = raw_data
        self.db.save_state(state)
        
        return {
            "raw_news_data": raw_data,
            "competitor_data": raw_data,
            "report_dir": report_dir
        }

    def _save_data_files(self, data: List[Dict], report_dir: str, market_domain: str):
        """Save data to JSON and CSV files"""
        domain_safe = sanitize_filename(market_domain)
        json_path = os.path.join(report_dir, f"{domain_safe}_data_sources.json")
        csv_path = os.path.join(report_dir, f"{domain_safe}_data_sources.csv")
        
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Data saved to JSON: {json_path}")
        except Exception as e:
            logger.error(f"Failed to save JSON: {str(e)}")

        try:
            import csv
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                if data:
                    fieldnames = ["title", "summary", "url", "source"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for row in data:
                        writer.writerow(row)
            logger.info(f"Data saved to CSV: {csv_path}")
        except Exception as e:
            logger.error(f"Failed to save CSV: {str(e)}")

    def _call_llm_with_prompt(self, system_prompt: str, user_input: str, parser_type: str = "json") -> Any:
        """Helper method to call LLM with standardized error handling"""
        try:
            llm = init_chat_model(Settings.LLM_MODEL, model_provider="google_genai")
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "{input}")
            ])
            
            if parser_type == "json":
                parser = JsonOutputParser()
            else:
                parser = StrOutputParser()
            
            chain = prompt | llm | parser
            result = chain.invoke({"input": user_input})
            return result
        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            return None

    def trend_analyzer(self, state: MarketIntelligenceState) -> Dict[str, Any]:
        """Analyze market trends using LLM"""
        logger.info(f"Running trend analysis for {state.market_domain}")
        
        system_prompt = f"""Analyze data for {state.market_domain}. Return JSON array of trends with: 
        trend_name, description, supporting_evidence, estimated_impact (High/Medium/Low), 
        timeframe (Short-term/Medium-term/Long-term). At least 3 trends."""
        
        input_data = safe_json_dumps({
            "news_data": state.raw_news_data,
            "competitor_data": state.competitor_data
        })
        
        trends = self._call_llm_with_prompt(system_prompt, input_data)
        
        if not trends:
            trends = [
                {
                    "trend_name": "Digital Transformation",
                    "description": "Accelerated adoption of digital technologies.",
                    "supporting_evidence": "Industry reports and market data.",
                    "estimated_impact": "High",
                    "timeframe": "Medium-term"
                }
            ]
        
        state.market_trends = trends
        self.db.save_state(state)
        return {"market_trends": trends}

    def opportunity_identifier(self, state: MarketIntelligenceState) -> Dict[str, Any]:
        """Identify market opportunities using LLM"""
        logger.info(f"Running opportunity identification for {state.market_domain}")
        
        system_prompt = f"""Identify opportunities in {state.market_domain}. Return JSON array with: 
        opportunity_name, description, target_segment, competitive_advantage, 
        estimated_potential (High/Medium/Low), timeframe_to_capture (Short-term/Medium-term/Long-term). 
        At least 3 opportunities."""
        
        input_data = safe_json_dumps({
            "market_trends": state.market_trends,
            "competitor_data": state.competitor_data,
            "news_data": state.raw_news_data
        })
        
        opportunities = self._call_llm_with_prompt(system_prompt, input_data)
        
        if not opportunities:
            opportunities = [
                {
                    "opportunity_name": "AI-Powered Solutions",
                    "description": "Develop AI-driven products and services.",
                    "target_segment": "Enterprise customers",
                    "competitive_advantage": "Advanced AI capabilities",
                    "estimated_potential": "High",
                    "timeframe_to_capture": "Medium-term"
                }
            ]
        
        state.opportunities = opportunities
        self.db.save_state(state)
        return {"opportunities": opportunities}

    def strategy_recommender(self, state: MarketIntelligenceState) -> Dict[str, Any]:
        """Generate strategic recommendations using LLM"""
        logger.info(f"Running strategy recommendation for {state.market_domain}")
        
        system_prompt = f"""Recommend strategies for {state.market_domain}. Return JSON array with: 
        strategy_title, description, implementation_steps, expected_outcome, 
        resource_requirements, priority_level (High/Medium/Low), success_metrics. 
        At least 3 strategies."""
        
        input_data = safe_json_dumps({
            "opportunities": state.opportunities,
            "market_trends": state.market_trends,
            "competitor_data": state.competitor_data
        })
        
        strategies = self._call_llm_with_prompt(system_prompt, input_data)
        
        if not strategies:
            strategies = [
                {
                    "strategy_title": "Market Expansion",
                    "description": "Expand into new market segments.",
                    "implementation_steps": ["Market research", "Product adaptation", "Launch"],
                    "expected_outcome": "Increased market share",
                    "resource_requirements": "Marketing and development team",
                    "priority_level": "High",
                    "success_metrics": "Revenue growth, market penetration"
                }
            ]
        
        state.strategic_recommendations = strategies
        self.db.save_state(state)
        return {"strategic_recommendations": strategies}

    def report_template_generator(self, state: MarketIntelligenceState) -> Dict[str, Any]:
        """Generate report template using LLM"""
        logger.info(f"Generating template for {state.market_domain}")
        
        system_prompt = f"""Create a markdown template for a {state.market_domain} market intelligence report. 
        Include title, executive summary, trends, opportunities, recommendations, competitive landscape, 
        appendix, and visualization placeholders. Use markdown, no \`\`\`markdown\`\`\` fences."""
        
        template = self._call_llm_with_prompt(
            system_prompt, 
            f"Generate template for {state.market_domain} focusing on {state.query}",
            "text"
        )
        
        if not template:
            template = f"# Market Intelligence Report: {state.market_domain}\n\n## Executive Summary\n[INSERT CONTENT]\n\n## Market Trends\n[INSERT TRENDS]\n\n## Opportunities\n[INSERT OPPORTUNITIES]\n\n## Recommendations\n[INSERT RECOMMENDATIONS]"
        
        state.report_template = template
        self.db.save_state(state)
        return {"report_template": template}

    def setup_vector_store(self, state: MarketIntelligenceState) -> Dict[str, Any]:
        """Setup vector store for RAG queries"""
        logger.info(f"Setting up vector store for state {state.state_id}")
        
        if not state.report_dir:
            raise ValueError("Report directory not initialized")

        # Prepare documents for vector store
        documents = self._prepare_documents_for_vectorstore(state)
        
        try:
            # Create vector store
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            texts = []
            metadatas = []
            
            for doc in documents:
                chunks = text_splitter.split_text(doc["content"])
                for chunk in chunks:
                    texts.append(chunk)
                    metadatas.append(doc["metadata"])

            embeddings = HuggingFaceEmbeddings(model_name=Settings.EMBEDDING_MODEL)
            vector_store = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
            
            vector_store_path = os.path.join(state.report_dir, f"vector_store_{state.state_id[:4]}")
            vector_store.save_local(vector_store_path)
            
            state.vector_store_path = vector_store_path
            self.db.save_state(state)
            
            logger.info(f"Vector store saved: {vector_store_path}")
            return {"vector_store_path": vector_store_path}
            
        except Exception as e:
            logger.error(f"Failed to create vector store: {str(e)}")
            return {"vector_store_path": None}

    def _prepare_documents_for_vectorstore(self, state: MarketIntelligenceState) -> List[Dict[str, Any]]:
        """Prepare documents for vector store creation"""
        documents = []
        
        # Add state data
        documents.append({
            "content": safe_json_dumps({
                "market_trends": state.market_trends,
                "opportunities": state.opportunities,
                "strategic_recommendations": state.strategic_recommendations,
                "competitor_data": state.competitor_data,
                "raw_news_data": state.raw_news_data
            }),
            "metadata": {"source": "state_data", "state_id": state.state_id}
        })
        
        # Add data sources
        for item in state.raw_news_data:
            documents.append({
                "content": f"Title: {item.get('title', '')}\nSummary: {item.get('summary', '')}\nURL: {item.get('url', '')}",
                "metadata": {"source": "data_source", "url": item.get('url', ''), "state_id": state.state_id}
            })
        
        return documents

    def rag_query(self, state: MarketIntelligenceState) -> Dict[str, Any]:
        """Process RAG query if question is provided"""
        if not state.question or not state.vector_store_path:
            logger.info("RAG query: Skipped (no question or vector store)")
            return {"query_response": None}

        logger.info(f"RAG query: Processing {state.question}")
        
        try:
            embeddings = HuggingFaceEmbeddings(model_name=Settings.EMBEDDING_MODEL)
            vector_store = FAISS.load_local(
                state.vector_store_path, 
                embeddings, 
                allow_dangerous_deserialization=True
            )
            retriever = vector_store.as_retriever(search_kwargs={"k": 5})
            
            llm = init_chat_model(Settings.LLM_MODEL, model_provider="google_genai")
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True
            )
            
            result = qa_chain({"query": state.question})
            answer = result["result"]
            
            # Log RAG response
            log_path = os.path.join(state.report_dir, f"rag_responses_{state.state_id[:4]}.log")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] Question: {state.question}\nAnswer: {answer}\n\n")
            
            state.query_response = answer
            self.db.save_state(state)
            
            return {"query_response": answer}
            
        except Exception as e:
            logger.error(f"RAG query failed: {str(e)}")
            return {"query_response": f"Error in RAG query: {str(e)}"}

    def generate_final_report(self, state: MarketIntelligenceState) -> Dict[str, Any]:
        """Generate final markdown report with contextual charts"""
        logger.info(f"Generating final report for {state.market_domain}")
        
        if not state.report_dir:
            raise ValueError("Report directory not initialized")

        # Generate contextual charts using intelligent analysis
        chart_gen = IntelligentChartGenerator(state.report_dir)
        
        chart_data = {
            "query": state.query,
            "market_domain": state.market_domain,
            "market_trends": state.market_trends,
            "opportunities": state.opportunities,
            "strategic_recommendations": state.strategic_recommendations,
            "competitor_data": state.competitor_data,
            "raw_news_data": state.raw_news_data
        }
        
        # Generate contextual charts
        chart_files = chart_gen.generate_contextual_charts(chart_data)
        
        # Generate report content
        report_content = self._generate_report_content(state, chart_files)
        
        # Save report
        report_filename = f"{sanitize_filename(state.market_domain)}_report_{state.state_id[:4]}.md"
        report_path = os.path.join(state.report_dir, report_filename)
        
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_content)
            logger.info(f"Report saved: {report_path}")
        except Exception as e:
            logger.error(f"Failed to save report: {str(e)}")
            raise
        
        return {"report_path": report_path, "chart_files": chart_files}

    def _generate_report_content(self, state: MarketIntelligenceState, chart_files: List[str]) -> str:
        """Generate the final report content"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create chart references
        chart_references = "\n".join([f"![{chart}]({chart})" for chart in chart_files])
        
        if state.report_template:
            # Use LLM to fill template
            try:
                system_prompt = """Fill the markdown template with the provided data. 
                Use 'N/A' for missing data. Include chart references where appropriate. 
                No \`\`\`markdown\`\`\` fences. Add timestamp and attribution."""
                
                input_data = f"""
                Template: {state.report_template}
                
                Data: {safe_json_dumps({
                    'market_trends': state.market_trends,
                    'opportunities': state.opportunities,
                    'strategic_recommendations': state.strategic_recommendations,
                    'competitor_data': state.competitor_data
                })}
                
                Charts: {', '.join(chart_files)}
                Timestamp: {timestamp}
                """
                
                content = self._call_llm_with_prompt(system_prompt, input_data, "text")
                if content:
                    return content
            except Exception as e:
                logger.error(f"Template filling failed: {str(e)}")
        
        # Fallback: create basic report
        return f"""# Market Intelligence Report: {state.market_domain}

## Executive Summary
This report provides comprehensive market intelligence for {state.market_domain} based on the query: "{state.query or 'General analysis'}".

## Market Trends
{self._format_trends(state.market_trends)}

## Opportunities
{self._format_opportunities(state.opportunities)}

## Strategic Recommendations
{self._format_recommendations(state.strategic_recommendations)}

## Visualizations
{chart_references}

## Data Sources
Based on {len(state.raw_news_data)} data sources including news articles, competitor analysis, and market reports.

---
*Generated on {timestamp} by Market Intelligence Agent*
*State ID: {state.state_id}*
"""

    def _format_trends(self, trends: List[Dict[str, Any]]) -> str:
        """Format trends for report"""
        if not trends:
            return "No trends identified."
        
        formatted = []
        for trend in trends:
            formatted.append(f"### {trend.get('trend_name', 'Unknown Trend')}")
            formatted.append(f"**Description:** {trend.get('description', 'N/A')}")
            formatted.append(f"**Impact:** {trend.get('estimated_impact', 'N/A')}")
            formatted.append(f"**Timeframe:** {trend.get('timeframe', 'N/A')}")
            formatted.append("")
        
        return "\n".join(formatted)

    def _format_opportunities(self, opportunities: List[Dict[str, Any]]) -> str:
        """Format opportunities for report"""
        if not opportunities:
            return "No opportunities identified."
        
        formatted = []
        for opp in opportunities:
            formatted.append(f"### {opp.get('opportunity_name', 'Unknown Opportunity')}")
            formatted.append(f"**Description:** {opp.get('description', 'N/A')}")
            formatted.append(f"**Target Segment:** {opp.get('target_segment', 'N/A')}")
            formatted.append(f"**Potential:** {opp.get('estimated_potential', 'N/A')}")
            formatted.append("")
        
        return "\n".join(formatted)

    def _format_recommendations(self, recommendations: List[Dict[str, Any]]) -> str:
        """Format recommendations for report"""
        if not recommendations:
            return "No recommendations available."
        
        formatted = []
        for rec in recommendations:
            formatted.append(f"### {rec.get('strategy_title', 'Unknown Strategy')}")
            formatted.append(f"**Description:** {rec.get('description', 'N/A')}")
            formatted.append(f"**Priority:** {rec.get('priority_level', 'N/A')}")
            formatted.append(f"**Expected Outcome:** {rec.get('expected_outcome', 'N/A')}")
            formatted.append("")
        
        return "\n".join(formatted)

    def chat_with_agent(self, message: str, session_id: str) -> str:
        """Chat with the agent using conversation history"""
        try:
            # Load chat history
            history = self.db.load_chat_history(session_id)
            
            # Initialize LLM
            llm = init_chat_model(Settings.LLM_MODEL, model_provider="google_genai")
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful assistant for the Market Intelligence Agent. Answer questions conversationally, providing insights on market intelligence topics. Use previous messages for context if relevant."),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}")
            ])
            
            chain = prompt | llm | StrOutputParser()
            
            # Convert history to LangChain message objects
            message_history = []
            for msg in history:
                if msg["type"] == "human":
                    message_history.append(HumanMessage(content=msg["content"]))
                elif msg["type"] == "ai":
                    message_history.append(AIMessage(content=msg["content"]))
            
            # Generate response
            response = chain.invoke({
                "history": message_history,
                "input": message
            })
            
            # Save messages to database
            self.db.save_chat_message(session_id, "human", message)
            self.db.save_chat_message(session_id, "ai", response)
            
            return response
            
        except Exception as e:
            logger.error(f"Chat failed for session {session_id}: {str(e)}")
            return f"I apologize, but I encountered an error processing your message. Please try again."

    def create_workflow(self):
        """Create the LangGraph workflow"""
        workflow = StateGraph(MarketIntelligenceState)
        
        # Add nodes
        workflow.add_node("market_data_collector", self.market_data_collector)
        workflow.add_node("trend_analyzer", self.trend_analyzer)
        workflow.add_node("opportunity_identifier", self.opportunity_identifier)
        workflow.add_node("strategy_recommender", self.strategy_recommender)
        workflow.add_node("report_template_generator", self.report_template_generator)
        workflow.add_node("setup_vector_store", self.setup_vector_store)
        workflow.add_node("rag_query", self.rag_query)
        workflow.add_node("generate_final_report", self.generate_final_report)

        # Define workflow
        workflow.set_entry_point("market_data_collector")
        workflow.add_edge("market_data_collector", "trend_analyzer")
        workflow.add_edge("trend_analyzer", "opportunity_identifier")
        workflow.add_edge("opportunity_identifier", "strategy_recommender")
        workflow.add_edge("strategy_recommender", "report_template_generator")
        workflow.add_edge("report_template_generator", "setup_vector_store")
        workflow.add_edge("setup_vector_store", "rag_query")
        workflow.add_edge("rag_query", "generate_final_report")
        workflow.add_edge("generate_final_report", END)

        return workflow.compile()

    def run_analysis(self, query: str, market_domain: str, question: Optional[str] = None) -> Dict[str, Any]:
        """Run the complete market intelligence analysis"""
        logger.info(f"Starting analysis for {market_domain}, query: {query}")
        
        try:
            # Validate settings
            Settings.validate()
            
            # Create workflow and state
            workflow = self.create_workflow()
            state = MarketIntelligenceState(
                query=query, 
                market_domain=market_domain, 
                question=question
            )
            
            # Run workflow
            final_state = workflow.invoke(state)
            final_state = MarketIntelligenceState(**final_state)
            
            # Return results
            return {
                "success": True,
                "state_id": final_state.state_id,
                "report_dir": final_state.report_dir,
                "query_response": final_state.query_response,
                "market_trends": final_state.market_trends,
                "opportunities": final_state.opportunities,
                "strategic_recommendations": final_state.strategic_recommendations
            }
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "state_id": None
            }
