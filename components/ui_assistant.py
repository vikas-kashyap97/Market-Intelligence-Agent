import streamlit as st
import json
from typing import List, Dict, Any
from datetime import datetime
from core.integrations.groq_client import GroqClient
from core.db import DatabaseManager

def render_assistant_ui():
    """Render the AI Assistant interface"""
    st.title("🤖 AI Assistant")
    st.markdown("Chat with your intelligent market research assistant powered by Groq")
    
    # Initialize session state
    if 'assistant_messages' not in st.session_state:
        st.session_state.assistant_messages = []
    
    if 'groq_client' not in st.session_state:
        st.session_state.groq_client = GroqClient()
    
    if 'assistant_session_id' not in st.session_state:
        st.session_state.assistant_session_id = f"assistant_{int(datetime.now().timestamp())}"
    
    # Sidebar with assistant features
    with st.sidebar:
        st.header("🎯 Assistant Features")
        
        # Quick actions
        st.subheader("Quick Actions")
        
        if st.button("📊 Summarize Last Analysis"):
            if st.session_state.get('current_results'):
                summary_prompt = create_analysis_summary_prompt(st.session_state.current_results)
                add_assistant_message("user", "Summarize my last analysis")
                response = get_assistant_response(summary_prompt)
                add_assistant_message("assistant", response)
                st.rerun()
        
        if st.button("💡 Generate Startup Ideas"):
            market_domain = st.session_state.get('current_results', {}).get('market_domain', 'Technology')
            startup_prompt = f"Generate 3 innovative startup ideas for the {market_domain} market based on current trends"
            add_assistant_message("user", "Generate startup ideas")
            response = get_assistant_response(startup_prompt)
            add_assistant_message("assistant", response)
            st.rerun()
        
        if st.button("🔍 Compare Markets"):
            compare_prompt = "Compare the current market analysis with similar markets globally"
            add_assistant_message("user", "Compare with similar markets")
            response = get_assistant_response(compare_prompt)
            add_assistant_message("assistant", response)
            st.rerun()
        
        # Suggested prompts
        st.subheader("💬 Suggested Prompts")
        suggested_prompts = [
            "What are the key risks in my analysis?",
            "How can I validate these opportunities?",
            "What metrics should I track?",
            "Explain the competitive landscape",
            "What are the next steps?",
            "How do these trends affect pricing?",
            "What partnerships should I consider?",
            "How to prioritize recommendations?"
        ]
        
        for prompt in suggested_prompts:
            if st.button(f"💭 {prompt}", key=f"prompt_{hash(prompt)}"):
                add_assistant_message("user", prompt)
                response = get_assistant_response(prompt)
                add_assistant_message("assistant", response)
                st.rerun()
        
        # Clear conversation
        st.markdown("---")
        if st.button("🗑️ Clear Conversation"):
            st.session_state.assistant_messages = []
            st.rerun()
    
    # Main chat interface
    st.subheader("💬 Chat with Assistant")
    
    # Display chat history
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.assistant_messages:
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.write(message["content"])
            else:
                with st.chat_message("assistant"):
                    st.write(message["content"])
    
    # Chat input
    user_input = st.chat_input("Ask me anything about market intelligence...")
    
    if user_input:
        # Add user message
        add_assistant_message("user", user_input)
        
        # Get assistant response
        with st.spinner("🤔 Thinking..."):
            response = get_assistant_response(user_input)
        
        # Add assistant response
        add_assistant_message("assistant", response)
        
        # Rerun to update chat
        st.rerun()
    
    # Context information
    if st.session_state.get('current_results'):
        st.markdown("---")
        st.subheader("📋 Current Analysis Context")
        
        results = st.session_state.current_results
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Market Domain", results.get('market_domain', 'N/A'))
        
        with col2:
            st.metric("Trends Found", len(results.get('market_trends', [])))
        
        with col3:
            st.metric("Opportunities", len(results.get('opportunities', [])))
        
        # Show analysis summary
        with st.expander("📊 Analysis Summary for Context"):
            st.write(f"**Query:** {results.get('query', 'N/A')}")
            st.write(f"**Market:** {results.get('market_domain', 'N/A')}")
            
            if results.get('market_trends'):
                st.write("**Top Trends:**")
                for i, trend in enumerate(results['market_trends'][:3], 1):
                    st.write(f"{i}. {trend.get('trend_name', 'Unknown')}")
            
            if results.get('opportunities'):
                st.write("**Top Opportunities:**")
                for i, opp in enumerate(results['opportunities'][:3], 1):
                    st.write(f"{i}. {opp.get('opportunity_name', 'Unknown')}")

