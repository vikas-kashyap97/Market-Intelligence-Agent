import asyncio
import logging
import os
from typing import Dict, List, Any
from datetime import datetime
from core.agents.base_agent import BaseAgent
from core.charts import IntelligentChartGenerator
from core.export.report_exporter import ReportExporter
from config.settings import Settings

logger = logging.getLogger(__name__)

class FormatterAgent(BaseAgent):
    """Agent responsible for formatting reports, charts, and export layouts"""
    
    def __init__(self):
        super().__init__(
            name="Formatter Agent",
            description="Formats charts, reports, and handles export functionality"
        )
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute formatting and export tasks"""
        self.update_progress(10, "Initializing report formatting")
        
        # Get all analysis results
        trends = input_data.get("market_trends", [])
        opportunities = input_data.get("opportunities", [])
        competitive_landscape = input_data.get("competitive_landscape", {})
        recommendations = input_data.get("strategic_recommendations", [])
        action_plans = input_data.get("action_plans", [])
        risk_assessment = input_data.get("risk_assessment", {})
        success_metrics = input_data.get("success_metrics", {})
        roadmap = input_data.get("strategic_roadmap", {})
        query = input_data.get("query", "")
        market_domain = input_data.get("market_domain", "")
        
        # Create report directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        report_dir = os.path.join(Settings.REPORTS_DIR, f"report_{timestamp}")
        os.makedirs(report_dir, exist_ok=True)
        
        # Execute formatting tasks concurrently
        tasks = [
            self._generate_charts(trends, opportunities, recommendations, report_dir, query, market_domain),
            self._format_report_content(trends, opportunities, competitive_landscape, recommendations, roadmap, query, market_domain),
            self._create_dashboard_data(trends, opportunities, recommendations, success_metrics)
        ]
        
        self.update_progress(40, "Generating charts and formatting content")
        
        chart_files, report_content, dashboard_data = await asyncio.gather(*tasks)
        
        self.update_progress(70, "Creating export files")
        
        # Create export files
        export_files = await self._create_export_files(
            report_content, chart_files, dashboard_data, report_dir, query, market_domain
        )
        
        self.update_progress(100, "Formatting completed")
        
        return {
            "success": True,
            "report_dir": report_dir,
            "chart_files": chart_files,
            "report_content": report_content,
            "dashboard_data": dashboard_data,
            "export_files": export_files
        }
    
    async def _generate_charts(self, trends: List[Dict], opportunities: List[Dict], 
                             recommendations: List[Dict], report_dir: str, 
                             query: str, market_domain: str) -> List[str]:
        """Generate intelligent charts based on analysis results"""
        try:
            chart_gen = IntelligentChartGenerator(report_dir)
            
            chart_data = {
                "query": query,
                "market_domain": market_domain,
                "market_trends": trends,
                "opportunities": opportunities,
                "strategic_recommendations": recommendations
            }
            
            chart_files = chart_gen.generate_contextual_charts(chart_data)
            
            logger.info(f"Generated {len(chart_files)} charts")
            return chart_files
            
        except Exception as e:
            logger.error(f"Failed to generate charts: {str(e)}")
            return []
    
    async def _format_report_content(self, trends: List[Dict], opportunities: List[Dict], 
                                   competitive_landscape: Dict, recommendations: List[Dict], 
                                   roadmap: Dict, query: str, market_domain: str) -> str:
        """Format comprehensive report content"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            report_content = f"""# Market Intelligence Report: {market_domain}

## Executive Summary
This comprehensive market intelligence report analyzes **{query}** in the {market_domain} sector. Our analysis identified {len(trends)} key market trends, {len(opportunities)} strategic opportunities, and {len(recommendations)} actionable recommendations.

## Market Trends Analysis
{self._format_trends_section(trends)}

## Strategic Opportunities
{self._format_opportunities_section(opportunities)}

## Competitive Landscape
{self._format_competitive_section(competitive_landscape)}

## Strategic Recommendations
{self._format_recommendations_section(recommendations)}

