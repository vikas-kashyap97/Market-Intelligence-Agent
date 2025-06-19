import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from core.agents.reader_agent import ReaderAgent
from core.agents.analyst_agent import AnalystAgent
from core.agents.strategist_agent import StrategistAgent
from core.agents.formatter_agent import FormatterAgent
from core.agents.base_agent import AgentStatus

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """Orchestrates the multi-agent workflow for market intelligence"""

    def __init__(self):
        self.agents = {
            "reader": ReaderAgent(),
            "analyst": AnalystAgent(),
            "strategist": StrategistAgent(),
            "formatter": FormatterAgent()
        }
        self.workflow_status = "idle"
        self.current_step = ""
        self.progress = 0
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.results: Dict[str, Any] = {}
        
    async def run_intelligence_workflow(self, query: str, market_domain: str, 
                                      question: Optional[str] = None) -> Dict[str, Any]:
        """Run the complete market intelligence workflow"""
        try:
            self.workflow_status = "running"
            self.start_time = datetime.now()
            self.progress = 0
            
            logger.info(f"Starting market intelligence workflow for {market_domain}: {query}")
            
            # Prepare initial input data
            input_data = {
                "query": query,
                "market_domain": market_domain,
                "question": question
            }
            
            # Step 1: Reader Agent - Data Collection
            self.current_step = "Data Collection"
            self.progress = 10
            logger.info("Step 1: Running Reader Agent")
            
            reader_results = await self.agents["reader"].run(input_data)
            if not reader_results.get("success"):
                raise Exception(f"Reader Agent failed: {reader_results.get('error')}")
            
            # Merge results for next step
            input_data.update(reader_results)
            
            # Step 2: Analyst Agent - Data Analysis
            self.current_step = "Data Analysis"
            self.progress = 35
            logger.info("Step 2: Running Analyst Agent")
            
            analyst_results = await self.agents["analyst"].run(input_data)
            if not analyst_results.get("success"):
                raise Exception(f"Analyst Agent failed: {analyst_results.get('error')}")
            
            # Merge results for next step
            input_data.update(analyst_results)
            
            # Step 3: Strategist Agent - Strategic Planning
            self.current_step = "Strategic Planning"
            self.progress = 65
            logger.info("Step 3: Running Strategist Agent")
            
            strategist_results = await self.agents["strategist"].run(input_data)
            if not strategist_results.get("success"):
                raise Exception(f"Strategist Agent failed: {strategist_results.get('error')}")
            
            # Merge results for next step
            input_data.update(strategist_results)
            
            # Step 4: Formatter Agent - Report Generation
            self.current_step = "Report Generation"
            self.progress = 85
            logger.info("Step 4: Running Formatter Agent")
            
            formatter_results = await self.agents["formatter"].run(input_data)
            if not formatter_results.get("success"):
                raise Exception(f"Formatter Agent failed: {formatter_results.get('error')}")
            
            # Compile final results
            self.progress = 100
            self.current_step = "Completed"
            self.workflow_status = "completed"
            self.end_time = datetime.now()
            
            final_results = {
                "success": True,
                "workflow_id": f"workflow_{int(self.start_time.timestamp())}",
                "state_id": f"workflow_{int(self.start_time.timestamp())}",  # Add state_id
                "query": query,
                "market_domain": market_domain,
                "question": question,
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                "duration": (self.end_time - self.start_time).total_seconds(),
                
                # Data from Reader Agent
                "data_sources": reader_results.get("total_sources", 0),
                "web_content": reader_results.get("web_content", []),
                "news_data": reader_results.get("news_data", []),
                "processed_data": reader_results.get("processed_data", {}),
                
                # Data from Analyst Agent
                "market_trends": analyst_results.get("market_trends", []),
                "opportunities": analyst_results.get("opportunities", []),
                "competitive_landscape": analyst_results.get("competitive_landscape", {}),
                "key_metrics": analyst_results.get("key_metrics", {}),
                "analysis_synthesis": analyst_results.get("analysis_synthesis", {}),
                
                # Data from Strategist Agent
                "strategic_recommendations": strategist_results.get("strategic_recommendations", []),
                "action_plans": strategist_results.get("action_plans", []),
                "risk_assessment": strategist_results.get("risk_assessment", {}),
                "success_metrics": strategist_results.get("success_metrics", {}),
                "strategic_roadmap": strategist_results.get("strategic_roadmap", {}),
                
                # Data from Formatter Agent
                "report_dir": formatter_results.get("report_dir", ""),
                "chart_files": formatter_results.get("chart_files", []),
                "report_content": formatter_results.get("report_content", ""),
                "dashboard_data": formatter_results.get("dashboard_data", {}),
                "export_files": formatter_results.get("export_files", {})
            }
            
            self.results = final_results
            
            # Save to database
            await self._save_analysis_to_history(final_results)
            
            logger.info(f"Workflow completed successfully in {final_results['duration']:.2f} seconds")
            return final_results
            
        except Exception as e:
            self.workflow_status = "failed"
            self.end_time = datetime.now()
            error_message = str(e)
            
            logger.error(f"Workflow failed: {error_message}")
            
            return {
                "success": False,
                "error": error_message,
                "workflow_id": f"workflow_{int(self.start_time.timestamp()) if self.start_time else 0}",
                "state_id": f"workflow_{int(self.start_time.timestamp()) if self.start_time else 0}",
                "query": query,
                "market_domain": market_domain,
                "question": question,
                "failed_step": self.current_step,
                "progress": self.progress
            }

    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status"""
        agent_statuses = {}
        for name, agent in self.agents.items():
            agent_statuses[name] = agent.get_status()
        
        duration = None
        if self.start_time:
            end = self.end_time or datetime.now()
            duration = (end - self.start_time).total_seconds()
        
        return {
            "workflow_status": self.workflow_status,
            "current_step": self.current_step,
            "progress": self.progress,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": duration,
            "agent_statuses": agent_statuses
        }

    async def cancel_workflow(self):
        """Cancel the running workflow"""
        try:
            self.workflow_status = "cancelling"
            
            # Cancel all running agents
            for agent in self.agents.values():
                if agent.status == AgentStatus.RUNNING:
                    # This would cancel the agent's tasks
                    agent.status = AgentStatus.CANCELLED
            
            self.workflow_status = "cancelled"
            self.end_time = datetime.now()
            
            logger.info("Workflow cancelled successfully")
            
        except Exception as e:
            logger.error(f"Failed to cancel workflow: {str(e)}")

    def get_agent_logs(self, agent_name: str) -> List[str]:
        """Get logs for a specific agent"""
        # This would return agent-specific logs
        # For now, return a placeholder
        return [f"Log entry for {agent_name}"]

    async def run_single_agent(self, agent_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single agent for testing or debugging"""
        if agent_name not in self.agents:
            return {"success": False, "error": f"Agent {agent_name} not found"}
        
        try:
            logger.info(f"Running single agent: {agent_name}")
            result = await self.agents[agent_name].run(input_data)
            logger.info(f"Single agent {agent_name} completed")
            return result
            
        except Exception as e:
            logger.error(f"Single agent {agent_name} failed: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _save_analysis_to_history(self, results: Dict[str, Any]):
        """Save completed analysis to history database"""
        try:
            from core.db import DatabaseManager
            from core.state import MarketIntelligenceState
            
            # Create a state object from results
            state = MarketIntelligenceState(
                state_id=results.get("state_id", results.get("workflow_id", "unknown")),
                query=results.get("query", ""),
                market_domain=results.get("market_domain", ""),
                question=results.get("question", ""),
                report_dir=results.get("report_dir", ""),
                market_trends=results.get("market_trends", []),
                opportunities=results.get("opportunities", []),
                strategic_recommendations=results.get("strategic_recommendations", [])
            )
            
            db = DatabaseManager()
            success = db.save_state(state)
            
            if success:
                logger.info(f"Analysis {state.state_id[:8]} saved to history")
            else:
                logger.error(f"Failed to save analysis {state.state_id[:8]} to history")
                
        except Exception as e:
            logger.error(f"Error saving analysis to history: {str(e)}")
