"""Agent Review Board - Main Streamlit Application.

This is the entry point for the Agent Review Board application.
It handles routing between different pages and manages the sidebar navigation.

ANTI-RECURSION PROTECTION:
This module uses safe_rerun utilities to prevent infinite recursion loops.
All navigation changes go through safe_navigation_change() which checks
if the target page differs from current page before triggering rerun.
"""

import streamlit as st

# CRITICAL: Page config must be the first Streamlit command
st.set_page_config(
    page_title="Agent Review Board",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state safely (prevents cloud refresh issues)
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.current_page = "start_session"

from app.ui.pages import start_session, llm_settings, review_session
from app.utils.rerun_guard import init_rerun_guards, safe_navigation_change, reset_rerun_guards
from app.ui.theme.theme_manager import apply_liquid_glass_theme_once
from app.utils.env import is_cloud


def main():
    """Main application entry point.
    
    ANTI-RECURSION: Initializes rerun guards to prevent infinite loops.
    """
    
    # Apply Liquid Glass theme (CSS only - no logic changes)
    theme_html = apply_liquid_glass_theme_once()
    if theme_html:
        st.markdown(theme_html, unsafe_allow_html=True)
    
    # Initialize rerun guards (CRITICAL: must be first)
    init_rerun_guards()
    
    # Sidebar navigation
    st.sidebar.title("🤖 Agent Review Board")
    
    # Show cloud deployment banner if running on Streamlit Cloud
    if is_cloud():
        st.sidebar.info("☁️ Running on Streamlit Cloud – API keys required in Secrets.")
    
    st.sidebar.markdown("---")
    
    # Navigation buttons with anti-recursion protection
    # WHY SAFE: safe_navigation_change only reruns if page actually changes
    if st.sidebar.button("🚀 Start Session", use_container_width=True):
        safe_navigation_change(st.session_state.current_page, 'start_session')
    
    if st.sidebar.button("⚙️ LLM Settings", use_container_width=True):
        safe_navigation_change(st.session_state.current_page, 'llm_settings')
    
    if st.sidebar.button("📊 Review Session", use_container_width=True):
        safe_navigation_change(st.session_state.current_page, 'review_session')
    
    st.sidebar.markdown("---")
    
    # About section
    with st.sidebar.expander("ℹ️ About / Incognito Mode"):
        st.markdown("""
        ### Agent Review Board
        
        A multi-agent system for iterative content refinement with 
        mandatory human-in-the-loop oversight.
        
        ### 🔒 Incognito Mode
        
        **No data is stored persistently.**
        
        - All session data lives in memory only
        - API keys are cleared on exit
        - Uploaded files are temporary
        - **Browser refresh clears everything**
        
        Your privacy is guaranteed.
        """)
    
    # Route to appropriate page
    if st.session_state.current_page == 'start_session':
        start_session.render()
    elif st.session_state.current_page == 'llm_settings':
        llm_settings.render()
    elif st.session_state.current_page == 'review_session':
        review_session.render()
    else:
        # Default to start session
        start_session.render()
    
    # Reset rerun guards after successful page render
    # WHY: Clears the _rerun_in_progress flag so next cycle is clean
    reset_rerun_guards()


if __name__ == "__main__":
    main()

