"""Start Session page for Agent Review Board.

ANTI-RECURSION PROTECTION:
Uses safe_navigation_change for page transitions to prevent recursion loops.
"""

import streamlit as st
from typing import List
from app.utils.rerun_guard import safe_navigation_change


def render():
    """Render the Start Session page.
    
    This page allows users to:
    - Enter session name and requirements
    - Upload reference files
    - Select reviewer roles (2-3)
    - Assign models to each agent
    - Start the review session
    
    Note: This is a UI skeleton only. Business logic will be added in Phase 2.
    """
    
    # Header
    st.title("🚀 Agent Review Board")
    st.subheader("Start New Session (Incognito Mode)")
    
    # Incognito notice banner
    st.info("🔒 **Incognito Mode Active** — No data is stored. Refresh clears everything.")
    
    st.markdown("---")
    
    # Session configuration section
    st.header("Session Configuration")
    
    # Session name input
    session_name = st.text_input(
        "Session Name",
        placeholder="e.g., Product Requirements Review",
        help="Give your session a memorable name"
    )
    
    # Requirements/description input
    requirements = st.text_area(
        "Description / Requirements",
        placeholder="Describe what you want the agents to review and refine...",
        height=150,
        help="Provide detailed requirements or description for the content you want to create"
    )
    
    # File uploader
    st.subheader("📎 Reference Files (Optional)")
    uploaded_files = st.file_uploader(
        "Upload reference documents, requirements, or context files",
        accept_multiple_files=True,
        help="Upload files that provide context or requirements"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) uploaded")
        with st.expander("View uploaded files"):
            for file in uploaded_files:
                st.text(f"• {file.name} ({file.size} bytes)")
    
    st.markdown("---")
    
    # Reviewer role selection section
    st.header("🎭 Select Reviewer Roles")
    st.caption("Choose 2-3 specialized reviewers for your session")
    
    # Available roles (hardcoded for Phase 1)
    available_roles = [
        "Technical Reviewer - Evaluates technical accuracy and best practices",
        "Clarity Reviewer - Focuses on readability and comprehension",
        "Security Reviewer - Checks for security and privacy concerns",
        "Business Reviewer - Assesses business value and feasibility",
        "UX Reviewer - Evaluates user experience and usability"
    ]
    
    # Suggested roles placeholder
    with st.expander("💡 Suggested Roles (based on requirements)"):
        st.info("Phase 1: Role suggestions will be implemented in Phase 2")
        st.markdown("For now, manually select 2-3 roles below.")
    
    # Role selection checkboxes
    selected_roles = []
    
    col1, col2 = st.columns(2)
    
    for idx, role in enumerate(available_roles):
        role_name = role.split(" - ")[0]
        role_desc = role.split(" - ")[1] if " - " in role else ""
        
        col = col1 if idx % 2 == 0 else col2
        with col:
            if st.checkbox(role_name, key=f"role_{idx}"):
                selected_roles.append(role_name)
    
    # Validation message for role count
    if len(selected_roles) < 2:
        st.warning("⚠️ Please select at least 2 reviewers")
    elif len(selected_roles) > 3:
        st.warning("⚠️ Maximum 3 reviewers allowed")
    else:
        st.success(f"✅ {len(selected_roles)} reviewers selected")
    
    st.markdown("---")
    
    # Model selection section
    st.header("🤖 Model Selection")
    st.caption("Assign models to each agent (Presenter + Reviewers)")
    
    # Load models from configured provider (or use mock as fallback)
    if 'llm_config' in st.session_state and 'available_models' in st.session_state:
        # Use models from configured provider
        available_models = st.session_state.available_models
        provider_name = st.session_state.llm_config.get('provider', 'Mock').upper()
        
        if available_models and len(available_models) > 0:
            st.info(f"📡 Using models from **{provider_name}** provider (configured in LLM Settings)")
        else:
            # Fallback if provider returned empty list
            available_models = ["mock-model-small", "mock-model-medium", "mock-model-large"]
            st.warning("⚠️ Provider returned no models. Using mock models as fallback.")
    else:
        # No provider configured - use mock models
        available_models = ["mock-model-small", "mock-model-medium", "mock-model-large"]
        
        col_warn1, col_warn2 = st.columns([3, 1])
        with col_warn1:
            st.warning("⚠️ No LLM provider configured. Using mock models for testing only.")
        with col_warn2:
            if st.button("⚙️ Configure Provider"):
                safe_navigation_change(st.session_state.get('current_page', 'start_session'), 'llm_settings')
    
    # Presenter model selection
    st.subheader("Presenter Agent")
    presenter_model = st.selectbox(
        "Select model for Presenter",
        available_models,
        key="presenter_model"
    )
    
    # Reviewer model selection
    if selected_roles:
        st.subheader("Reviewer Agents")
        reviewer_models = {}
        for role in selected_roles:
            model = st.selectbox(
                f"Select model for {role}",
                available_models,
                key=f"model_{role}"
            )
            reviewer_models[role] = model
    
    st.markdown("---")
    
    # Start session button
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Determine if button should be enabled
        can_start = (
            session_name and 
            requirements and 
            len(selected_roles) >= 2 and 
            len(selected_roles) <= 3
        )
        
        if st.button(
            "🚀 START SESSION",
            use_container_width=True,
            disabled=not can_start,
            type="primary"
        ):
            # Initialize session manager if not exists
            if 'session_manager' not in st.session_state:
                from app.core.session_manager import SessionManager
                st.session_state.session_manager = SessionManager()
            
            session_manager = st.session_state.session_manager
            
            # Create session
            try:
                # Build models config with provider information
                models_config = {
                    'presenter': presenter_model,
                    'provider': st.session_state.llm_config.get('provider', 'mock') if 'llm_config' in st.session_state else 'mock'
                }
                if selected_roles:
                    for role in selected_roles:
                        models_config[role] = reviewer_models.get(role, available_models[0])
                
                # Create session
                session = session_manager.create_session(
                    session_name=session_name,
                    requirements=requirements,
                    selected_roles=selected_roles,
                    models_config=models_config
                )
                
                # Handle uploaded files
                if uploaded_files:
                    for uploaded_file in uploaded_files:
                        content = uploaded_file.read()
                        session_manager.save_uploaded_file(uploaded_file.name, content)
                
                # Reset orchestrator for new session to ensure fresh iteration
                st.session_state.orchestrator = None
                
                # Store session config for UI
                st.session_state.session_config = {
                    'session_name': session_name,
                    'requirements': requirements,
                    'uploaded_files': uploaded_files,
                    'selected_roles': selected_roles,
                    'presenter_model': presenter_model,
                    'reviewer_models': reviewer_models
                }
                
                # Success and navigate
                st.success(f"✅ Session '{session_name}' created successfully!")
                st.info("Navigating to Review Session...")
                # WHY SAFE: safe_navigation_change checks if page differs before rerun
                safe_navigation_change(st.session_state.get('current_page', 'start_session'), 'review_session')
            
            except Exception as e:
                st.error(f"❌ Failed to create session: {str(e)}")
        
        if not can_start:
            st.caption("Complete all required fields to start session")

