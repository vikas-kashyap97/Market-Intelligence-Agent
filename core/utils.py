import os
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
import re

logger = logging.getLogger(__name__)

def safe_json_loads(data: str, default=None):
    """Safely load JSON data"""
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse JSON: {str(e)}")
        return default or {}

def safe_json_dumps(data: Any, indent=2) -> str:
    """Safely dump data to JSON"""
    try:
        return json.dumps(data, indent=indent, ensure_ascii=False)
    except (TypeError, ValueError) as e:
        logger.warning(f"Failed to serialize JSON: {str(e)}")
        return "{}"

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    return re.sub(r'[^a-zA-Z0-9_-]', '_', filename.lower().replace(' ', '_'))

def ensure_dir_exists(directory: str) -> bool:
    """Ensure directory exists, create if it doesn't"""
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {directory}: {str(e)}")
        return False

def get_file_size_mb(file_path: str) -> float:
    """Get file size in MB"""
    try:
        return os.path.getsize(file_path) / (1024 * 1024)
    except Exception:
        return 0.0

def format_timestamp(timestamp: datetime = None) -> str:
    """Format timestamp for display"""
    if timestamp is None:
        timestamp = datetime.now()
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def extract_key_metrics(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract key metrics from data for display"""
    if not data:
        return {"total": 0, "summary": "No data available"}
    
    return {
        "total": len(data),
        "summary": f"{len(data)} items processed",
        "sample": data[0] if data else None
    }
