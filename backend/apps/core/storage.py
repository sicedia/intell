"""
Storage abstraction for artifacts.
Supports filesystem (MVP) with interface prepared for S3/MinIO.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, BinaryIO
from django.core.files.storage import default_storage
from django.conf import settings


class ArtifactStorage(ABC):
    """Abstract base class for artifact storage backends."""
    
    @abstractmethod
    def save(self, path: str, content: bytes) -> str:
        """Save content to storage and return the storage path."""
        pass
    
    @abstractmethod
    def read(self, path: str) -> bytes:
        """Read content from storage."""
        pass
    
    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if file exists in storage."""
        pass
    
    @abstractmethod
    def delete(self, path: str) -> bool:
        """Delete file from storage."""
        pass


class FileSystemArtifactStorage(ArtifactStorage):
    """Filesystem-based storage implementation (MVP)."""
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize filesystem storage.
        
        Args:
            base_path: Base path for artifacts (defaults to MEDIA_ROOT/artifacts)
        """
        if base_path is None:
            self.base_path = Path(settings.MEDIA_ROOT) / 'artifacts'
        else:
            self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def save(self, path: str, content: bytes) -> str:
        """Save content to filesystem."""
        full_path = self.base_path / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'wb') as f:
            f.write(content)
        
        # Return relative path from MEDIA_ROOT
        return str(full_path.relative_to(settings.MEDIA_ROOT))
    
    def read(self, path: str) -> bytes:
        """Read content from filesystem."""
        # If path is relative to MEDIA_ROOT, use it directly
        if Path(path).is_absolute():
            full_path = Path(path)
        else:
            full_path = Path(settings.MEDIA_ROOT) / path
        
        with open(full_path, 'rb') as f:
            return f.read()
    
    def exists(self, path: str) -> bool:
        """Check if file exists."""
        if Path(path).is_absolute():
            full_path = Path(path)
        else:
            full_path = Path(settings.MEDIA_ROOT) / path
        return full_path.exists()
    
    def delete(self, path: str) -> bool:
        """Delete file from filesystem."""
        try:
            if Path(path).is_absolute():
                full_path = Path(path)
            else:
                full_path = Path(settings.MEDIA_ROOT) / path
            full_path.unlink()
            return True
        except FileNotFoundError:
            return False


# Default storage instance
default_artifact_storage = FileSystemArtifactStorage()

