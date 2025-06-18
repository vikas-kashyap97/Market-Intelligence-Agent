import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from config.settings import Settings
from core.state import MarketIntelligenceState

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Handle all database operations"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Settings.DATABASE_PATH
        self.init_db()
    
    def init_db(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute('''
                    CREATE TABLE IF NOT EXISTS states (
                        id TEXT PRIMARY KEY,
                        market_domain TEXT,
                        query TEXT,
                        state_data TEXT,
                        created_at TIMESTAMP
                    )
                ''')
                c.execute('''
                    CREATE TABLE IF NOT EXISTS chat_history (
                        session_id TEXT,
                        message_type TEXT,
                        content TEXT,
                        timestamp TIMESTAMP,
                        PRIMARY KEY (session_id, timestamp)
                    )
                ''')
                conn.commit()
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise

    def save_state(self, state: MarketIntelligenceState):
        """Save state to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute(
                    'INSERT OR REPLACE INTO states (id, market_domain, query, state_data, created_at) VALUES (?, ?, ?, ?, ?)',
                    (state.state_id, state.market_domain, state.query, json.dumps(state.dict()), datetime.now())
                )
                conn.commit()
                logger.info(f"State saved: {state.state_id}")
        except Exception as e:
            logger.error(f"Failed to save state {state.state_id}: {str(e)}")
            raise

    def load_state(self, state_id: str) -> Optional[MarketIntelligenceState]:
        """Load state from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute('SELECT state_data FROM states WHERE id = ?', (state_id,))
                result = c.fetchone()
                if result:
                    return MarketIntelligenceState(**json.loads(result[0]))
                return None
        except Exception as e:
            logger.error(f"Failed to load state {state_id}: {str(e)}")
            return None

    def get_all_states(self) -> List[Dict[str, Any]]:
        """Get all saved states"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute('SELECT id, market_domain, query, created_at FROM states ORDER BY created_at DESC')
                return [
                    {
                        "id": row[0],
                        "market_domain": row[1],
                        "query": row[2] or "N/A",
                        "created_at": row[3]
                    }
                    for row in c.fetchall()
                ]
        except Exception as e:
            logger.error(f"Failed to get states: {str(e)}")
            return []

    def save_chat_message(self, session_id: str, message_type: str, content: str):
        """Save chat message to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute(
                    'INSERT INTO chat_history (session_id, message_type, content, timestamp) VALUES (?, ?, ?, ?)',
                    (session_id, message_type, content, datetime.now())
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save chat message: {str(e)}")

    def load_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Load chat history from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute('SELECT message_type, content FROM chat_history WHERE session_id = ? ORDER BY timestamp', (session_id,))
                return [{"type": row[0], "content": row[1]} for row in c.fetchall()]
        except Exception as e:
            logger.error(f"Failed to load chat history: {str(e)}")
            return []
