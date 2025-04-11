"""
Local filesystem storage implementation for the Cryptopedia application.
"""
import os
import aiofiles
from typing import Optional
from .base import StorageInterface

class LocalStorage(StorageInterface):
    """
    Local file system storage implementation.
    """
    def __init__(self, media_folder: str, base_url: str = "/media"):
        """
        Initialize local storage with the media folder path.
        
        Args:
            media_folder: Path to directory where files will be stored
            base_url: Base URL path for accessing the media files
        """
        self.media_folder = media_folder
        self.base_url = base_url
        
        # Create the media folder if it doesn't exist
        os.makedirs(media_folder, exist_ok=True)
    
    async def save_file(self, file_content: bytes, filename: str, content_type: Optional[str] = None) -> str:
        """
        Save a file to local storage and return its path.
        
        Args:
            file_content: The binary content of the file
            filename: The name to save the file as
            content_type: The MIME type of the file (not used for local storage)
            
        Returns:
            str: The relative URL path to the file
        """
        file_path = os.path.join(self.media_folder, filename)
        
        # Use aiofiles for non-blocking file I/O
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_content)
        
        # Return the relative URL path
        return f"{self.base_url}/{filename}"
    
    async def get_file(self, filename: str) -> Optional[bytes]:
        """
        Get a file's content from local storage.
        
        Args:
            filename: The name of the file to retrieve
            
        Returns:
            bytes: The content of the file, or None if not found
        """
        file_path = os.path.join(self.media_folder, filename)
        
        if not os.path.exists(file_path):
            return None
        
        async with aiofiles.open(file_path, "rb") as f:
            return await f.read()
    
    async def delete_file(self, filename: str) -> bool:
        """
        Delete a file from local storage.
        
        Args:
            filename: The name of the file to delete
            
        Returns:
            bool: True if the file was deleted, False otherwise
        """
        file_path = os.path.join(self.media_folder, filename)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        
        return False
    
    def get_file_url(self, filename: str) -> str:
        """
        Get the URL to access a file in local storage.
        
        Args:
            filename: The name of the file
            
        Returns:
            str: The URL where the file can be accessed
        """
        return f"{self.base_url}/{filename}"
