"""
File storage utility for handling uploads and file management
"""

import os
import hashlib
import aiofiles
from datetime import datetime
from pathlib import Path
from typing import Optional, BinaryIO
import uuid
import boto3
from botocore.exceptions import ClientError
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class FileStorage:
    """
    File storage handler supporting local and S3 storage
    """
    
    def __init__(self):
        self.use_s3 = settings.USE_S3
        
        if self.use_s3:
            self._init_s3()
        else:
            self._init_local()
    
    def _init_s3(self):
        """Initialize S3 client"""
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION
        )
        self.bucket = settings.S3_BUCKET
    
    def _init_local(self):
        """Initialize local storage"""
        self.upload_path = Path(settings.UPLOAD_PATH)
        self.upload_path.mkdir(parents=True, exist_ok=True)
    
    async def save_upload(self, file, user_id: str) -> str:
        """
        Save uploaded file
        
        Args:
            file: UploadFile object
            user_id: User ID for organization
            
        Returns:
            Storage path/key
        """
        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_id = str(uuid.uuid4())[:8]
        ext = os.path.splitext(file.filename)[1]
        filename = f"{timestamp}_{file_id}{ext}"
        
        # Create path
        path = f"uploads/{user_id}/{filename}"
        
        if self.use_s3:
            return await self._save_to_s3(file, path)
        else:
            return await self._save_to_local(file, path)
    
    async def _save_to_s3(self, file, key: str) -> str:
        """Save file to S3"""
        try:
            # Read file content
            content = await file.read()
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=content,
                ContentType=file.content_type or 'application/octet-stream'
            )
            
            logger.info(f"File uploaded to S3: {key}")
            return key
            
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise Exception(f"Failed to upload file: {str(e)}")
        finally:
            # Reset file position
            await file.seek(0)
    
    async def _save_to_local(self, file, path: str) -> str:
        """Save file to local storage"""
        full_path = self.upload_path / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Save file
            async with aiofiles.open(full_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            logger.info(f"File saved locally: {full_path}")
            return str(path)
            
        except Exception as e:
            logger.error(f"Local save failed: {e}")
            raise Exception(f"Failed to save file: {str(e)}")
        finally:
            # Reset file position
            await file.seek(0)
    
    async def get_file(self, path: str) -> bytes:
        """
        Retrieve file content
        
        Args:
            path: Storage path/key
            
        Returns:
            File content as bytes
        """
        if self.use_s3:
            return await self._get_from_s3(path)
        else:
            return await self._get_from_local(path)
    
    async def _get_from_s3(self, key: str) -> bytes:
        """Get file from S3"""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket,
                Key=key
            )
            return response['Body'].read()
        except ClientError as e:
            logger.error(f"S3 get failed: {e}")
            raise Exception(f"Failed to retrieve file: {str(e)}")
    
    async def _get_from_local(self, path: str) -> bytes:
        """Get file from local storage"""
        full_path = self.upload_path / path
        
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        async with aiofiles.open(full_path, 'rb') as f:
            return await f.read()
    
    async def delete_file(self, path: str) -> bool:
        """
        Delete file
        
        Args:
            path: Storage path/key
            
        Returns:
            True if successful
        """
        if self.use_s3:
            return await self._delete_from_s3(path)
        else:
            return await self._delete_from_local(path)
    
    async def _delete_from_s3(self, key: str) -> bool:
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket,
                Key=key
            )
            logger.info(f"File deleted from S3: {key}")
            return True
        except ClientError as e:
            logger.error(f"S3 delete failed: {e}")
            return False
    
    async def _delete_from_local(self, path: str) -> bool:
        """Delete file from local storage"""
        full_path = self.upload_path / path
        
        try:
            if full_path.exists():
                full_path.unlink()
                logger.info(f"File deleted locally: {full_path}")
            return True
        except Exception as e:
            logger.error(f"Local delete failed: {e}")
            return False
    
    async def get_file_url(self, path: str, expires_in: int = 3600) -> str:
        """
        Get presigned URL for file access
        
        Args:
            path: Storage path/key
            expires_in: URL expiration in seconds
            
        Returns:
            Presigned URL
        """
        if self.use_s3:
            return self._get_s3_presigned_url(path, expires_in)
        else:
            # For local storage, return a path that the API can serve
            return f"/files/{path}"
    
    def _get_s3_presigned_url(self, key: str, expires_in: int) -> str:
        """Generate S3 presigned URL"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise Exception(f"Failed to generate file URL: {str(e)}")
    
    @staticmethod
    def calculate_file_hash(file_content: bytes) -> str:
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    async def save_export(self, content: bytes, filename: str, user_id: str) -> tuple[str, int]:
        """
        Save export file
        
        Args:
            content: File content
            filename: Original filename
            user_id: User ID
            
        Returns:
            Tuple of (storage_path, file_size)
        """
        # Generate path
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        path = f"exports/{user_id}/{timestamp}_{filename}"
        
        if self.use_s3:
            # Upload to S3
            try:
                self.s3_client.put_object(
                    Bucket=self.bucket,
                    Key=path,
                    Body=content
                )
                return path, len(content)
            except ClientError as e:
                logger.error(f"S3 export save failed: {e}")
                raise Exception(f"Failed to save export: {str(e)}")
        else:
            # Save locally
            full_path = self.upload_path / path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(full_path, 'wb') as f:
                await f.write(content)
            
            return str(path), len(content)