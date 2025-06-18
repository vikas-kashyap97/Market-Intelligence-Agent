import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.status = AgentStatus.IDLE
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.progress = 0
        self.current_task = ""
        self.results: Dict[str, Any] = {}
        
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's main task"""
        pass
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the agent with error handling and status tracking"""
        try:
            self.status = AgentStatus.RUNNING
            self.start_time = datetime.now()
            self.progress = 0
            self.error_message = None
            
            logger.info(f"Agent {self.name} started execution")
            
            # Execute the main task
            results = await self.execute(input_data)
            
            self.results = results
            self.status = AgentStatus.COMPLETED
            self.progress = 100
            self.end_time = datetime.now()
            
            logger.info(f"Agent {self.name} completed successfully")
            return results
            
        except asyncio.CancelledError:
            self.status = AgentStatus.CANCELLED
            self.end_time = datetime.now()
            logger.warning(f"Agent {self.name} was cancelled")
            raise
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            self.error_message = str(e)
            self.end_time = datetime.now()
            logger.error(f"Agent {self.name} failed: {str(e)}")
            
            return {
                "success": False,
                "error": str(e),
                "agent": self.name
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        duration = None
        if self.start_time:
            end = self.end_time or datetime.now()
            duration = (end - self.start_time).total_seconds()
        
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "progress": self.progress,
            "current_task": self.current_task,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": duration,
            "error_message": self.error_message
        }
    
    def update_progress(self, progress: int, task: str = ""):
        """Update agent progress"""
        self.progress = min(100, max(0, progress))
        if task:
            self.current_task = task
        logger.debug(f"Agent {self.name} progress: {self.progress}% - {task}")
