import { useQuery } from "@tanstack/react-query";
import { getJob } from "../api/jobs";
import { Job, JobStatus } from "../constants/job";

interface UseJobPollingOptions {
    jobId: number | null;
    enabled: boolean;
}

/**
 * Hook to poll job status when WebSocket is unavailable
 */
export function useJobPolling({
    jobId,
    enabled,
}: UseJobPollingOptions): Job | undefined {
    const { data: polledJob } = useQuery({
        queryKey: ["job", jobId, "poll"],
        queryFn: () => getJob(jobId!),
        enabled: enabled && !!jobId,
        refetchInterval: (query) => {
            const status = query.state.data?.status;
            if (
                status === JobStatus.SUCCESS ||
                status === JobStatus.FAILED ||
                status === JobStatus.CANCELLED ||
                status === JobStatus.PARTIAL_SUCCESS
            ) {
                return false;
            }
            return 2000;
        },
    });

    return polledJob;
}
