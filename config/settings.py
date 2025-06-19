import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Existing API Keys
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    
    # New API Keys
    FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
    NEWSDATA_IO_KEY = os.getenv("NEWSDATA_IO_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    NOTION_API_KEY = os.getenv("NOTION_API_KEY")  # Optional
    
    USER_AGENT = os.getenv("USER_AGENT", "MarketIntelligenceAgent/2.0")
    
    # Database
    DATABASE_PATH = "market_intelligence.db"
    
    # Directories
    REPORTS_DIR = "reports"
    ASSETS_DIR = "assets"
    EXPORTS_DIR = "exports"
    
    # Model Settings
    LLM_MODEL = "gemini-2.0-flash"
    GROQ_MODEL = "llama3-8b-8192"
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Cache Settings
    SEARCH_CACHE_SIZE = 100
    SEARCH_CACHE_TTL = 3600
    
    # Agent Settings
    MAX_CONCURRENT_AGENTS = 4
    AGENT_TIMEOUT = 300  # 5 minutes
    
    # Export Settings
    PDF_TEMPLATE = "modern"
    DOCX_TEMPLATE = "professional"
    
    # Logging
    LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    LOG_LEVEL = "INFO"
    
    @classmethod
    def validate(cls):
        """Validate required environment variables"""
        required_vars = ["GOOGLE_API_KEY", "TAVILY_API_KEY"]
        optional_vars = ["FIRECRAWL_API_KEY", "NEWSDATA_IO_KEY", "GROQ_API_KEY"]
        
        missing_required = [var for var in required_vars if not getattr(cls, var)]
        if missing_required:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_required)}")
        
        missing_optional = [var for var in optional_vars if not getattr(cls, var)]
        if missing_optional:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Missing optional environment variables (some features may be limited): {', '.join(missing_optional)}")
        
        return True
