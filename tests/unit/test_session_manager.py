"""Unit tests for SessionManager."""

import pytest
import os
from app.core.session_manager import SessionManager
from app.models.session_state import SessionState


class TestSessionFinalization:
    """Tests for session finalization functionality."""
    
    def test_finalize_session(self):
        """Test that finalize_session marks session as complete."""
        manager = SessionManager()
        
        session = manager.create_session(
            session_name="Test Session",
            requirements="Test",
            selected_roles=["technical"],
            models_config={}
        )
        
        # Initially not finalized
        assert not manager.is_session_finalized()
        
        # Finalize it
        result = manager.finalize_session()
        
        assert result is True
        assert manager.is_session_finalized()
        assert session.is_finalized is True
    
    def test_finalize_session_no_active_session(self):
        """Test finalize_session returns False with no active session."""
        manager = SessionManager()
        
        result = manager.finalize_session()
        
        assert result is False
        assert not manager.is_session_finalized()
    
    def test_is_session_finalized_no_session(self):
        """Test is_session_finalized returns False with no session."""
        manager = SessionManager()
        
        assert not manager.is_session_finalized()
    
    def test_get_session_data(self):
        """Test get_session_data returns correct dictionary."""
        manager = SessionManager()
        
        session = manager.create_session(
            session_name="Data Test Session",
            requirements="Test requirements",
            selected_roles=["technical", "security"],
            models_config={"provider": "openai", "model": "gpt-4"}
        )
        
        data = manager.get_session_data()
        
        assert data is not None
        assert data['session_name'] == "Data Test Session"
        assert data['requirements'] == "Test requirements"
        assert len(data['selected_roles']) == 2
        assert data['provider'] == "openai"
        assert data['iteration'] == 0
        assert data['is_finalized'] is False
    
    def test_get_session_data_no_session(self):
        """Test get_session_data returns None with no active session."""
        manager = SessionManager()
        
        data = manager.get_session_data()
        
        assert data is None
    
    def test_finalize_session_persists_after_increment(self):
        """Test that finalization status persists after iteration increment."""
        manager = SessionManager()
        
        manager.create_session(
            session_name="Test",
            requirements="Test",
            selected_roles=["technical"],
            models_config={}
        )
        
        manager.finalize_session()
        assert manager.is_session_finalized()
        
        manager.increment_iteration()
        assert manager.is_session_finalized()  # Should still be finalized


class TestSessionManager:
    """Tests for SessionManager."""
    
    def test_session_manager_initialization(self):
        """Test that SessionManager can be initialized."""
        manager = SessionManager()
        
        assert manager is not None
        assert manager.current_session is None
        assert isinstance(manager.session_history, dict)
    
    def test_create_session(self):
        """Test that create_session creates a new session."""
        manager = SessionManager()
        
        session = manager.create_session(
            session_name="Test Session",
            requirements="Test requirements",
            selected_roles=["technical", "clarity"],
            models_config={"presenter": "mock-model"}
        )
        
        assert isinstance(session, SessionState)
        assert session.session_name == "Test Session"
        assert session.requirements == "Test requirements"
        assert len(session.selected_roles) == 2
        assert session.session_id is not None
    
    def test_create_session_generates_unique_id(self):
        """Test that each session gets a unique ID."""
        manager = SessionManager()
        
        session1 = manager.create_session(
            session_name="Session 1",
            requirements="Req 1",
            selected_roles=["technical"],
            models_config={}
        )
        
        session2 = manager.create_session(
            session_name="Session 2",
            requirements="Req 2",
            selected_roles=["clarity"],
            models_config={}
        )
        
        assert session1.session_id != session2.session_id
    
    def test_create_session_creates_temp_folder(self):
        """Test that create_session creates a temp folder."""
        manager = SessionManager()
        
        session = manager.create_session(
            session_name="Test Session",
            requirements="Test requirements",
            selected_roles=["technical"],
            models_config={}
        )
        
        assert session.temp_folder is not None
        assert os.path.exists(session.temp_folder)
        
        # Cleanup
        manager.end_session()
    
    def test_get_current_session(self):
        """Test that get_current_session returns the active session."""
        manager = SessionManager()
        
        # No session initially
        assert manager.get_current_session() is None
        
        # Create session
        session = manager.create_session(
            session_name="Test Session",
            requirements="Test requirements",
            selected_roles=["technical"],
            models_config={}
        )
        
        # Should return the session
        current = manager.get_current_session()
        assert current is not None
        assert current.session_id == session.session_id
        
        # Cleanup
        manager.end_session()
    
    def test_end_session_clears_current_session(self):
        """Test that end_session clears the current session."""
        manager = SessionManager()
        
        session = manager.create_session(
            session_name="Test Session",
            requirements="Test requirements",
            selected_roles=["technical"],
            models_config={}
        )
        
        assert manager.current_session is not None
        
        manager.end_session()
        
        assert manager.current_session is None
    
    def test_end_session_cleans_temp_folder(self):
        """Test that end_session removes the temp folder."""
        manager = SessionManager()
        
        session = manager.create_session(
            session_name="Test Session",
            requirements="Test requirements",
            selected_roles=["technical"],
            models_config={}
        )
        
        temp_folder = session.temp_folder
        assert os.path.exists(temp_folder)
        
        manager.end_session()
        
        assert not os.path.exists(temp_folder)
    
    def test_increment_iteration(self):
        """Test that increment_iteration increases iteration count."""
        manager = SessionManager()
        
        manager.create_session(
            session_name="Test Session",
            requirements="Test requirements",
            selected_roles=["technical"],
            models_config={}
        )
        
        assert manager.get_iteration() == 0
        
        manager.increment_iteration()
        assert manager.get_iteration() == 1
        
        manager.increment_iteration()
        assert manager.get_iteration() == 2
        
        # Cleanup
        manager.end_session()
    
    def test_increment_iteration_raises_without_session(self):
        """Test that increment_iteration raises error without active session."""
        manager = SessionManager()
        
        with pytest.raises(ValueError):
            manager.increment_iteration()
    
    def test_get_iteration_raises_without_session(self):
        """Test that get_iteration raises error without active session."""
        manager = SessionManager()
        
        with pytest.raises(ValueError):
            manager.get_iteration()

