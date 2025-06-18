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
            
            # Make request
            response = requests.get(f"{self.base_url}/{endpoint}", params=params)
            
            # Handle different HTTP status codes as per documentation
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 400:
                logger.error(f"Bad Request (400): Parameter missing or malformed - {response.text}")
                return {"status": "error", "code": 400, "message": "Parameter missing or malformed"}
            elif response.status_code == 401:
                logger.error(f"Unauthorized (401): Invalid API key - {response.text}")
                return {"status": "error", "code": 401, "message": "Invalid API key"}
            elif response.status_code == 403:
                logger.error(f"Forbidden (403): CORS policy failed or IP/Domain restricted - {response.text}")
                return {"status": "error", "code": 403, "message": "Access forbidden"}
            elif response.status_code == 409:
                logger.error(f"Conflict (409): Parameter duplicate - {response.text}")
                return {"status": "error", "code": 409, "message": "Parameter duplicate"}
            elif response.status_code == 422:
                logger.error(f"Unprocessable Entity (422): Query malformed - {response.text}")
                return {"status": "error", "code": 422, "message": "Query malformed or invalid"}
            elif response.status_code == 429:
                logger.error(f"Too Many Requests (429): Rate limit exceeded - {response.text}")
                return {"status": "error", "code": 429, "message": "Rate limit exceeded"}
            elif response.status_code == 500:
                logger.error(f"Internal Server Error (500): Server error - {response.text}")
                return {"status": "error", "code": 500, "message": "Internal server error"}
            else:
                logger.error(f"Unexpected status code {response.status_code}: {response.text}")
                return {"status": "error", "code": response.status_code, "message": "Unexpected error"}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            return {"status": "error", "code": 0, "message": f"Request failed: {str(e)}"}
    
    def _sanitize_query(self, query: str) -> str:
        """Sanitize query according to NewsData.io requirements"""
        if not query:
            return ""
        
        # Remove extra whitespace and limit to 100 characters as per API docs
        clean_query = query.strip()[:100]
        
        # Remove duplicate words while preserving order
        words = clean_query.split()
        seen = set()
        unique_words = []
        for word in words:
            if word.lower() not in seen:
                seen.add(word.lower())
                unique_words.append(word)
        
        return " ".join(unique_words)
    
    def get_latest_news(self, query: str = None, language: str = "en", country: str = None, 
                       category: str = None, size: int = 10) -> List[Dict[str, Any]]:
        """Get latest news articles using the /latest endpoint"""
        try:
            params = {
                "language": language,
                "size": min(size, 50)  # API limit is 50
            }
            
            # Add optional parameters
            if query:
                sanitized_query = self._sanitize_query(query)
                if sanitized_query:
                    params["q"] = sanitized_query
            
            if country:
                params["country"] = country
            if category:
                params["category"] = category
            
            # Make request
            response_data = self._make_request("latest", params)
            
            # Check if request was successful
            if response_data.get("status") != "success":
                logger.error(f"API request failed: {response_data.get('message', 'Unknown error')}")
                return []
            
            # Process articles
            articles = []
            for article in response_data.get("results", []):
                processed_article = {
                    "article_id": article.get("article_id", ""),
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "content": article.get("content", ""),
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
                articles.append(processed_article)
            
            logger.info(f"Retrieved {len(articles)} news articles for query: {query}")
            
            # Add small delay to respect rate limits
            time.sleep(self.rate_limit_delay)
            
            return articles
            
        except Exception as e:
            logger.error(f"Failed to get latest news: {str(e)}")
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
