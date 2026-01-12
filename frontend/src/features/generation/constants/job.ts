export enum JobStatus {
    PENDING = "PENDING",
    RUNNING = "RUNNING",
    SUCCESS = "SUCCESS",
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS",
    FAILED = "FAILED",
    CANCELLED = "CANCELLED",
}

// Backend response interfaces (raw API response)
export interface BackendImageTask {
    id: number;
    job: number;
    created_by: number | null;
    created_by_username?: string | null;
    created_by_email?: string | null;
    algorithm_key: string;
    algorithm_version: string;
    params: Record<string, unknown>;
    output_format: "png" | "svg" | "both";
    status: JobStatus;
    progress: number;
    artifact_png_url: string | null;
    artifact_svg_url: string | null;
    chart_data?: unknown;
    error_code?: string | null;
    error_message?: string | null;
    trace_id?: string | null;
    is_published?: boolean;
    published_at?: string | null;
    created_at: string;
    updated_at: string;
}

export interface BackendJob {
    id: number;
    created_by: number | null;
    dataset_id: number;
    status: JobStatus;
    progress_total: number;
    progress?: number; // Alias for progress_total
    idempotency_key: string | null;
    image_tasks: BackendImageTask[];
    images?: BackendImageTask[]; // Alias for image_tasks
    description_tasks?: unknown[];
    events?: BackendJobEvent[];
    source_type?: "lens" | "espacenet_excel" | "custom";
    created_at: string;
    updated_at: string;
}

export interface BackendJobEvent {
    id: number;
    event_type: string;
    level: string;
    message: string;
    progress: number;
    created_at: string;
    payload: unknown;
}

// Frontend interfaces (normalized format)
export interface ImageTask {
    id: number;
    algorithm_key: string;
    status: JobStatus;
    progress: number;
    result_urls: {
        png?: string;
        svg?: string;
    };
    error_message?: string;
    is_published?: boolean;
    published_at?: string | null;
    created_at: string;
    updated_at: string;
    chart_data?: unknown;
    title?: string | null;
    user_description?: string | null;
    created_by?: number | null;
    created_by_username?: string | null;
    created_by_email?: string | null;
}

export interface Job {
    id: number;
    status: JobStatus;
    source_type: "espacenet_excel" | "lens" | "custom";
    created_at: string;
    updated_at: string;
    images: ImageTask[];
    events?: JobEvent[];
    progress: number;
    message?: string;
}

export interface JobEvent {
    job_id: string | number;
    entity_type: string;
    entity_id: string | number;
    event_type: string;
    level: string;
    progress: number;
    message: string;
    payload: unknown;
    trace_id: string;
    created_at: string;
}

// Legacy types for backward compatibility (deprecated - use types above)
// These match the old backend.ts types for mock data
export type TaskStatus = JobStatus;
export type EventType = 'INFO' | 'WARNING' | 'ERROR' | 'SUCCESS' | 'PROGRESS';
export type EventLevel = 'INFO' | 'WARNING' | 'ERROR' | 'SUCCESS';

/**
 * Legacy interface for mock data compatibility
 * @deprecated Use ImageTask from this file instead
 */
export interface LegacyImageTask {
    id: string;
    algorithm_key: string;
    status: TaskStatus;
    artifact_png_url?: string;
    artifact_svg_url?: string;
    chart_data?: unknown;
    params?: Record<string, unknown>;
}

/**
 * Legacy interface for mock data compatibility
 * @deprecated Use Job from this file instead
 */
export interface LegacyJob {
    id: string;
    status: JobStatus;
    progress_total: number;
    dataset_id?: string;
    image_tasks: LegacyImageTask[];
    description_tasks?: unknown[];
    created_at: string;
}

/**
 * Legacy interface for event log payload (used in mocks)
 * @deprecated Use JobEvent from this file instead
 */
export interface EventLogPayload {
    job_id: string;
    entity_type: 'JOB' | 'TASK';
    entity_id: string;
    event_type: EventType;
    level: EventLevel;
    progress?: number;
    message: string;
    payload?: unknown;
    trace_id?: string;
    created_at: string;
}

