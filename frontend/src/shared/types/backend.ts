
export type JobStatus =
    | 'PENDING'
    | 'RUNNING'
    | 'SUCCESS'
    | 'PARTIAL_SUCCESS'
    | 'FAILED'
    | 'CANCELLED';

export type TaskStatus =
    | 'PENDING'
    | 'RUNNING'
    | 'SUCCESS'
    | 'FAILED';

export type EventType = 'INFO' | 'WARNING' | 'ERROR' | 'SUCCESS' | 'PROGRESS';
export type EventLevel = 'INFO' | 'WARNING' | 'ERROR' | 'SUCCESS';

export interface ImageTask {
    id: string;
    algorithm_key: string;
    status: TaskStatus;
    artifact_png_url?: string;
    artifact_svg_url?: string;
    chart_data?: any; // Replace with specific ChartData type if needed
    params?: Record<string, any>;
}

export interface DescriptionTask {
    id: string;
    status: TaskStatus;
    result_text?: string;
    provider?: string;
}

export interface Job {
    id: string;
    status: JobStatus;
    progress_total: number;
    dataset_id?: string;
    image_tasks: ImageTask[];
    description_tasks?: DescriptionTask[];
    created_at: string;
}

export interface EventLogPayload {
    job_id: string;
    entity_type: 'JOB' | 'TASK';
    entity_id: string;
    event_type: EventType;
    level: EventLevel;
    progress?: number;
    message: string;
    payload?: any;
    trace_id?: string;
    created_at: string;
}
