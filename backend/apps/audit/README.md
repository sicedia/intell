# Audit App

Append-only event logging for traceability. Single source of truth for event emission.

## Modules

### `models.py`
- `EventLog`: Append-only event log model
  - **CRITICAL**: `managed=True`, only INSERTs allowed (never UPDATEs)
  - State/progress changes occur in Job/ImageTask/DescriptionTask, never here
  - Fields: `job`, `image_task`, `description_task` (FKs nullable), `trace_id`, `event_type`, `level`, `message`, `payload`, `created_at`
  - Event types: START, PROGRESS, RETRY, ERROR, DONE, VALIDATION_ERROR, EXTERNAL_API_ERROR, ALGORITHM_ERROR, RENDER_ERROR, STORAGE_ERROR, AI_PROVIDER_ERROR

### `helpers.py`
- `emit_event()`: **SINGLE SOURCE OF TRUTH** for event emission
  - Always does:
    a) Insert EventLog
    b) Update status/progress in Job/ImageTask/DescriptionTask (via mapping)
    c) Publish to WebSocket channel `job_<job_id>`
  - Generates `trace_id` automatically if not provided
  - Mapping `event_type → status/progress` (see plan for details)
  - WebSocket payload: stable structure with job_id, entity_type, entity_id, event_type, level, progress, message, payload, trace_id, created_at

## Usage

Emit event:
```python
from apps.audit.helpers import emit_event

emit_event(
    job_id=1,
    event_type="START",
    level="INFO",
    message="Job started",
    progress=0
)
```

Query events:
```python
from apps.audit.models import EventLog
events = EventLog.objects.filter(job_id=1).order_by('-created_at')
```

## Admin

EventLog is read-only in admin (no add/edit/delete permissions).

