"""
Base interface for storage services used in the Cryptopedia application.
"""
from abc import ABC, abstractmethod
from typing import Optional

class StorageInterface(ABC):
    """
    Abstract interface for file storage operations.
    Implementations should handle local filesystem, S3, etc.
    """
    
    @abstractmethod
    async def save_file(self, file_content: bytes, filename: str, content_type: Optional[str] = None) -> str:
        """
        Save a file and return its path/URL.
        
        Args:
            file_content: The binary content of the file
            filename: The name to save the file as
            content_type: The MIME type of the file, if known
            
        Returns:
            str: The path or URL where the file can be accessed
        """
        pass
    
    @abstractmethod
    async def get_file(self, filename: str) -> Optional[bytes]:
        """
        Get a file's content.
        
        Args:
            filename: The name of the file to retrieve
            
        Returns:
            bytes: The content of the file, or None if not found
        """
        pass
    
    @abstractmethod
    async def delete_file(self, filename: str) -> bool:
        """
        Delete a file.
        
        Args:
            filename: The name of the file to delete
            
        Returns:
            bool: True if the file was deleted, False otherwise
        """
        pass
    
    @abstractmethod
    def get_file_url(self, filename: str) -> str:
        """
        Get the URL to access a file.
        
        Args:
            filename: The name of the file
            
        Returns:
            str: The URL where the file can be accessed
        """
        pass
