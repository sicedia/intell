import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { getJob } from "../api/jobs";
import { Job, JobEvent, JobStatus, transformJobEvent } from "../constants/job";
import { useJobWebSocket } from "./useJobWebSocket";

interface UseJobProgressReturn {
    job: Job | undefined;
    events: JobEvent[];
    connectionStatus: "connecting" | "connected" | "disconnected" | "failed";
    isConnected: boolean;
}

/**
 * Check if job is truly finished (status is final AND all tasks are done)
 */
function isJobTrulyFinished(job: Job | undefined): boolean {
    if (!job) return false;
    
    const finalStatuses = [
        JobStatus.SUCCESS,
        JobStatus.FAILED,
        JobStatus.CANCELLED,
        JobStatus.PARTIAL_SUCCESS,
    ];
    
    if (!finalStatuses.includes(job.status)) {
        return false;
    }
    
    // All tasks must also be in final states
    if (job.images && job.images.length > 0) {
        return job.images.every(
            (img) => img.status === JobStatus.SUCCESS || 
                     img.status === JobStatus.FAILED || 
                     img.status === JobStatus.CANCELLED
        );
    }
    
    return true;
}

/**
 * Main hook to track job progress
 * 
 * Architecture:
 * - React Query as single source of truth
 * - WebSocket updates the cache directly (no throttling)
 * - Polling as safety net (every 2 seconds until finished)
 */
export const useJobProgress = (jobId: number | null): UseJobProgressReturn => {
    // Main job query - this is the single source of truth
    const { data: job } = useQuery({
        queryKey: ["job", jobId, "initial"],
        queryFn: () => getJob(jobId!),
        enabled: !!jobId,
        refetchOnWindowFocus: true,
        // Poll every 2 seconds until job is truly finished
        // This is our primary update mechanism - reliable and simple
        refetchInterval: (query) => {
            const jobData = query.state.data;
            if (isJobTrulyFinished(jobData)) {
                return false; // Stop polling when done
            }
            return 2000; // Poll every 2 seconds
        },
        // Keep data fresh
        staleTime: 1000,
    });

    // WebSocket for real-time events (Activity Log) and faster updates
    // WebSocket updates the same cache that the query uses
    const {
        connectionStatus,
        isConnected,
        events: wsEvents,
    } = useJobWebSocket({
        jobId,
    });

    // Derive events from job history when WebSocket events are empty
    const initialEvents = useMemo(() => {
        if (job?.events && job.events.length > 0) {
            return job.events.map(transformJobEvent);
        }
        return [];
    }, [job?.events]);

    // Prefer WebSocket events (real-time) over job history events
    const events = wsEvents.length > 0 ? wsEvents : initialEvents;

    return {
        job,
        events,
        connectionStatus,
        isConnected,
    };
};
