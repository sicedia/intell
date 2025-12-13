
import { Job, EventLogPayload, ImageTask } from "@/shared/types/backend";

export const MOCK_CHART_DATA = {
    categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
    series: [
        { name: 'Revenue', data: [10, 20, 15, 25, 30] },
        { name: 'Cost', data: [5, 10, 8, 12, 15] },
    ]
};

export const MOCK_IMAGE_TASKS: ImageTask[] = [
    {
        id: 'task-1',
        algorithm_key: 'clustering_kmeans',
        status: 'SUCCESS',
        artifact_png_url: 'https://placehold.co/600x400/png',
        chart_data: MOCK_CHART_DATA,
        params: { k: 5 }
    },
    {
        id: 'task-2',
        algorithm_key: 'regression_linear',
        status: 'RUNNING',
        // No artifacts yet
        params: { target: 'price' }
    }
];

export const MOCK_JOB: Job = {
    id: 'job-123',
    status: 'RUNNING',
    progress_total: 45,
    dataset_id: 'ds-001',
    created_at: new Date().toISOString(),
    image_tasks: MOCK_IMAGE_TASKS,
};

export const MOCK_EVENTS: EventLogPayload[] = [
    {
        job_id: 'job-123',
        entity_type: 'JOB',
        entity_id: 'job-123',
        event_type: 'INFO',
        level: 'INFO',
        message: 'Job started',
        created_at: new Date(Date.now() - 10000).toISOString(),
        progress: 0
    },
    {
        job_id: 'job-123',
        entity_type: 'TASK',
        entity_id: 'task-1',
        event_type: 'SUCCESS',
        level: 'SUCCESS',
        message: 'K-Means clustering completed successfully',
        created_at: new Date(Date.now() - 5000).toISOString(),
        progress: 100
    },
    {
        job_id: 'job-123',
        entity_type: 'TASK',
        entity_id: 'task-2',
        event_type: 'PROGRESS',
        level: 'INFO',
        message: 'Linear regression training...',
        created_at: new Date().toISOString(),
        progress: 50
    }
];
