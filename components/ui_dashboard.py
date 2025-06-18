import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
import json

def render_dashboard_ui():
    """Render the interactive dashboard interface"""
    st.title("📊 Interactive Dashboard")
    
    if not st.session_state.get('analysis_complete') or not st.session_state.get('current_results'):
        st.warning("⚠️ No analysis results available. Please run an analysis first.")
        return
    
    results = st.session_state.current_results
    dashboard_data = results.get('dashboard_data', {})
    
    # Dashboard header
    col1, col2, col3, col4 = st.columns(4)
    
    summary_metrics = dashboard_data.get('summary_metrics', {})
    
    with col1:
        st.metric(
            "Market Trends",
            summary_metrics.get('total_trends', 0),
            delta=None
        )
    
    with col2:
        st.metric(
            "Opportunities",
            summary_metrics.get('total_opportunities', 0),
            delta=None
        )
    
    with col3:
        st.metric(
            "Recommendations",
            summary_metrics.get('total_recommendations', 0),
            delta=None
        )
    
    with col4:
        st.metric(
            "High Priority Items",
            summary_metrics.get('high_priority_items', 0),
            delta=None
        )
    
    # Main dashboard content
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Trends", "🎯 Opportunities", "💡 Strategy", "⏱️ Timeline"])
    
    with tab1:
        render_trends_dashboard(dashboard_data.get('trend_data', []))
    
    with tab2:
        render_opportunities_dashboard(dashboard_data.get('opportunity_data', []))
    
    with tab3:
        render_strategy_dashboard(dashboard_data.get('recommendation_data', []))
    
    with tab4:
        render_timeline_dashboard(dashboard_data.get('timeline_data', {}))

