"""
Storage dependencies for FastAPI.
"""
import config
from services.storage import get_storage_service, StorageInterface

# Create storage service based on configuration
storage_service = get_storage_service(
    storage_type=config.STORAGE_TYPE,
    media_folder=config.MEDIA_FOLDER,
    s3_bucket=config.S3_BUCKET,
    aws_region=config.AWS_REGION,
    aws_access_key=config.AWS_ACCESS_KEY,
    aws_secret_key=config.AWS_SECRET_KEY
)

async def get_storage() -> StorageInterface:
    """
    Dependency to get the storage service.
    Used in route functions that handle file operations.
    
    Returns:
        StorageInterface: The storage service
    """
    return storage_service
