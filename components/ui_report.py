import streamlit as st
import os
from typing import Dict, Any
from core.utils import get_file_size_mb
import zipfile
import tempfile

def render_report_ui():
    """Render the report viewing interface"""
    st.title("📄 Intelligence Report")
    
    if not st.session_state.get('analysis_complete') or not st.session_state.get('current_results'):
        st.warning("⚠️ No analysis results available. Please run an analysis first.")
        return
    
    results = st.session_state.current_results

    if not results.get("success"):
        st.error("❌ Analysis failed. No report available.")
        return

    report_dir = results.get("report_dir")
    if not report_dir or not os.path.exists(report_dir):
        st.error("📁 Report directory not found.")
        return

    # Extract info
    state_id = results.get("state_id", "unknown")
    question = results.get("question") or results.get("query")
    market_domain = results.get("market_domain", "Unknown Domain")

    # Try to find the report file dynamically
    report_filename = next((f for f in os.listdir(report_dir) if f.endswith('.md')), None)
    if report_filename:
        report_path = os.path.join(report_dir, report_filename)
    else:
        st.error("📄 No markdown report file found in report directory.")
        return

    # Header with download options
    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader(f"📋 {market_domain} Analysis Report")
        if question and question.strip():
            short_question = question[:80] + "..." if len(question) > 80 else question
            st.caption(f"🔍 Query: {short_question}")
        st.caption(f"📊 Report ID: {state_id[:8] if state_id != 'unknown' else 'N/A'}")

    with col2:
        # Create a ZIP package for download
        try:
            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
            tmp_file.close()  # Prevent Windows locking issue

            with zipfile.ZipFile(tmp_file.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(report_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, report_dir)
                        zipf.write(file_path, arcname)

            with open(tmp_file.name, "rb") as f:
                zip_data = f.read()

            st.download_button(
                label="📦 Download Complete Analysis Package",
                data=zip_data,
                file_name=f"market_intelligence_{os.path.basename(report_dir)}.zip",
                mime="application/zip",
                key="download_complete_package"
            )

            os.unlink(tmp_file.name)

        except Exception as e:
            st.error(f"❌ Error creating download package: {str(e)}")

    # Display report content
    if os.path.exists(report_path):
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                report_content = f.read()

            st.markdown("---")
            st.markdown(report_content)

            # Report info
            st.markdown("---")
            st.subheader("📊 Report Information")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("File Size", f"{get_file_size_mb(report_path):.2f} MB")
            with col2:
                st.metric("State ID", state_id[:8])

        except Exception as e:
            st.error(f"❌ Error reading report: {str(e)}")
    else:
        st.error("📄 Report file not found.")

    # Additional files section
    st.markdown("---")
    st.subheader("📁 Report Contents")

    if os.path.exists(report_dir):
        files = os.listdir(report_dir)
        if files:
            for file in sorted(files):
                file_path = os.path.join(report_dir, file)
                if os.path.isfile(file_path):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.text(f"📄 {file}")
                    with col2:
                        st.text(f"{get_file_size_mb(file_path):.2f} MB")
        else:
            st.info("No files found in report directory.")
