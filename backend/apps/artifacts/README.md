# Artifacts App

Artifact storage management for chart images (PNG/SVG).

## Modules

### `storage.py`
Wrapper functions for artifact storage:
- `save_artifact(artifact_type, job_id, task_id, content, extension) -> str`: Save artifact
- `read_artifact(storage_path) -> bytes`: Read artifact
- `artifact_exists(storage_path) -> bool`: Check existence

Uses `apps.core.storage.default_artifact_storage` (filesystem MVP, prepared for S3/MinIO).

## Usage

Save artifact:
```python
from apps.artifacts.storage import save_artifact
path = save_artifact("png", job_id=1, task_id=2, content=png_bytes, extension="png")
```

Read artifact:
```python
from apps.artifacts.storage import read_artifact
content = read_artifact(storage_path)
```

