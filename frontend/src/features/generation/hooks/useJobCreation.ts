import { useState, useEffect, useCallback, useRef } from "react";
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

    // Ref to prevent double submissions (React Strict Mode, race conditions)
    const isSubmittingRef = useRef(false);

    // Generate idempotency key - regenerate on retry
    const [idempotencyKey, setIdempotencyKey] = useState(() =>
        `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    );

    const generateNewIdempotencyKey = useCallback(() => {
        setIdempotencyKey(`job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
    }, []);

    // Reset state when jobId is cleared (e.g., when wizard is reset)
    useEffect(() => {
        if (!jobId) {
            setHasStarted(false);
            setCreateError(null);
            setIsCreating(false);
            isSubmittingRef.current = false;
        }
    }, [jobId]);

    // Auto-start job creation when component mounts and conditions are met
    useEffect(() => {
        const startJob = async () => {
            // If we already have a job ID, or are currently creating, or missing file, or already attempted
            if (jobId || isCreating || !sourceFile || hasStarted) return;

            // Prevent double submissions using ref (persists across renders)
            if (isSubmittingRef.current) return;
            isSubmittingRef.current = true;

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
                let errorMessage = "Failed to create generation job";
                
                // Try to extract detailed error message from API response
                if (err && typeof err === 'object' && 'data' in err) {
                    const errorData = (err as { data?: unknown }).data;
                    if (errorData && typeof errorData === 'object') {
                        const data = errorData as Record<string, unknown>;
                        if (typeof data.error === 'string') {
                            errorMessage = data.error;
                        } else if (typeof data.message === 'string') {
                            errorMessage = data.message;
                        } else if (Array.isArray(data.detail) && data.detail.length > 0) {
                            errorMessage = String(data.detail[0]);
                        }
                    }
                } else if (err instanceof Error) {
                    errorMessage = err.message;
                }
                
                setCreateError(errorMessage);
                // Don't reset hasStarted so it doesn't retry automatically
            } finally {
                setIsCreating(false);
                isSubmittingRef.current = false;
            }
        };

        startJob();
    }, [jobId, isCreating, sourceFile, sourceType, selectedAlgorithms, visualizationConfig, idempotencyKey, setJobId, hasStarted]);

    const handleRetry = useCallback(() => {
        generateNewIdempotencyKey(); // Generate new key for retry
        setHasStarted(false);
        setCreateError(null);
    }, [generateNewIdempotencyKey]);

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
