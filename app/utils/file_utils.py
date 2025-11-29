"""File utility functions."""

import os
import shutil
import tempfile
from typing import Optional
from pathlib import Path


def create_session_temp_folder(session_id: str) -> str:
    """Create a temporary folder for a session.
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        Path to the created temporary folder
        
    Raises:
        OSError: If folder creation fails
    """
    temp_base = tempfile.gettempdir()
    session_folder = os.path.join(temp_base, f"arb_session_{session_id}")
    
    os.makedirs(session_folder, exist_ok=True)
    
    return session_folder


def cleanup_session_temp_folder(session_folder: str) -> bool:
    """Clean up and remove a session's temporary folder.
    
    Args:
        session_folder: Path to the session folder to remove
        
    Returns:
        True if cleanup successful, False otherwise
    """
    try:
        if os.path.exists(session_folder):
            shutil.rmtree(session_folder)
        return True
    except Exception as e:
        # Log error but don't raise - cleanup is best effort
        print(f"Warning: Failed to cleanup temp folder {session_folder}: {e}")
        return False


def save_uploaded_file(uploaded_file_content: bytes, filename: str, session_folder: str) -> str:
    """Save an uploaded file to the session temp folder.
    
    Args:
        uploaded_file_content: File content as bytes
        filename: Original filename
        session_folder: Session temporary folder path
        
    Returns:
        Path to the saved file
        
    Raises:
        OSError: If file save fails
    """
    file_path = os.path.join(session_folder, filename)
    
    with open(file_path, 'wb') as f:
        f.write(uploaded_file_content)
    
    return file_path


def read_file_content(file_path: str) -> str:
    """Read content from a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File content as string
        
    Raises:
        OSError: If file read fails
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def write_file_content(file_path: str, content: str) -> None:
    """Write content to a file.
    
    Args:
        file_path: Path to the file
        content: Content to write
        
    Raises:
        OSError: If file write fails
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def ensure_directory_exists(directory_path: str) -> None:
    """Ensure a directory exists, creating it if necessary.
    
    Args:
        directory_path: Path to the directory
        
    Raises:
        OSError: If directory creation fails
    """
    Path(directory_path).mkdir(parents=True, exist_ok=True)

