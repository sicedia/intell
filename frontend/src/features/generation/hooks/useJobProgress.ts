import { useEffect, useRef, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { getJob } from "../api/jobs";
import { Job, JobEvent, transformJobEvent } from "../constants/job";
import { useJobWebSocket } from "./useJobWebSocket";
import { useJobPolling } from "./useJobPolling";

interface UseJobProgressReturn {
    job: Job | undefined;
    events: JobEvent[];
    connectionStatus: "connecting" | "connected" | "disconnected" | "failed";
    isConnected: boolean;
}

/**
 * Main hook to track job progress via WebSocket and polling fallback
 */
export const useJobProgress = (jobId: number | null): UseJobProgressReturn => {
    const jobRef = useRef<Job | undefined>(undefined);

    // Main job query - fetches initial state and refetches on completion
    const { data: jobData, refetch: refetchJob } = useQuery({
        queryKey: ["job", jobId, "initial"],
        queryFn: () => getJob(jobId!),
        enabled: !!jobId,
        refetchOnWindowFocus: false,
    });

    // Update job ref when data changes
    useEffect(() => {
        if (jobData) {
            jobRef.current = jobData;
        }
    }, [jobData]);

    // WebSocket connection for real-time updates
    const {
        connectionStatus,
        isConnected,
        events: wsEvents,
    } = useJobWebSocket({
        jobId,
        jobRef,
        refetchJob,
    });

    // Polling fallback when WebSocket is unavailable
    const polledJob = useJobPolling({
        jobId,
        enabled: connectionStatus === "failed" || connectionStatus === "disconnected",
    });

    // Effective job object - prefer polled (if WS failed) or initial (if WS connected)
    const job = polledJob || jobData;

    // Extract job events for dependency tracking
    const jobEvents = job?.events;

    // Derive initial events from job history
    const initialEvents = useMemo(() => {
        if (jobEvents && jobEvents.length > 0) {
            return jobEvents.map(transformJobEvent);
        }
        return [];
    }, [jobEvents]);

    // Use WebSocket events if available, otherwise use initial events from job
    const effectiveEvents = wsEvents.length > 0 ? wsEvents : initialEvents;

    return {
        job,
        events: effectiveEvents,
        connectionStatus,
        isConnected,
    };
};
