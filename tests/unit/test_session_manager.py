"""Unit tests for SessionManager."""

import pytest
import os
from app.core.session_manager import SessionManager
from app.models.session_state import SessionState


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

