# Cryptopedia Storage Configuration

Cryptopedia supports multiple storage options for media files. This document explains the different storage options and how to configure them.

## Storage Options

### 1. Local Storage (Default)

By default, Cryptopedia uses the local file system to store uploaded media files. This is the simplest option and requires no external services.

**Configuration**:
```
STORAGE_TYPE=local
MEDIA_FOLDER=media
```

With local storage:
- Files are stored in the specified `MEDIA_FOLDER` directory
- The FastAPI application serves these files directly via a mounted `/media` endpoint

### 2. Amazon S3 Storage

For production environments or when you need more scalable storage, you can configure Cryptopedia to use Amazon S3 for media storage.

**Requirements**:
- Install boto3: `pip install boto3`
- AWS account with S3 access

**Configuration**:
```
STORAGE_TYPE=s3
S3_BUCKET=your-bucket-name
AWS_ACCESS_KEY=your-access-key
AWS_SECRET_KEY=your-secret-key
AWS_REGION=us-east-1
```

With S3 storage:
- Files are stored in the specified S3 bucket
- File URLs will point directly to S3
- The application provides a `/api/media/{filename}/content` endpoint as an alternative way to access files

## Switching Storage Types

You can switch between storage types by changing the `STORAGE_TYPE` environment variable. However, note that switching storage types does not automatically migrate existing files. You will need to manually copy files if you switch storage types after uploading files.

## Accessing Media Files

### When using Local Storage:
- Files are available directly at: `http://your-server/media/{filename}`
- File metadata is available at: `http://your-server/api/media/{id}`

### When using S3 Storage:
- Files are available directly from S3: `https://{bucket}.s3.{region}.amazonaws.com/{filename}`
- Files are also available through the API: `http://your-server/api/media/{filename}/content`
- File metadata is available at: `http://your-server/api/media/{id}`

## Storage Interface

The storage system uses a pluggable interface that makes it easy to implement additional storage backends if needed. The interface provides three main methods:

- `save_file(file_content, filename, content_type)` - Save a file to storage
- `get_file(filename)` - Retrieve a file from storage
- `delete_file(filename)` - Delete a file from storage

If you need to implement a different storage backend (e.g., Google Cloud Storage, Azure Blob Storage), you can create a new class that implements this interface.
