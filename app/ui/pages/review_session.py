"""Review Session page - main review board interface.

ANTI-RECURSION PROTECTION:
This page uses RerunGuard to prevent iteration loops and safe_navigation_change
for page transitions. All reruns are eliminated in favor of natural Streamlit
refresh cycles after button clicks.
"""

import streamlit as st
from app.core.session_manager import SessionManager
from app.core.orchestrator import Orchestrator
from app.llm.provider_factory import ProviderFactory
from app.utils.rerun_guard import RerunGuard, safe_navigation_change


def init_session_objects():
    """Initialize session manager and orchestrator if not already done."""
    if 'session_manager' not in st.session_state:
        st.session_state.session_manager = SessionManager()
    
    if 'orchestrator' not in st.session_state:
        st.session_state.orchestrator = None


def render():
    """Render the Review Session page.
    
    This page displays:
    - 3-panel layout (Presenter Output, Reviewer Board, Confidence Overview)
    - HITL indicator and controls
    - Iteration progress
    """
    
    init_session_objects()
    
    # Header
    st.title("📊 Review Session")
    
    # HITL mandatory notice banner
    st.info("🚨 **Human-In-The-Loop: Enabled (Mandatory)** — Review and approve all feedback before proceeding")
    
    # Check if we have an active session
    session_manager = st.session_state.session_manager
    current_session = session_manager.get_current_session()
    
    if not current_session:
        st.warning("⚠️ No active session. Please start a session first.")
        
        if st.button("🚀 Go to Start Session"):
            # WHY SAFE: safe_navigation_change only reruns if page actually changes
            safe_navigation_change(st.session_state.current_page, 'start_session')
        
        return
    
    # Session info bar
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Session", current_session.session_name)
    
    with col2:
        st.metric("Iteration", current_session.iteration)
    
    with col3:
        st.metric("Reviewers", len(current_session.selected_roles))
    
    with col4:
        # Get confidence from orchestrator if available
        confidence_score = "N/A"
        if st.session_state.orchestrator:
            current_result = st.session_state.orchestrator.get_current_result()
            if current_result and current_result.confidence_result:
                confidence_score = f"{current_result.confidence_result.get('score', 0):.0f}/100"
        st.metric("Confidence", confidence_score)
    
    st.markdown("---")
    
    # Check if provider is configured
    if 'llm_config' not in st.session_state or not st.session_state.llm_config.get('provider'):
        st.error("❌ LLM Provider not configured. Please configure a provider first.")
        if st.button("⚙️ Go to LLM Settings"):
            # WHY SAFE: safe_navigation_change only reruns if page actually changes
            safe_navigation_change(st.session_state.current_page, 'llm_settings')
        return
    
    # Initialize orchestrator if needed
    if not st.session_state.orchestrator:
        try:
            provider = ProviderFactory.create_provider(
                st.session_state.llm_config['provider'],
                st.session_state.llm_config.get('api_key')
            )
            st.session_state.orchestrator = Orchestrator(session_manager, provider)
        except Exception as e:
            st.error(f"Failed to initialize orchestrator: {str(e)}")
            return
    
    orchestrator = st.session_state.orchestrator
    
    # Control buttons
    col_control1, col_control2, col_control3 = st.columns([1, 1, 1])
    
    with col_control1:
        run_iteration_clicked = st.button(
            "▶️ Run Iteration",
            use_container_width=True,
            type="primary",
            disabled=orchestrator.can_proceed_to_next_iteration() if current_session.iteration > 0 else False
        )
    
    with col_control2:
        regenerate_clicked = st.button(
            "🔄 Regenerate",
            use_container_width=True,
            disabled=not orchestrator.get_current_result()
        )
    
    with col_control3:
        end_session_clicked = st.button(
            "🛑 End Session",
            use_container_width=True,
            type="secondary"
        )
    
    # Handle button clicks
    if run_iteration_clicked:
        run_iteration(current_session, session_manager, orchestrator)
    
    if regenerate_clicked:
        orchestrator.reject_current_iteration()
        run_iteration(current_session, session_manager, orchestrator)
    
    if end_session_clicked:
        session_manager.end_session()
        st.session_state.orchestrator = None
        st.success("✅ Session ended")
        # WHY NO RERUN: End session naturally refreshes, navigate via sidebar
    
    st.markdown("---")
    
    # Get current result
    current_result = orchestrator.get_current_result()
    
    if not current_result:
        st.info("👆 Click 'Run Iteration' to start the review process")
        return
    
    # Display error if present
    if current_result.error:
        st.error(f"❌ Error: {current_result.error}")
        return
    
    # Panel 1: Presenter Output
    st.header("📝 Panel 1: Presenter Output")
    
    with st.container():
        presenter_tab1, presenter_tab2 = st.tabs(["Current Output", "History"])
        
        with presenter_tab1:
            if current_result.presenter_output:
                st.markdown(current_result.presenter_output)
            else:
                st.info("No presenter output yet")
        
        with presenter_tab2:
            history = orchestrator.get_iteration_history()
            if len(history) > 1:
                for i, result in enumerate(history[:-1], 1):
                    with st.expander(f"Iteration {i}"):
                        st.markdown(result.presenter_output)
            else:
                st.caption("No previous iterations")
    
    st.markdown("---")
    
    # Panel 2: Reviewer Agents Board
    st.header("🎭 Panel 2: Reviewer Feedback")
    
    if current_result.reviewer_feedback:
        # Create columns for reviewers
        reviewer_cols = st.columns(len(current_result.reviewer_feedback))
        
        for idx, feedback in enumerate(current_result.reviewer_feedback):
            with reviewer_cols[idx]:
                render_reviewer_card(feedback, idx)
    else:
        st.info("No reviewer feedback yet")
    
    st.markdown("---")
    
    # Panel 3: Confidence Overview
    st.header("📊 Panel 3: Confidence Overview")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Confidence Score")
        
        if current_result.confidence_result:
            score = current_result.confidence_result.get('score', 0)
            reasoning = current_result.confidence_result.get('reasoning', '')
            
            # Progress bar
            st.progress(score / 100)
            st.caption(f"Confidence: {score:.0f}/100")
            
            # Reasoning
            st.info(reasoning)
            
            # Convergence metrics
            with st.expander("📈 Convergence Metrics"):
                history = orchestrator.get_iteration_history()
                if len(history) > 1:
                    scores = [h.confidence_result.get('score', 0) for h in history]
                    st.line_chart(scores)
                    st.caption("Confidence score trend across iterations")
                else:
                    st.caption("Need multiple iterations for trend analysis")
        else:
            st.info("No confidence score available")
    
    with col2:
        st.subheader("Actions")
        
        # HITL Approval
        if current_result and not current_result.human_gate_approved:
            st.warning("⚠️ Requires Human Approval")
            
            if st.button(
                "✅ Approve & Continue",
                use_container_width=True,
                type="primary"
            ):
                orchestrator.approve_current_iteration()
                st.success("✅ Approved! You can now run the next iteration.")
        else:
            st.success("✅ Iteration Approved")
            st.caption("Ready for next iteration")
    
    st.markdown("---")
    
    # Iteration log section
    with st.expander("📋 Iteration Log"):
        history = orchestrator.get_iteration_history()
        if history:
            for result in history:
                st.text(f"Iteration {result.iteration}: Score {result.confidence_result.get('score', 0):.0f}/100")
        else:
            st.text("No iterations yet")


