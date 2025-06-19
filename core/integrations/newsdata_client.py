import requests
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from config.settings import Settings
import time

logger = logging.getLogger(__name__)

class NewsDataClient:
    """Client for NewsData.io API integration following official documentation"""
    
    def __init__(self):
        self.api_key = Settings.NEWSDATA_IO_KEY
        self.base_url = "https://newsdata.io/api/1"
        self.rate_limit_delay = 1  # Delay between requests to respect rate limits
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to NewsData.io API with proper error handling"""
        try:
            # Add API key to params
            params["apikey"] = self.api_key
        
            # Make request with timeout
            response = requests.get(f"{self.base_url}/{endpoint}", params=params, timeout=30)
        
            # Log the request for debugging
            logger.info(f"NewsData.io request: {endpoint} with params: {list(params.keys())}")
        
            # Handle different HTTP status codes
            if response.status_code == 200:
                data = response.json()
                # Check if the response has the expected structure
                if data.get("status") == "success":
                    logger.info(f"NewsData.io success: Retrieved {len(data.get('results', []))} articles")
                    return data
                else:
                    logger.error(f"NewsData.io API error: {data}")
                    return {"status": "error", "message": data.get("message", "Unknown API error")}
            else:
                logger.error(f"NewsData.io HTTP error {response.status_code}: {response.text}")
                return {"status": "error", "code": response.status_code, "message": response.text}
            
        except requests.exceptions.Timeout:
            logger.error("NewsData.io request timeout")
            return {"status": "error", "message": "Request timeout"}
        except requests.exceptions.RequestException as e:
            logger.error(f"NewsData.io request failed: {str(e)}")
            return {"status": "error", "message": f"Request failed: {str(e)}"}
    
    def _sanitize_query(self, query: str) -> str:
        """Sanitize query according to NewsData.io requirements"""
        if not query:
            return ""
    
        # Clean and limit query
        clean_query = query.strip()
    
        # Remove special characters that might cause issues
        import re
        clean_query = re.sub(r'[^\w\s-]', ' ', clean_query)
    
        # Limit to reasonable length and remove extra spaces
        clean_query = ' '.join(clean_query.split())[:80]
    
        return clean_query
    
    def get_latest_news(self, query: str = None, language: str = "en", country: str = None, 
                       category: str = None, size: int = 10) -> List[Dict[str, Any]]:
        """Get latest news articles using the /latest endpoint"""
        try:
            params = {
                "language": language,
                "size": min(size, 50)  # API limit is 50
            }
        
            # Add query if provided
            if query:
                sanitized_query = self._sanitize_query(query)
                if sanitized_query:
                    params["q"] = sanitized_query
                    logger.info(f"NewsData.io query: {sanitized_query}")
        
            # Add optional parameters
            if country:
                params["country"] = country
            if category:
                params["category"] = category
        
            # Make request
            response_data = self._make_request("latest", params)
        
            # Check if request was successful
            if response_data.get("status") != "success":
                logger.error(f"NewsData.io API request failed: {response_data.get('message', 'Unknown error')}")
                return []
        
            # Process articles
            articles = []
            results = response_data.get("results", [])
        
            for article in results:
                if not article:  # Skip empty articles
                    continue
                
                processed_article = {
                    "article_id": article.get("article_id", ""),
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "content": article.get("content", article.get("description", "")),  # Fallback to description
                    "url": article.get("link", ""),
                    "source": article.get("source_id", ""),
                    "source_name": article.get("source_name", ""),
                    "published_date": article.get("pubDate", ""),
                    "image_url": article.get("image_url", ""),
                    "category": article.get("category", []),
                    "keywords": article.get("keywords", []),
                    "country": article.get("country", []),
                    "language": article.get("language", ""),
                    "sentiment": article.get("sentiment", ""),
                    "ai_tag": article.get("ai_tag", []),
                    "duplicate": article.get("duplicate", False)
                }
            
                # Only add articles with meaningful content
                if processed_article["title"] or processed_article["description"]:
                    articles.append(processed_article)
        
            logger.info(f"NewsData.io: Successfully processed {len(articles)} articles from {len(results)} results")
        
            # Add delay to respect rate limits
            time.sleep(self.rate_limit_delay)
        
            return articles
        
        except Exception as e:
            logger.error(f"NewsData.io get_latest_news failed: {str(e)}")
            return []
    
    def get_news_by_domain(self, domain: str, query: str = None, size: int = 10) -> List[Dict[str, Any]]:
        """Get news from specific domain using domainurl parameter"""
        try:
            params = {
                "domainurl": domain,
                "size": min(size, 50)
            }
            
            if query:
                sanitized_query = self._sanitize_query(query)
                if sanitized_query:
                    params["q"] = sanitized_query
            
            response_data = self._make_request("latest", params)
            
            if response_data.get("status") != "success":
                logger.error(f"API request failed: {response_data.get('message', 'Unknown error')}")
                return []
            
            articles = []
            for article in response_data.get("results", []):
                processed_article = {
                    "article_id": article.get("article_id", ""),
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "content": article.get("content", ""),
                    "url": article.get("link", ""),
                    "source": article.get("source_id", ""),
                    "published_date": article.get("pubDate", ""),
                    "domain": domain
                }
                articles.append(processed_article)
            
            logger.info(f"Retrieved {len(articles)} articles from domain: {domain}")
            
            time.sleep(self.rate_limit_delay)
            return articles
            
        except Exception as e:
            logger.error(f"Failed to get news from domain {domain}: {str(e)}")
            return []
    
    def get_trending_topics(self, language: str = "en", country: str = None, size: int = 20) -> List[Dict[str, Any]]:
        """Get trending topics by analyzing recent news"""
        try:
            params = {
                "language": language,
                "size": min(size, 50),
                "timeframe": "24"  # Last 24 hours for trending topics
            }
            
            if country:
                params["country"] = country
            
            response_data = self._make_request("latest", params)
            
            if response_data.get("status") != "success":
                logger.error(f"API request failed: {response_data.get('message', 'Unknown error')}")
                return []
            
            # Extract trending keywords from articles
            keyword_counts = {}
            for article in response_data.get("results", []):
                # Count keywords
                keywords = article.get("keywords", [])
                for keyword in keywords:
                    if keyword and len(keyword) > 2:  # Filter out very short keywords
                        keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
                
                # Count AI tags if available
                ai_tags = article.get("ai_tag", [])
                for tag in ai_tags:
                    if tag and len(tag) > 2:
                        keyword_counts[tag] = keyword_counts.get(tag, 0) + 1
            
            # Sort by frequency and return top trending topics
            trending = [
                {"topic": topic, "frequency": count}
                for topic, count in sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            ]
            
            logger.info(f"Retrieved {len(trending)} trending topics")
            
            time.sleep(self.rate_limit_delay)
            return trending
            
        except Exception as e:
            logger.error(f"Failed to get trending topics: {str(e)}")
            return []
    
    def get_crypto_news(self, coin: str = None, query: str = None, size: int = 10) -> List[Dict[str, Any]]:
        """Get cryptocurrency news using the /crypto endpoint"""
        try:
            params = {
                "size": min(size, 50)
            }
            
            if coin:
                params["coin"] = coin.lower()  # Crypto symbols should be lowercase
            
            if query:
                sanitized_query = self._sanitize_query(query)
                if sanitized_query:
                    params["q"] = sanitized_query
            
            response_data = self._make_request("crypto", params)
            
            if response_data.get("status") != "success":
                logger.error(f"API request failed: {response_data.get('message', 'Unknown error')}")
                return []
            
            articles = []
            for article in response_data.get("results", []):
                processed_article = {
                    "article_id": article.get("article_id", ""),
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "content": article.get("content", ""),
                    "url": article.get("link", ""),
                    "source": article.get("source_id", ""),
                    "published_date": article.get("pubDate", ""),
                    "coin": article.get("coin", []),
                    "category": article.get("category", [])
                }
                articles.append(processed_article)
            
            logger.info(f"Retrieved {len(articles)} crypto news articles")
            
            time.sleep(self.rate_limit_delay)
            return articles
            
        except Exception as e:
            logger.error(f"Failed to get crypto news: {str(e)}")
            return []
    
    def get_news_sources(self, country: str = None, category: str = None, language: str = None) -> List[Dict[str, Any]]:
        """Get available news sources using the /sources endpoint"""
        try:
            params = {}
            
            if country:
                params["country"] = country
            if category:
                params["category"] = category
            if language:
                params["language"] = language
            
            response_data = self._make_request("sources", params)
            
            if response_data.get("status") != "success":
                logger.error(f"API request failed: {response_data.get('message', 'Unknown error')}")
                return []
            
            sources = response_data.get("results", [])
            logger.info(f"Retrieved {len(sources)} news sources")
            
            time.sleep(self.rate_limit_delay)
            return sources
            
        except Exception as e:
            logger.error(f"Failed to get news sources: {str(e)}")
            return []
