"""
Amazon S3 storage implementation for the Cryptopedia application.
"""
import boto3
import aioboto3
from typing import Optional
from botocore.exceptions import ClientError
from .base import StorageInterface

class S3Storage(StorageInterface):
    """
    Amazon S3 storage implementation.
    """
    def __init__(self, bucket: str, region: str, access_key: Optional[str] = None, secret_key: Optional[str] = None):
        """
        Initialize S3 storage with bucket and credentials.
        
        Args:
            bucket: S3 bucket name
            region: AWS region (e.g., us-east-1)
            access_key: AWS access key (optional if using IAM roles)
            secret_key: AWS secret key (optional if using IAM roles)
        """
        self.bucket = bucket
        self.region = region
        self.access_key = access_key
        self.secret_key = secret_key
        
        # Create a session for the async client
        self.session = aioboto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        # Also create a standard boto3 client for operations that don't need to be async
        if access_key and secret_key:
            self.s3 = boto3.client(
                's3',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
        else:
            # Use IAM role or environment variables
            self.s3 = boto3.client('s3', region_name=region)
    
    async def save_file(self, file_content: bytes, filename: str, content_type: Optional[str] = None) -> str:
        """
        Save a file to S3 and return its URL.
        
        Args:
            file_content: The binary content of the file
            filename: The name to save the file as
            content_type: The MIME type of the file
            
        Returns:
            str: The URL where the file can be accessed
        """
        try:
            # Use the async client to upload the file
            async with self.session.client('s3') as s3:
                await s3.put_object(
                    Bucket=self.bucket,
                    Key=filename,
                    Body=file_content,
                    ContentType=content_type or 'application/octet-stream'
                )
            
            # Return the S3 URL
            return self.get_file_url(filename)
        except Exception as e:
            # Log the error
            print(f"S3 upload error: {str(e)}")
            raise
    
    async def get_file(self, filename: str) -> Optional[bytes]:
        """
        Get a file's content from S3.
        
        Args:
            filename: The name of the file to retrieve
            
        Returns:
            bytes: The content of the file, or None if not found
        """
        try:
            async with self.session.client('s3') as s3:
                response = await s3.get_object(
                    Bucket=self.bucket,
                    Key=filename
                )
                return await response['Body'].read()
        except ClientError as e:
            # Check for 404 error (NoSuchKey)
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            # Log other errors
            print(f"S3 download error: {str(e)}")
            return None
        except Exception as e:
            # Log the error
            print(f"S3 download error: {str(e)}")
            return None
    
    async def delete_file(self, filename: str) -> bool:
        """
        Delete a file from S3.
        
        Args:
            filename: The name of the file to delete
            
        Returns:
            bool: True if the file was deleted, False otherwise
        """
        try:
            async with self.session.client('s3') as s3:
                await s3.delete_object(
                    Bucket=self.bucket,
                    Key=filename
                )
            return True
        except Exception as e:
            # Log the error
            print(f"S3 delete error: {str(e)}")
            return False
    
    def get_file_url(self, filename: str) -> str:
        """
        Get the URL to access a file in S3.
        
        Args:
            filename: The name of the file
            
        Returns:
            str: The URL where the file can be accessed
        """
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{filename}"
