import { useEffect } from "react";
import { useJobProgress } from "../hooks/useJobProgress";
import { useJobCreation } from "../hooks/useJobCreation";
import { useWizardStore } from "../stores/useWizardStore";
import { JobProgress } from "./JobProgress";
import { JobResults } from "./JobResults";
import { Button } from "@/shared/components/ui/button";
import { AlertCircle, Loader2 } from "lucide-react";
import { JobStatus } from "../constants/job";

interface RunStepProps {
    onReset: () => void;
}

export const RunStep = ({ onReset }: RunStepProps) => {
    const { jobId, isCreating, createError, handleRetry, handleCancel } = useJobCreation();
    const { job, events, connectionStatus } = useJobProgress(jobId);
    const setJobCompleted = useWizardStore((state) => state.setJobCompleted);

    const isFinished = job?.status && [
        JobStatus.SUCCESS,
        JobStatus.FAILED,
        JobStatus.CANCELLED,
        JobStatus.PARTIAL_SUCCESS
    ].includes(job.status);

    // Update wizard store when job completes
    useEffect(() => {
        if (isFinished) {
            setJobCompleted(true);
        }
    }, [isFinished, setJobCompleted]);

    return (
        <div className="space-y-6">
            {/* Creation Phase Error */}
            {createError && (
                <div className="border border-red-500/50 bg-red-500/10 text-red-600 dark:text-red-400 p-4 rounded-md flex items-start gap-3">
                    <AlertCircle className="h-5 w-5 mt-0.5" />
                    <div className="flex-1">
                        <h5 className="font-medium mb-1">Error creating job</h5>
                        <p className="text-sm">{createError}</p>
                        <div className="mt-2">
                            <Button onClick={handleRetry} variant="outline" size="sm">Try Again</Button>
                        </div>
                    </div>
                </div>
            )}

            {/* Creation Loading */}
            {isCreating && (
                <div className="flex flex-col items-center justify-center p-12 space-y-4">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                    <p className="text-muted-foreground">Uploading data and starting generation...</p>
                </div>
            )}

            {/* Active Job State */}
            {jobId && (
                <div className="space-y-6">
                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <h2 className="text-2xl font-bold tracking-tight">
                                {isFinished ? "Generation Complete" : "Generating Visualizations"}
                            </h2>
                            <p className="text-muted-foreground flex items-center gap-2">
                                Status: <span className="font-mono font-medium">{job?.status || "Starting..."}</span>
                                {connectionStatus === "connected" && <span className="inline-block w-2 h-2 rounded-full bg-green-500 animate-pulse" title="Live updates active" />}
                                {connectionStatus === "failed" && <span className="text-xs text-amber-500">(Live updates off, polling active)</span>}
                            </p>
                        </div>
                        {!isFinished && (
                            <Button variant="destructive" onClick={handleCancel}>
                                Cancel Generation
                            </Button>
                        )}
                        {isFinished && (
                            <Button onClick={onReset}>
                                Start New
                            </Button>
                        )}
                    </div>

                    {/* Progress / Events */}
                    <JobProgress events={events} job={job} />

                    {/* Results - Show if job has any completed images, even if not fully finished */}
                    {job && (isFinished || (job.images && job.images.some(img => img.status === JobStatus.SUCCESS))) && (
                        <div className="pt-6 border-t">
                            <h2 className="text-xl font-bold mb-4">Generated Images</h2>
                            <JobResults job={job} />
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};
