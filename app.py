import streamlit as st
import logging
import os
import asyncio
from config.settings import Settings
from components.ui_home import render_home_ui
from components.ui_report import render_report_ui
from components.ui_dashboard import render_dashboard_ui
from components.ui_assistant import render_assistant_ui
from components.ui_history import render_history_ui
from core.workflow.agent_orchestrator import AgentOrchestrator

# Configure logging
logging.basicConfig(
    level=getattr(logging, Settings.LOG_LEVEL),
    format=Settings.LOG_FORMAT,
    handlers=[
        logging.FileHandler('market_intelligence_app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main Streamlit application"""
    
    # Page configuration
    st.set_page_config(
        page_title="Market Intelligence Agent v2.0",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for enhanced UI
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        background-color: #f0f2f6;
        border-radius: 8px 8px 0 0;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #667eea;
        color: white;
    }
    
    .agent-status {
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.25rem 0;
    }
    
    .agent-running {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
    }
    
    .agent-completed {
        background-color: #d1edff;
        border-left: 4px solid #0084ff;
    }
    
    .agent-failed {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
    }
    
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    
    .plotly-graph-div {
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Check environment variables
    try:
        Settings.validate()
    except ValueError as e:
        st.error(f"⚠️ Configuration Error: {str(e)}")
        st.info("""
        Please check your .env file and ensure all required API keys are set:
        - GOOGLE_API_KEY (for Gemini)
        - TAVILY_API_KEY (for web search)
        - FIRECRAWL_API_KEY (for web scraping)
        - NEWSDATA_IO_KEY (for news data)
        - GROQ_API_KEY (for AI assistant)
        """)
        st.stop()
    
    # Ensure directories exist
    for directory in [Settings.REPORTS_DIR, Settings.ASSETS_DIR, Settings.EXPORTS_DIR]:
        os.makedirs(directory, exist_ok=True)
    
    # Initialize session state
    if 'orchestrator' not in st.session_state:
        st.session_state.orchestrator = AgentOrchestrator()
    
    if 'workflow_running' not in st.session_state:
        st.session_state.workflow_running = False
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🚀 Market Intelligence Agent v2.0</h1>
        <p>Advanced AI-Powered Market Research with Multi-Agent Workflow</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for workflow status
    with st.sidebar:
        st.header("🔄 Workflow Status")
        
        if st.session_state.workflow_running:
            status = st.session_state.orchestrator.get_workflow_status()
            
            # Overall progress
            st.progress(status['progress'] / 100)
            st.write(f"**Status:** {status['workflow_status'].title()}")
            st.write(f"**Current Step:** {status['current_step']}")
            
            if status['duration']:
                st.write(f"**Duration:** {status['duration']:.1f}s")
            
            # Agent statuses
            st.subheader("🤖 Agent Status")
            
            for agent_name, agent_status in status['agent_statuses'].items():
                status_class = f"agent-{agent_status['status'].replace('_', '-')}"
                
                st.markdown(f"""
                <div class="agent-status {status_class}">
                    <strong>{agent_name.title()} Agent</strong><br>
                    Status: {agent_status['status'].title()}<br>
                    Progress: {agent_status['progress']}%
                    {f"<br>Task: {agent_status['current_task']}" if agent_status['current_task'] else ""}
                </div>
                """, unsafe_allow_html=True)
            
            # Cancel button
            if st.button("🛑 Cancel Workflow"):
                asyncio.run(st.session_state.orchestrator.cancel_workflow())
                st.session_state.workflow_running = False
                st.rerun()
        
        else:
            st.info("No workflow currently running")
        
        # System info
        st.markdown("---")
        st.subheader("ℹ️ System Info")
        st.write(f"**Version:** 2.0")
        st.write(f"**Agents:** 4 (Reader, Analyst, Strategist, Formatter)")
        st.write(f"**Integrations:** Firecrawl, NewsData.io, Groq")
    
    # Main navigation
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 Home", 
        "📊 Dashboard", 
        "📄 Report", 
        "🤖 Assistant", 
        "📚 History"
    ])
    
    with tab1:
        render_home_ui()
    
    with tab2:
        render_dashboard_ui()
    
    with tab3:
        render_report_ui()
    
    with tab4:
        render_assistant_ui()
    
    with tab5:
        render_history_ui()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        🚀 Market Intelligence Agent v2.0 | 
        Powered by Google Gemini, Groq, Firecrawl, NewsData.io, and Multi-Agent AI
        <br>
        <small>Built with Streamlit, LangChain, Plotly, and Advanced AI Workflows</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
