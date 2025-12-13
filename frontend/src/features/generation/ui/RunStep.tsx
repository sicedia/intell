import { useEffect, useState } from "react";
import { useWizardStore } from "../stores/useWizardStore";
import { createJob, cancelJob } from "../api/jobs";
import { useJobProgress } from "../hooks/useJobProgress";
import { JobProgress } from "./JobProgress";
import { JobResults } from "./JobResults";
import { Button } from "@/shared/components/ui/button";
import { AlertCircle, Loader2 } from "lucide-react";
import { JobStatus } from "../constants/job";

interface RunStepProps {
    onReset: () => void;
}

export const RunStep = ({ onReset }: RunStepProps) => {
    const {
        sourceFile,
        sourceType,
        selectedAlgorithms,
        jobId,
        setJobId
    } = useWizardStore();

    const [createError, setCreateError] = useState<string | null>(null);
    const [isCreating, setIsCreating] = useState(false);

    // Idempotency key generation (simple)
    const [idempotencyKey] = useState(() =>
        `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    );

    // Track if we've attempted to start to prevent loops
    const [hasStarted, setHasStarted] = useState(false);

    const { job, events, connectionStatus } = useJobProgress(jobId);

    // Auto-start job if not started
    useEffect(() => {
        const startJob = async () => {
            // If we already have a job ID, or are currently creating, or missing file, or ALREADY ATTEMPTED
            if (jobId || isCreating || !sourceFile || hasStarted) return;

            try {
                setIsCreating(true);
                setHasStarted(true); // Mark as started immediately
                setCreateError(null);

                const formData = new FormData();
                formData.append("source_type", sourceType);
                formData.append("source_data", sourceFile);
                formData.append("images", JSON.stringify(selectedAlgorithms));
                formData.append("idempotency_key", idempotencyKey);

                const res = await createJob(formData);
                setJobId(res.job_id);
            } catch (err: any) {
                console.error("Job Creation Failed:", err);
                setCreateError(err.message || "Failed to create generation job");
                // We do NOT reset hasStarted, so it doesn't retry automatically. 
                // User must use "Try Again" or Reset.
            } finally {
                setIsCreating(false);
            }
        };

        startJob();
    }, [jobId, isCreating, sourceFile, sourceType, selectedAlgorithms, idempotencyKey, setJobId, hasStarted]);

    const handleRetry = () => {
        setHasStarted(false);
        setCreateError(null);
    };

    const handleCancel = async () => {
        if (!jobId) return;
        try {
            await cancelJob(jobId);
        } catch (err) {
            console.error("Failed to cancel", err);
        }
    };

    const isFinished = job?.status && [
        JobStatus.SUCCESS,
        JobStatus.FAILED,
        JobStatus.CANCELLED,
        JobStatus.PARTIAL_SUCCESS
    ].includes(job.status);

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
                    {/* Only show progress if running or failed to debug */}
                    <JobProgress events={events} />

                    {/* Results */}
                    {isFinished && job && (
                        <div className="pt-6 border-t">
                            <JobResults job={job} />
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};