## Strategic Roadmap
{self._format_roadmap_section(roadmap)}

## Implementation Guidelines
{self._format_implementation_section(recommendations)}

---
*Report generated on {timestamp} by Market Intelligence Agent v2.0*
*Query: {query} | Market: {market_domain}*
"""
            
            logger.info("Formatted comprehensive report content")
            return report_content
            
        except Exception as e:
            logger.error(f"Failed to format report content: {str(e)}")
            return f"# Market Intelligence Report: {market_domain}\n\nReport generation encountered an error."
    
    async def _create_dashboard_data(self, trends: List[Dict], opportunities: List[Dict], 
                                   recommendations: List[Dict], success_metrics: Dict) -> Dict[str, Any]:
        """Create data structure for interactive dashboard"""
        try:
            dashboard_data = {
                "summary_metrics": {
                    "total_trends": len(trends),
                    "total_opportunities": len(opportunities),
                    "total_recommendations": len(recommendations),
                    "high_priority_items": len([r for r in recommendations if r.get("priority_level") == "High"])
                },
                "trend_data": self._prepare_trend_data(trends),
                "opportunity_data": self._prepare_opportunity_data(opportunities),
                "recommendation_data": self._prepare_recommendation_data(recommendations),
                "timeline_data": self._prepare_timeline_data(recommendations),
                "risk_data": self._prepare_risk_data(recommendations),
                "success_metrics": success_metrics
            }
            
            logger.info("Created dashboard data structure")
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Failed to create dashboard data: {str(e)}")
            return {}
    
    async def _create_export_files(self, report_content: str, chart_files: List[str], 
                                 dashboard_data: Dict, report_dir: str, 
                                 query: str, market_domain: str) -> Dict[str, str]:
        """Create various export file formats"""
        try:
            exporter = ReportExporter(report_dir)
            export_files = {}
            
            # Save markdown report
            md_file = os.path.join(report_dir, f"{market_domain.lower().replace(' ', '_')}_report.md")
            with open(md_file, "w", encoding="utf-8") as f:
                f.write(report_content)
            export_files["markdown"] = md_file
            
            # Create PDF export
            try:
                pdf_file = await exporter.export_to_pdf(report_content, chart_files, f"{market_domain} Market Intelligence Report")
                export_files["pdf"] = pdf_file
            except Exception as e:
                logger.warning(f"PDF export failed: {str(e)}")
            
            # Create DOCX export
            try:
                docx_file = await exporter.export_to_docx(report_content, chart_files, f"{market_domain} Market Intelligence Report")
                export_files["docx"] = docx_file
            except Exception as e:
                logger.warning(f"DOCX export failed: {str(e)}")
            
            # Save dashboard data as JSON
            json_file = os.path.join(report_dir, "dashboard_data.json")
            import json
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
            export_files["json"] = json_file
            
            logger.info(f"Created {len(export_files)} export files")
            return export_files
            
        except Exception as e:
            logger.error(f"Failed to create export files: {str(e)}")
            return {}
    
    def _format_trends_section(self, trends: List[Dict]) -> str:
        """Format trends section"""
        if not trends:
            return "No significant trends identified in the current analysis."
        
        formatted = []
        for i, trend in enumerate(trends, 1):
            formatted.append(f"""### {i}. {trend.get('trend_name', 'Unnamed Trend')}

**Impact Level:** {trend.get('impact_level', 'Unknown')} | **Timeframe:** {trend.get('timeframe', 'Unknown')} | **Confidence:** {trend.get('confidence_score', 0.7):.1%}

{trend.get('description', 'No description available.')}

**Key Drivers:**
{chr(10).join([f"- {driver}" for driver in trend.get('key_drivers', [])])}

**Supporting Evidence:**
{chr(10).join([f"- {evidence}" for evidence in trend.get('supporting_evidence', [])])}

