"""
Storage service for file uploads.
Supports local filesystem and S3 storage backends.
"""
import os
import hashlib
import uuid
import mimetypes
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional, BinaryIO,  List

from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.config import settings
from src.models.attachment import Attachment, AttachmentEntityType, AttachmentCategory


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    async def save(self, file: BinaryIO, path: str, content_type: str) -> None:
        """Save file to storage."""
        pass

    @abstractmethod
    async def get(self, path: str) -> bytes:
        """Retrieve file from storage."""
        pass

    @abstractmethod
    async def delete(self, path: str) -> None:
        """Delete file from storage."""
        pass

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """Check if file exists."""
        pass


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend."""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_full_path(self, path: str) -> Path:
        """Get full path and ensure it's within base_path."""
        full_path = (self.base_path / path).resolve()
        # Security: prevent directory traversal
        if not str(full_path).startswith(str(self.base_path.resolve())):
            raise ValueError("Invalid path: directory traversal detected")
        return full_path

    async def save(self, file: BinaryIO, path: str, content_type: str) -> None:
        """Save file to local filesystem."""
        full_path = self._get_full_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, 'wb') as f:
            # Read in chunks to handle large files
            while chunk := file.read(8192):
                f.write(chunk)

    async def get(self, path: str) -> bytes:
        """Retrieve file from local filesystem."""
        full_path = self._get_full_path(path)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return full_path.read_bytes()

    async def delete(self, path: str) -> None:
        """Delete file from local filesystem."""
        full_path = self._get_full_path(path)
        if full_path.exists():
            full_path.unlink()

    async def exists(self, path: str) -> bool:
        """Check if file exists."""
        full_path = self._get_full_path(path)
        return full_path.exists()


class S3StorageBackend(StorageBackend):
    """S3 storage backend (supports S3-compatible services like MinIO)."""

    def __init__(
        self,
        bucket_name: str,
        region: str,
        access_key: str,
        secret_key: str,
        endpoint_url: Optional[str] = None,
    ):
        self.bucket_name = bucket_name
        self.region = region
        self.access_key = access_key
        self.secret_key = secret_key
        self.endpoint_url = endpoint_url or None
        self._client = None

    def _get_client(self):
        """Lazy-load boto3 client."""
        if self._client is None:
            try:
                import boto3
                from botocore.config import Config

                config = Config(
                    region_name=self.region,
                    signature_version='s3v4',
                )

                self._client = boto3.client(
                    's3',
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    endpoint_url=self.endpoint_url,
                    config=config,
                )
            except ImportError:
                raise ImportError(
                    "boto3 is required for S3 storage. "
                    "Install it with: pip install boto3"
                )
        return self._client

    async def save(self, file: BinaryIO, path: str, content_type: str) -> None:
        """Save file to S3."""
        client = self._get_client()
        file.seek(0)
        client.upload_fileobj(
            file,
            self.bucket_name,
            path,
            ExtraArgs={'ContentType': content_type},
        )

    async def get(self, path: str) -> bytes:
        """Retrieve file from S3."""
        import io
        client = self._get_client()
        buffer = io.BytesIO()
        client.download_fileobj(self.bucket_name, path, buffer)
        buffer.seek(0)
        return buffer.read()

    async def delete(self, path: str) -> None:
        """Delete file from S3."""
        client = self._get_client()
        client.delete_object(Bucket=self.bucket_name, Key=path)

    async def exists(self, path: str) -> bool:
        """Check if file exists in S3."""
        try:
            client = self._get_client()
            client.head_object(Bucket=self.bucket_name, Key=path)
            return True
        except Exception:
            return False


