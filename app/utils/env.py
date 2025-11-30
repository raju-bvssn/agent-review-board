"""Environment detection utilities for Streamlit Cloud deployment."""

import os


def is_cloud() -> bool:
    """Detect if the app is running on Streamlit Cloud.
    
    Returns:
        True if running on Streamlit Cloud, False if running locally
    """
    # Streamlit Cloud sets this environment variable
    return os.environ.get("STREAMLIT_RUNTIME") == "cloud"


def is_local() -> bool:
    """Detect if the app is running locally.
    
    Returns:
        True if running locally, False if running on Streamlit Cloud
    """
    return not is_cloud()