---""")
        
        return "\n\n".join(formatted)
    
    def _format_opportunities_section(self, opportunities: List[Dict]) -> str:
        """Format opportunities section"""
        if not opportunities:
            return "No specific opportunities identified in the current analysis."
        
        formatted = []
        for i, opp in enumerate(opportunities, 1):
            formatted.append(f"""### {i}. {opp.get('opportunity_name', 'Unnamed Opportunity')}

**Revenue Potential:** {opp.get('revenue_potential', 'Unknown')} | **Implementation:** {opp.get('implementation_difficulty', 'Unknown')} | **Time to Market:** {opp.get('time_to_market', 'Unknown')}

{opp.get('description', 'No description available.')}

**Target Segment:** {opp.get('target_segment', 'Not specified')}

**Key Requirements:**
{chr(10).join([f"- {req}" for req in opp.get('key_requirements', [])])}

**Competitive Advantage:** {opp.get('competitive_advantage', 'Not specified')}

---""")
        
        return "\n\n".join(formatted)
    
    def _format_competitive_section(self, competitive_landscape: Dict) -> str:
        """Format competitive landscape section"""
        if not competitive_landscape:
            return "Competitive landscape analysis not available."
        
        formatted = [f"**Market Concentration:** {competitive_landscape.get('market_concentration', 'Unknown')}"]
        formatted.append(f"**Competitive Intensity:** {competitive_landscape.get('competitive_intensity', 'Unknown')}")
        
        leaders = competitive_landscape.get('market_leaders', [])
        if leaders:
            formatted.append("\n### Market Leaders")
            for leader in leaders:
                formatted.append(f"- **{leader.get('company_name', 'Unknown')}**: {leader.get('recent_developments', 'No recent developments')}")
        
        emerging = competitive_landscape.get('emerging_players', [])
        if emerging:
            formatted.append("\n### Emerging Players")
            for player in emerging:
                formatted.append(f"- **{player.get('company_name', 'Unknown')}**: {player.get('competitive_edge', 'No competitive edge specified')}")
        
        barriers = competitive_landscape.get('barriers_to_entry', [])
        if barriers:
            formatted.append("\n### Barriers to Entry")
            formatted.extend([f"- {barrier}" for barrier in barriers])
        
        return "\n".join(formatted)
    
    def _format_recommendations_section(self, recommendations: List[Dict]) -> str:
        """Format recommendations section"""
        if not recommendations:
            return "No strategic recommendations generated."
        
        formatted = []
        for i, rec in enumerate(recommendations, 1):
            formatted.append(f"""### {i}. {rec.get('strategy_title', 'Unnamed Strategy')}

**Priority:** {rec.get('priority_level', 'Unknown')} | **Timeline:** {rec.get('implementation_timeline', 'Unknown')}

{rec.get('description', 'No description available.')}

**Strategic Objective:** {rec.get('strategic_objective', 'Not specified')}

**Expected Outcomes:**
- **Revenue Impact:** {rec.get('expected_outcomes', {}).get('revenue_impact', 'Not specified')}
- **Market Share Impact:** {rec.get('expected_outcomes', {}).get('market_share_impact', 'Not specified')}
- **Competitive Advantage:** {rec.get('expected_outcomes', {}).get('competitive_advantage', 'Not specified')}

**Resource Requirements:**
- **Budget:** {rec.get('resource_requirements', {}).get('budget_estimate', 'Not specified')}
- **Team Size:** {rec.get('resource_requirements', {}).get('team_size', 'Not specified')}
- **Key Skills:** {', '.join(rec.get('resource_requirements', {}).get('key_skills', []))}

**Success Indicators:**
{chr(10).join([f"- {indicator}" for indicator in rec.get('success_indicators', [])])}

