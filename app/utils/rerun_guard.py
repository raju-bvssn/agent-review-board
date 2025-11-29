"""Rerun Guard Utility - Prevents Streamlit Recursion Loops.

This module provides defensive programming utilities to prevent infinite
recursion loops caused by improper use of st.rerun().

WHY THIS MATTERS:
- st.rerun() can cause infinite loops if called unconditionally
- Button callbacks persist across reruns, causing recursive execution
- Navigation changes need careful state management to avoid loops

RULES ENFORCED:
1. Never call st.rerun() without a state change
2. Never call st.rerun() if already in a rerun cycle
3. Track rerun depth to prevent deep recursion
4. Log all rerun attempts for debugging

Usage:
    from app.utils.rerun_guard import safe_rerun, should_rerun
    
    # Instead of st.rerun(), use:
    if should_rerun(old_state, new_state):
        safe_rerun(reason="State changed from X to Y")
"""

import streamlit as st
from typing import Any, Optional
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Maximum recursion depth allowed
MAX_RERUN_DEPTH = 3

# Session state keys for tracking
_RERUN_IN_PROGRESS_KEY = "_rerun_in_progress"
_RERUN_DEPTH_KEY = "_rerun_depth"
_LAST_RERUN_REASON_KEY = "_last_rerun_reason"
_RERUN_HISTORY_KEY = "_rerun_history"


def init_rerun_guards():
    """Initialize rerun guard flags in session state.
    
    Call this once at app startup to ensure tracking state exists.
    """
    if _RERUN_IN_PROGRESS_KEY not in st.session_state:
        st.session_state[_RERUN_IN_PROGRESS_KEY] = False
    
    if _RERUN_DEPTH_KEY not in st.session_state:
        st.session_state[_RERUN_DEPTH_KEY] = 0
    
    if _RERUN_HISTORY_KEY not in st.session_state:
        st.session_state[_RERUN_HISTORY_KEY] = []


def get_rerun_depth() -> int:
    """Get current rerun depth.
    
    Returns:
        Current depth level (0 = no reruns)
    """
    init_rerun_guards()
    return st.session_state.get(_RERUN_DEPTH_KEY, 0)


def is_rerun_in_progress() -> bool:
    """Check if a rerun is currently in progress.
    
    Returns:
        True if rerun flag is set, False otherwise
    """
    init_rerun_guards()
    return st.session_state.get(_RERUN_IN_PROGRESS_KEY, False)


def should_rerun(old_value: Any, new_value: Any) -> bool:
    """Check if a rerun is needed based on value change.
    
    This is the key defensive check - only rerun if value actually changed.
    
    Args:
        old_value: Previous state value
        new_value: New state value
        
    Returns:
        True if values differ and rerun is safe, False otherwise
    """
    init_rerun_guards()
    
    # No rerun if values are the same
    if old_value == new_value:
        logger.debug(f"No rerun needed: values identical ({old_value})")
        return False
    
    # No rerun if already in progress
    if is_rerun_in_progress():
        logger.warning("Rerun blocked: already in progress")
        return False
    
    # No rerun if depth exceeded
    current_depth = get_rerun_depth()
    if current_depth >= MAX_RERUN_DEPTH:
        logger.error(f"Rerun blocked: max depth {MAX_RERUN_DEPTH} exceeded (current: {current_depth})")
        return False
    
    return True


def safe_rerun(reason: Optional[str] = None, force: bool = False):
    """Safely trigger a Streamlit rerun with recursion protection.
    
    This is the ONLY function that should call st.rerun() in the entire app.
    
    Args:
        reason: Optional description of why rerun is needed (for debugging)
        force: If True, skip safety checks (use with extreme caution!)
        
    Raises:
        RuntimeError: If rerun would cause recursion
    """
    init_rerun_guards()
    
    # Safety checks (unless forced)
    if not force:
        if is_rerun_in_progress():
            error_msg = "RECURSION BLOCKED: Attempted rerun while already in progress"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        current_depth = get_rerun_depth()
        if current_depth >= MAX_RERUN_DEPTH:
            error_msg = f"RECURSION BLOCKED: Max depth {MAX_RERUN_DEPTH} exceeded"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    # Set rerun flag
    st.session_state[_RERUN_IN_PROGRESS_KEY] = True
    st.session_state[_RERUN_DEPTH_KEY] = get_rerun_depth() + 1
    
    # Log the rerun
    if reason:
        st.session_state[_LAST_RERUN_REASON_KEY] = reason
        logger.info(f"RERUN TRIGGERED: {reason} (depth: {get_rerun_depth()})")
    
    # Add to history for debugging
    history = st.session_state.get(_RERUN_HISTORY_KEY, [])
    history.append({
        "depth": get_rerun_depth(),
        "reason": reason or "No reason provided",
        "forced": force
    })
    st.session_state[_RERUN_HISTORY_KEY] = history[-10:]  # Keep last 10
    
    # Actual rerun
    st.rerun()


def reset_rerun_guards():
    """Reset rerun guards after successful execution.
    
    This should be called at the end of each page render to clear flags.
    """
    init_rerun_guards()
    st.session_state[_RERUN_IN_PROGRESS_KEY] = False
    st.session_state[_RERUN_DEPTH_KEY] = 0


def get_rerun_history() -> list:
    """Get history of recent reruns for debugging.
    
    Returns:
        List of recent rerun events with reasons and depths
    """
    init_rerun_guards()
    return st.session_state.get(_RERUN_HISTORY_KEY, [])


def safe_navigation_change(current_page: str, new_page: str):
    """Safely change page with recursion protection.
    
    This is a specialized helper for navigation buttons.
    
    Args:
        current_page: Current page name in session state
        new_page: Target page name
    """
    if should_rerun(current_page, new_page):
        st.session_state.current_page = new_page
        safe_rerun(reason=f"Navigation: {current_page} -> {new_page}")


class RerunGuard:
    """Context manager to protect code blocks from recursion.
    
    Usage:
        with RerunGuard("iteration_execution"):
            # Code that might trigger reruns
            run_iteration()
    """
    
    def __init__(self, operation_name: str):
        """Initialize guard.
        
        Args:
            operation_name: Name of the operation being protected
        """
        self.operation_name = operation_name
        self.guard_key = f"_guard_{operation_name}"
    
    def __enter__(self):
        """Enter guard context."""
        if st.session_state.get(self.guard_key, False):
            raise RuntimeError(
                f"RECURSION BLOCKED: Operation '{self.operation_name}' "
                f"already in progress"
            )
        st.session_state[self.guard_key] = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit guard context."""
        st.session_state[self.guard_key] = False
        return False  # Don't suppress exceptions


def check_recursion_safety():
    """Check if app is in a safe state (no active recursion).
    
    Returns:
        Tuple of (is_safe: bool, warning_message: str)
    """
    init_rerun_guards()
    
    depth = get_rerun_depth()
    in_progress = is_rerun_in_progress()
    
    if depth >= MAX_RERUN_DEPTH:
        return False, f"⚠️ Rerun depth {depth} exceeds maximum {MAX_RERUN_DEPTH}"
    
    if in_progress:
        return False, "⚠️ Rerun currently in progress"
    
    return True, "✅ Recursion checks passed"

