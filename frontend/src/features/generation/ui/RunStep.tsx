import { useEffect, useState, useMemo } from "react";
import { useTranslations } from "next-intl";
import { useJobProgress } from "../hooks/useJobProgress";
import { useJobCreation } from "../hooks/useJobCreation";
import { useWizardStore } from "../stores/useWizardStore";
import { JobProgress } from "./JobProgress";
import { JobResults } from "./JobResults";
import { ActivityLog } from "./ActivityLog";
import { Button } from "@/shared/components/ui/button";
import { Badge } from "@/shared/components/ui/badge";
import { AlertCircle, Loader2, CheckCircle2, XCircle, Wifi, WifiOff, RotateCcw } from "lucide-react";
import { JobStatus } from "../constants/job";
import { statusHeaderPattern, loadingStatePattern, errorAlertPattern } from "@/shared/design-system";
import { retryAllFailedTasks } from "../api/jobs";
import { useQueryClient } from "@tanstack/react-query";

interface RunStepProps {
    onReset: () => void;
}

/**
 * Determines if a job is truly finished based on both job status AND task statuses.
 * This provides a stable "finished" state that doesn't flicker.
 */
function isJobTrulyFinished(job: { status: JobStatus; images?: { status: JobStatus }[] } | undefined): boolean {
    if (!job) return false;
    
    const finalJobStatuses = [
        JobStatus.SUCCESS,
        JobStatus.FAILED,
        JobStatus.CANCELLED,
        JobStatus.PARTIAL_SUCCESS,
    ];
    
    // Job must be in a final status
    if (!finalJobStatuses.includes(job.status)) {
        return false;
    }
    
    // If there are tasks, ALL must be in final states
    if (job.images && job.images.length > 0) {
        const allTasksFinished = job.images.every(
            (img) => img.status === JobStatus.SUCCESS || 
                     img.status === JobStatus.FAILED || 
                     img.status === JobStatus.CANCELLED
        );
        return allTasksFinished;
    }
    
    return true;
}