def run_iteration(current_session, session_manager, orchestrator):
    """Run a full iteration cycle.
    
    ANTI-RECURSION: Protected by RerunGuard to prevent nested execution.
    
    Args:
        current_session: Current session state
        session_manager: Session manager instance
        orchestrator: Orchestrator instance
    """
    try:
        # CRITICAL: RerunGuard prevents recursive iteration calls
        with RerunGuard("run_iteration"):
            # Get session configuration
            config = st.session_state.get('session_config', {})
            requirements = current_session.requirements
            selected_roles = current_session.selected_roles
            
            # Get approved feedback from previous iteration if any
            approved_feedback = None
            if current_session.iteration > 0 and orchestrator.can_proceed_to_next_iteration():
                approved_feedback = orchestrator.get_approved_feedback()
            
            # Show spinner (outside of critical section if possible)
            with st.spinner("🤖 Running iteration... This may take a minute..."):
                # Run iteration
                result = orchestrator.run_iteration(
                    requirements=requirements,
                    selected_roles=selected_roles,
                    approved_feedback=approved_feedback
                )
            
            if result.error:
                st.error(f"❌ Iteration failed: {result.error}")
            else:
                st.success("✅ Iteration complete! Review the feedback below.")
            
            # WHY NO RERUN: Streamlit naturally refreshes after button click completes
    
    except RuntimeError as e:
        if "RECURSION BLOCKED" in str(e):
            st.error("⚠️ Iteration already in progress. Please wait for completion.")
        else:
            raise
    
    except Exception as e:
        st.error(f"❌ Failed to run iteration: {str(e)}")


def render_reviewer_card(feedback, idx):
    """Render a reviewer feedback card.
    
    Args:
        feedback: Feedback object
        idx: Index for unique keys
    """
    st.subheader(f"👤 {feedback.reviewer_role.replace('_', ' ').title()}")
    
    # Status badge
    if feedback.approved:
        if feedback.modified:
            st.success("✅ Approved (Modified)")
        else:
            st.success("✅ Approved")
    else:
        st.warning("⏳ Pending Approval")
    
    # Feedback points
    st.caption(f"Feedback ({len(feedback.feedback_points)} points):")
    
    for i, point in enumerate(feedback.feedback_points, 1):
        st.markdown(f"{i}. {point}")
    
    # Modification option
    with st.expander("✏️ Modify Feedback"):
        modified_points = st.text_area(
            "Edit feedback points (one per line)",
            value="\n".join(feedback.feedback_points),
            key=f"modify_{feedback.reviewer_role}_{idx}",
            height=150
        )
        
        if st.button("Save Changes", key=f"save_{feedback.reviewer_role}_{idx}"):
            new_points = [p.strip() for p in modified_points.split('\n') if p.strip()]
            if len(new_points) > 0:
                feedback.feedback_points = new_points[:8]  # Max 8
                feedback.modified = True
                st.success("Changes saved!")
