import { useState, useEffect, useCallback } from "react";
import { useWizardStore } from "../stores/useWizardStore";
import { createJob, cancelJob } from "../api/jobs";

interface UseJobCreationReturn {
    jobId: number | null;
    isCreating: boolean;
    createError: string | null;
    handleRetry: () => void;
    handleCancel: () => Promise<void>;
}

/**
 * Hook to manage job creation logic
 * Handles form submission, error handling, and job cancellation
 */
export function useJobCreation(): UseJobCreationReturn {
    const {
        sourceFile,
        sourceType,
        selectedAlgorithms,
        visualizationConfig,
        jobId,
        setJobId,
    } = useWizardStore();

    const [createError, setCreateError] = useState<string | null>(null);
    const [isCreating, setIsCreating] = useState(false);
    const [hasStarted, setHasStarted] = useState(false);

    // Generate idempotency key once
    const [idempotencyKey] = useState(() =>
        `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    );

    // Auto-start job creation when component mounts and conditions are met
    useEffect(() => {
        const startJob = async () => {
            // If we already have a job ID, or are currently creating, or missing file, or already attempted
            if (jobId || isCreating || !sourceFile || hasStarted) return;

            try {
                setIsCreating(true);
                setHasStarted(true);
                setCreateError(null);

                const formData = new FormData();
                formData.append("source_type", sourceType);
                formData.append("source_data", sourceFile);
                formData.append("images", JSON.stringify(selectedAlgorithms));
                formData.append("idempotency_key", idempotencyKey);
                formData.append("visualization_config", JSON.stringify(visualizationConfig));

                const res = await createJob(formData);
                setJobId(res.job_id);
            } catch (err) {
                console.error("Job Creation Failed:", err);
                const errorMessage = err instanceof Error 
                    ? err.message 
                    : "Failed to create generation job";
                setCreateError(errorMessage);
                // Don't reset hasStarted so it doesn't retry automatically
            } finally {
                setIsCreating(false);
            }
        };

        startJob();
    }, [jobId, isCreating, sourceFile, sourceType, selectedAlgorithms, visualizationConfig, idempotencyKey, setJobId, hasStarted]);

    const handleRetry = useCallback(() => {
        setHasStarted(false);
        setCreateError(null);
    }, []);

    const handleCancel = useCallback(async () => {
        if (!jobId) return;
        try {
            await cancelJob(jobId);
            // The job status will be updated via WebSocket events
        } catch (err) {
            console.error("Failed to cancel", err);
            // Could show an error toast here
        }
    }, [jobId]);

    return {
        jobId,
        isCreating,
        createError,
        handleRetry,
        handleCancel,
    };
}
