import streamlit as st
import os
from PIL import Image
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import Dict, Any, List

def render_charts_ui():
    """Render the charts visualization interface"""
    st.title("📊 Market Intelligence Charts")
    
    if not st.session_state.get('analysis_complete') or not st.session_state.get('current_results'):
        st.warning("⚠️ No analysis results available. Please run an analysis first.")
        return
    
    results = st.session_state.current_results
    
    if not results.get("success"):
        st.error("❌ Analysis failed. No charts available.")
        return
    
    report_dir = results.get("report_dir")
    if not report_dir or not os.path.exists(report_dir):
        st.error("📁 Report directory not found.")
        return
    
    # Clear old chart state when new analysis is loaded
    if 'last_analysis_id' not in st.session_state:
        st.session_state.last_analysis_id = None
    
    current_analysis_id = results.get("state_id")
    if st.session_state.last_analysis_id != current_analysis_id:
        st.session_state.last_analysis_id = current_analysis_id
        # Clear any cached chart data
        if 'cached_charts' in st.session_state:
            del st.session_state.cached_charts
    
    # Look for dynamically generated chart files
    chart_files = []
    if os.path.exists(report_dir):
        for file in os.listdir(report_dir):
            if file.endswith('.png') and os.path.isfile(os.path.join(report_dir, file)):
                chart_files.append(file)
    
    if not chart_files:
        st.info("📊 No charts were generated for this analysis. This may be because:")
        st.markdown("""
        - The query didn't contain data suitable for visualization
        - The AI analysis didn't identify chartable patterns
        - The data structure wasn't compatible with chart generation
        """)
        return
    
    st.success(f"📈 Generated {len(chart_files)} contextual charts based on your query")
    
    # Display charts dynamically
    for chart_file in sorted(chart_files):
        chart_path = os.path.join(report_dir, chart_file)
        
        # Create a more readable title from filename
        chart_title = chart_file.replace('.png', '').replace('_', ' ').title()
        
        st.subheader(f"📊 {chart_title}")
        
        try:
            # Display the chart
            image = Image.open(chart_path)
            st.image(image, use_column_width=True)
            
            # Chart metadata
            col1, col2, col3 = st.columns(3)
            with col1:
                file_size = os.path.getsize(chart_path) / 1024  # KB
                st.caption(f"Size: {file_size:.1f} KB")
            with col2:
                st.caption(f"File: {chart_file}")
            with col3:
                # Download button
                with open(chart_path, "rb") as f:
                    st.download_button(
                        label="📥 Download",
                        data=f.read(),
                        file_name=chart_file,
                        mime="image/png",
                        key=f"download_{chart_file}_{current_analysis_id}"
                    )
            
        except Exception as e:
            st.error(f"❌ Error displaying {chart_file}: {str(e)}")
        
        st.markdown("---")
    
    # Interactive analysis section
    st.subheader("🎯 Interactive Data Analysis")
    
    # Show data insights
    if results.get("market_trends"):
        with st.expander("📈 Market Trends Data", expanded=False):
            df_trends = pd.DataFrame(results["market_trends"])
            st.dataframe(df_trends, use_container_width=True)
    
    if results.get("opportunities"):
        with st.expander("🎯 Opportunities Data", expanded=False):
            df_opportunities = pd.DataFrame(results["opportunities"])
            st.dataframe(df_opportunities, use_container_width=True)
    
    if results.get("strategic_recommendations"):
        with st.expander("💡 Recommendations Data", expanded=False):
            df_recommendations = pd.DataFrame(results["strategic_recommendations"])
            st.dataframe(df_recommendations, use_container_width=True)
    
    # Chart generation insights
    st.subheader("🔍 Chart Generation Insights")
    st.info(f"""
    **Query:** {results.get('query', 'N/A')}
    
    **Market Domain:** {results.get('market_domain', 'N/A')}
    
    **Charts Generated:** {len(chart_files)} contextual visualizations
    
    The charts above were intelligently selected based on your specific query and the AI analysis results. 
    Each chart visualizes relevant patterns found in the market intelligence data.
    """)

