"""Pytest configuration and fixtures."""

import pytest
import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)


@pytest.fixture
def mock_llm_provider():
    """Fixture providing a MockLLMProvider instance."""
    from app.llm.mock_provider import MockLLMProvider
    provider = MockLLMProvider()
    yield provider
    provider.reset()


@pytest.fixture
def session_manager():
    """Fixture providing a SessionManager instance."""
    from app.core.session_manager import SessionManager
    manager = SessionManager()
    yield manager
    # Cleanup any active session
    if manager.current_session:
        manager.end_session()


@pytest.fixture
def presenter_agent(mock_llm_provider):
    """Fixture providing a PresenterAgent instance."""
    from app.agents.presenter import PresenterAgent
    return PresenterAgent(mock_llm_provider)


@pytest.fixture
def technical_reviewer(mock_llm_provider):
    """Fixture providing a TechnicalReviewer instance."""
    from app.agents.reviewer import TechnicalReviewer
    return TechnicalReviewer(mock_llm_provider)


@pytest.fixture
def confidence_agent(mock_llm_provider):
    """Fixture providing a ConfidenceAgent instance."""
    from app.agents.confidence import ConfidenceAgent
    return ConfidenceAgent(mock_llm_provider)

