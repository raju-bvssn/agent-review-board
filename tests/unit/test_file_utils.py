"""Unit tests for file utilities."""

import pytest
import os
import tempfile
from app.utils.file_utils import (
    create_session_temp_folder,
    cleanup_session_temp_folder,
    save_uploaded_file,
    read_file_content,
    write_file_content,
    ensure_directory_exists
)


class TestFileUtils:
    """Tests for file utility functions."""
    
    def test_create_session_temp_folder(self):
        """Test that create_session_temp_folder creates a folder."""
        session_id = "test-session-123"
        
        folder = create_session_temp_folder(session_id)
        
        assert os.path.exists(folder)
        assert session_id in folder
        
        # Cleanup
        cleanup_session_temp_folder(folder)
    
    def test_create_session_temp_folder_is_unique(self):
        """Test that each session gets a unique folder."""
        folder1 = create_session_temp_folder("session-1")
        folder2 = create_session_temp_folder("session-2")
        
        assert folder1 != folder2
        assert os.path.exists(folder1)
        assert os.path.exists(folder2)
        
        # Cleanup
        cleanup_session_temp_folder(folder1)
        cleanup_session_temp_folder(folder2)
    
    def test_cleanup_session_temp_folder(self):
        """Test that cleanup_session_temp_folder removes the folder."""
        folder = create_session_temp_folder("test-cleanup")
        
        assert os.path.exists(folder)
        
        success = cleanup_session_temp_folder(folder)
        
        assert success is True
        assert not os.path.exists(folder)
    
    def test_cleanup_nonexistent_folder(self):
        """Test that cleanup handles nonexistent folders gracefully."""
        success = cleanup_session_temp_folder("/tmp/nonexistent-folder-xyz")
        
        # Should return True (no-op)
        assert success is True
    
    def test_save_uploaded_file(self):
        """Test that save_uploaded_file saves content correctly."""
        folder = create_session_temp_folder("test-upload")
        
        content = b"Test file content"
        filename = "test.txt"
        
        file_path = save_uploaded_file(content, filename, folder)
        
        assert os.path.exists(file_path)
        assert filename in file_path
        
        # Verify content
        with open(file_path, 'rb') as f:
            saved_content = f.read()
        
        assert saved_content == content
        
        # Cleanup
        cleanup_session_temp_folder(folder)
    
    def test_read_file_content(self):
        """Test that read_file_content reads file correctly."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Test content")
            temp_path = f.name
        
        try:
            content = read_file_content(temp_path)
            assert content == "Test content"
        finally:
            os.unlink(temp_path)
    
    def test_write_file_content(self):
        """Test that write_file_content writes file correctly."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_path = f.name
        
        try:
            content = "New test content"
            write_file_content(temp_path, content)
            
            # Verify
            with open(temp_path, 'r') as f:
                saved_content = f.read()
            
            assert saved_content == content
        finally:
            os.unlink(temp_path)
    
    def test_ensure_directory_exists(self):
        """Test that ensure_directory_exists creates directories."""
        temp_base = tempfile.gettempdir()
        test_dir = os.path.join(temp_base, "test_arb_dir_xyz")
        
        # Remove if exists
        if os.path.exists(test_dir):
            os.rmdir(test_dir)
        
        ensure_directory_exists(test_dir)
        
        assert os.path.exists(test_dir)
        assert os.path.isdir(test_dir)
        
        # Cleanup
        os.rmdir(test_dir)
    
    def test_ensure_directory_exists_nested(self):
        """Test that ensure_directory_exists creates nested directories."""
        temp_base = tempfile.gettempdir()
        test_dir = os.path.join(temp_base, "test_arb_nested", "subdir", "deep")
        
        ensure_directory_exists(test_dir)
        
        assert os.path.exists(test_dir)
        
        # Cleanup
        import shutil
        shutil.rmtree(os.path.join(temp_base, "test_arb_nested"))