def create_trends_chart(trends: List[Dict[str, Any]]):
    """Create interactive trends chart"""
    st.subheader("📈 Market Trends Analysis")
    
    if not trends:
        st.info("No trends data available")
        return
    
    # Prepare data
    trend_data = []
    for trend in trends:
        impact = trend.get('estimated_impact', 'Low')
        impact_score = {'High': 3, 'Medium': 2, 'Low': 1}.get(impact, 1)
        
        trend_data.append({
            'Trend': trend.get('trend_name', 'Unknown')[:20],
            'Impact Score': impact_score,
            'Impact Level': impact,
            'Timeframe': trend.get('timeframe', 'Unknown')
        })
    
    df = pd.DataFrame(trend_data)
    
    # Create chart
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(df['Trend'], df['Impact Score'], 
                  color=['#FF6B6B' if x == 3 else '#FFA07A' if x == 2 else '#98D8C8' 
                         for x in df['Impact Score']])
    
    ax.set_title('Market Trends Impact Analysis', fontsize=16, fontweight='bold')
    ax.set_xlabel('Trends', fontsize=12)
    ax.set_ylabel('Impact Level', fontsize=12)
    ax.set_yticks([1, 2, 3])
    ax.set_yticklabels(['Low', 'Medium', 'High'])
    plt.xticks(rotation=45, ha='right')
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    
    st.pyplot(fig)
    
    # Data table
    st.subheader("📋 Trends Details")
    st.dataframe(df, use_container_width=True)

def create_opportunities_chart(opportunities: List[Dict[str, Any]]):
    """Create interactive opportunities chart"""
    st.subheader("🎯 Market Opportunities")
    
    if not opportunities:
        st.info("No opportunities data available")
        return
    
    # Prepare data
    opp_data = []
    for opp in opportunities:
        potential = opp.get('estimated_potential', 'Low')
        potential_score = {'High': 3, 'Medium': 2, 'Low': 1}.get(potential, 1)
        
        opp_data.append({
            'Opportunity': opp.get('opportunity_name', 'Unknown')[:20],
            'Potential Score': potential_score,
            'Potential Level': potential,
            'Target Segment': opp.get('target_segment', 'Unknown')
        })
    
    df = pd.DataFrame(opp_data)
    
    # Create pie chart
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Pie chart for potential distribution
    potential_counts = df['Potential Level'].value_counts()
    colors = ['#FF6B6B', '#FFA07A', '#98D8C8']
    ax1.pie(potential_counts.values, labels=potential_counts.index, autopct='%1.1f%%', 
            colors=colors[:len(potential_counts)], startangle=90)
    ax1.set_title('Opportunities by Potential Level')
    
    # Bar chart for individual opportunities
    bars = ax2.bar(df['Opportunity'], df['Potential Score'],
                   color=['#FF6B6B' if x == 3 else '#FFA07A' if x == 2 else '#98D8C8' 
                          for x in df['Potential Score']])
    ax2.set_title('Individual Opportunity Potential')
    ax2.set_xlabel('Opportunities')
    ax2.set_ylabel('Potential Level')
    ax2.set_yticks([1, 2, 3])
    ax2.set_yticklabels(['Low', 'Medium', 'High'])
    plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # Data table
    st.subheader("📋 Opportunities Details")
    st.dataframe(df, use_container_width=True)

def create_recommendations_chart(recommendations: List[Dict[str, Any]]):
    """Create interactive recommendations chart"""
    st.subheader("💡 Strategic Recommendations")
    
    if not recommendations:
        st.info("No recommendations data available")
        return
    
    # Prepare data
    rec_data = []
    for rec in recommendations:
        priority = rec.get('priority_level', 'Low')
        priority_score = {'High': 3, 'Medium': 2, 'Low': 1}.get(priority, 1)
        
        rec_data.append({
            'Strategy': rec.get('strategy_title', 'Unknown')[:20],
            'Priority Score': priority_score,
            'Priority Level': priority,
            'Expected Outcome': rec.get('expected_outcome', 'Unknown')[:30]
        })
    
    df = pd.DataFrame(rec_data)
    
    # Create horizontal bar chart
    fig, ax = plt.subplots(figsize=(12, 8))
    bars = ax.barh(df['Strategy'], df['Priority Score'],
                   color=['#FF6B6B' if x == 3 else '#FFA07A' if x == 2 else '#98D8C8' 
                          for x in df['Priority Score']])
    
    ax.set_title('Strategic Recommendations by Priority', fontsize=16, fontweight='bold')
    ax.set_xlabel('Priority Level', fontsize=12)
    ax.set_ylabel('Strategies', fontsize=12)
    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels(['Low', 'Medium', 'High'])
    ax.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # Data table
    st.subheader("📋 Recommendations Details")
    st.dataframe(df, use_container_width=True)
