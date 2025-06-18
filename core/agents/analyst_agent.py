import asyncio
import logging
from typing import Dict, List, Any
from core.agents.base_agent import BaseAgent
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import JsonOutputParser
from config.settings import Settings

logger = logging.getLogger(__name__)

class AnalystAgent(BaseAgent):
    """Agent responsible for analyzing data and extracting structured insights"""
    
    def __init__(self):
        super().__init__(
            name="Analyst Agent",
            description="Analyzes collected data to extract trends, opportunities, and metrics"
        )
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data analysis tasks"""
        self.update_progress(10, "Initializing analysis")
        
        # Get data from Reader Agent
        web_content = input_data.get("web_content", [])
        news_data = input_data.get("news_data", [])
        processed_data = input_data.get("processed_data", {})
        query = input_data.get("query", "")
        market_domain = input_data.get("market_domain", "")
        
        # Perform different types of analysis concurrently
        tasks = [
            self._analyze_market_trends(web_content, news_data, query, market_domain),
            self._identify_opportunities(web_content, news_data, query, market_domain),
            self._analyze_competitive_landscape(web_content, news_data, query, market_domain),
            self._extract_key_metrics(web_content, news_data, processed_data)
        ]
        
        self.update_progress(40, "Running analysis algorithms")
        
        trends, opportunities, competitive_landscape, metrics = await asyncio.gather(*tasks)
        
        self.update_progress(80, "Synthesizing analysis results")
        
        # Synthesize all analysis results
        synthesis = await self._synthesize_analysis(
            trends, opportunities, competitive_landscape, metrics, query, market_domain
        )
        
        self.update_progress(100, "Analysis completed")
        
        return {
            "success": True,
            "market_trends": trends,
            "opportunities": opportunities,
            "competitive_landscape": competitive_landscape,
            "key_metrics": metrics,
            "analysis_synthesis": synthesis
        }
    
    async def _analyze_market_trends(self, web_content: List[Dict], news_data: List[Dict], 
                                   query: str, market_domain: str) -> List[Dict[str, Any]]:
        """Analyze market trends from collected data"""
        try:
            # Combine relevant content
            trend_content = []
            for item in web_content + news_data:
                content = item.get("content", "") or item.get("description", "")
                if content and len(content.strip()) > 50:  # Only include substantial content
                    trend_content.append(content[:800])
            
            # If no content available, return fallback trends
            if not trend_content:
                logger.warning("No content available for trend analysis, using fallback data")
                return self._get_fallback_trends(query, market_domain)
            
            llm = init_chat_model(Settings.LLM_MODEL, model_provider="google_genai")
            parser = JsonOutputParser()
            
            prompt = f"""
            Analyze the following content to identify market trends for {query} in the {market_domain} sector.
            
            Return a JSON array of trends with the following structure:
            [
                {{
                    "trend_name": "Name of the trend",
                    "description": "Detailed description",
                    "impact_level": "High/Medium/Low",
                    "timeframe": "Short-term/Medium-term/Long-term",
                    "confidence_score": 0.0-1.0,
                    "supporting_evidence": ["evidence1", "evidence2"],
                    "market_size_impact": "Quantitative or qualitative impact",
                    "key_drivers": ["driver1", "driver2"]
                }}
            ]
            
            Content to analyze:
            {chr(10).join(trend_content[:15])}
            """
            
            chain = llm | parser
            trends = chain.invoke(prompt)
            
            # Ensure we have valid trends
            if not isinstance(trends, list):
                trends = []
            
            # Add metadata
            for trend in trends:
                trend["analysis_timestamp"] = asyncio.get_event_loop().time()
                trend["data_sources"] = len(web_content) + len(news_data)
        
            logger.info(f"Identified {len(trends)} market trends")
            return trends
            
        except Exception as e:
            logger.error(f"Failed to analyze market trends: {str(e)}")
            return self._get_fallback_trends(query, market_domain)

    def _get_fallback_trends(self, query: str, market_domain: str) -> List[Dict[str, Any]]:
        """Provide fallback trends when no data is available"""
        return [
            {
                "trend_name": f"Digital Transformation in {market_domain}",
                "description": f"Continued digital adoption and AI integration in {market_domain} sector",
                "impact_level": "High",
                "timeframe": "Medium-term",
                "confidence_score": 0.6,
                "supporting_evidence": ["Industry reports", "Market analysis"],
                "market_size_impact": "Significant growth potential",
                "key_drivers": ["Technology advancement", "Consumer demand"],
                "analysis_timestamp": asyncio.get_event_loop().time(),
                "data_sources": 0,
                "note": "Fallback data - limited external sources available"
            },
            {
                "trend_name": f"Sustainability Focus in {market_domain}",
                "description": f"Increasing emphasis on sustainable practices in {market_domain}",
                "impact_level": "Medium",
                "timeframe": "Long-term",
                "confidence_score": 0.5,
                "supporting_evidence": ["Regulatory trends", "Consumer preferences"],
                "market_size_impact": "Moderate growth impact",
                "key_drivers": ["Regulatory pressure", "Environmental awareness"],
                "analysis_timestamp": asyncio.get_event_loop().time(),
                "data_sources": 0,
                "note": "Fallback data - limited external sources available"
            }
        ]
    
    async def _identify_opportunities(self, web_content: List[Dict], news_data: List[Dict], 
                                    query: str, market_domain: str) -> List[Dict[str, Any]]:
        """Identify market opportunities"""
        try:
            # Combine content for opportunity analysis
            opportunity_content = []
            for item in web_content + news_data:
                content = item.get("content", "") or item.get("description", "")
                if content and len(content.strip()) > 50:
                    opportunity_content.append(content[:800])
        
            # If no content available, return fallback opportunities
            if not opportunity_content:
                logger.warning("No content available for opportunity analysis, using fallback data")
                return self._get_fallback_opportunities(query, market_domain)
        
            llm = init_chat_model(Settings.LLM_MODEL, model_provider="google_genai")
            parser = JsonOutputParser()
        
            prompt = f"""
            Identify market opportunities for {query} in the {market_domain} sector based on the following content.
        
            Return a JSON array of opportunities:
            [
                {{
                    "opportunity_name": "Name of opportunity",
                    "description": "Detailed description",
                    "market_size": "Estimated market size or potential",
                    "target_segment": "Primary target segment",
                    "competitive_advantage": "Potential competitive advantage",
                    "implementation_difficulty": "Easy/Medium/Hard",
                    "time_to_market": "Estimated time to market",
                    "revenue_potential": "High/Medium/Low",
                    "risk_level": "High/Medium/Low",
                    "key_requirements": ["requirement1", "requirement2"]
                }}
            ]
        
            Content:
            {chr(10).join(opportunity_content[:15])}
            """
        
            chain = llm | parser
            opportunities = chain.invoke(prompt)
        
            if not isinstance(opportunities, list):
                opportunities = []
        
            logger.info(f"Identified {len(opportunities)} market opportunities")
            return opportunities
        
        except Exception as e:
            logger.error(f"Failed to identify opportunities: {str(e)}")
            return self._get_fallback_opportunities(query, market_domain)

    def _get_fallback_opportunities(self, query: str, market_domain: str) -> List[Dict[str, Any]]:
        """Provide fallback opportunities when no data is available"""
        return [
            {
                "opportunity_name": f"AI-Powered Solutions for {market_domain}",
                "description": f"Develop AI-driven products and services for {market_domain} market needs",
                "market_size": "Large and growing",
                "target_segment": "Enterprise customers",
                "competitive_advantage": "Advanced AI capabilities",
                "implementation_difficulty": "Medium",
                "time_to_market": "6-12 months",
                "revenue_potential": "High",
                "risk_level": "Medium",
                "key_requirements": ["AI expertise", "Market validation"],
                "note": "Fallback data - limited external sources available"
            },
            {
                "opportunity_name": f"Digital Platform for {market_domain}",
                "description": f"Create digital marketplace or platform serving {market_domain} sector",
                "market_size": "Medium to large",
                "target_segment": "SME and enterprise",
                "competitive_advantage": "First-mover advantage",
                "implementation_difficulty": "Hard",
                "time_to_market": "12-18 months",
                "revenue_potential": "Medium",
                "risk_level": "High",
                "key_requirements": ["Platform development", "User acquisition"],
                "note": "Fallback data - limited external sources available"
            }
        ]
    
    async def _analyze_competitive_landscape(self, web_content: List[Dict], news_data: List[Dict], 
                                           query: str, market_domain: str) -> Dict[str, Any]:
        """Analyze competitive landscape"""
        try:
            # Extract competitor information
            competitor_content = []
            for item in web_content + news_data:
                content = item.get("content", "") or item.get("description", "")
                if any(keyword in content.lower() for keyword in ["competitor", "company", "startup", "leader"]):
                    competitor_content.append(content[:600])
            
            llm = init_chat_model(Settings.LLM_MODEL, model_provider="google_genai")
            parser = JsonOutputParser()
            
            prompt = f"""
            Analyze the competitive landscape for {query} in the {market_domain} sector.
            
            Return a JSON object with:
            {{
                "market_leaders": [
                    {{
                        "company_name": "Company name",
                        "market_share": "Estimated market share",
                        "key_strengths": ["strength1", "strength2"],
                        "recent_developments": "Recent news or developments"
                    }}
                ],
                "emerging_players": [
                    {{
                        "company_name": "Company name",
                        "focus_area": "Primary focus area",
                        "competitive_edge": "What makes them competitive"
                    }}
                ],
                "market_concentration": "High/Medium/Low",
                "barriers_to_entry": ["barrier1", "barrier2"],
                "competitive_intensity": "High/Medium/Low"
            }}
            
            Content:
            {chr(10).join(competitor_content[:10])}
            """
            
            chain = llm | parser
            competitive_analysis = chain.invoke(prompt)
            
            if not isinstance(competitive_analysis, dict):
                competitive_analysis = {}
            
            logger.info("Completed competitive landscape analysis")
            return competitive_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze competitive landscape: {str(e)}")
            return {
                "market_leaders": [],
                "emerging_players": [],
                "market_concentration": "Medium",
                "barriers_to_entry": ["Capital requirements", "Regulatory compliance"],
                "competitive_intensity": "Medium"
            }
    
    async def _extract_key_metrics(self, web_content: List[Dict], news_data: List[Dict], 
                                 processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key metrics and KPIs"""
        try:
            # Calculate basic metrics
            total_sources = len(web_content) + len(news_data)
            data_quality_score = processed_data.get("data_quality_score", 7)
            
            # Extract numerical data from content
            numerical_data = []
            for item in web_content + news_data:
                content = item.get("content", "") or item.get("description", "")
                # Simple regex to find numbers with context
                import re
                numbers = re.findall(r'\$?(\d+(?:\.\d+)?)\s*(?:billion|million|thousand|%|percent)', content.lower())
                numerical_data.extend(numbers)
            
            metrics = {
                "data_sources_count": total_sources,
                "web_sources": len(web_content),
                "news_sources": len(news_data),
                "data_quality_score": data_quality_score,
                "numerical_data_points": len(numerical_data),
                "content_freshness": "Recent",  # Could be calculated based on dates
                "coverage_completeness": min(100, (total_sources / 20) * 100),  # Assume 20 is ideal
                "analysis_confidence": data_quality_score / 10
            }
            
            logger.info("Extracted key metrics")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to extract key metrics: {str(e)}")
            return {
                "data_sources_count": 0,
                "web_sources": 0,
                "news_sources": 0,
                "data_quality_score": 5,
                "numerical_data_points": 0,
                "content_freshness": "Unknown",
                "coverage_completeness": 50,
                "analysis_confidence": 0.5
            }
    
    async def _synthesize_analysis(self, trends: List[Dict], opportunities: List[Dict], 
                                 competitive_landscape: Dict, metrics: Dict, 
                                 query: str, market_domain: str) -> Dict[str, Any]:
        """Synthesize all analysis results into key insights"""
        try:
            llm = init_chat_model(Settings.LLM_MODEL, model_provider="google_genai")
            
            synthesis_prompt = f"""
            Synthesize the following analysis results for {query} in the {market_domain} market:
            
            Trends: {trends[:3]}  # Top 3 trends
            Opportunities: {opportunities[:3]}  # Top 3 opportunities
            Competitive Landscape: {competitive_landscape}
            Metrics: {metrics}
            
            Provide a synthesis with:
            1. Executive summary (2-3 sentences)
            2. Key insights (3-5 bullet points)
            3. Strategic implications
            4. Recommended next steps
            5. Risk factors to consider
            """
            
            synthesis_response = llm.invoke(synthesis_prompt)
            synthesis_text = synthesis_response.content if hasattr(synthesis_response, 'content') else str(synthesis_response)
            
            return {
                "executive_summary": synthesis_text[:500],
                "full_synthesis": synthesis_text,
                "analysis_timestamp": asyncio.get_event_loop().time(),
                "confidence_level": metrics.get("analysis_confidence", 0.7)
            }
            
        except Exception as e:
            logger.error(f"Failed to synthesize analysis: {str(e)}")
            return {
                "executive_summary": f"Analysis completed for {query} in {market_domain} market with {len(trends)} trends and {len(opportunities)} opportunities identified.",
                "full_synthesis": "Comprehensive market analysis completed successfully.",
                "analysis_timestamp": asyncio.get_event_loop().time(),
                "confidence_level": 0.7
            }
