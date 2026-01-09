/**
 * Event types emitted by the backend job system
 */
export const JOB_EVENT_TYPES = {
    // Job lifecycle events
    START: "START",
    DONE: "DONE",
    ERROR: "ERROR",
    JOB_STATUS_CHANGED: "job_status_changed",
    ALGORITHM_ERROR: "ALGORITHM_ERROR",
    
    // Progress events
    PROGRESS: "PROGRESS",
    INFO: "INFO",
    WARNING: "WARNING",
    SUCCESS: "SUCCESS",
} as const;

/**
 * Entity types for events
 */
export const ENTITY_TYPES = {
    JOB: "job",
    IMAGE_TASK: "image_task",
    DESCRIPTION_TASK: "description_task",
} as const;

/**
 * Event levels
 */
export const EVENT_LEVELS = {
    INFO: "INFO",
    WARNING: "WARNING",
    ERROR: "ERROR",
    SUCCESS: "SUCCESS",
} as const;

export type JobEventType = typeof JOB_EVENT_TYPES[keyof typeof JOB_EVENT_TYPES];
export type EntityType = typeof ENTITY_TYPES[keyof typeof ENTITY_TYPES];
export type EventLevel = typeof EVENT_LEVELS[keyof typeof EVENT_LEVELS];
