export enum JobStatus {
    PENDING = "PENDING",
    RUNNING = "RUNNING",
    SUCCESS = "SUCCESS",
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS",
    FAILED = "FAILED",
    CANCELLED = "CANCELLED",
}

export interface ImageTask {
    id: number;
    algorithm_key: string;
    status: JobStatus;
    result_urls: {
        png?: string;
        svg?: string;
    };
    error_message?: string;
    created_at: string;
    updated_at: string;
    chart_data?: unknown;
}

export interface Job {
    id: number;
    status: JobStatus;
    source_type: "espacenet_excel" | "lens_query";
    created_at: string;
    updated_at: string;
    images: ImageTask[];
    events?: JobEvent[];
    progress: number;
    message?: string;
}

export interface JobEvent {
    job_id: string;
    entity_type: string;
    entity_id: string;
    event_type: string;
    level: string;
    progress: number;
    message: string;
    payload: unknown;
    trace_id: string;
    created_at: string;
}
