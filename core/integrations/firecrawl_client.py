import requests
import logging
import time
from typing import Dict, List, Any, Optional
from config.settings import Settings

logger = logging.getLogger(__name__)


class FirecrawlClient:
    """Client for Firecrawl.dev API integration"""

    def __init__(self):
        self.api_key = Settings.FIRECRAWL_API_KEY
        self.base_url = "https://api.firecrawl.dev/v0"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def scrape_url(self, url: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Scrape a single URL"""
        try:
            payload = {
                "url": url,
                "pageOptions": options or {
                    "onlyMainContent": True,
                    "includeHtml": False,
                    "screenshot": False
                }
            }

            response = requests.post(
                f"{self.base_url}/scrape",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            logger.info(f"Successfully scraped URL: {url}")

            return {
                "success": True,
                "url": url,
                "title": data.get("data", {}).get("title", ""),
                "content": data.get("data", {}).get("markdown", ""),
                "metadata": data.get("data", {}).get("metadata", {})
            }

        except Exception as e:
            logger.error(f"Failed to scrape URL {url}: {str(e)}")
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }

    def crawl_website(self, url: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Crawl an entire website"""
        try:
            payload = {
                "url": url,
                "crawlerOptions": options or {
                    "maxDepth": 2,
                    "limit": 10,
                    "allowBackwardCrawling": False
                },
                "pageOptions": {
                    "onlyMainContent": True,
                    "includeHtml": False
                }
            }

            response = requests.post(
                f"{self.base_url}/crawl",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            job_id = data.get("jobId")

            if job_id:
                return self._poll_crawl_status(job_id)
            else:
                raise Exception("No job ID returned from crawl request")

        except Exception as e:
            logger.error(f"Failed to crawl website {url}: {str(e)}")
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }

    def _poll_crawl_status(self, job_id: str, max_attempts: int = 30) -> Dict[str, Any]:
        """Poll crawl job status"""
        for attempt in range(max_attempts):
            try:
                response = requests.get(
                    f"{self.base_url}/crawl/status/{job_id}",
                    headers=self.headers
                )
                response.raise_for_status()

                data = response.json()
                status = data.get("status")

                if status == "completed":
                    return {
                        "success": True,
                        "job_id": job_id,
                        "data": data.get("data", [])
                    }
                elif status == "failed":
                    return {
                        "success": False,
                        "job_id": job_id,
                        "error": data.get("error", "Crawl failed")
                    }

                time.sleep(2)  # Wait before next poll

            except Exception as e:
                logger.error(f"Error polling crawl status: {str(e)}")
                break

        return {
            "success": False,
            "job_id": job_id,
            "error": "Crawl timeout or polling failed"
        }

    def search_and_scrape(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Search for URLs and scrape them with retry logic"""
        for attempt in range(3):  # Retry up to 3 times
            try:
                payload = {
                    "query": query[:100],
                    "pageOptions": {
                        "onlyMainContent": True,
                        "includeHtml": False
                    },
                    "searchOptions": {
                        "limit": min(num_results, 10)
                    }
                }

                response = requests.post(
                    f"{self.base_url}/search",
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()

                data = response.json()
                results = []

                for item in data.get("data", []):
                    results.append({
                        "url": item.get("url", ""),
                        "title": item.get("title", ""),
                        "content": item.get("markdown", ""),
                        "metadata": item.get("metadata", {})
                    })

                logger.info(f"Successfully searched and scraped {len(results)} results for query: {query}")
                return results

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1} for query: {query}")
                if attempt < 2:
                    time.sleep(2 ** attempt)  # Exponential backoff

            except Exception as e:
                logger.error(f"Failed to search and scrape for query {query} on attempt {attempt + 1}: {str(e)}")
                if attempt < 2:
                    time.sleep(2 ** attempt)

        logger.error(f"All retry attempts failed for query: {query}")
        return []