export const RunStep = ({ onReset }: RunStepProps) => {
    const { jobId, isCreating, createError, handleRetry, handleCancel } = useJobCreation();
    const { job, events, connectionStatus } = useJobProgress(jobId);
    const isJobAlreadyCompleted = useWizardStore((state) => state.isJobCompleted);
    const setJobCompleted = useWizardStore((state) => state.setJobCompleted);
    const queryClient = useQueryClient();
    const [isRetryingAll, setIsRetryingAll] = useState(false);
    const t = useTranslations('generate.run');
    const tCommon = useTranslations('common');
    
    // Stable "finished" state that prevents UI flickering when navigating back to this page
    // Uses both live job data AND the persisted store flag for consistency
    const isFinished = useMemo(() => {
        // If job data shows it's truly finished, use that (source of truth)
        if (isJobTrulyFinished(job)) return true;
        
        // If job is actively running or pending, it's not finished
        // This handles retry scenarios where job restarts
        if (job?.status === JobStatus.RUNNING || job?.status === JobStatus.PENDING) return false;
        
        // If store says job was completed and job data is still loading/stale,
        // trust the store to prevent UI flickering when returning to this page
        if (isJobAlreadyCompleted) return true;
        
        return false;
    }, [job, isJobAlreadyCompleted]);

    // Task analysis for UI decisions
    const taskAnalysis = useMemo(() => {
        const images = job?.images ?? [];
        const failedTasks = images.filter(t => t.status === JobStatus.FAILED);
        const successTasks = images.filter(t => t.status === JobStatus.SUCCESS);
        const activeTasks = images.filter(
            t => t.status === JobStatus.RUNNING || t.status === JobStatus.PENDING
        );
        
        return {
            failedTasks,
            successTasks,
            activeTasks,
            hasFailedTasks: failedTasks.length > 0,
            hasSuccessTasks: successTasks.length > 0,
            hasActiveTasks: activeTasks.length > 0,
            totalTasks: images.length,
        };
    }, [job?.images]);

    // Show retry button when there are failed tasks (even during running)
    const showRetryButton = taskAnalysis.hasFailedTasks;
    // Can only click retry when no active tasks
    const canRetryFailed = taskAnalysis.hasFailedTasks && !taskAnalysis.hasActiveTasks;

    // Retry all failed tasks
    const handleRetryAllFailed = async () => {
        if (isRetryingAll || !canRetryFailed) return;
        
        setIsRetryingAll(true);
        try {
            const failedIds = taskAnalysis.failedTasks.map(t => t.id);
            await retryAllFailedTasks(failedIds);
            
            // Invalidate queries to refresh data
            await queryClient.invalidateQueries({ queryKey: ["job", jobId] });
            
            // Schedule follow-up refetches
            setTimeout(() => queryClient.invalidateQueries({ queryKey: ["job", jobId] }), 1500);
            setTimeout(() => queryClient.invalidateQueries({ queryKey: ["job", jobId] }), 4000);
        } finally {
            setIsRetryingAll(false);
        }
    };

    // Update wizard store when job completes or restarts
    useEffect(() => {
        if (isFinished) {
            setJobCompleted(true);
        }
    }, [isFinished, setJobCompleted]);

    // Reset completed flag if job goes back to running (e.g., after retry)
    useEffect(() => {
        if (job?.status === JobStatus.RUNNING && isJobAlreadyCompleted) {
            setJobCompleted(false);
        }
    }, [job?.status, isJobAlreadyCompleted, setJobCompleted]);

    // Get status details for header - uses stable isFinished for consistency
    const statusInfo = useMemo(() => {
        if (!job?.status) {
            return { icon: Loader2, color: "text-muted-foreground", label: "Starting...", isSpinning: true };
        }
        
        // When truly finished, show final status
        if (isFinished) {
            switch (job.status) {
                case JobStatus.SUCCESS:
                    return { icon: CheckCircle2, color: "text-green-500", label: "Completed", isSpinning: false };
                case JobStatus.FAILED:
                    return { icon: XCircle, color: "text-red-500", label: "Failed", isSpinning: false };
                case JobStatus.PARTIAL_SUCCESS:
                    return { icon: AlertCircle, color: "text-amber-500", label: "Partial Success", isSpinning: false };
                case JobStatus.CANCELLED:
                    return { icon: XCircle, color: "text-muted-foreground", label: "Cancelled", isSpinning: false };
            }
        }
        
        // Still running - show appropriate status based on task progress
        if (taskAnalysis.hasActiveTasks) {
            return { icon: Loader2, color: "text-primary", label: "Running", isSpinning: true };
        }
        
        // Edge case: job status might be transitioning
        return { icon: Loader2, color: "text-primary", label: "Processing...", isSpinning: true };
    }, [job?.status, isFinished, taskAnalysis.hasActiveTasks]);

    const StatusIcon = statusInfo.icon;

    return (
        <div className="space-y-6">
            {/* Creation Phase Error - uses errorAlertPattern from design system */}
            {createError && (
                <div className={errorAlertPattern.containerClasses}>
                    <AlertCircle className={errorAlertPattern.iconClasses} />
                    <div className="flex-1 min-w-0">
                        <h5 className={errorAlertPattern.titleClasses}>{t('errorCreatingJob')}</h5>
                        <p className={errorAlertPattern.messageClasses}>{createError}</p>
                        <div className="mt-3">
                            <Button onClick={handleRetry} variant="outline" size="sm">
                                {t('tryAgain')}
                            </Button>
                        </div>
                    </div>
                </div>
            )}

            {/* Creation Loading - uses loadingStatePattern from design system */}
            {isCreating && (
                <div className={loadingStatePattern.containerClasses}>
                    <div className="relative">
                        <Loader2 className={loadingStatePattern.spinnerClasses} />
                    </div>
                    <div className="text-center">
                        <p className={loadingStatePattern.titleClasses}>{t('startingGeneration')}</p>
                        <p className={loadingStatePattern.descriptionClasses}>
                            {t('uploadingData')}
                        </p>
                    </div>
                </div>
            )}

            {/* Active Job State */}
            {jobId && (
                <div className="space-y-6">
                    {/* Header with Status - uses statusHeaderPattern from design system */}
                    <div className={statusHeaderPattern.containerClasses}>
                        <div className="flex items-start gap-3">
                            <div className={`${statusHeaderPattern.iconContainerClasses} ${statusInfo.color}`}>
                                <StatusIcon
                                    className={`h-5 w-5 ${statusInfo.isSpinning ? "animate-spin" : ""}`}
                                />
                            </div>
                            <div>
                                <h2 className={statusHeaderPattern.titleClasses}>
                                    {isFinished ? t('generationComplete') : t('generatingVisualizations')}
                                </h2>
                                <div className={statusHeaderPattern.badgeContainerClasses}>
                                    <Badge
                                        variant={
                                            isFinished && job?.status === JobStatus.SUCCESS
                                                ? "default"
                                                : isFinished && (job?.status === JobStatus.FAILED || job?.status === JobStatus.PARTIAL_SUCCESS)
                                                  ? "destructive"
                                                  : "secondary"
                                        }
                                    >
                                        {statusInfo.label}
                                    </Badge>
                                    {/* Only show connection status while running */}
                                    {!isFinished && connectionStatus === "connected" && (
                                        <Badge variant="outline" className="gap-1 text-green-600">
                                            <Wifi className="h-3 w-3" />
                                            {t('live')}
                                        </Badge>
                                    )}
                                    {!isFinished && connectionStatus === "failed" && (
                                        <Badge variant="outline" className="gap-1 text-amber-600">
                                            <WifiOff className="h-3 w-3" />
                                            {t('polling')}
                                        </Badge>
                                    )}
                                </div>
                            </div>
                        </div>
                        <div className="flex gap-2 flex-wrap">
                            {/* Retry All Failed - shows when there are failed tasks */}
                            {showRetryButton && (
                                <Button 
                                    variant="outline" 
                                    size="sm" 
                                    onClick={handleRetryAllFailed}
                                    disabled={isRetryingAll || !canRetryFailed}
                                    title={taskAnalysis.hasActiveTasks ? t('waitForRunningTasks') : t('retryAllFailedTasks')}
                                    className="gap-1.5 border-red-200 text-red-600 hover:bg-red-50 hover:text-red-700 dark:border-red-800 dark:text-red-400 dark:hover:bg-red-950 disabled:opacity-50"
                                >
                                    {isRetryingAll ? (
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                    ) : (
                                        <RotateCcw className="h-4 w-4" />
                                    )}
                                    {t('retryFailed', { count: taskAnalysis.failedTasks.length })}
                                </Button>
                            )}
                            {/* Cancel button - only while job is truly running */}
                            {!isFinished && (
                                <Button variant="destructive" size="sm" onClick={handleCancel}>
                                    {tCommon('cancel')}
                                </Button>
                            )}
                            {/* Start New Generation - only when truly finished */}
                            {isFinished && (
                                <Button onClick={onReset} size="sm">
                                    {t('startNewGeneration')}
                                </Button>
                            )}
                        </div>
                    </div>

                    {/* Main Content */}
                    <div className="space-y-6">
                        {/* Progress and Tasks */}
                        <JobProgress job={job} />

                        {/* Results - Show if job has any completed images */}
                        {job && (isFinished || taskAnalysis.hasSuccessTasks) && (
                            <div className="pt-6 border-t">
                                <h2 className="text-lg font-bold mb-4">{t('generatedImages')}</h2>
                                <JobResults job={job} />
                            </div>
                        )}

                        {/* Activity Log - Secondary, collapsed by default */}
                        <ActivityLog
                            events={events}
                            defaultCollapsed={true}
                            maxHeight="300px"
                        />
                    </div>
                </div>
            )}
        </div>
    );
};