def render_trends_dashboard(trend_data: List[Dict]):
    """Render trends analysis dashboard"""
    st.subheader("📈 Market Trends Analysis")
    
    if not trend_data:
        st.info("No trend data available for visualization.")
        return
    
    # Create DataFrame
    df = pd.DataFrame(trend_data)
    
    # Trends impact chart
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Impact Distribution")
        
        # Count by impact level
        impact_counts = df['impact'].value_counts()
        
        fig_pie = px.pie(
            values=impact_counts.values,
            names=impact_counts.index,
            title="Trends by Impact Level",
            color_discrete_map={
                'High': '#FF6B6B',
                'Medium': '#FFA07A',
                'Low': '#98D8C8'
            }
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("Timeframe Analysis")
        
        # Count by timeframe
        timeframe_counts = df['timeframe'].value_counts()
        
        fig_bar = px.bar(
            x=timeframe_counts.index,
            y=timeframe_counts.values,
            title="Trends by Timeframe",
            color=timeframe_counts.values,
            color_continuous_scale='Viridis'
        )
        
        fig_bar.update_layout(
            xaxis_title="Timeframe",
            yaxis_title="Number of Trends",
            showlegend=False
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Confidence vs Impact scatter plot
    st.subheader("Confidence vs Impact Analysis")
    
    # Map impact to numeric values
    impact_map = {'High': 3, 'Medium': 2, 'Low': 1}
    df['impact_numeric'] = df['impact'].map(impact_map)
    
    fig_scatter = px.scatter(
        df,
        x='confidence',
        y='impact_numeric',
        text='name',
        title="Trend Confidence vs Impact",
        labels={'confidence': 'Confidence Score', 'impact_numeric': 'Impact Level'},
        color='impact',
        color_discrete_map={
            'High': '#FF6B6B',
            'Medium': '#FFA07A',
            'Low': '#98D8C8'
        }
    )
    
    fig_scatter.update_traces(textposition='top center')
    fig_scatter.update_layout(
        yaxis=dict(tickmode='array', tickvals=[1, 2, 3], ticktext=['Low', 'Medium', 'High'])
    )
    
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Detailed trends table
    st.subheader("📋 Detailed Trends Data")
    
    # Add filters
    col1, col2 = st.columns(2)
    
    with col1:
        impact_filter = st.multiselect(
            "Filter by Impact",
            options=df['impact'].unique(),
            default=df['impact'].unique()
        )
    
    with col2:
        timeframe_filter = st.multiselect(
            "Filter by Timeframe",
            options=df['timeframe'].unique(),
            default=df['timeframe'].unique()
        )
    
    # Apply filters
    filtered_df = df[
        (df['impact'].isin(impact_filter)) &
        (df['timeframe'].isin(timeframe_filter))
    ]
    
    st.dataframe(
        filtered_df[['name', 'impact', 'timeframe', 'confidence']],
        use_container_width=True
    )

def render_opportunities_dashboard(opportunity_data: List[Dict]):
    """Render opportunities analysis dashboard"""
    st.subheader("🎯 Market Opportunities Analysis")
    
    if not opportunity_data:
        st.info("No opportunity data available for visualization.")
        return
    
    df = pd.DataFrame(opportunity_data)
    
    # Opportunity matrix
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Revenue Potential Distribution")
        
        revenue_counts = df['revenue_potential'].value_counts()
        
        fig_donut = go.Figure(data=[go.Pie(
            labels=revenue_counts.index,
            values=revenue_counts.values,
            hole=.3
        )])
        
        fig_donut.update_layout(title="Opportunities by Revenue Potential")
        st.plotly_chart(fig_donut, use_container_width=True)
    
    with col2:
        st.subheader("Implementation Difficulty")
        
        difficulty_counts = df['implementation_difficulty'].value_counts()
        
        fig_bar = px.bar(
            x=difficulty_counts.index,
            y=difficulty_counts.values,
            title="Implementation Difficulty Distribution",
            color=difficulty_counts.values,
            color_continuous_scale='RdYlGn_r'
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Opportunity matrix (Revenue vs Difficulty)
    st.subheader("Opportunity Prioritization Matrix")
    
    # Map categorical values to numeric
    revenue_map = {'High': 3, 'Medium': 2, 'Low': 1}
    difficulty_map = {'Easy': 1, 'Medium': 2, 'Hard': 3}
    
    df['revenue_numeric'] = df['revenue_potential'].map(revenue_map)
    df['difficulty_numeric'] = df['implementation_difficulty'].map(difficulty_map)
    
    fig_matrix = px.scatter(
        df,
        x='difficulty_numeric',
        y='revenue_numeric',
        text='name',
        title="Revenue Potential vs Implementation Difficulty",
        labels={'difficulty_numeric': 'Implementation Difficulty', 'revenue_numeric': 'Revenue Potential'},
        color='revenue_potential',
        size_max=20
    )
    
    fig_matrix.update_traces(textposition='top center')
    fig_matrix.update_layout(
        xaxis=dict(tickmode='array', tickvals=[1, 2, 3], ticktext=['Easy', 'Medium', 'Hard']),
        yaxis=dict(tickmode='array', tickvals=[1, 2, 3], ticktext=['Low', 'Medium', 'High'])
    )
    
    # Add quadrant lines
    fig_matrix.add_hline(y=2, line_dash="dash", line_color="gray", opacity=0.5)
    fig_matrix.add_vline(x=2, line_dash="dash", line_color="gray", opacity=0.5)
    
    st.plotly_chart(fig_matrix, use_container_width=True)
    
    # Time to market analysis
    st.subheader("⏰ Time to Market Analysis")
    
    time_counts = df['time_to_market'].value_counts()
    
    fig_timeline = px.bar(
        x=time_counts.index,
        y=time_counts.values,
        title="Opportunities by Time to Market",
        color=time_counts.values,
        color_continuous_scale='Blues'
    )
    
    st.plotly_chart(fig_timeline, use_container_width=True)

def render_strategy_dashboard(recommendation_data: List[Dict]):
    """Render strategy recommendations dashboard"""
    st.subheader("💡 Strategic Recommendations Dashboard")
    
    if not recommendation_data:
        st.info("No recommendation data available for visualization.")
        return
    
    df = pd.DataFrame(recommendation_data)
    
    # Priority analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Priority Distribution")
        
        priority_counts = df['priority'].value_counts()
        
        fig_priority = px.pie(
            values=priority_counts.values,
            names=priority_counts.index,
            title="Recommendations by Priority",
            color_discrete_map={
                'High': '#FF6B6B',
                'Medium': '#FFA07A',
                'Low': '#98D8C8'
            }
        )
        
        st.plotly_chart(fig_priority, use_container_width=True)
    
    with col2:
        st.subheader("Implementation Timeline")
        
        timeline_counts = df['timeline'].value_counts()
        
        fig_timeline = px.bar(
            x=timeline_counts.index,
            y=timeline_counts.values,
            title="Recommendations by Timeline",
            color=timeline_counts.values,
            color_continuous_scale='Viridis'
        )
        
        st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Priority vs Timeline matrix
    st.subheader("Strategy Prioritization Matrix")
    
    priority_map = {'High': 3, 'Medium': 2, 'Low': 1}
    timeline_map = {'Short-term': 1, 'Medium-term': 2, 'Long-term': 3}
    
    df['priority_numeric'] = df['priority'].map(priority_map)
    df['timeline_numeric'] = df['timeline'].map(timeline_map)
    
    fig_strategy = px.scatter(
        df,
        x='timeline_numeric',
        y='priority_numeric',
        text='title',
        title="Priority vs Implementation Timeline",
        labels={'timeline_numeric': 'Implementation Timeline', 'priority_numeric': 'Priority Level'},
        color='priority',
        size='confidence',
        size_max=20
    )
    
    fig_strategy.update_traces(textposition='top center')
    fig_strategy.update_layout(
        xaxis=dict(tickmode='array', tickvals=[1, 2, 3], ticktext=['Short-term', 'Medium-term', 'Long-term']),
        yaxis=dict(tickmode='array', tickvals=[1, 2, 3], ticktext=['Low', 'Medium', 'High'])
    )
    
    st.plotly_chart(fig_strategy, use_container_width=True)
    
    # Confidence analysis
    st.subheader("📊 Confidence Analysis")
    
    fig_confidence = px.histogram(
        df,
        x='confidence',
        nbins=10,
        title="Distribution of Recommendation Confidence Scores",
        color_discrete_sequence=['#4ECDC4']
    )
    
    fig_confidence.update_layout(
        xaxis_title="Confidence Score",
        yaxis_title="Number of Recommendations"
    )
    
    st.plotly_chart(fig_confidence, use_container_width=True)

def render_timeline_dashboard(timeline_data: Dict[str, List]):
    """Render implementation timeline dashboard"""
    st.subheader("⏱️ Implementation Timeline Dashboard")
    
    if not timeline_data:
        st.info("No timeline data available for visualization.")
        return
    
    # Timeline overview
    st.subheader("📅 Implementation Phases")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Short-term Items", len(timeline_data.get('Short-term', [])))
        if timeline_data.get('Short-term'):
            st.write("**Items:**")
            for item in timeline_data['Short-term']:
                st.write(f"• {item}")
    
    with col2:
        st.metric("Medium-term Items", len(timeline_data.get('Medium-term', [])))
        if timeline_data.get('Medium-term'):
            st.write("**Items:**")
            for item in timeline_data['Medium-term']:
                st.write(f"• {item}")
    
    with col3:
        st.metric("Long-term Items", len(timeline_data.get('Long-term', [])))
        if timeline_data.get('Long-term'):
            st.write("**Items:**")
            for item in timeline_data['Long-term']:
                st.write(f"• {item}")
    
    # Timeline visualization
    st.subheader("📊 Timeline Distribution")
    
    timeline_counts = {phase: len(items) for phase, items in timeline_data.items()}
    
    fig_timeline = px.bar(
        x=list(timeline_counts.keys()),
        y=list(timeline_counts.values()),
        title="Distribution of Items Across Timeline",
        color=list(timeline_counts.values()),
        color_continuous_scale='Blues'
    )
    
    fig_timeline.update_layout(
        xaxis_title="Timeline Phase",
        yaxis_title="Number of Items",
        showlegend=False
    )
    
    st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Gantt-style timeline
    st.subheader("📈 Implementation Roadmap")
    
    # Create a simple roadmap visualization
    roadmap_data = []
    start_month = 0
    
    for phase, items in timeline_data.items():
        if phase == 'Short-term':
            duration = 3
        elif phase == 'Medium-term':
            duration = 6
        else:
            duration = 12
        
        for item in items:
            roadmap_data.append({
                'Task': item[:30],
                'Start': start_month,
                'Duration': duration,
                'Phase': phase
            })
        
        start_month += duration
    
    if roadmap_data:
        df_roadmap = pd.DataFrame(roadmap_data)
        
        fig_roadmap = px.bar(
            df_roadmap,
            x='Duration',
            y='Task',
            orientation='h',
            color='Phase',
            title="Implementation Roadmap (Months)",
            color_discrete_map={
                'Short-term': '#98D8C8',
                'Medium-term': '#FFA07A',
                'Long-term': '#FF6B6B'
            }
        )
        
        fig_roadmap.update_layout(
            xaxis_title="Duration (Months)",
            yaxis_title="Tasks",
            height=max(400, len(roadmap_data) * 30)
        )
        
        st.plotly_chart(fig_roadmap, use_container_width=True)

def render_export_dashboard():
    """Render export options for dashboard data"""
    st.subheader("📤 Export Dashboard Data")
    
    if not st.session_state.get('current_results'):
        st.warning("No data available for export.")
        return
    
    results = st.session_state.current_results
    dashboard_data = results.get('dashboard_data', {})
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export as JSON"):
            json_data = json.dumps(dashboard_data, indent=2)
            st.download_button(
                label="Download JSON",
                data=json_data,
                file_name=f"dashboard_data_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("📈 Export Charts"):
            st.info("Chart export functionality would be implemented here")
    
    with col3:
        if st.button("📋 Export Summary"):
            summary = create_dashboard_summary(dashboard_data)
            st.download_button(
                label="Download Summary",
                data=summary,
                file_name=f"dashboard_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )

def create_dashboard_summary(dashboard_data: Dict[str, Any]) -> str:
    """Create a text summary of dashboard data"""
    summary_metrics = dashboard_data.get('summary_metrics', {})
    
    summary = f"""Dashboard Summary
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Overview:
- Total Trends: {summary_metrics.get('total_trends', 0)}
- Total Opportunities: {summary_metrics.get('total_opportunities', 0)}
- Total Recommendations: {summary_metrics.get('total_recommendations', 0)}
- High Priority Items: {summary_metrics.get('high_priority_items', 0)}

Trends Analysis:
{len(dashboard_data.get('trend_data', []))} trends analyzed across various impact levels and timeframes.

Opportunities Analysis:
{len(dashboard_data.get('opportunity_data', []))} opportunities identified with varying revenue potential and implementation difficulty.

Strategic Recommendations:
{len(dashboard_data.get('recommendation_data', []))} strategic recommendations prioritized by impact and timeline.

Timeline Distribution:
{dashboard_data.get('timeline_data', {})}
"""
    
    return summary
