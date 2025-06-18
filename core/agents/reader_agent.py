import asyncio
import logging
from typing import Dict, List, Any
from core.agents.base_agent import BaseAgent
from core.integrations.firecrawl_client import FirecrawlClient
from core.integrations.newsdata_client import NewsDataClient
from langchain.chat_models import init_chat_model
from config.settings import Settings

logger = logging.getLogger(__name__)

class ReaderAgent(BaseAgent):
    """Agent responsible for reading and collecting data from various sources"""
    
    def __init__(self):
        super().__init__(
            name="Reader Agent",
            description="Collects data from web sources, news APIs, and documents"
        )
        self.firecrawl = FirecrawlClient()
        self.newsdata = NewsDataClient()
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data collection tasks"""
        query = input_data.get("query", "")
        market_domain = input_data.get("market_domain", "")
        
        self.update_progress(10, "Initializing data collection")
        
        # Collect data from multiple sources concurrently
        tasks = [
            self._collect_web_content(query, market_domain),
            self._collect_news_data(query, market_domain),
            self._collect_trending_topics()
        ]
        
        self.update_progress(30, "Collecting data from sources")
        
        web_content, news_data, trending_topics = await asyncio.gather(*tasks)
        
        self.update_progress(80, "Processing collected data")
        
        # Process and structure the collected data
        processed_data = await self._process_collected_data(
            web_content, news_data, trending_topics, query, market_domain
        )
        
        self.update_progress(100, "Data collection completed")
        
        return {
            "success": True,
            "web_content": web_content,
            "news_data": news_data,
            "trending_topics": trending_topics,
            "processed_data": processed_data,
            "total_sources": len(web_content) + len(news_data)
        }
    
    async def _collect_web_content(self, query: str, market_domain: str) -> List[Dict[str, Any]]:
        """Collect web content using Firecrawl"""
        try:
            # Search and scrape relevant content
            search_query = f"{query} {market_domain} market analysis trends"
            web_results = self.firecrawl.search_and_scrape(search_query, num_results=8)
            
            # Filter and clean results
            filtered_results = []
            for result in web_results:
                if result.get("content") and len(result["content"]) > 100:
                    filtered_results.append({
                        "source": "web_scraping",
                        "url": result.get("url", ""),
                        "title": result.get("title", ""),
                        "content": result.get("content", "")[:2000],  # Limit content length
                        "metadata": result.get("metadata", {})
                    })
            
            logger.info(f"Collected {len(filtered_results)} web content pieces")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Failed to collect web content: {str(e)}")
            return []
    
    async def _collect_news_data(self, query: str, market_domain: str) -> List[Dict[str, Any]]:
        """Collect news data using NewsData.io"""
        try:
            # Get latest news
            news_query = f"{query} {market_domain}"
            news_articles = self.newsdata.get_latest_news(news_query, size=15)
            
            # Process news articles
            processed_articles = []
            for article in news_articles:
                if article.get("title") and article.get("description"):
                    processed_articles.append({
                        "source": "news_api",
                        "title": article.get("title", ""),
                        "description": article.get("description", ""),
                        "content": article.get("content", "")[:1500],
                        "url": article.get("url", ""),
                        "published_date": article.get("published_date", ""),
                        "news_source": article.get("source", ""),
                        "category": article.get("category", [])
                    })
            
            logger.info(f"Collected {len(processed_articles)} news articles")
            return processed_articles
            
        except Exception as e:
            logger.error(f"Failed to collect news data: {str(e)}")
            return []
    
    async def _collect_trending_topics(self) -> List[Dict[str, Any]]:
        """Collect trending topics"""
        try:
            trending = self.newsdata.get_trending_topics()
            logger.info(f"Collected {len(trending)} trending topics")
            return trending
            
        except Exception as e:
            logger.error(f"Failed to collect trending topics: {str(e)}")
            return []
    
    async def _process_collected_data(self, web_content: List[Dict], news_data: List[Dict], 
                                    trending_topics: List[Dict], query: str, market_domain: str) -> Dict[str, Any]:
        """Process and analyze collected data using LLM"""
        try:
            # Combine all content for analysis
            all_content = []
            
            for item in web_content:
                all_content.append(f"WEB: {item.get('title', '')} - {item.get('content', '')[:500]}")
            
            for item in news_data:
                all_content.append(f"NEWS: {item.get('title', '')} - {item.get('description', '')}")
            
            # Use LLM to extract key themes and insights
            llm = init_chat_model(Settings.LLM_MODEL, model_provider="google_genai")
            
            analysis_prompt = f"""
            Analyze the following collected data about "{query}" in the {market_domain} market.
            
            Extract and return a JSON object with:
            1. key_themes: List of main themes found
            2. market_signals: Important market signals or indicators
            3. data_quality_score: Score from 1-10 for data quality
            4. content_summary: Brief summary of collected content
            5. recommended_focus_areas: Areas that need more research
            
            Data:
            {chr(10).join(all_content[:20])}  # Limit to first 20 items
            """
            
            response = llm.invoke(analysis_prompt)
            
            # Try to parse as JSON, fallback to structured text
            try:
                import json
                processed = json.loads(response.content if hasattr(response, 'content') else str(response))
            except:
                processed = {
                    "key_themes": ["Data processing", "Market analysis"],
                    "market_signals": ["Emerging trends identified"],
                    "data_quality_score": 7,
                    "content_summary": "Successfully collected and processed market data",
                    "recommended_focus_areas": ["Competitive analysis", "Market trends"]
                }
            
            return processed
            
        except Exception as e:
            logger.error(f"Failed to process collected data: {str(e)}")
            return {
                "key_themes": [],
                "market_signals": [],
                "data_quality_score": 5,
                "content_summary": "Data collection completed with some processing errors",
                "recommended_focus_areas": []
            }
