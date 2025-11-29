"""Integration tests for UI page imports."""

import pytest


class TestUIPageImports:
    """Test that all UI pages can be imported without errors."""
    
    def test_import_start_session_page(self):
        """Test that start_session page can be imported."""
        try:
            from app.ui.pages import start_session
            assert hasattr(start_session, 'render')
        except ImportError as e:
            pytest.fail(f"Failed to import start_session: {e}")
    
    def test_import_llm_settings_page(self):
        """Test that llm_settings page can be imported."""
        try:
            from app.ui.pages import llm_settings
            assert hasattr(llm_settings, 'render')
        except ImportError as e:
            pytest.fail(f"Failed to import llm_settings: {e}")
    
    def test_import_review_session_page(self):
        """Test that review_session page can be imported."""
        try:
            from app.ui.pages import review_session
            assert hasattr(review_session, 'render')
        except ImportError as e:
            pytest.fail(f"Failed to import review_session: {e}")
    
    def test_all_pages_have_render_method(self):
        """Test that all pages have a render method."""
        from app.ui.pages import start_session, llm_settings, review_session
        
        assert callable(start_session.render)
        assert callable(llm_settings.render)
        assert callable(review_session.render)


class TestStreamlitAppImport:
    """Test that main streamlit app can be imported."""
    
    def test_import_streamlit_app(self):
        """Test that streamlit_app.py can be imported."""
        try:
            import streamlit_app
            assert hasattr(streamlit_app, 'main')
        except ImportError as e:
            pytest.fail(f"Failed to import streamlit_app: {e}")