/**
 * Transform backend ImageTask response to frontend format
 */
export function transformImageTask(backendTask: BackendImageTask): ImageTask {
    return {
        id: backendTask.id,
        algorithm_key: backendTask.algorithm_key,
        status: backendTask.status,
        progress: Number(backendTask.progress) || 0, // Ensure progress is always a number
        result_urls: {
            png: backendTask.artifact_png_url || undefined,
            svg: backendTask.artifact_svg_url || undefined,
        },
        error_message: backendTask.error_message || undefined,
        is_published: backendTask.is_published || false,
        published_at: backendTask.published_at || null,
        created_at: backendTask.created_at,
        updated_at: backendTask.updated_at,
        chart_data: backendTask.chart_data,
        created_by: backendTask.created_by || null,
        created_by_username: backendTask.created_by_username || null,
        created_by_email: backendTask.created_by_email || null,
    };
}

/**
 * Transform backend Job response to frontend format
 */
export function transformJob(backendJob: BackendJob): Job {
    // Use images if available, otherwise fall back to image_tasks
    const imageTasks = backendJob.images || backendJob.image_tasks || [];
    
    return {
        id: backendJob.id,
        status: backendJob.status,
        source_type: backendJob.source_type || "espacenet_excel",
        created_at: backendJob.created_at,
        updated_at: backendJob.updated_at,
        images: imageTasks.map(transformImageTask),
        events: backendJob.events?.map(transformJobEvent),
        progress: Number(backendJob.progress ?? backendJob.progress_total) || 0, // Ensure progress is always a number
    };
}

/**
 * Type guard to check if an event is already in frontend format
 */
function isJobEvent(event: unknown): event is JobEvent {
    return (
        typeof event === "object" &&
        event !== null &&
        "job_id" in event &&
        "entity_type" in event &&
        "event_type" in event
    );
}

/**
 * Type guard to check if an event is in backend format
 */
function isBackendJobEvent(event: unknown): event is BackendJobEvent {
    return (
        typeof event === "object" &&
        event !== null &&
        "id" in event &&
        "event_type" in event &&
        "level" in event &&
        "message" in event
    );
}

/**
 * Transform backend JobEvent response to frontend format
 * Handles both WebSocket events (already in correct format) and API EventLog responses
 */
export function transformJobEvent(backendEvent: BackendJobEvent | JobEvent | unknown): JobEvent {
    // WebSocket events and frontend format already have job_id and entity_type at top level
    if (isJobEvent(backendEvent)) {
        // Already in frontend format - ensure all required fields exist
        return {
            job_id: backendEvent.job_id ?? "",
            entity_type: backendEvent.entity_type ?? "",
            entity_id: backendEvent.entity_id ?? "",
            event_type: backendEvent.event_type ?? "",
            level: backendEvent.level ?? "INFO",
            progress: Number(backendEvent.progress) || 0,
            message: backendEvent.message ?? "",
            payload: backendEvent.payload ?? {},
            trace_id: backendEvent.trace_id ?? "",
            created_at: backendEvent.created_at ?? new Date().toISOString(),
        };
    }
    
    // Transform from backend API EventLog format
    if (!isBackendJobEvent(backendEvent)) {
        // Fallback for unknown format
        return {
            job_id: "",
            entity_type: "",
            entity_id: "",
            event_type: "",
            level: "INFO",
            progress: 0,
            message: "Unknown event format",
            payload: {},
            trace_id: "",
            created_at: new Date().toISOString(),
        };
    }
    
    const be = backendEvent;
    const payload = (typeof be.payload === "object" && be.payload !== null) 
        ? be.payload as Record<string, unknown>
        : {};
    
    return {
        job_id: payload.job_id as string | number || "",
        entity_type: payload.entity_type as string || "",
        entity_id: payload.entity_id as string | number || "",
        event_type: be.event_type,
        level: be.level,
        progress: Number(be.progress) || 0, // Ensure progress is always a number
        message: be.message,
        payload: be.payload,
        trace_id: (payload.trace_id as string) || "",
        created_at: be.created_at,
    };
}
