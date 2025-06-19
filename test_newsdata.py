"""Test script for NewsData.io integration"""
import os
import sys
import logging
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_newsdata_integration():
    """Test NewsData.io integration"""
    try:
        from core.integrations.newsdata_client import NewsDataClient
        from config.settings import Settings
        
        # Check if API key is available
        if not Settings.NEWSDATA_IO_KEY:
            logger.error("NEWSDATA_IO_KEY not found in environment variables")
            return False
        
        logger.info(f"Testing NewsData.io with API key: {Settings.NEWSDATA_IO_KEY[:10]}...")
        
        # Initialize client
        client = NewsDataClient()
        
        # Test 1: Get latest news with a simple query
        logger.info("Test 1: Getting latest news with query 'technology'")
        news = client.get_latest_news("technology", size=5)
        
        if news:
            logger.info(f"✅ Successfully retrieved {len(news)} articles")
            for i, article in enumerate(news[:2], 1):
                logger.info(f"  Article {i}: {article.get('title', 'No title')[:50]}...")
        else:
            logger.warning("❌ No news articles retrieved")
        
        # Test 2: Get trending topics
        logger.info("Test 2: Getting trending topics")
        trending = client.get_trending_topics(size=5)
        
        if trending:
            logger.info(f"✅ Successfully retrieved {len(trending)} trending topics")
            for i, topic in enumerate(trending[:3], 1):
                logger.info(f"  Topic {i}: {topic.get('topic', 'Unknown')} (freq: {topic.get('frequency', 0)})")
        else:
            logger.warning("❌ No trending topics retrieved")
        
        # Test 3: Get news sources
        logger.info("Test 3: Getting news sources")
        sources = client.get_news_sources(language="en")
        
        if sources:
            logger.info(f"✅ Successfully retrieved {len(sources)} news sources")
        else:
            logger.warning("❌ No news sources retrieved")
        
        return len(news) > 0 or len(trending) > 0 or len(sources) > 0
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting NewsData.io integration test...")
    success = test_newsdata_integration()
    
    if success:
        logger.info("✅ NewsData.io integration test completed successfully!")
    else:
        logger.error("❌ NewsData.io integration test failed!")
        
    logger.info("Test completed.")
