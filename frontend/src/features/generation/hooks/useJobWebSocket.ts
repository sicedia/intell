import { useState, useEffect, useRef, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { WSClient } from "@/shared/lib/ws";
import { Job, JobEvent, JobStatus } from "../constants/job";
import { JOB_EVENT_TYPES, ENTITY_TYPES } from "../constants/events";
import { transformJobEvent } from "../constants/job";

interface UseJobWebSocketOptions {
    jobId: number | null;
    jobRef: React.MutableRefObject<Job | undefined>;
    refetchJob: () => void;
    onEvent?: (event: JobEvent) => void;
}

interface UseJobWebSocketReturn {
    connectionStatus: "connecting" | "connected" | "disconnected" | "failed";
    isConnected: boolean;
    events: JobEvent[];
}

/**
 * Throttle function specifically for Job updates
 */
function throttleJobUpdate(
    func: (updatedJob: Job) => void,
    delay: number
): (updatedJob: Job) => void {
    let lastCall = 0;
    return (updatedJob: Job) => {
        const now = Date.now();
        if (now - lastCall >= delay) {
            lastCall = now;
            func(updatedJob);
        }
    };
}

/**
 * Hook to manage WebSocket connection for job progress updates
 */
export function useJobWebSocket({
    jobId,
    jobRef,
    refetchJob,
    onEvent,
}: UseJobWebSocketOptions): UseJobWebSocketReturn {
    const [events, setEvents] = useState<JobEvent[]>([]);
    const [connectionStatus, setConnectionStatus] = useState<
        "connecting" | "connected" | "disconnected" | "failed"
    >("disconnected");

    const queryClient = useQueryClient();
    const wsRef = useRef<WSClient | null>(null);
    const connectionTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    // Throttled update function to prevent excessive re-renders
    // Use useRef to store the throttled function and recreate when dependencies change
    const throttledUpdateCacheRef = useRef<((updatedJob: Job) => void) | null>(null);
    
    useEffect(() => {
        const updateCache = (updatedJob: Job) => {
            queryClient.setQueryData(["job", jobId, "initial"], updatedJob);
            jobRef.current = updatedJob;
        };
        throttledUpdateCacheRef.current = throttleJobUpdate(updateCache, 200);
        // jobRef is stable, no need to include in deps
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [jobId, queryClient]);

    const throttledUpdateCache = useCallback(
        (updatedJob: Job) => {
            throttledUpdateCacheRef.current?.(updatedJob);
        },
        []
    );

    // Process job event and update job state
    const processJobEvent = useCallback(
        (transformedEvent: JobEvent) => {
            const currentJob = jobRef.current;
            if (!currentJob) return false;

            const updatedJob: Job = { ...currentJob };
            let shouldRefetch = false;

            // Handle job-level events
            if (transformedEvent.entity_type === ENTITY_TYPES.JOB) {
                // Update overall progress
                if (
                    transformedEvent.progress !== undefined &&
                    transformedEvent.progress !== null
                ) {
                    updatedJob.progress = transformedEvent.progress;
                }

                // Handle job status changes
                if (
                    transformedEvent.event_type === JOB_EVENT_TYPES.JOB_STATUS_CHANGED
                ) {
                    const newStatus = (transformedEvent.payload as { status?: string })
                        ?.status;
                    if (
                        newStatus &&
                        Object.values(JobStatus).includes(newStatus as JobStatus)
                    ) {
                        updatedJob.status = newStatus as JobStatus;
                        shouldRefetch = [
                            JobStatus.SUCCESS,
                            JobStatus.FAILED,
                            JobStatus.CANCELLED,
                            JobStatus.PARTIAL_SUCCESS,
                        ].includes(newStatus as JobStatus);
                    }
                }

                // Handle job completion events
                if (transformedEvent.event_type === JOB_EVENT_TYPES.DONE) {
                    updatedJob.status = JobStatus.SUCCESS;
                    if (
                        transformedEvent.progress !== undefined &&
                        transformedEvent.progress !== null
                    ) {
                        updatedJob.progress = transformedEvent.progress;
                    }
                    shouldRefetch = true;
                } else if (transformedEvent.event_type === JOB_EVENT_TYPES.ERROR) {
                    updatedJob.status = JobStatus.FAILED;
                    shouldRefetch = true;
                } else if (transformedEvent.event_type === JOB_EVENT_TYPES.START) {
                    updatedJob.status = JobStatus.RUNNING;
                }
            }

            // Handle individual image task updates
            if (
                transformedEvent.entity_type === ENTITY_TYPES.IMAGE_TASK &&
                transformedEvent.entity_id
            ) {
                const taskId = Number(transformedEvent.entity_id);
                const taskIndex = updatedJob.images.findIndex((img) => img.id === taskId);

                if (taskIndex >= 0) {
                    const updatedImages = [...updatedJob.images];
                    updatedImages[taskIndex] = {
                        ...updatedImages[taskIndex],
                        progress:
                            Number(
                                transformedEvent.progress ??
                                    updatedImages[taskIndex].progress
                            ) || 0,
                    };

                    // Update status based on event type
                    if (transformedEvent.event_type === JOB_EVENT_TYPES.DONE) {
                        updatedImages[taskIndex].status = JobStatus.SUCCESS;
                    } else if (
                        transformedEvent.event_type === JOB_EVENT_TYPES.ERROR ||
                        transformedEvent.event_type === JOB_EVENT_TYPES.ALGORITHM_ERROR
                    ) {
                        updatedImages[taskIndex].status = JobStatus.FAILED;
                        updatedImages[taskIndex].error_message = transformedEvent.message;
                    } else if (transformedEvent.event_type === JOB_EVENT_TYPES.START) {
                        updatedImages[taskIndex].status = JobStatus.RUNNING;
                    }

                    updatedJob.images = updatedImages;

                    // Check if job is finalized
                    const isFinalized =
                        updatedJob.status === JobStatus.SUCCESS ||
                        updatedJob.status === JobStatus.FAILED ||
                        updatedJob.status === JobStatus.PARTIAL_SUCCESS ||
                        updatedJob.status === JobStatus.CANCELLED;

                    // Only recalculate progress if job is not finalized
                    if (
                        !isFinalized &&
                        updatedJob.status !== JobStatus.CANCELLED &&
                        updatedJob.images.length > 0
                    ) {
                        const totalProgress = updatedJob.images.reduce(
                            (sum, img) => sum + (Number(img.progress) || 0),
                            0
                        );
                        updatedJob.progress = Math.round(
                            totalProgress / updatedJob.images.length
                        );
                    }

                    // Check if all tasks are done
                    const allDone = updatedJob.images.every(
                        (img) =>
                            img.status === JobStatus.SUCCESS ||
                            img.status === JobStatus.FAILED ||
                            img.status === JobStatus.CANCELLED
                    );

                    if (allDone && updatedJob.status === JobStatus.RUNNING) {
                        const successCount = updatedJob.images.filter(
                            (img) => img.status === JobStatus.SUCCESS
                        ).length;
                        const cancelledCount = updatedJob.images.filter(
                            (img) => img.status === JobStatus.CANCELLED
                        ).length;

                        if (cancelledCount === updatedJob.images.length) {
                            updatedJob.status = JobStatus.CANCELLED;
                        } else if (successCount === updatedJob.images.length) {
                            updatedJob.status = JobStatus.SUCCESS;
                            updatedJob.progress = 100;
                        } else if (successCount > 0) {
                            updatedJob.status = JobStatus.PARTIAL_SUCCESS;
                            updatedJob.progress = 100;
                        } else {
                            updatedJob.status = JobStatus.FAILED;
                            updatedJob.progress = 100;
                        }
                        shouldRefetch = true;
                    }
                }
            } else if (
                transformedEvent.progress !== undefined &&
                transformedEvent.progress !== null &&
                transformedEvent.entity_type !== ENTITY_TYPES.IMAGE_TASK
            ) {
                // Update overall progress for other job-level events
                if (updatedJob.status !== JobStatus.CANCELLED) {
                    updatedJob.progress = transformedEvent.progress;
                }
            }

            // Update cache with throttling
            throttledUpdateCache(updatedJob);

            // Refetch if job finished
            if (shouldRefetch) {
                setTimeout(() => {
                    refetchJob();
                }, 500);
            }

            return shouldRefetch;
        },
        [jobRef, refetchJob, throttledUpdateCache]
    );

    // WebSocket connection logic
    useEffect(() => {
        if (!jobId) {
            // Use setTimeout to avoid setState in effect
            const timeoutId = setTimeout(() => {
                setConnectionStatus("disconnected");
                setEvents([]);
            }, 0);
            return () => clearTimeout(timeoutId);
        }

        setConnectionStatus("connecting");

        // Small delay to prevent double-connect in Strict Mode
        connectionTimeoutRef.current = setTimeout(() => {
            const ws = new WSClient(`jobs/${jobId}/`, {
                onOpen: () => {
                    setConnectionStatus("connected");
                },
                onMessage: (data: unknown) => {
                    if (
                        !data ||
                        typeof data !== "object" ||
                        !("event_type" in data)
                    ) {
                        return;
                    }

                    // Transform and add event
                    const transformedEvent = transformJobEvent(data);
                    setEvents((prev) => {
                        // Avoid duplicates based on trace_id and created_at
                        const exists = prev.some(
                            (e) =>
                                e.trace_id === transformedEvent.trace_id &&
                                e.created_at === transformedEvent.created_at
                        );
                        if (exists) return prev;
                        return [...prev, transformedEvent];
                    });

                    // Process event and update job state
                    processJobEvent(transformedEvent);

                    // Call optional callback
                    onEvent?.(transformedEvent);
                },
                onError: (err) => {
                    console.error("WS Error", err);
                    setConnectionStatus("failed");
                },
                onClose: () => {
                    setConnectionStatus((prev) => {
                        if (prev === "connected") {
                            return "disconnected";
                        }
                        return prev;
                    });
                },
            });

            wsRef.current = ws;
            ws.connect();
        }, 100);

        return () => {
            if (connectionTimeoutRef.current) {
                clearTimeout(connectionTimeoutRef.current);
            }
            if (wsRef.current) {
                wsRef.current.disconnect();
                wsRef.current = null;
            }
        };
    }, [jobId, processJobEvent, onEvent]);

    const isConnected = connectionStatus === "connected";

    return {
        connectionStatus,
        isConnected,
        events,
    };
}
