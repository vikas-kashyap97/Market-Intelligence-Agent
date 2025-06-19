import streamlit as st
import asyncio
from typing import Dict, Any
from core.workflow.agent_orchestrator import AgentOrchestrator
from core.db import DatabaseManager

def render_home_ui():
    """Render the enhanced home interface with multi-agent workflow"""
    st.title("🚀 Advanced Market Intelligence")
    st.markdown("Generate comprehensive market intelligence reports with AI-powered multi-agent analysis")

    # Initialize session state
    if 'orchestrator' not in st.session_state:
        st.session_state.orchestrator = AgentOrchestrator()

    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False

    if 'current_results' not in st.session_state:
        st.session_state.current_results = None

    # Main input section
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📊 Analysis Configuration")
        
        # Input fields
        query = st.text_input(
            "🔍 Research Query",
            placeholder="e.g., AI trends in healthcare, fintech market opportunities",
            help="What specific aspect would you like to analyze?"
        )
        
        market_domain = st.selectbox(
            "🏢 Market Domain",
            ["Technology", "Healthcare", "Finance", "Education", "E-commerce", 
             "Manufacturing", "Energy", "Real Estate", "Media", "Transportation", "Other"],
            help="Select the primary market domain"
        )
        
        if market_domain == "Other":
            market_domain = st.text_input("Specify Market Domain")
        
        question = st.text_area(
            "❓ Optional Specific Question",
            placeholder="Ask a specific question about the analysis...",
            help="This will be answered using the collected data via RAG"
        )
        
        # Advanced options
        with st.expander("⚙️ Advanced Options"):
            col_a, col_b = st.columns(2)
            
            with col_a:
                data_sources = st.multiselect(
                    "Data Sources",
                    ["Web Scraping", "News APIs", "Industry Reports", "Social Media"],
                    default=["Web Scraping", "News APIs"]
                )
            
            with col_b:
                analysis_depth = st.select_slider(
                    "Analysis Depth",
                    options=["Quick", "Standard", "Comprehensive"],
                    value="Standard"
                )
        
        # Run analysis button
        run_analysis = st.button(
            "🚀 Run Multi-Agent Analysis", 
            type="primary",
            disabled=st.session_state.get('workflow_running', False)
        )

    with col2:
        st.subheader("🎯 What You'll Get")
        
        st.markdown("""
        **🔍 Data Collection**
        - Real-time web scraping
        - Latest news aggregation
        - Industry trend analysis
        
        **📊 AI Analysis**
        - Market trend identification
        - Opportunity assessment
        - Competitive landscape
        
        **💡 Strategic Insights**
        - Actionable recommendations
        - Implementation roadmap
        - Risk assessment
        
        **📈 Interactive Outputs**
        - Dynamic dashboards
        - Contextual charts
        - Exportable reports
        """)

    # Load existing analysis section
    st.markdown("---")
    st.subheader("📋 Previous Analyses")

    db = DatabaseManager()
    previous_states = db.get_all_states()

    if previous_states:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_state = st.selectbox(
                "Load Previous Analysis",
                options=["Select..."] + [f"{s['id'][:8]} - {s['market_domain']} - {s['query'][:30]}..." for s in previous_states],
                help="Load a previously completed analysis"
            )
        
        with col2:
            if st.button("📂 Load Analysis") and selected_state != "Select...":
                state_id = selected_state.split(" - ")[0]
                loaded_state = db.load_state(state_id)
                if loaded_state:
                    st.session_state.current_results = {
                        "success": True,
                        "workflow_id": loaded_state.state_id,
                        "state_id": loaded_state.state_id,  # Add this field
                        "query": loaded_state.query,
                        "market_domain": loaded_state.market_domain,
                        "question": getattr(loaded_state, 'question', ''),  # Add question field
                        "report_dir": loaded_state.report_dir,
                        "market_trends": loaded_state.market_trends,
                        "opportunities": loaded_state.opportunities,
                        "strategic_recommendations": loaded_state.strategic_recommendations,
                        "dashboard_data": {
                            "summary_metrics": {
                                "total_trends": len(loaded_state.market_trends),
                                "total_opportunities": len(loaded_state.opportunities),
                                "total_recommendations": len(loaded_state.strategic_recommendations),
                                "high_priority_items": len([r for r in loaded_state.strategic_recommendations if r.get("priority_level") == "High"])
                            }
                        }
                    }
                    st.session_state.analysis_complete = True
                    st.success(f"✅ Analysis {state_id[:8]} loaded successfully!")
                    st.rerun()
    else:
        st.info("No previous analyses found. Run your first analysis to see it here!")

    # Run analysis workflow
    if run_analysis:
        if not query.strip():
            st.error("Please enter a research query")
            return
        
        if not market_domain.strip():
            st.error("Please specify a market domain")
            return
        
        # Start the workflow
        st.session_state.workflow_running = True
        
        # Create progress containers
        progress_container = st.container()
        status_container = st.container()
        
        with progress_container:
            st.info("🚀 Starting multi-agent workflow...")
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        # Run the workflow
        try:
            # Use asyncio to run the workflow
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            results = loop.run_until_complete(
                st.session_state.orchestrator.run_intelligence_workflow(
                    query=query,
                    market_domain=market_domain,
                    question=question if question.strip() else None
                )
            )
            
            loop.close()
            
            # Update progress
            progress_bar.progress(100)
            status_text.success("✅ Analysis completed!")
            
            # Store results with all required fields
            st.session_state.current_results = results
            # Ensure state_id is available
            if 'state_id' not in results:
                results['state_id'] = results.get('workflow_id', 'unknown')
            
            st.session_state.analysis_complete = True
            st.session_state.workflow_running = False
            
            if results["success"]:
                st.success(f"✅ Analysis completed! Workflow ID: {results['workflow_id']}")
                
                # Check for data collection issues
                data_sources = results.get("data_sources", 0)
                if data_sources == 0:
                    st.warning("""
                    ⚠️ **Limited Data Collection**: No external data sources were available. 
                    The analysis uses fallback data and general market knowledge. 
                    For better results, please check your API keys and network connection.
                    """)
                
                st.balloons()
                
                # Show quick summary
                with status_container:
                    st.subheader("📊 Quick Summary")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Data Sources", results.get("data_sources", 0))
                    
                    with col2:
                        st.metric("Trends Found", len(results.get("market_trends", [])))
                    
                    with col3:
                        st.metric("Opportunities", len(results.get("opportunities", [])))
                    
                    with col4:
                        st.metric("Recommendations", len(results.get("strategic_recommendations", [])))
                    
                    st.info("📋 Navigate to other tabs to explore the detailed analysis!")
            else:
                st.error(f"❌ Analysis failed: {results.get('error', 'Unknown error')}")
                st.session_state.workflow_running = False
                
        except Exception as e:
            st.error(f"❌ Workflow failed: {str(e)}")
            st.session_state.workflow_running = False
            progress_bar.progress(0)
            status_text.error("❌ Analysis failed")
            
            # Show troubleshooting tips
            with st.expander("🔧 Troubleshooting Tips"):
                st.markdown("""
                **Common Issues:**
                - **API Keys**: Ensure all API keys are set in your .env file
                - **Network**: Check your internet connection
                - **Query**: Try a simpler, more specific query
                - **Rate Limits**: Wait a few minutes if you've made many requests
                
                **Required API Keys:**
                - GOOGLE_API_KEY (for Gemini)
                - FIRECRAWL_API_KEY (for web scraping)
                - NEWSDATA_IO_KEY (for news data)
                - GROQ_API_KEY (for AI assistant)
                """)

    # Display current results if available
    if st.session_state.analysis_complete and st.session_state.current_results:
        results = st.session_state.current_results
        
        if results.get("success"):
            st.markdown("---")
            st.subheader("📊 Current Analysis Results")
            
            # Enhanced metrics display
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                trends_count = len(results.get("market_trends", []))
                st.metric(
                    "Market Trends",
                    trends_count,
                    delta=f"+{trends_count}" if trends_count > 0 else None
                )
            
            with col2:
                opp_count = len(results.get("opportunities", []))
                st.metric(
                    "Opportunities",
                    opp_count,
                    delta=f"+{opp_count}" if opp_count > 0 else None
                )
            
            with col3:
                rec_count = len(results.get("strategic_recommendations", []))
                st.metric(
                    "Recommendations",
                    rec_count,
                    delta=f"+{rec_count}" if rec_count > 0 else None
                )
            
            with col4:
                duration = results.get("duration", 0)
                st.metric(
                    "Analysis Time",
                    f"{duration:.1f}s",
                    delta=None
                )
            
            # Key insights preview
            st.subheader("🔍 Key Insights Preview")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if results.get("market_trends"):
                    st.write("**🔥 Top Trends:**")
                    for i, trend in enumerate(results["market_trends"][:3], 1):
                        impact = trend.get("impact_level", "Medium")
                        emoji = "🔴" if impact == "High" else "🟡" if impact == "Medium" else "🟢"
                        st.write(f"{emoji} {trend.get('trend_name', 'Unknown')}")
            
            with col2:
                if results.get("opportunities"):
                    st.write("**🎯 Top Opportunities:**")
                    for i, opp in enumerate(results["opportunities"][:3], 1):
                        potential = opp.get("revenue_potential", "Medium")
                        emoji = "💰" if potential == "High" else "💵" if potential == "Medium" else "💴"
                        st.write(f"{emoji} {opp.get('opportunity_name', 'Unknown')}")
            
            # Navigation hints
            st.info("""
            🎯 **Next Steps:**
            - 📊 **Dashboard**: Explore interactive visualizations
            - 📄 **Report**: Read the comprehensive analysis
            - 🤖 **Assistant**: Ask questions about your data
            - 📚 **History**: Manage your analyses
            """)
            
            # Quick actions
            st.subheader("⚡ Quick Actions")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.info("📊 **Dashboard Tab**: View interactive visualizations above")

            with col2:
                st.info("📄 **Report Tab**: Read comprehensive analysis above")

            with col3:
                st.info("🤖 **Assistant Tab**: Ask questions about your data above")
        
        else:
            st.error("Analysis failed. Please try again with different parameters.")

    elif not st.session_state.analysis_complete:
        # Show welcome message and features
        st.markdown("---")
        st.subheader("🌟 Advanced Features")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🔍 Enhanced Data Collection**
            - **Firecrawl Integration**: Real-time web scraping
            - **NewsData.io**: Latest news aggregation
            - **Tavily Search**: Comprehensive web search
            - **Smart Filtering**: Relevant content extraction
            
            **🧠 Multi-Agent Intelligence**
            - **Reader Agent**: Data collection and processing
            - **Analyst Agent**: Trend and opportunity analysis
            - **Strategist Agent**: Strategic recommendations
            - **Formatter Agent**: Report generation and export
            """)
        
        with col2:
            st.markdown("""
            **📊 Interactive Outputs**
            - **Plotly Dashboards**: Dynamic visualizations
            - **Contextual Charts**: AI-generated relevant charts
            - **Export Options**: PDF, DOCX, JSON formats
            - **Notion Integration**: One-click publishing
            
            **🤖 AI Assistant**
            - **Groq-Powered**: Fast LLaMA3 inference
            - **Context-Aware**: Understands your analysis
            - **Persistent Memory**: Conversation history
            - **Smart Suggestions**: Relevant prompts
            """)
        
        # Technology showcase
        st.subheader("🛠️ Technology Stack")
        
        tech_cols = st.columns(4)
        
        with tech_cols[0]:
            st.markdown("""
            **🔍 Data Sources**
            - Firecrawl.dev
            - NewsData.io
            - Tavily API
            - Web Scraping
            """)
        
        with tech_cols[1]:
            st.markdown("""
            **🧠 AI Models**
            - Google Gemini 2.0
            - Groq LLaMA3
            - HuggingFace Embeddings
            - LangChain Framework
            """)
        
        with tech_cols[2]:
            st.markdown("""
            **📊 Visualization**
            - Plotly Interactive
            - Matplotlib Static
            - Seaborn Styling
            - Custom Dashboards
            """)
        
        with tech_cols[3]:
            st.markdown("""
            **🔧 Infrastructure**
            - Streamlit UI
            - SQLite Database
            - Async Workflows
            - Multi-Agent System
            """)

def ui_home():
    render_home_ui()
