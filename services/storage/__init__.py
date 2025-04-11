"""
Storage services package for the Cryptopedia application.
"""
from .base import StorageInterface
from .local import LocalStorage
from .s3 import S3Storage

__all__ = ['StorageInterface', 'LocalStorage', 'S3Storage']

def get_storage_service(storage_type: str, **kwargs) -> StorageInterface:
    """
    Factory function to get the appropriate storage service based on configuration.
    
    Args:
        storage_type: The type of storage to use ('local' or 's3')
        **kwargs: Additional configuration parameters
        
    Returns:
        StorageInterface: An instance of the appropriate storage service
        
    Raises:
        ValueError: If the storage type is invalid
    """
    if storage_type == "local":
        media_folder = kwargs.get("media_folder", "media")
        base_url = kwargs.get("base_url", "/media")
        return LocalStorage(media_folder=media_folder, base_url=base_url)
    
    elif storage_type == "s3":
        bucket = kwargs.get("s3_bucket")
        region = kwargs.get("aws_region")
        access_key = kwargs.get("aws_access_key")
        secret_key = kwargs.get("aws_secret_key")
        
        if not bucket or not region:
            raise ValueError("S3 storage requires bucket and region")
        
        return S3Storage(
            bucket=bucket,
            region=region,
            access_key=access_key,
            secret_key=secret_key
        )
    
    else:
        raise ValueError(f"Invalid storage type: {storage_type}")
