# Core App

Shared utilities and base classes used across all apps in the Intelli project.

## Modules

### `exceptions.py`
Custom exception classes for the Intelli project:
- `IntelliException`: Base exception for all Intelli-specific exceptions
- `ValidationError`: Raised when data validation fails
- `ExternalAPIError`: Raised when external API calls fail
- `AlgorithmError`: Raised when algorithm execution fails
- `RenderError`: Raised when chart rendering fails
- `StorageError`: Raised when storage operations fail
- `AIProviderError`: Raised when AI provider calls fail

### `storage.py`
Storage abstraction layer for artifacts (PNG/SVG files):
- `ArtifactStorage`: Abstract base class for storage backends
- `FileSystemArtifactStorage`: Filesystem implementation (MVP)
  - Supports saving, reading, existence checking, and deletion
  - Prepared for future S3/MinIO integration
- `default_artifact_storage`: Default storage instance

## Usage

Import exceptions:
```python
from apps.core.exceptions import ValidationError, AlgorithmError
```

Use storage:
```python
from apps.core.storage import default_artifact_storage
path = default_artifact_storage.save("path/to/file.png", png_bytes)
```

