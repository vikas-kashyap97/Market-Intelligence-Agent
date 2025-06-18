import asyncio
import logging
from typing import Dict, List, Any
from core.agents.base_agent import BaseAgent
from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import JsonOutputParser
from config.settings import Settings

logger = logging.getLogger(__name__)

class StrategistAgent(BaseAgent):
    """Agent responsible for generating strategic recommendations and action plans"""
    
    def __init__(self):
        super().__init__(
            name="Strategist Agent",
            description="Generates strategic recommendations and actionable insights"
        )
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute strategic analysis and recommendation generation"""
        self.update_progress(10, "Initializing strategic analysis")
        
        # Get analysis results from Analyst Agent
        trends = input_data.get("market_trends", [])
        opportunities = input_data.get("opportunities", [])
        competitive_landscape = input_data.get("competitive_landscape", {})
        metrics = input_data.get("key_metrics", {})
        synthesis = input_data.get("analysis_synthesis", {})
        query = input_data.get("query", "")
        market_domain = input_data.get("market_domain", "")
        
        # Generate strategic recommendations concurrently
        tasks = [
            self._generate_strategic_recommendations(trends, opportunities, competitive_landscape, query, market_domain),
            self._create_action_plans(opportunities, trends, query, market_domain),
            self._assess_risks_and_mitigation(trends, opportunities, competitive_landscape),
            self._develop_success_metrics(opportunities, trends, market_domain)
        ]
        
        self.update_progress(40, "Generating strategic recommendations")
        
        recommendations, action_plans, risk_assessment, success_metrics = await asyncio.gather(*tasks)
        
        self.update_progress(80, "Creating strategic roadmap")
        
        # Create comprehensive strategic roadmap
        roadmap = await self._create_strategic_roadmap(
            recommendations, action_plans, risk_assessment, success_metrics, query, market_domain
        )
        
        self.update_progress(100, "Strategic analysis completed")
        
        return {
            "success": True,
            "strategic_recommendations": recommendations,
            "action_plans": action_plans,
            "risk_assessment": risk_assessment,
            "success_metrics": success_metrics,
            "strategic_roadmap": roadmap
        }
    
    async def _generate_strategic_recommendations(self, trends: List[Dict], opportunities: List[Dict], 
                                                competitive_landscape: Dict, query: str, market_domain: str) -> List[Dict[str, Any]]:
        """Generate strategic recommendations based on analysis"""
        try:
            llm = init_chat_model(Settings.LLM_MODEL, model_provider="google_genai")
            parser = JsonOutputParser()
            
            prompt = f"""
            Based on the market analysis for {query} in the {market_domain} sector, generate strategic recommendations.
            
            Market Trends: {trends[:5]}
            Opportunities: {opportunities[:5]}
            Competitive Landscape: {competitive_landscape}
            
            Return a JSON array of strategic recommendations:
            [
                {{
                    "strategy_title": "Clear, actionable strategy title",
                    "description": "Detailed description of the strategy",
                    "strategic_objective": "Primary objective this strategy achieves",
                    "priority_level": "High/Medium/Low",
                    "implementation_timeline": "Short-term/Medium-term/Long-term",
                    "resource_requirements": {{
                        "budget_estimate": "Budget range or estimate",
                        "team_size": "Estimated team size needed",
                        "key_skills": ["skill1", "skill2"],
                        "technology_stack": ["tech1", "tech2"]
                    }},
                    "expected_outcomes": {{
                        "revenue_impact": "Expected revenue impact",
                        "market_share_impact": "Expected market share impact",
                        "competitive_advantage": "Competitive advantage gained"
                    }},
                    "success_indicators": ["indicator1", "indicator2"],
                    "implementation_steps": [
                        {{
                            "step": "Step description",
                            "timeline": "Timeline for this step",
                            "dependencies": ["dependency1", "dependency2"]
                        }}
                    ]
                }}
            ]
            """
            
            chain = llm | parser
            recommendations = chain.invoke(prompt)
            
            if not isinstance(recommendations, list):
                recommendations = []
            
            # Enhance recommendations with additional metadata
            for rec in recommendations:
                rec["generated_timestamp"] = asyncio.get_event_loop().time()
                rec["confidence_score"] = self._calculate_recommendation_confidence(rec, trends, opportunities)
            
            logger.info(f"Generated {len(recommendations)} strategic recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate strategic recommendations: {str(e)}")
            return [{
                "strategy_title": "Market Entry Strategy",
                "description": "Develop a comprehensive market entry approach",
                "strategic_objective": "Establish market presence and capture market share",
                "priority_level": "High",
                "implementation_timeline": "Medium-term",
                "resource_requirements": {
                    "budget_estimate": "$100K - $500K",
                    "team_size": "5-10 people",
                    "key_skills": ["Market research", "Product development"],
                    "technology_stack": ["Analytics platform", "CRM system"]
                },
                "expected_outcomes": {
                    "revenue_impact": "Positive revenue growth",
                    "market_share_impact": "5-10% market share",
                    "competitive_advantage": "First-mover advantage"
                },
                "success_indicators": ["Revenue targets", "Customer acquisition"],
                "implementation_steps": [
                    {
                        "step": "Market research and validation",
                        "timeline": "1-2 months",
                        "dependencies": ["Budget approval", "Team assembly"]
                    }
                ]
            }]
    
    async def _create_action_plans(self, opportunities: List[Dict], trends: List[Dict], 
                                 query: str, market_domain: str) -> List[Dict[str, Any]]:
        """Create detailed action plans for top opportunities"""
        try:
            # Focus on top 3 opportunities
            top_opportunities = opportunities[:3]
            action_plans = []
            
            for opportunity in top_opportunities:
                llm = init_chat_model(Settings.LLM_MODEL, model_provider="google_genai")
                parser = JsonOutputParser()
                
                prompt = f"""
                Create a detailed action plan for the following opportunity in the {market_domain} sector:
                
                Opportunity: {opportunity}
                Market Context: {query}
                Relevant Trends: {trends[:3]}
                
                Return a JSON object with:
                {{
                    "opportunity_name": "Name of the opportunity",
                    "action_plan": {{
                        "phase_1": {{
                            "title": "Phase 1 title",
                            "duration": "Duration estimate",
                            "objectives": ["objective1", "objective2"],
                            "key_activities": ["activity1", "activity2"],
                            "deliverables": ["deliverable1", "deliverable2"],
                            "resources_needed": ["resource1", "resource2"],
                            "success_criteria": ["criteria1", "criteria2"]
                        }},
                        "phase_2": {{
                            "title": "Phase 2 title",
                            "duration": "Duration estimate",
                            "objectives": ["objective1", "objective2"],
                            "key_activities": ["activity1", "activity2"],
                            "deliverables": ["deliverable1", "deliverable2"],
                            "resources_needed": ["resource1", "resource2"],
                            "success_criteria": ["criteria1", "criteria2"]
                        }},
                        "phase_3": {{
                            "title": "Phase 3 title",
                            "duration": "Duration estimate",
                            "objectives": ["objective1", "objective2"],
                            "key_activities": ["activity1", "activity2"],
                            "deliverables": ["deliverable1", "deliverable2"],
                            "resources_needed": ["resource1", "resource2"],
                            "success_criteria": ["criteria1", "criteria2"]
                        }}
                    }},
                    "total_timeline": "Overall timeline estimate",
                    "budget_estimate": "Total budget estimate",
                    "risk_factors": ["risk1", "risk2"],
                    "contingency_plans": ["plan1", "plan2"]
                }}
                """
                
                chain = llm | parser
                action_plan = chain.invoke(prompt)
                
                if isinstance(action_plan, dict):
                    action_plans.append(action_plan)
            
            logger.info(f"Created {len(action_plans)} detailed action plans")
            return action_plans
            
        except Exception as e:
            logger.error(f"Failed to create action plans: {str(e)}")
            return []
    
    async def _assess_risks_and_mitigation(self, trends: List[Dict], opportunities: List[Dict], 
                                         competitive_landscape: Dict) -> Dict[str, Any]:
        """Assess risks and develop mitigation strategies"""
        try:
            llm = init_chat_model(Settings.LLM_MODEL, model_provider="google_genai")
            parser = JsonOutputParser()
            
            prompt = f"""
            Assess risks and develop mitigation strategies based on:
            
            Market Trends: {trends[:5]}
            Opportunities: {opportunities[:5]}
            Competitive Landscape: {competitive_landscape}
            
            Return a JSON object with:
            {{
                "market_risks": [
                    {{
                        "risk_name": "Risk name",
                        "description": "Risk description",
                        "probability": "High/Medium/Low",
                        "impact": "High/Medium/Low",
                        "risk_score": 1-10,
                        "mitigation_strategies": ["strategy1", "strategy2"],
                        "monitoring_indicators": ["indicator1", "indicator2"]
                    }}
                ],
                "competitive_risks": [
                    {{
                        "risk_name": "Risk name",
                        "description": "Risk description",
                        "probability": "High/Medium/Low",
                        "impact": "High/Medium/Low",
                        "risk_score": 1-10,
                        "mitigation_strategies": ["strategy1", "strategy2"],
                        "monitoring_indicators": ["indicator1", "indicator2"]
                    }}
                ],
                "operational_risks": [
                    {{
                        "risk_name": "Risk name",
                        "description": "Risk description",
                        "probability": "High/Medium/Low",
                        "impact": "High/Medium/Low",
                        "risk_score": 1-10,
                        "mitigation_strategies": ["strategy1", "strategy2"],
                        "monitoring_indicators": ["indicator1", "indicator2"]
                    }}
                ],
                "overall_risk_level": "High/Medium/Low",
                "risk_management_framework": "Description of risk management approach"
            }}
            """
            
            chain = llm | parser
            risk_assessment = chain.invoke(prompt)
            
            if not isinstance(risk_assessment, dict):
                risk_assessment = {}
            
            logger.info("Completed risk assessment and mitigation planning")
            return risk_assessment
            
        except Exception as e:
            logger.error(f"Failed to assess risks: {str(e)}")
            return {
                "market_risks": [],
                "competitive_risks": [],
                "operational_risks": [],
                "overall_risk_level": "Medium",
                "risk_management_framework": "Standard risk management practices recommended"
            }
    
    async def _develop_success_metrics(self, opportunities: List[Dict], trends: List[Dict], 
                                     market_domain: str) -> Dict[str, Any]:
        """Develop success metrics and KPIs"""
        try:
            llm = init_chat_model(Settings.LLM_MODEL, model_provider="google_genai")
            parser = JsonOutputParser()
            
            prompt = f"""
            Develop success metrics and KPIs for the {market_domain} market based on:
            
            Opportunities: {opportunities[:5]}
            Market Trends: {trends[:5]}
            
            Return a JSON object with:
            {{
                "financial_metrics": [
                    {{
                        "metric_name": "Metric name",
                        "description": "What this metric measures",
                        "target_value": "Target value or range",
                        "measurement_frequency": "How often to measure",
                        "data_source": "Where to get the data"
                    }}
                ],
                "market_metrics": [
                    {{
                        "metric_name": "Metric name",
                        "description": "What this metric measures",
                        "target_value": "Target value or range",
                        "measurement_frequency": "How often to measure",
                        "data_source": "Where to get the data"
                    }}
                ],
                "operational_metrics": [
                    {{
                        "metric_name": "Metric name",
                        "description": "What this metric measures",
                        "target_value": "Target value or range",
                        "measurement_frequency": "How often to measure",
                        "data_source": "Where to get the data"
                    }}
                ],
                "leading_indicators": ["indicator1", "indicator2"],
                "lagging_indicators": ["indicator1", "indicator2"],
                "dashboard_recommendations": "Recommendations for metric dashboards"
            }}
            """
            
            chain = llm | parser
            success_metrics = chain.invoke(prompt)
            
            if not isinstance(success_metrics, dict):
                success_metrics = {}
            
            logger.info("Developed success metrics and KPIs")
            return success_metrics
            
        except Exception as e:
            logger.error(f"Failed to develop success metrics: {str(e)}")
            return {
                "financial_metrics": [],
                "market_metrics": [],
                "operational_metrics": [],
                "leading_indicators": [],
                "lagging_indicators": [],
                "dashboard_recommendations": "Standard business metrics dashboard recommended"
            }
    
    async def _create_strategic_roadmap(self, recommendations: List[Dict], action_plans: List[Dict], 
                                      risk_assessment: Dict, success_metrics: Dict, 
                                      query: str, market_domain: str) -> Dict[str, Any]:
        """Create comprehensive strategic roadmap"""
        try:
            # Organize recommendations by priority and timeline
            high_priority = [r for r in recommendations if r.get("priority_level") == "High"]
            medium_priority = [r for r in recommendations if r.get("priority_level") == "Medium"]
            low_priority = [r for r in recommendations if r.get("priority_level") == "Low"]
            
            short_term = [r for r in recommendations if r.get("implementation_timeline") == "Short-term"]
            medium_term = [r for r in recommendations if r.get("implementation_timeline") == "Medium-term"]
            long_term = [r for r in recommendations if r.get("implementation_timeline") == "Long-term"]
            
            roadmap = {
                "executive_summary": f"Strategic roadmap for {query} in the {market_domain} market with {len(recommendations)} key recommendations",
                "strategic_priorities": {
                    "high_priority": high_priority,
                    "medium_priority": medium_priority,
                    "low_priority": low_priority
                },
                "timeline_view": {
                    "short_term": short_term,
                    "medium_term": medium_term,
                    "long_term": long_term
                },
                "implementation_sequence": self._create_implementation_sequence(recommendations),
                "resource_allocation": self._calculate_resource_allocation(recommendations),
                "milestone_schedule": self._create_milestone_schedule(recommendations, action_plans),
                "success_tracking": success_metrics,
                "risk_monitoring": risk_assessment,
                "review_schedule": {
                    "monthly_reviews": "Track short-term progress and adjust tactics",
                    "quarterly_reviews": "Assess strategic progress and resource allocation",
                    "annual_reviews": "Comprehensive strategy review and roadmap updates"
                }
            }
            
            logger.info("Created comprehensive strategic roadmap")
            return roadmap
            
        except Exception as e:
            logger.error(f"Failed to create strategic roadmap: {str(e)}")
            return {
                "executive_summary": f"Strategic roadmap for {market_domain} market analysis",
                "strategic_priorities": {"high_priority": [], "medium_priority": [], "low_priority": []},
                "timeline_view": {"short_term": [], "medium_term": [], "long_term": []},
                "implementation_sequence": [],
                "resource_allocation": {},
                "milestone_schedule": [],
                "success_tracking": {},
                "risk_monitoring": {},
                "review_schedule": {}
            }
    
    def _calculate_recommendation_confidence(self, recommendation: Dict, trends: List[Dict], opportunities: List[Dict]) -> float:
        """Calculate confidence score for a recommendation"""
        try:
            # Simple confidence calculation based on data availability and alignment
            base_confidence = 0.7
            
            # Boost confidence if recommendation aligns with multiple trends
            trend_alignment = sum(1 for trend in trends if any(
                keyword in recommendation.get("description", "").lower() 
                for keyword in trend.get("description", "").lower().split()[:5]
            ))
            
            # Boost confidence if recommendation addresses high-impact opportunities
            opportunity_alignment = sum(1 for opp in opportunities if 
                                      opp.get("revenue_potential") == "High" and
                                      any(keyword in recommendation.get("description", "").lower() 
                                          for keyword in opp.get("description", "").lower().split()[:5]))
            
            confidence_boost = min(0.3, (trend_alignment + opportunity_alignment) * 0.05)
            return min(1.0, base_confidence + confidence_boost)
            
        except:
            return 0.7
    
    def _create_implementation_sequence(self, recommendations: List[Dict]) -> List[Dict]:
        """Create optimal implementation sequence"""
        try:
            # Sort by priority and dependencies
            sequence = []
            for i, rec in enumerate(recommendations):
                sequence.append({
                    "sequence_number": i + 1,
                    "strategy_title": rec.get("strategy_title", ""),
                    "priority_level": rec.get("priority_level", "Medium"),
                    "dependencies": rec.get("implementation_steps", [{}])[0].get("dependencies", []),
                    "estimated_duration": rec.get("implementation_timeline", "Medium-term")
                })
            
            return sequence
        except:
            return []
    
    def _calculate_resource_allocation(self, recommendations: List[Dict]) -> Dict[str, Any]:
        """Calculate resource allocation across recommendations"""
        try:
            total_budget = 0
            total_team_size = 0
            skill_requirements = {}
            
            for rec in recommendations:
                resources = rec.get("resource_requirements", {})
                
                # Extract budget (simple parsing)
                budget_str = resources.get("budget_estimate", "0")
                try:
                    import re
                    budget_numbers = re.findall(r'\d+', budget_str.replace(',', ''))
                    if budget_numbers:
                        total_budget += int(budget_numbers[-1]) * 1000  # Assume thousands
                except:
                    pass
                
                # Extract team size
                team_str = resources.get("team_size", "0")
                try:
                    team_numbers = re.findall(r'\d+', team_str)
                    if team_numbers:
                        total_team_size += int(team_numbers[-1])
                except:
                    pass
                
                # Collect skills
                skills = resources.get("key_skills", [])
                for skill in skills:
                    skill_requirements[skill] = skill_requirements.get(skill, 0) + 1
            
            return {
                "total_budget_estimate": f"${total_budget:,}",
                "total_team_size": total_team_size,
                "top_skills_needed": sorted(skill_requirements.items(), key=lambda x: x[1], reverse=True)[:5],
                "resource_distribution": "Balanced across strategic priorities"
            }
        except:
            return {
                "total_budget_estimate": "To be determined",
                "total_team_size": "To be determined",
                "top_skills_needed": [],
                "resource_distribution": "Resource planning needed"
            }
    
    def _create_milestone_schedule(self, recommendations: List[Dict], action_plans: List[Dict]) -> List[Dict]:
        """Create milestone schedule"""
        try:
            milestones = []
            
            for i, rec in enumerate(recommendations[:5]):  # Top 5 recommendations
                milestones.append({
                    "milestone_name": f"Complete {rec.get('strategy_title', f'Strategy {i+1}')}",
                    "target_date": "To be determined based on start date",
                    "success_criteria": rec.get("success_indicators", []),
                    "dependencies": [],
                    "responsible_team": "Strategy implementation team"
                })
            
            return milestones
        except:
            return []
