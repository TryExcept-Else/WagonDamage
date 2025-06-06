"""
S3 Utility functions for wagon damage detection application.
This module provides functions to interact with AWS S3 using only allowed operations:
- put_object (upload)
- get_object (download)
- delete_object (delete)

No ListBucket or HeadBucket operations are used.
"""

import os
import boto3
import logging
from botocore.exceptions import ClientError
from werkzeug.utils import secure_filename
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

def get_s3_client():
    """
    Initialize and return an S3 client using environment variables.
    
    Returns:
        boto3.client: The S3 client or None if initialization fails
    """
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        return s3_client
    except Exception as e:
        logger.error(f"Error initializing S3 client: {str(e)}")
        return None

def upload_file_to_s3(file, bucket_name, folder_path, mime_types=None, filename=None):
    """
    Upload a file to S3 using put_object operation.
    
    Args:
        file: File object to upload
        bucket_name: Name of the S3 bucket
        folder_path: Path within the bucket to store the file
        mime_types: Dictionary mapping file extensions to MIME types
        filename: Custom filename to use instead of the original (optional)
        
    Returns:
        tuple: (bool success, str message, str s3_key or None)
    """
    if mime_types is None:
        mime_types = {}
    
    try:
        s3_client = get_s3_client()
        if s3_client is None:
            return False, "S3 client initialization failed", None
        
        # Use the provided filename or secure the original one
        if filename:
            new_filename = filename
        else:
            # Secure the filename
            original_filename = secure_filename(file.filename)
            
            # Add datetime stamp to filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = os.path.splitext(original_filename)[0]
            extension = os.path.splitext(original_filename)[1].lower()  # Include the dot
            new_filename = f"{base_filename}_{timestamp}{extension}"
        
        # Generate S3 key with folder structure
        s3_key = f"{folder_path}/{new_filename}" if folder_path else new_filename
        
        # Log the exact S3 key being used
        logger.info(f"Uploading file with S3 key: {s3_key}")
        
        # Determine content type
        extension = os.path.splitext(new_filename)[1].lower()[1:]  # Remove the dot
        content_type = mime_types.get(extension, 'application/octet-stream')
        
        # Upload using put_object
        file.seek(0)  # Ensure we're at the beginning of the file
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=file,
            ContentType=content_type
        )
        
        logger.info(f"Successfully uploaded {new_filename} to S3 folder {folder_path}")
        return True, f"File {new_filename} uploaded successfully", s3_key
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        logger.error(f"S3 client error ({error_code}): {error_message}")
        return False, f"S3 error: {error_message}", None
        
    except Exception as e:
        logger.error(f"General error during upload: {str(e)}")
        return False, f"Error: {str(e)}", None

def download_file_from_s3(bucket_name, s3_key, local_path=None):
    """
    Download a file from S3 using get_object operation.
    
    Args:
        bucket_name: Name of the S3 bucket
        s3_key: Key of the object in S3
        local_path: Local path to save the file (optional)
        
    Returns:
        tuple: (bool success, str message, bytes file_content or None)
    """
    try:
        s3_client = get_s3_client()
        if s3_client is None:
            return False, "S3 client initialization failed", None
        
        # Get the object from S3
        response = s3_client.get_object(
            Bucket=bucket_name,
            Key=s3_key
        )
        
        # Read the content
        file_content = response['Body'].read()
        
        # If local path is provided, save the file
        if local_path:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(file_content)
            logger.info(f"Successfully downloaded {s3_key} to {local_path}")
            return True, f"File {s3_key} downloaded successfully", None
        
        # Otherwise return the content
        logger.info(f"Successfully retrieved {s3_key} from S3")
        return True, f"File {s3_key} retrieved successfully", file_content
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        logger.error(f"S3 client error ({error_code}): {error_message}")
        return False, f"S3 error: {error_message}", None
        
    except Exception as e:
        logger.error(f"General error during download: {str(e)}")
        return False, f"Error: {str(e)}", None

def delete_file_from_s3(bucket_name, s3_key):
    """
    Delete a file from S3 using delete_object operation.
    
    Args:
        bucket_name: Name of the S3 bucket
        s3_key: Key of the object in S3
        
    Returns:
        tuple: (bool success, str message)
    """
    try:
        s3_client = get_s3_client()
        if s3_client is None:
            return False, "S3 client initialization failed"
        
        # Delete the object
        s3_client.delete_object(
            Bucket=bucket_name,
            Key=s3_key
        )
        
        logger.info(f"Successfully deleted {s3_key} from S3")
        return True, f"File {s3_key} deleted successfully"
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        logger.error(f"S3 client error ({error_code}): {error_message}")
        return False, f"S3 error: {error_message}"
        
    except Exception as e:
        logger.error(f"General error during deletion: {str(e)}")
        return False, f"Error: {str(e)}"

def check_file_exists(bucket_name, s3_key):
    """
    Check if a file exists in S3 using get_object operation with a try/except pattern
    instead of using HeadBucket.
    
    Args:
        bucket_name: Name of the S3 bucket
        s3_key: Key of the object in S3
        
    Returns:
        bool: True if file exists, False otherwise
    """
    try:
        s3_client = get_s3_client()
        if s3_client is None:
            return False
        
        # Try to get the object metadata
        s3_client.get_object(
            Bucket=bucket_name,
            Key=s3_key
        )
        
        # If no exception is raised, the file exists
        return True
        
    except ClientError as e:
        # If the error code is 404 (NoSuchKey), the file doesn't exist
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'NoSuchKey':
            return False
        
        # For other errors, log and return False
        logger.error(f"S3 client error ({error_code}): {str(e)}")
        return False
        
    except Exception as e:
        logger.error(f"General error checking file existence: {str(e)}")
        return False

def generate_presigned_url(bucket_name, s3_key, expiration=3600):
    """
    Generate a presigned URL for an S3 object to allow temporary access.
    
    Args:
        bucket_name: Name of the S3 bucket
        s3_key: Key of the object in S3
        expiration: Time in seconds until the URL expires (default: 1 hour)
        
    Returns:
        tuple: (bool success, str url or error message)
    """
    try:
        s3_client = get_s3_client()
        if s3_client is None:
            return False, "S3 client initialization failed"
        
        # Generate the presigned URL
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket_name,
                'Key': s3_key
            },
            ExpiresIn=expiration
        )
        
        logger.info(f"Generated presigned URL for {s3_key}")
        return True, url
        
    except ClientError as e:
        logger.error(f"Error generating presigned URL: {str(e)}")
        return False, f"Error: {str(e)}"
        
    except Exception as e:
        logger.error(f"General error generating presigned URL: {str(e)}")
        return False, f"Error: {str(e)}"
