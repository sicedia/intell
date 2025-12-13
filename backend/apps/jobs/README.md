# Jobs App

Job orchestration, task management, and API endpoints.

## Modules

### `models.py`
Job-related models:
- `Job`: Orchestrates multiple ImageTasks
  - FK to `Dataset` (canonical format)
  - Status: PENDING, RUNNING, PARTIAL_SUCCESS, SUCCESS, FAILED, CANCELLED
  - Idempotency: `UniqueConstraint(created_by, idempotency_key)`
  - Method: `cancel()`
- `ImageTask`: Generates a single chart image
  - FK to `Job`
  - Consumes `Job.dataset`
  - Stores artifacts (PNG/SVG) and `chart_data`
- `DescriptionTask`: Generates AI description for a chart
  - FK to `ImageTask`
  - Uses `ImageTask.chart_data`

### `tasks.py`
Celery tasks:
- `generate_image_task(image_task_id)`: Generates chart image
  - Gets Dataset from Job.dataset
  - Executes algorithm via AlgorithmRegistry
  - Saves artifacts
  - Uses `emit_event()` for tracing
  - Checks cancellation
- `run_job(job_id)`: Orchestrates job execution
  - Creates ImageTasks
  - Enqueues group of `generate_image_task`
  - Uses Celery chord with `finalize_job` callback
- `finalize_job(job_id, task_results)`: Calculates final job status
  - SUCCESS if all tasks succeed
  - PARTIAL_SUCCESS if some fail
  - FAILED if all fail
  - Recalculates `progress_total`

### `views.py`
REST API endpoints:
- `JobViewSet`: Job CRUD operations
  - `create()`: POST /api/jobs/ - Creates job with idempotency
  - `retrieve()`: GET /api/jobs/<id>/ - Gets job details
  - `cancel()`: POST /api/jobs/<id>/cancel/ - Cancels job
- `ImageTaskViewSet`: Read-only ImageTask views
- `DescriptionTaskViewSet`: Read-only DescriptionTask views
- `AIDescribeView`: POST /api/ai/describe/ - Creates description task

### `serializers.py`
DRF serializers:
- `JobCreateSerializer`: For job creation
- `JobDetailSerializer`: For job details (includes tasks)
- `ImageTaskSerializer`: Includes artifact URLs
- `DescriptionTaskSerializer`: For description tasks

### `consumers.py`
WebSocket consumer:
- `JobProgressConsumer`: WebSocket for `/ws/jobs/<job_id>/`
  - Subscribes to `job_<job_id>` channel group
  - Receives events from `emit_event()`

### `routing.py`
WebSocket URL routing:
- `websocket_urlpatterns`: Maps `/ws/jobs/<job_id>/` to consumer

## Usage

Create job via API:
```python
POST /api/jobs/
{
  "source_type": "espacenet_excel",
  "source_data": <file>,
  "images": [{"algorithm_key": "top_patent_countries", "params": {"top_n": 15}}],
  "idempotency_key": "unique-key"
}
```

Connect to WebSocket:
```javascript
ws://localhost:8000/ws/jobs/<job_id>/
```

