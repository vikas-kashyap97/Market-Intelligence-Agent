import streamlit as st
from core.db import DatabaseManager
from datetime import datetime

def render_history_ui():
    """Render the analysis history interface"""
    st.title("📚 Analysis History")
    
    try:
        db = DatabaseManager()
        
        # Get all previous analyses
        states = db.get_all_states()
        
        if not states:
            st.info("📭 No previous analyses found. Run your first analysis to see it here!")
            
            # Show debug info
            with st.expander("🔧 Debug Information"):
                st.write("Database path:", db.db_path if hasattr(db, 'db_path') else "Unknown")
                st.write("Session state keys:", list(st.session_state.keys()))
                if 'current_results' in st.session_state:
                    st.write("Current results:", st.session_state.current_results)
            return
        
        st.markdown(f"### 📊 Found {len(states)} previous analyses")
        
        # Display analyses in a more organized way
        for i, state in enumerate(states):
            # Create a more informative title
            title = f"🔍 {state.get('market_domain', 'Unknown')} Analysis"
            query = state.get('query') or state.get('question', 'General Analysis')
            if query and query != 'N/A':
                title += f" - {query[:50]}{'...' if len(query) > 50 else ''}"
            
            with st.expander(f"{title} ({state.get('id', 'unknown')[:8]})"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Market Domain", state.get('market_domain', 'Unknown'))
                
                with col2:
                    query_text = state.get('query') or state.get('question', 'General Analysis')
                    st.metric("Query", query_text if query_text != 'N/A' else 'General Analysis')
                
                with col3:
                    created_at = state.get('created_at', 'Unknown')
                    if created_at != 'Unknown':
                        try:
                            created_date = datetime.fromisoformat(created_at).strftime("%Y-%m-%d %H:%M")
                        except:
                            created_date = created_at
                    else:
                        created_date = 'Unknown'
                    st.metric("Created", created_date)
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button(f"📂 Load Analysis", key=f"load_{i}"):
                        load_analysis(state.get('id'))
                
                with col2:
                    if st.button(f"🗑️ Delete", key=f"delete_{i}"):
                        delete_analysis(state.get('id'))
                
                with col3:
                    st.text(f"ID: {state.get('id', 'unknown')[:8]}")
    
    except Exception as e:
        st.error(f"❌ Error loading history: {str(e)}")
        st.write("Debug info:", str(e))
    
    # Bulk operations
    st.markdown("---")
    st.subheader("🔧 Bulk Operations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clear All History", type="secondary"):
            if st.session_state.get('confirm_clear_all'):
                clear_all_history()
                st.session_state.confirm_clear_all = False
                st.rerun()
            else:
                st.session_state.confirm_clear_all = True
                st.warning("⚠️ Click again to confirm deletion of ALL analyses")
    
    with col2:
        if st.button("📊 Export History", type="secondary"):
            export_history(states)

def load_analysis(state_id: str):
    """Load a specific analysis"""
    db = DatabaseManager()
    loaded_state = db.load_state(state_id)
    
    if loaded_state:
        # Update session state with loaded analysis
        st.session_state.current_results = {
            "success": True,
            "state_id": loaded_state.state_id,
            "report_dir": loaded_state.report_dir,
            "query_response": loaded_state.query_response,
            "market_trends": loaded_state.market_trends,
            "opportunities": loaded_state.opportunities,
            "strategic_recommendations": loaded_state.strategic_recommendations
        }
        st.session_state.analysis_complete = True
        
        st.success(f"✅ Analysis {state_id[:8]} loaded successfully!")
        st.info("📋 Navigate to other tabs to view the loaded analysis.")
    else:
        st.error(f"❌ Failed to load analysis {state_id[:8]}")

def delete_analysis(state_id: str):
    """Delete a specific analysis"""
    try:
        import sqlite3
        from config.settings import Settings
        
        with sqlite3.connect(Settings.DATABASE_PATH) as conn:
            c = conn.cursor()
            c.execute('DELETE FROM states WHERE id = ?', (state_id,))
            c.execute('DELETE FROM chat_history WHERE session_id = ?', (state_id,))
            conn.commit()
        
        st.success(f"✅ Analysis {state_id[:8]} deleted successfully!")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Failed to delete analysis: {str(e)}")

def clear_all_history():
    """Clear all analysis history"""
    try:
        import sqlite3
        from config.settings import Settings
        
        with sqlite3.connect(Settings.DATABASE_PATH) as conn:
            c = conn.cursor()
            c.execute('DELETE FROM states')
            c.execute('DELETE FROM chat_history')
            conn.commit()
        
        st.success("✅ All analysis history cleared!")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Failed to clear history: {str(e)}")

def export_history(states):
    """Export analysis history"""
    if not states:
        st.warning("No history to export")
        return
    
    # Create export content
    export_content = []
    export_content.append("# Market Intelligence Analysis History")
    export_content.append(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    export_content.append(f"Total Analyses: {len(states)}")
    export_content.append("\n---\n")
    
    for state in states:
        export_content.append(f"## Analysis: {state['id'][:8]}")
        export_content.append(f"- **Market Domain:** {state['market_domain']}")
        export_content.append(f"- **Query:** {state['query']}")
        export_content.append(f"- **Created:** {state['created_at']}")
        export_content.append("")
    
    export_text = "\n".join(export_content)
    
    st.download_button(
        label="📥 Download History",
        data=export_text,
        file_name=f"market_intelligence_history_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
        mime="text/markdown"
    )
