import { useState, useEffect, useRef, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { WSClient } from "@/shared/lib/ws";
import { Job, JobEvent, JobStatus } from "../constants/job";
import { JOB_EVENT_TYPES, ENTITY_TYPES } from "../constants/events";
import { transformJobEvent } from "../constants/job";

interface UseJobWebSocketOptions {
    jobId: number | null;
    onJobUpdate?: (job: Job) => void;
    onEvent?: (event: JobEvent) => void;
}

interface UseJobWebSocketReturn {
    connectionStatus: "connecting" | "connected" | "disconnected" | "failed";
    isConnected: boolean;
    events: JobEvent[];
}

/**
 * Hook to manage WebSocket connection for job progress updates
 * Simplified: focuses only on receiving events and updating React Query cache
 */
export function useJobWebSocket({
    jobId,
    onJobUpdate,
    onEvent,
}: UseJobWebSocketOptions): UseJobWebSocketReturn {
    const [events, setEvents] = useState<JobEvent[]>([]);
    const [connectionStatus, setConnectionStatus] = useState<
        "connecting" | "connected" | "disconnected" | "failed"
    >("disconnected");

    const queryClient = useQueryClient();
    const wsRef = useRef<WSClient | null>(null);
    const connectionTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    // Update job in React Query cache - NO THROTTLING to avoid missing updates
    const updateJobCache = useCallback(
        (updater: (currentJob: Job | undefined) => Job | undefined) => {
            // Update the main query cache
            queryClient.setQueryData<Job | undefined>(
                ["job", jobId, "initial"],
                (currentJob) => {
                    const updated = updater(currentJob);
                    if (updated) {
                        onJobUpdate?.(updated);
                    }
                    return updated;
                }
            );
            // Also update poll cache to keep them in sync
            queryClient.setQueryData<Job | undefined>(
                ["job", jobId, "poll"],
                (currentJob) => updater(currentJob)
            );
        },
        [jobId, queryClient, onJobUpdate]
    );

    // Process job event and update job state
    const processJobEvent = useCallback(
        (transformedEvent: JobEvent) => {
            updateJobCache((currentJob) => {
                if (!currentJob) return currentJob;

                const updatedJob: Job = { 
                    ...currentJob,
                    images: [...currentJob.images],
                };
                let shouldRefetch = false;

                // Handle job-level events
                if (transformedEvent.entity_type === ENTITY_TYPES.JOB) {
                    // Update overall progress for any job event
                    if (
                        transformedEvent.progress !== undefined &&
                        transformedEvent.progress !== null
                    ) {
                        updatedJob.progress = transformedEvent.progress;
                    }

                    // Handle PROGRESS event - ensure job is marked as running
                    if (transformedEvent.event_type === JOB_EVENT_TYPES.PROGRESS) {
                        // Only update to RUNNING if not already in a final state
                        const isFinalized = [
                            JobStatus.SUCCESS,
                            JobStatus.FAILED,
                            JobStatus.CANCELLED,
                            JobStatus.PARTIAL_SUCCESS,
                        ].includes(updatedJob.status);
                        
                        if (!isFinalized && updatedJob.status !== JobStatus.RUNNING) {
                            updatedJob.status = JobStatus.RUNNING;
                        }
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
                    
                    // Handle RETRY event
                    if (transformedEvent.event_type === JOB_EVENT_TYPES.RETRY) {
                        if (updatedJob.status === JobStatus.FAILED || updatedJob.status === JobStatus.PARTIAL_SUCCESS) {
                            updatedJob.status = JobStatus.RUNNING;
                        }
                    }

                    // Handle job completion events
                    if (transformedEvent.event_type === JOB_EVENT_TYPES.DONE) {
                        updatedJob.status = JobStatus.SUCCESS;
                        updatedJob.progress = 100;
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
                        updatedJob.images[taskIndex] = {
                            ...updatedJob.images[taskIndex],
                            progress:
                                Number(
                                    transformedEvent.progress ??
                                        updatedJob.images[taskIndex].progress
                                ) || 0,
                        };

                        // Update status based on event type
                        if (transformedEvent.event_type === JOB_EVENT_TYPES.DONE) {
                            updatedJob.images[taskIndex].status = JobStatus.SUCCESS;
                            updatedJob.images[taskIndex].progress = 100;
                            shouldRefetch = true;
                        } else if (
                            transformedEvent.event_type === JOB_EVENT_TYPES.ERROR ||
                            transformedEvent.event_type === JOB_EVENT_TYPES.ALGORITHM_ERROR
                        ) {
                            updatedJob.images[taskIndex].status = JobStatus.FAILED;
                            updatedJob.images[taskIndex].error_message = transformedEvent.message;
                        } else if (transformedEvent.event_type === JOB_EVENT_TYPES.CANCELLED) {
                            updatedJob.images[taskIndex].status = JobStatus.CANCELLED;
                        } else if (
                            transformedEvent.event_type === JOB_EVENT_TYPES.START ||
                            transformedEvent.event_type === JOB_EVENT_TYPES.RETRY
                        ) {
                            updatedJob.images[taskIndex].status = JobStatus.RUNNING;
                            updatedJob.images[taskIndex].error_message = undefined;
                            updatedJob.images[taskIndex].progress = 0;
                        }

                        // Recalculate overall progress from tasks
                        const isJobFinalized =
                            updatedJob.status === JobStatus.SUCCESS ||
                            updatedJob.status === JobStatus.FAILED ||
                            updatedJob.status === JobStatus.PARTIAL_SUCCESS ||
                            updatedJob.status === JobStatus.CANCELLED;

                        if (!isJobFinalized && updatedJob.images.length > 0) {
                            const totalProgress = updatedJob.images.reduce(
                                (sum, img) => sum + (Number(img.progress) || 0),
                                0
                            );
                            updatedJob.progress = Math.round(
                                totalProgress / updatedJob.images.length
                            );
                        }

                        // Check if all tasks are done and update job status
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
                            } else if (successCount > 0) {
                                updatedJob.status = JobStatus.PARTIAL_SUCCESS;
                            } else {
                                updatedJob.status = JobStatus.FAILED;
                            }
                            updatedJob.progress = 100;
                            shouldRefetch = true;
                        }
                    }
                }

                // Refetch from server to get complete data (e.g., artifact URLs)
                if (shouldRefetch) {
                    setTimeout(() => {
                        queryClient.invalidateQueries({ queryKey: ["job", jobId] });
                    }, 300);
                }

                return updatedJob;
            });
        },
        [updateJobCache, queryClient, jobId]
    );

    // WebSocket connection logic
    useEffect(() => {
        if (!jobId) {
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
                        // Avoid duplicates
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
