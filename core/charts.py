import os
import logging
from typing import Dict, Any, List, Optional
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from config.settings import Settings

logger = logging.getLogger(__name__)

class IntelligentChartGenerator:
    """Advanced chart generator with AI-powered contextual analysis"""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Set styling
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Plotly theme
        self.plotly_theme = "plotly_white"
        
    def generate_contextual_charts(self, data: Dict[str, Any]) -> List[str]:
        """Generate contextual charts using AI analysis"""
        logger.info("Starting intelligent chart generation")
        
        try:
            # Analyze data to determine optimal charts
            chart_suggestions = self._analyze_data_with_ai(data)
            
            generated_charts = []
            
            for suggestion in chart_suggestions:
                try:
                    chart_file = self._generate_chart_from_suggestion(suggestion, data)
                    if chart_file:
                        generated_charts.append(chart_file)
                except Exception as e:
                    logger.error(f"Failed to generate chart {suggestion.get('filename', 'unknown')}: {str(e)}")
            
            # Generate additional Plotly interactive charts
            interactive_charts = self._generate_interactive_charts(data)
            generated_charts.extend(interactive_charts)
            
            if not generated_charts:
                logger.warning("No charts generated, creating fallback charts")
                generated_charts = self._create_fallback_charts(data)
            
            logger.info(f"Generated {len(generated_charts)} contextual charts")
            return generated_charts
            
        except Exception as e:
            logger.error(f"Chart generation failed: {str(e)}")
            return self._create_fallback_charts(data)
    
    def _analyze_data_with_ai(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Use AI to analyze data and suggest optimal charts"""
        try:
            llm = init_chat_model(Settings.LLM_MODEL, model_provider="google_genai")
            parser = JsonOutputParser()
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert data visualization analyst. Analyze the provided market intelligence data and suggest the most effective charts to visualize the insights.

Consider:
- Data types and structures available
- Key insights that need highlighting
- Audience needs (business executives)
- Visual impact and clarity

Return a JSON array of chart suggestions with:
- chart_type: 'bar', 'pie', 'line', 'scatter', 'heatmap', 'radar', 'treemap', 'funnel'
- title: descriptive title
- filename: snake_case filename without extension
- data_source: which data to use
- visualization_goal: what insight this chart reveals
- priority: 'high', 'medium', 'low'
- interactive: true/false (whether to make it interactive)

Maximum 5 suggestions, prioritize high-impact visualizations."""),
                ("human", "Query: {query}\nMarket Domain: {market_domain}\n\nData Summary:\n- Trends: {trend_count}\n- Opportunities: {opp_count}\n- Recommendations: {rec_count}\n\nSample Data: {sample_data}")
            ])
            
            chain = prompt | llm | parser
            
            # Prepare data summary
            trends = data.get("market_trends", [])
            opportunities = data.get("opportunities", [])
            recommendations = data.get("strategic_recommendations", [])
            
            sample_data = {
                "trends_sample": trends[:2] if trends else [],
                "opportunities_sample": opportunities[:2] if opportunities else [],
                "recommendations_sample": recommendations[:2] if recommendations else []
            }
            
            suggestions = chain.invoke({
                "query": data.get("query", ""),
                "market_domain": data.get("market_domain", ""),
                "trend_count": len(trends),
                "opp_count": len(opportunities),
                "rec_count": len(recommendations),
                "sample_data": str(sample_data)[:1000]
            })
            
            if isinstance(suggestions, list):
                logger.info(f"AI suggested {len(suggestions)} charts")
                return suggestions
            else:
                logger.warning("AI returned invalid chart suggestions")
                return self._get_default_suggestions(data)
                
        except Exception as e:
            logger.error(f"AI chart analysis failed: {str(e)}")
            return self._get_default_suggestions(data)
    
    def _get_default_suggestions(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get default chart suggestions when AI analysis fails"""
        suggestions = []
        
        if data.get("market_trends"):
            suggestions.append({
                "chart_type": "bar",
                "title": f"Market Trends Impact Analysis - {data.get('market_domain', 'Analysis')}",
                "filename": "trends_impact_analysis",
                "data_source": "market_trends",
                "visualization_goal": "Show relative impact of market trends",
                "priority": "high",
                "interactive": True
            })
        
        if data.get("opportunities"):
            suggestions.append({
                "chart_type": "pie",
                "title": f"Opportunities by Revenue Potential - {data.get('market_domain', 'Analysis')}",
                "filename": "opportunities_revenue_potential",
                "data_source": "opportunities",
                "visualization_goal": "Show distribution of opportunity potential",
                "priority": "high",
                "interactive": True
            })
        
        if data.get("strategic_recommendations"):
            suggestions.append({
                "chart_type": "bar",
                "title": f"Strategic Recommendations Priority - {data.get('market_domain', 'Analysis')}",
                "filename": "recommendations_priority",
                "data_source": "strategic_recommendations",
                "visualization_goal": "Show priority levels of recommendations",
                "priority": "medium",
                "interactive": True
            })
        
        return suggestions
    
    def _generate_chart_from_suggestion(self, suggestion: Dict[str, Any], data: Dict[str, Any]) -> Optional[str]:
        """Generate a chart based on AI suggestion"""
        chart_type = suggestion.get("chart_type", "bar")
        is_interactive = suggestion.get("interactive", False)
        
        if is_interactive:
            return self._generate_plotly_chart(suggestion, data)
        else:
            return self._generate_matplotlib_chart(suggestion, data)
    
    def _generate_plotly_chart(self, suggestion: Dict[str, Any], data: Dict[str, Any]) -> Optional[str]:
        """Generate interactive Plotly chart"""
        try:
            chart_type = suggestion.get("chart_type", "bar")
            title = suggestion.get("title", "Analysis Chart")
            filename = suggestion.get("filename", "chart") + "_interactive.html"
            data_source = suggestion.get("data_source", "market_trends")
            
            source_data = data.get(data_source, [])
            if not source_data:
                return None
            
            fig = None
            
            if chart_type == "bar":
                fig = self._create_plotly_bar_chart(source_data, title)
            elif chart_type == "pie":
                fig = self._create_plotly_pie_chart(source_data, title)
            elif chart_type == "line":
                fig = self._create_plotly_line_chart(source_data, title)
            elif chart_type == "scatter":
                fig = self._create_plotly_scatter_chart(source_data, title)
            elif chart_type == "treemap":
                fig = self._create_plotly_treemap(source_data, title)
            elif chart_type == "funnel":
                fig = self._create_plotly_funnel_chart(source_data, title)
            
            if fig:
                filepath = os.path.join(self.output_dir, filename)
                fig.write_html(filepath)
                logger.info(f"Generated interactive chart: {filepath}")
                return filename
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to generate Plotly chart: {str(e)}")
            return None
    
    def _generate_matplotlib_chart(self, suggestion: Dict[str, Any], data: Dict[str, Any]) -> Optional[str]:
        """Generate static matplotlib chart"""
        try:
            chart_type = suggestion.get("chart_type", "bar")
            title = suggestion.get("title", "Analysis Chart")
            filename = suggestion.get("filename", "chart") + ".png"
            data_source = suggestion.get("data_source", "market_trends")
            
            source_data = data.get(data_source, [])
            if not source_data:
                return None
            
            plt.figure(figsize=(12, 8))
            
            if chart_type == "bar":
                self._create_matplotlib_bar_chart(source_data, title)
            elif chart_type == "pie":
                self._create_matplotlib_pie_chart(source_data, title)
            elif chart_type == "heatmap":
                self._create_matplotlib_heatmap(source_data, title)
            elif chart_type == "radar":
                self._create_matplotlib_radar_chart(source_data, title)
            
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            logger.info(f"Generated static chart: {filepath}")
            return filename
            
        except Exception as e:
            logger.error(f"Failed to generate matplotlib chart: {str(e)}")
            plt.close()
            return None
    
    def _create_plotly_bar_chart(self, data: List[Dict], title: str) -> go.Figure:
        """Create interactive bar chart with Plotly"""
        labels = []
        values = []
        colors = []
        
        for item in data:
            # Extract label
            label = (item.get('trend_name') or item.get('opportunity_name') or 
                    item.get('strategy_title') or 'Unknown')[:25]
            labels.append(label)
            
            # Extract value
            impact = item.get('impact_level') or item.get('revenue_potential') or item.get('priority_level') or 'Medium'
            if impact.lower() == 'high':
                values.append(3)
                colors.append('#FF6B6B')
            elif impact.lower() == 'medium':
                values.append(2)
                colors.append('#FFA07A')
            else:
                values.append(1)
                colors.append('#98D8C8')
        
        fig = go.Figure(data=[
            go.Bar(
                x=labels,
                y=values,
                marker_color=colors,
                text=[f"{impact}" for impact in [item.get('impact_level', 'Medium') for item in data]],
                textposition='auto',
                hovertemplate='<b>%{x}</b><br>Impact: %{text}<br>Score: %{y}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title=title,
            xaxis_title="Items",
            yaxis_title="Impact Level",
            yaxis=dict(tickmode='array', tickvals=[1, 2, 3], ticktext=['Low', 'Medium', 'High']),
            template=self.plotly_theme,
            height=600
        )
        
        return fig
    
    def _create_plotly_pie_chart(self, data: List[Dict], title: str) -> go.Figure:
        """Create interactive pie chart with Plotly"""
        # Count categories
        categories = {}
        for item in data:
            category = (item.get('timeframe') or item.get('implementation_difficulty') or 
                       item.get('revenue_potential') or 'Other')
            categories[category] = categories.get(category, 0) + 1
        
        if not categories:
            return None
        
        fig = go.Figure(data=[
            go.Pie(
                labels=list(categories.keys()),
                values=list(categories.values()),
                hole=0.3,
                hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title=title,
            template=self.plotly_theme,
            height=600
        )
        
        return fig
    
    def _create_plotly_line_chart(self, data: List[Dict], title: str) -> go.Figure:
        """Create interactive line chart with Plotly"""
        x_values = list(range(1, len(data) + 1))
        y_values = []
        
        for item in data:
            confidence = item.get('confidence_score', 0.7)
            if isinstance(confidence, (int, float)):
                y_values.append(confidence)
            else:
                y_values.append(0.7)
        
        fig = go.Figure(data=[
            go.Scatter(
                x=x_values,
                y=y_values,
                mode='lines+markers',
                line=dict(color='#FF6B6B', width=3),
                marker=dict(size=8),
                hovertemplate='<b>Item %{x}</b><br>Confidence: %{y:.1%}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title=title,
            xaxis_title="Sequence",
            yaxis_title="Confidence Score",
            yaxis=dict(tickformat='.0%'),
            template=self.plotly_theme,
            height=600
        )
        
        return fig
    
    def _create_plotly_scatter_chart(self, data: List[Dict], title: str) -> go.Figure:
        """Create interactive scatter chart with Plotly"""
        x_values = []
        y_values = []
        text_labels = []
        
        for item in data:
            # Use confidence as x-axis
            confidence = item.get('confidence_score', 0.7)
            x_values.append(confidence if isinstance(confidence, (int, float)) else 0.7)
            
            # Use impact as y-axis
            impact = item.get('impact_level', 'Medium')
            if impact.lower() == 'high':
                y_values.append(3)
            elif impact.lower() == 'medium':
                y_values.append(2)
            else:
                y_values.append(1)
            
            # Label
            label = (item.get('trend_name') or item.get('opportunity_name') or 
                    item.get('strategy_title') or 'Unknown')[:20]
            text_labels.append(label)
        
        fig = go.Figure(data=[
            go.Scatter(
                x=x_values,
                y=y_values,
                mode='markers+text',
                text=text_labels,
                textposition='top center',
                marker=dict(size=12, color='#4ECDC4', opacity=0.7),
                hovertemplate='<b>%{text}</b><br>Confidence: %{x:.1%}<br>Impact: %{y}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title=title,
            xaxis_title="Confidence Score",
            yaxis_title="Impact Level",
            xaxis=dict(tickformat='.0%'),
            yaxis=dict(tickmode='array', tickvals=[1, 2, 3], ticktext=['Low', 'Medium', 'High']),
            template=self.plotly_theme,
            height=600
        )
        
        return fig
    
    def _create_plotly_treemap(self, data: List[Dict], title: str) -> go.Figure:
        """Create interactive treemap with Plotly"""
        labels = []
        parents = []
        values = []
        
        # Create hierarchy: Category -> Items
        categories = {}
        for item in data:
            category = (item.get('timeframe') or item.get('implementation_difficulty') or 
                       item.get('category') or 'General')
            if category not in categories:
                categories[category] = []
            categories[category].append(item)
        
        # Add root
        labels.append(title)
        parents.append("")
        values.append(len(data))
        
        # Add categories
        for category, items in categories.items():
            labels.append(category)
            parents.append(title)
            values.append(len(items))
            
            # Add items
            for item in items:
                item_name = (item.get('trend_name') or item.get('opportunity_name') or 
                           item.get('strategy_title') or 'Unknown')[:20]
                labels.append(item_name)
                parents.append(category)
                values.append(1)
        
        fig = go.Figure(go.Treemap(
            labels=labels,
            parents=parents,
            values=values,
            hovertemplate='<b>%{label}</b><br>Value: %{value}<extra></extra>'
        ))
        
        fig.update_layout(
            title=title,
            template=self.plotly_theme,
            height=600
        )
        
        return fig
    
    def _create_plotly_funnel_chart(self, data: List[Dict], title: str) -> go.Figure:
        """Create interactive funnel chart with Plotly"""
        # Sort by priority/impact for funnel effect
        sorted_data = sorted(data, key=lambda x: self._get_priority_score(x), reverse=True)
        
        labels = []
        values = []
        
        for i, item in enumerate(sorted_data[:6]):  # Limit to 6 items for clarity
            label = (item.get('trend_name') or item.get('opportunity_name') or 
                    item.get('strategy_title') or f'Item {i+1}')[:25]
            labels.append(label)
            values.append(100 - i * 15)  # Decreasing values for funnel effect
        
        fig = go.Figure(go.Funnel(
            y=labels,
            x=values,
            textinfo="value+percent initial",
            hovertemplate='<b>%{y}</b><br>Value: %{x}<extra></extra>'
        ))
        
        fig.update_layout(
            title=title,
            template=self.plotly_theme,
            height=600
        )
        
        return fig
    
    def _get_priority_score(self, item: Dict) -> int:
        """Get numeric priority score for sorting"""
        priority = item.get('priority_level') or item.get('impact_level') or 'Medium'
        if priority.lower() == 'high':
            return 3
        elif priority.lower() == 'medium':
            return 2
        else:
            return 1
    
    def _generate_interactive_charts(self, data: Dict[str, Any]) -> List[str]:
        """Generate additional interactive charts"""
        interactive_charts = []
        
        try:
            # Generate comprehensive dashboard chart
            dashboard_chart = self._create_comprehensive_dashboard(data)
            if dashboard_chart:
                interactive_charts.append(dashboard_chart)
            
            # Generate timeline chart if recommendations exist
            if data.get("strategic_recommendations"):
                timeline_chart = self._create_timeline_chart(data["strategic_recommendations"])
                if timeline_chart:
                    interactive_charts.append(timeline_chart)
            
        except Exception as e:
            logger.error(f"Failed to generate interactive charts: {str(e)}")
        
        return interactive_charts
    
    def _create_comprehensive_dashboard(self, data: Dict[str, Any]) -> Optional[str]:
        """Create comprehensive dashboard with multiple subplots"""
        try:
            trends = data.get("market_trends", [])
            opportunities = data.get("opportunities", [])
            recommendations = data.get("strategic_recommendations", [])
            
            if not any([trends, opportunities, recommendations]):
                return None
            
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Market Trends Impact', 'Opportunities Distribution', 
                              'Recommendations Priority', 'Implementation Timeline'),
                specs=[[{"type": "bar"}, {"type": "pie"}],
                       [{"type": "bar"}, {"type": "bar"}]]
            )
            
            # Trends chart
            if trends:
                trend_labels = [t.get('trend_name', 'Unknown')[:15] for t in trends[:5]]
                trend_values = [self._get_impact_score(t.get('impact_level', 'Medium')) for t in trends[:5]]
                
                fig.add_trace(
                    go.Bar(x=trend_labels, y=trend_values, name="Trends", 
                          marker_color='#FF6B6B'),
                    row=1, col=1
                )
            
            # Opportunities pie chart
            if opportunities:
                opp_categories = {}
                for opp in opportunities:
                    category = opp.get('revenue_potential', 'Medium')
                    opp_categories[category] = opp_categories.get(category, 0) + 1
                
                fig.add_trace(
                    go.Pie(labels=list(opp_categories.keys()), 
                          values=list(opp_categories.values()), name="Opportunities"),
                    row=1, col=2
                )
            
            # Recommendations chart
            if recommendations:
                rec_labels = [r.get('strategy_title', 'Unknown')[:15] for r in recommendations[:5]]
                rec_values = [self._get_priority_score(r) for r in recommendations[:5]]
                
                fig.add_trace(
                    go.Bar(x=rec_labels, y=rec_values, name="Recommendations", 
                          marker_color='#4ECDC4'),
                    row=2, col=1
                )
            
            # Timeline chart
            if recommendations:
                timeline_data = {'Short-term': 0, 'Medium-term': 0, 'Long-term': 0}
                for rec in recommendations:
                    timeline = rec.get('implementation_timeline', 'Medium-term')
                    if timeline in timeline_data:
                        timeline_data[timeline] += 1
                
                fig.add_trace(
                    go.Bar(x=list(timeline_data.keys()), y=list(timeline_data.values()), 
                          name="Timeline", marker_color='#FFA07A'),
                    row=2, col=2
                )
            
            fig.update_layout(
                title_text=f"Market Intelligence Dashboard - {data.get('market_domain', 'Analysis')}",
                showlegend=False,
                height=800,
                template=self.plotly_theme
            )
            
            filename = "comprehensive_dashboard.html"
            filepath = os.path.join(self.output_dir, filename)
            fig.write_html(filepath)
            
            logger.info(f"Generated comprehensive dashboard: {filepath}")
            return filename
            
        except Exception as e:
            logger.error(f"Failed to create comprehensive dashboard: {str(e)}")
            return None
    
    def _create_timeline_chart(self, recommendations: List[Dict]) -> Optional[str]:
        """Create timeline Gantt chart for recommendations"""
        try:
            # Prepare timeline data
            timeline_data = []
            start_date = datetime.now()
            
            for i, rec in enumerate(recommendations[:8]):  # Limit to 8 for clarity
                title = rec.get('strategy_title', f'Strategy {i+1}')[:30]
                timeline = rec.get('implementation_timeline', 'Medium-term')
                
                # Calculate duration based on timeline
                if timeline == 'Short-term':
                    duration = 90  # 3 months
                elif timeline == 'Long-term':
                    duration = 365  # 1 year
                else:
                    duration = 180  # 6 months
                
                start = start_date.strftime('%Y-%m-%d')
                end = (start_date + pd.Timedelta(days=duration)).strftime('%Y-%m-%d')
                
                timeline_data.append({
                    'Task': title,
                    'Start': start,
                    'Finish': end,
                    'Priority': rec.get('priority_level', 'Medium')
                })
                
                # Offset start date for next item
                start_date += pd.Timedelta(days=30)
            
            df = pd.DataFrame(timeline_data)
            
            # Create Gantt chart
            fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", 
                            color="Priority", title="Strategic Implementation Timeline")
            
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(
                height=600,
                template=self.plotly_theme,
                xaxis_title="Timeline",
                yaxis_title="Strategic Initiatives"
            )
            
            filename = "implementation_timeline.html"
            filepath = os.path.join(self.output_dir, filename)
            fig.write_html(filepath)
            
            logger.info(f"Generated timeline chart: {filepath}")
            return filename
            
        except Exception as e:
            logger.error(f"Failed to create timeline chart: {str(e)}")
            return None
    
    def _get_impact_score(self, impact: str) -> int:
        """Convert impact level to numeric score"""
        if impact.lower() == 'high':
            return 3
        elif impact.lower() == 'medium':
            return 2
        else:
            return 1
    
    def _create_fallback_charts(self, data: Dict[str, Any]) -> List[str]:
        """Create basic fallback charts when AI generation fails"""
        charts = []
        
        try:
            # Simple trends chart
            if data.get("market_trends"):
                chart = self._create_simple_trends_chart(data["market_trends"], data.get("market_domain", "Analysis"))
                if chart:
                    charts.append(chart)
            
            # Simple opportunities chart
            if data.get("opportunities"):
                chart = self._create_simple_opportunities_chart(data["opportunities"], data.get("market_domain", "Analysis"))
                if chart:
                    charts.append(chart)
            
        except Exception as e:
            logger.error(f"Failed to create fallback charts: {str(e)}")
        
        return charts
    
    def _create_simple_trends_chart(self, trends: List[Dict], market_domain: str) -> Optional[str]:
        """Create simple trends chart as fallback"""
        try:
            plt.figure(figsize=(12, 6))
            
            trend_names = [trend.get('trend_name', f'Trend {i+1}')[:20] for i, trend in enumerate(trends[:6])]
            impact_values = [self._get_impact_score(trend.get('impact_level', 'Medium')) for trend in trends[:6]]
            colors = ['#FF6B6B' if v == 3 else '#FFA07A' if v == 2 else '#98D8C8' for v in impact_values]
            
            plt.bar(trend_names, impact_values, color=colors)
            plt.title(f'Market Trends Impact Analysis - {market_domain}', fontsize=16, fontweight='bold')
            plt.xlabel('Trends', fontsize=12)
            plt.ylabel('Impact Level', fontsize=12)
            plt.xticks(rotation=45, ha='right')
            plt.yticks([1, 2, 3], ['Low', 'Medium', 'High'])
            plt.grid(True, alpha=0.3, axis='y')
            plt.tight_layout()
            
            filename = 'fallback_trends_analysis.png'
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            logger.info(f"Generated fallback trends chart: {filepath}")
            return filename
            
        except Exception as e:
            logger.error(f"Failed to create simple trends chart: {str(e)}")
            plt.close()
            return None
    
    def _create_simple_opportunities_chart(self, opportunities: List[Dict], market_domain: str) -> Optional[str]:
        """Create simple opportunities chart as fallback"""
        try:
            # Count by revenue potential
            potential_counts = {}
            for opp in opportunities:
                potential = opp.get('revenue_potential', 'Medium')
                potential_counts[potential] = potential_counts.get(potential, 0) + 1
            
            if not potential_counts:
                return None
            
            plt.figure(figsize=(10, 8))
            
            labels = list(potential_counts.keys())
            sizes = list(potential_counts.values())
            colors = ['#FF6B6B', '#FFA07A', '#98D8C8'][:len(labels)]
            
            plt.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
            plt.title(f'Opportunities by Revenue Potential - {market_domain}', fontsize=16, fontweight='bold')
            plt.axis('equal')
            
            filename = 'fallback_opportunities_analysis.png'
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            logger.info(f"Generated fallback opportunities chart: {filepath}")
            return filename
            
        except Exception as e:
            logger.error(f"Failed to create simple opportunities chart: {str(e)}")
            plt.close()
            return None