def add_assistant_message(role: str, content: str):
    """Add a message to the assistant conversation"""
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    }
    st.session_state.assistant_messages.append(message)
    
    # Save to database
    db = DatabaseManager()
    db.save_chat_message(st.session_state.assistant_session_id, role, content)

def get_assistant_response(user_input: str) -> str:
    """Get response from the AI assistant"""
    try:
        # Prepare context from current analysis
        context = ""
        if st.session_state.get('current_results'):
            results = st.session_state.current_results
            context = f"""
Current Analysis Context:
- Market Domain: {results.get('market_domain', 'N/A')}
- Query: {results.get('query', 'N/A')}
- Trends Found: {len(results.get('market_trends', []))}
- Opportunities: {len(results.get('opportunities', []))}
- Recommendations: {len(results.get('strategic_recommendations', []))}

Recent Trends: {[t.get('trend_name', 'Unknown') for t in results.get('market_trends', [])[:3]]}
Recent Opportunities: {[o.get('opportunity_name', 'Unknown') for o in results.get('opportunities', [])[:3]]}
"""
        
        # Prepare conversation history
        messages = [
            {
                "role": "system",
                "content": f"""You are an expert market intelligence assistant. You help users understand and act on market research data.

{context}

Guidelines:
- Provide actionable insights and recommendations
- Reference the current analysis when relevant
- Be concise but comprehensive
- Use bullet points for clarity
- Suggest next steps when appropriate
- If asked about data not in the current analysis, acknowledge limitations and suggest how to get that information
"""
            }
        ]
        
        # Add recent conversation history (last 10 messages)
        recent_messages = st.session_state.assistant_messages[-10:]
        for msg in recent_messages:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add current user input
        messages.append({
            "role": "user",
            "content": user_input
        })
        
        # Get response from Groq
        response = st.session_state.groq_client.chat_completion(messages)
        return response
        
    except Exception as e:
        return f"I apologize, but I encountered an error: {str(e)}. Please try again or rephrase your question."

def create_analysis_summary_prompt(results: Dict[str, Any]) -> str:
    """Create a prompt for summarizing the current analysis"""
    return f"""
Please provide a comprehensive summary of my market intelligence analysis:

Market Domain: {results.get('market_domain', 'N/A')}
Query: {results.get('query', 'N/A')}

Key Findings:
- {len(results.get('market_trends', []))} market trends identified
- {len(results.get('opportunities', []))} opportunities found
- {len(results.get('strategic_recommendations', []))} strategic recommendations

Top Trends:
{chr(10).join([f"- {t.get('trend_name', 'Unknown')}: {t.get('description', 'No description')[:100]}..." for t in results.get('market_trends', [])[:3]])}

Top Opportunities:
{chr(10).join([f"- {o.get('opportunity_name', 'Unknown')}: {o.get('description', 'No description')[:100]}..." for o in results.get('opportunities', [])[:3]])}

Please summarize the key insights, highlight the most important findings, and suggest 3-5 actionable next steps.
"""

def render_assistant_analytics():
    """Render assistant usage analytics"""
    st.subheader("📈 Assistant Analytics")
    
    try:
        db = DatabaseManager()
        
        # Get conversation stats
        messages = db.load_chat_history(st.session_state.assistant_session_id)
        
        if messages:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Messages", len(messages))
            
            with col2:
                user_messages = [m for m in messages if m["type"] == "human"]
                st.metric("Your Questions", len(user_messages))
            
            with col3:
                ai_messages = [m for m in messages if m["type"] == "ai"]
                st.metric("AI Responses", len(ai_messages))
            
            # Show recent topics
            if user_messages:
                st.subheader("🔍 Recent Topics")
                for msg in user_messages[-5:]:
                    st.write(f"• {msg['content'][:100]}...")
        else:
            st.info("Start a conversation to see analytics!")
            
    except Exception as e:
        st.error(f"Failed to load analytics: {str(e)}")