class StorageService:
    """
    Service for managing file attachments.
    Handles upload, download, delete operations with metadata tracking.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.backend = self._get_backend()
        self.max_file_size = settings.STORAGE_MAX_FILE_SIZE_MB * 1024 * 1024
        self.allowed_extensions = settings.STORAGE_ALLOWED_EXTENSIONS

    def _get_backend(self) -> StorageBackend:
        """Get configured storage backend."""
        if settings.STORAGE_BACKEND == "s3":
            return S3StorageBackend(
                bucket_name=settings.S3_BUCKET_NAME,
                region=settings.S3_REGION,
                access_key=settings.S3_ACCESS_KEY,
                secret_key=settings.S3_SECRET_KEY,
                endpoint_url=settings.S3_ENDPOINT_URL or None,
            )
        else:
            return LocalStorageBackend(settings.STORAGE_LOCAL_PATH)

    def _validate_file(self, filename: str, file_size: int) -> None:
        """Validate file against constraints."""
        # Check file size
        if file_size > self.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {settings.STORAGE_MAX_FILE_SIZE_MB}MB",
            )

        # Check extension
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if ext not in self.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '{ext}' not allowed. Allowed types: {', '.join(self.allowed_extensions)}",
            )

    def _generate_storage_path(
        self,
        entity_type: AttachmentEntityType,
        entity_id: str,
        filename: str,
    ) -> str:
        """Generate unique storage path for file."""
        # Create organized path: entity_type/entity_id/year/month/uuid_filename
        now = datetime.utcnow()
        unique_id = uuid.uuid4().hex[:8]
        safe_filename = self._sanitize_filename(filename)

        return f"{entity_type.value}/{entity_id}/{now.year}/{now.month:02d}/{unique_id}_{safe_filename}"

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal and other issues."""
        # Remove path separators
        filename = filename.replace('/', '_').replace('\\', '_')
        # Remove null bytes
        filename = filename.replace('\x00', '')
        # Keep only safe characters
        safe_chars = set(
            'abcdefghijklmnopqrstuvwxyz'
            'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            '0123456789._-'
        )
        filename = ''.join(c if c in safe_chars else '_' for c in filename)
        # Limit length
        if len(filename) > 200:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:200 - len(ext) - 1] + '.' + ext if ext else name[:200]
        return filename or 'unnamed'

    def _calculate_hash(self, file: BinaryIO) -> str:
        """Calculate SHA-256 hash of file."""
        sha256 = hashlib.sha256()
        file.seek(0)
        while chunk := file.read(8192):
            sha256.update(chunk)
        file.seek(0)
        return sha256.hexdigest()

    def _detect_content_type(self, filename: str) -> str:
        """Detect MIME type from filename."""
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or 'application/octet-stream'

    async def upload(
        self,
        file: UploadFile,
        entity_type: AttachmentEntityType,
        entity_id: str,
        user_id: str,
        category: AttachmentCategory = AttachmentCategory.OTHER,
        description: Optional[str] = None,
    ) -> Attachment:
        """
        Upload a file and create attachment record.

        Args:
            file: The uploaded file
            entity_type: Type of entity this attachment belongs to
            entity_id: ID of the entity
            user_id: ID of the user uploading the file
            category: Category for organizing the attachment
            description: Optional description

        Returns:
            Created Attachment record
        """
        # Read file content
        content = await file.read()
        file_size = len(content)

        # Validate
        self._validate_file(file.filename, file_size)

        # Create file-like object for processing
        import io
        file_buffer = io.BytesIO(content)

        # Calculate hash
        file_hash = self._calculate_hash(file_buffer)

        # Check for duplicate (same hash for same entity)
        existing = await self.db.execute(
            select(Attachment).where(
                and_(
                    Attachment.entity_type == entity_type,
                    Attachment.entity_id == entity_id,
                    Attachment.file_hash == file_hash,
                    Attachment.is_deleted == 0,
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Duplicate file: this file has already been uploaded to this entity",
            )

        # Generate storage path and detect content type
        storage_path = self._generate_storage_path(entity_type, entity_id, file.filename)
        content_type = file.content_type or self._detect_content_type(file.filename)

        # Save to storage backend
        file_buffer.seek(0)
        await self.backend.save(file_buffer, storage_path, content_type)

        # Create attachment record
        attachment = Attachment(
            filename=file.filename,
            storage_path=storage_path,
            content_type=content_type,
            file_size=file_size,
            file_hash=file_hash,
            category=category,
            description=description,
            entity_type=entity_type,
            entity_id=entity_id,
            uploaded_by=user_id,
        )

        self.db.add(attachment)
        await self.db.flush()
        await self.db.refresh(attachment)

        return attachment

    async def download(self, attachment_id: str, user_id: str) -> tuple[bytes, Attachment]:
        """
        Download a file.

        Args:
            attachment_id: ID of the attachment
            user_id: ID of the user downloading (for tracking)

        Returns:
            Tuple of (file content, attachment record)
        """
        # Get attachment record
        result = await self.db.execute(
            select(Attachment).where(
                and_(
                    Attachment.id == attachment_id,
                    Attachment.is_deleted == 0,
                )
            )
        )
        attachment = result.scalar_one_or_none()

        if not attachment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment not found",
            )

        # Get file from storage
        try:
            content = await self.backend.get(attachment.storage_path)
        except FileNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found in storage",
            )

        # Update download tracking
        attachment.download_count += 1
        attachment.last_downloaded_at = datetime.utcnow()
        await self.db.flush()

        return content, attachment

    async def delete(
        self,
        attachment_id: str,
        user_id: str,
        permanent: bool = False,
    ) -> None:
        """
        Delete an attachment (soft delete by default).

        Args:
            attachment_id: ID of the attachment
            user_id: ID of the user deleting
            permanent: If True, permanently delete file and record
        """
        result = await self.db.execute(
            select(Attachment).where(Attachment.id == attachment_id)
        )
        attachment = result.scalar_one_or_none()

        if not attachment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment not found",
            )

        if permanent:
            # Delete from storage
            try:
                await self.backend.delete(attachment.storage_path)
            except Exception:
                pass  # File might already be deleted

            # Delete record
            await self.db.delete(attachment)
        else:
            # Soft delete
            attachment.is_deleted = 1
            attachment.deleted_at = datetime.utcnow()
            attachment.deleted_by = user_id

        await self.db.flush()

    async def get_attachment(self, attachment_id: str) -> Optional[Attachment]:
        """Get attachment by ID."""
        result = await self.db.execute(
            select(Attachment).where(
                and_(
                    Attachment.id == attachment_id,
                    Attachment.is_deleted == 0,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_attachments(
        self,
        entity_type: AttachmentEntityType,
        entity_id: str,
        category: Optional[AttachmentCategory] = None,
    ) -> List[Attachment]:
        """
        List all attachments for an entity.

        Args:
            entity_type: Type of entity
            entity_id: ID of the entity
            category: Optional filter by category

        Returns:
            List of attachments
        """
        query = select(Attachment).where(
            and_(
                Attachment.entity_type == entity_type,
                Attachment.entity_id == entity_id,
                Attachment.is_deleted == 0,
            )
        )

        if category:
            query = query.where(Attachment.category == category)

        query = query.order_by(Attachment.uploaded_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_entity_attachment_count(
        self,
        entity_type: AttachmentEntityType,
        entity_id: str,
    ) -> int:
        """Get count of attachments for an entity."""
        from sqlalchemy import func

        result = await self.db.execute(
            select(func.count(Attachment.id)).where(
                and_(
                    Attachment.entity_type == entity_type,
                    Attachment.entity_id == entity_id,
                    Attachment.is_deleted == 0,
                )
            )
        )
        return result.scalar() or 0

    async def verify_integrity(self, attachment_id: str) -> tuple[bool, str]:
        """
        Verify file integrity by comparing stored hash with actual file hash.

        Returns:
            Tuple of (is_valid, message)
        """
        attachment = await self.get_attachment(attachment_id)
        if not attachment:
            return False, "Attachment not found"

        try:
            content = await self.backend.get(attachment.storage_path)
        except FileNotFoundError:
            return False, "File not found in storage"

        import io
        file_buffer = io.BytesIO(content)
        actual_hash = self._calculate_hash(file_buffer)

        if actual_hash != attachment.file_hash:
            return False, f"Hash mismatch: expected {attachment.file_hash}, got {actual_hash}"

        return True, "File integrity verified"
