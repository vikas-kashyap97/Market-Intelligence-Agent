from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Any, Optional
from uuid import uuid4
import re

class MarketIntelligenceState(BaseModel):
    """State management for market intelligence workflow"""
    raw_news_data: List[Dict[str, Any]] = Field(default_factory=list)
    competitor_data: List[Dict[str, Any]] = Field(default_factory=list)
    market_trends: List[Dict[str, Any]] = Field(default_factory=list)
    opportunities: List[Dict[str, Any]] = Field(default_factory=list)
    strategic_recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    market_domain: str = "EdTech"
    query: Optional[str] = None
    question: Optional[str] = None
    query_response: Optional[str] = None
    report_template: Optional[str] = None
    vector_store_path: Optional[str] = None
    state_id: str = Field(default_factory=lambda: str(uuid4()))
    report_dir: Optional[str] = None

    @field_validator('market_domain')
    @classmethod
    def validate_market_domain(cls, v):
        if not re.match(r'^[a-zA-Z0-9\s\-]+$', v):
            raise ValueError("Market domain must contain only letters, numbers, spaces, or hyphens")
        return v.strip()

    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        if v and len(v.strip()) < 5:
            raise ValueError("Query must be at least 5 characters long")
        return v.strip() if v else v
