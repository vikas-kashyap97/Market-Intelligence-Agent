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
    
    # Report file path
    state_id = results.get("state_id", "unknown")
    market_domain = results.get("market_domain", "unknown")
    report_filename = f"{market_domain.lower().replace(' ', '_')}_report_{state_id[:4]}.md"
    report_path = os.path.join(report_dir, report_filename)
    
    # Header with download options
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.subheader(f"📋 Report: {state_id[:8]}")
    
    with col2:
        if st.button("📥 Download Report"):
            download_report(report_path)
    
    with col3:
        if st.button("📦 Download All"):
            download_all_files(report_dir)
    
    # Report content
    if os.path.exists(report_path):
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                report_content = f.read()
            
            # Display report
            st.markdown("---")
            st.markdown(report_content)
            
            # File info
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
    st.subheader("📁 Additional Files")
    
    # List all files in report directory
    if os.path.exists(report_dir):
        files = os.listdir(report_dir)
        if files:
            for file in sorted(files):
                file_path = os.path.join(report_dir, file)
                if os.path.isfile(file_path):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.text(file)
                    with col2:
                        st.text(f"{get_file_size_mb(file_path):.2f} MB")
                    with col3:
                        if st.button("⬇️", key=f"download_{file}"):
                            download_file(file_path, file)
        else:
            st.info("No additional files found.")

def download_report(report_path: str):
    """Download the main report file"""
    try:
        with open(report_path, "rb") as f:
            st.download_button(
                label="📄 Download Markdown Report",
                data=f.read(),
                file_name=os.path.basename(report_path),
                mime="text/markdown"
            )
    except Exception as e:
        st.error(f"❌ Error downloading report: {str(e)}")

def download_file(file_path: str, filename: str):
    """Download a specific file"""
    try:
        with open(file_path, "rb") as f:
            st.download_button(
                label=f"📥 Download {filename}",
                data=f.read(),
                file_name=filename,
                key=f"download_btn_{filename}"
            )
    except Exception as e:
        st.error(f"❌ Error downloading {filename}: {str(e)}")

def download_all_files(report_dir: str):
    """Download all files as a ZIP archive"""
    try:
        # Create temporary ZIP file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
            with zipfile.ZipFile(tmp_file.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(report_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, report_dir)
                        zipf.write(file_path, arcname)
            
            # Download ZIP file
            with open(tmp_file.name, "rb") as f:
                st.download_button(
                    label="📦 Download Complete Analysis Package",
                    data=f.read(),
                    file_name=f"market_intelligence_{os.path.basename(report_dir)}.zip",
                    mime="application/zip"
                )
            
            # Clean up temporary file
            os.unlink(tmp_file.name)
            
    except Exception as e:
        st.error(f"❌ Error creating download package: {str(e)}")
