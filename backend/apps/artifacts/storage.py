"""
Artifact storage wrapper for jobs app.
Uses core storage abstraction.
"""
from apps.core.storage import default_artifact_storage, ArtifactStorage
from typing import Optional


def save_artifact(artifact_type: str, job_id: int, task_id: int, content: bytes, extension: str = 'png') -> str:
    """
    Save artifact using storage abstraction.
    
    Args:
        artifact_type: Type of artifact (png, svg)
        job_id: Job ID
        task_id: Task ID
        content: Artifact content (bytes)
        extension: File extension (png, svg)
        
    Returns:
        Storage path (relative to MEDIA_ROOT)
    """
    path = f"{artifact_type}/job_{job_id}/task_{task_id}.{extension}"
    return default_artifact_storage.save(path, content)


def read_artifact(storage_path: str) -> bytes:
    """
    Read artifact from storage.
    
    Args:
        storage_path: Storage path
        
    Returns:
        Artifact content (bytes)
    """
    return default_artifact_storage.read(storage_path)


def artifact_exists(storage_path: str) -> bool:
    """
    Check if artifact exists.
    
    Args:
        storage_path: Storage path
        
    Returns:
        True if exists, False otherwise
    """
    return default_artifact_storage.exists(storage_path)

