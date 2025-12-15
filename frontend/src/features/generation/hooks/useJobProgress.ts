import { useState, useEffect, useCallback } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { WSClient } from "@/shared/lib/ws";
import { getJob } from "../api/jobs";
import { Job, JobEvent, JobStatus } from "../constants/job";

interface UseJobProgressReturn {
    job: Job | undefined;
    events: JobEvent[];
    connectionStatus: "connecting" | "connected" | "disconnected" | "failed";
    isConnected: boolean;
}

export const useJobProgress = (jobId: number | null): UseJobProgressReturn => {
    const [events, setEvents] = useState<JobEvent[]>([]);
    const [connectionStatus, setConnectionStatus] = useState<
        "connecting" | "connected" | "disconnected" | "failed"
    >("disconnected");

    const queryClient = useQueryClient();

    // Polling query - active only when WS is failed or disconnected and job is incomplete
    const { data: polledJob } = useQuery({
        queryKey: ["job", jobId],
        queryFn: () => getJob(jobId!),
        enabled: !!jobId && (connectionStatus === "failed" || connectionStatus === "disconnected"),
        refetchInterval: (query) => {
            const status = query.state.data?.status;
            if (status === JobStatus.SUCCESS || status === JobStatus.FAILED || status === JobStatus.CANCELLED || status === JobStatus.PARTIAL_SUCCESS) {
                return false;
            }
            return 2000;
        },
    });

    // WebSocket Logic
    useEffect(() => {
        if (!jobId) {
            setConnectionStatus("disconnected");
            setEvents([]);
            return;
        }

        let ws: WSClient | null = null;
        let connectionTimeout: NodeJS.Timeout | null = null;

        setConnectionStatus("connecting");

        // Small delay to prevent double-connect in Strict Mode
        connectionTimeout = setTimeout(() => {
            // We use the shared WSClient
            ws = new WSClient(`jobs/${jobId}/`, {
                onOpen: () => {
                    setConnectionStatus("connected");
                },
                onMessage: (data: any) => {
                    // Assume data is JobEvent
                    if (data && data.event_type) {
                        setEvents((prev) => [...prev, data]);
                    }

                    // Check if job finished via WS event to update cache immediately
                    if (data && data.event_type === "job_status_changed") {
                        const newStatus = data.payload?.status;
                        if (["SUCCESS", "FAILED", "CANCELLED", "PARTIAL_SUCCESS"].includes(newStatus)) {
                            // Update cache directly for immediate UI update
                            queryClient.setQueryData(["job", jobId, "initial"], (oldData: any) => {
                                if (!oldData) return oldData;
                                return { ...oldData, status: newStatus };
                            });

                            // Then refetch to get complete updated data (with images, etc.)
                            queryClient.refetchQueries({ queryKey: ["job", jobId], exact: false });
                        }
                    }
                },
                onError: (err) => {
                    console.error("WS Error", err);
                    setConnectionStatus("failed");
                },
                onClose: () => {
                    if (connectionStatus === "connected") {
                        setConnectionStatus("disconnected");
                    }
                },
            });

            ws.connect();
        }, 100);

        return () => {
            if (connectionTimeout) {
                clearTimeout(connectionTimeout);
            }
            if (ws) {
                ws.disconnect();
            }
        };
    }, [jobId, queryClient]); // connectionStatus in deps would loop? No.

    const isConnected = connectionStatus === "connected";

    // Combine polled job logic if needed, but mainly we want live events.
    // We can fetch the initial job state once we have an ID to populate current status?
    // Actually, we usually want the full job object available.

    // Let's explicitly fetch the job once when we start (or poll if WS fails)
    // We will run a separate query for the "official" job state that updates less frequently if WS is on.
    const { data: jobData } = useQuery({
        queryKey: ["job", jobId, "initial"],
        queryFn: () => getJob(jobId!),
        enabled: !!jobId,
        // Refetch when WS disconnects or we get a completion event
    });

    // Effective job object merging polled vs initial
    const job = polledJob || jobData;

    // Initialize events from job history if available and no local events captured yet
    // This handles cases where we connect after the job has already emitted some/all events
    useEffect(() => {
        if (job?.events && job.events.length > 0 && events.length === 0) {
            setEvents(job.events);
        }
    }, [job, events.length]);

    return {
        job,
        events,
        connectionStatus,
        isConnected,
    };
};