---""")
        
        return "\n\n".join(formatted)
    
    def _format_roadmap_section(self, roadmap: Dict) -> str:
        """Format strategic roadmap section"""
        if not roadmap:
            return "Strategic roadmap not available."
        
        formatted = [roadmap.get('executive_summary', 'No executive summary available.')]
        
        timeline_view = roadmap.get('timeline_view', {})
        if timeline_view:
            formatted.append("\n### Implementation Timeline")
            
            for timeframe, items in timeline_view.items():
                if items:
                    formatted.append(f"\n**{timeframe.replace('_', ' ').title()}:**")
                    for item in items:
                        formatted.append(f"- {item.get('strategy_title', 'Unnamed strategy')}")
        
        return "\n".join(formatted)
    
    def _format_implementation_section(self, recommendations: List[Dict]) -> str:
        """Format implementation guidelines section"""
        if not recommendations:
            return "No implementation guidelines available."
        
        formatted = ["### Getting Started"]
        formatted.append("1. **Prioritize High-Impact Initiatives**: Focus on high-priority recommendations first")
        formatted.append("2. **Secure Resources**: Ensure adequate budget and team allocation")
        formatted.append("3. **Establish Metrics**: Set up tracking for success indicators")
        formatted.append("4. **Create Timeline**: Develop detailed implementation schedule")
        formatted.append("5. **Monitor Progress**: Regular reviews and adjustments")
        
        formatted.append("\n### Next Steps")
        formatted.append("- Review and validate recommendations with stakeholders")
        formatted.append("- Develop detailed project plans for priority initiatives")
        formatted.append("- Establish governance and reporting structure")
        formatted.append("- Begin implementation of quick wins")
        
        return "\n".join(formatted)
    
    def _prepare_trend_data(self, trends: List[Dict]) -> List[Dict]:
        """Prepare trend data for dashboard visualization"""
        return [{
            "name": trend.get("trend_name", "Unknown"),
            "impact": trend.get("impact_level", "Medium"),
            "timeframe": trend.get("timeframe", "Medium-term"),
            "confidence": trend.get("confidence_score", 0.7)
        } for trend in trends]
    
    def _prepare_opportunity_data(self, opportunities: List[Dict]) -> List[Dict]:
        """Prepare opportunity data for dashboard visualization"""
        return [{
            "name": opp.get("opportunity_name", "Unknown"),
            "revenue_potential": opp.get("revenue_potential", "Medium"),
            "implementation_difficulty": opp.get("implementation_difficulty", "Medium"),
            "time_to_market": opp.get("time_to_market", "Unknown")
        } for opp in opportunities]
    
    def _prepare_recommendation_data(self, recommendations: List[Dict]) -> List[Dict]:
        """Prepare recommendation data for dashboard visualization"""
        return [{
            "title": rec.get("strategy_title", "Unknown"),
            "priority": rec.get("priority_level", "Medium"),
            "timeline": rec.get("implementation_timeline", "Medium-term"),
            "confidence": rec.get("confidence_score", 0.7)
        } for rec in recommendations]
    
    def _prepare_timeline_data(self, recommendations: List[Dict]) -> Dict[str, List]:
        """Prepare timeline data for dashboard visualization"""
        timeline = {"Short-term": [], "Medium-term": [], "Long-term": []}
        
        for rec in recommendations:
            timeframe = rec.get("implementation_timeline", "Medium-term")
            if timeframe in timeline:
                timeline[timeframe].append(rec.get("strategy_title", "Unknown"))
        
        return timeline
    
    def _prepare_risk_data(self, recommendations: List[Dict]) -> List[Dict]:
        """Prepare risk data for dashboard visualization"""
        # Extract risk information from recommendations
        risks = []
        for rec in recommendations:
            # Simple risk assessment based on implementation difficulty and timeline
            difficulty = rec.get("resource_requirements", {}).get("implementation_difficulty", "Medium")
            timeline = rec.get("implementation_timeline", "Medium-term")
            
            risk_level = "Low"
            if difficulty == "Hard" or timeline == "Long-term":
                risk_level = "High"
            elif difficulty == "Medium" or timeline == "Medium-term":
                risk_level = "Medium"
            
            risks.append({
                "strategy": rec.get("strategy_title", "Unknown"),
                "risk_level": risk_level,
                "category": "Implementation"
            })
        
        return risks
