import { useState } from "react";
import { useTranslations } from "next-intl";
import { Job, JobStatus } from "../constants/job";
import { Badge } from "@/shared/components/ui/badge";
import { Progress } from "@/shared/components/ui/progress";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent } from "@/shared/components/ui/card";
import { CheckCircle2, XCircle, Loader2, Clock, ImageIcon, RotateCcw } from "lucide-react";
import { cn } from "@/shared/lib/utils";
import { taskItemPattern, progressCardPattern } from "@/shared/design-system";
import { retryAllFailedTasks, retryImageTask } from "../api/jobs";
import { useQueryClient } from "@tanstack/react-query";

interface JobProgressProps {
    job?: Job;
    onRetryAllFailed?: () => void;
}

const getStatusIcon = (status: JobStatus) => {
    switch (status) {
        case JobStatus.SUCCESS:
            return <CheckCircle2 className="h-4 w-4 text-green-500" />;
        case JobStatus.FAILED:
            return <XCircle className="h-4 w-4 text-red-500" />;
        case JobStatus.RUNNING:
            return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
        default:
            return <Clock className="h-4 w-4 text-muted-foreground" />;
    }
};

export const JobProgress = ({ job, onRetryAllFailed }: JobProgressProps) => {
    const [isRetryingAll, setIsRetryingAll] = useState(false);
    const [retryingTaskIds, setRetryingTaskIds] = useState<Set<number>>(new Set());
    const queryClient = useQueryClient();
    const imageTasks = job?.images ?? [];
    const t = useTranslations('generate.run');

    // Calculate overall progress - prefer backend progress_total for finalized jobs
    const calculateOverallProgress = () => {
        // Use backend progress_total if available (especially for finalized jobs)
        if (job?.progress !== undefined && job.progress !== null) {
            return job.progress;
        }

        // Fallback to calculating from individual tasks
        if (!imageTasks || imageTasks.length === 0) {
            return 0;
        }

        const totalProgress = imageTasks.reduce((sum, task) => {
            return sum + (Number(task.progress) || 0);
        }, 0);

        return Math.round(totalProgress / imageTasks.length);
    };

    const overallProgress = calculateOverallProgress();
    const hasActiveTasks = imageTasks.some(
        (task) => task.status === JobStatus.RUNNING || task.status === JobStatus.PENDING
    );

    // Show overall progress if job is running, has active tasks, or is completed
    const isCompleted =
        job?.status === JobStatus.SUCCESS ||
        job?.status === JobStatus.FAILED ||
        job?.status === JobStatus.PARTIAL_SUCCESS;
    const shouldShowOverallProgress =
        job &&
        (hasActiveTasks || job.status === JobStatus.RUNNING || (isCompleted && overallProgress >= 100));

    // Count tasks by status
    const completedTasks = imageTasks.filter((t) => t.status === JobStatus.SUCCESS).length;
    const failedTasksList = imageTasks.filter((t) => t.status === JobStatus.FAILED);
    const failedTasks = failedTasksList.length;
    const pendingTasks = imageTasks.filter(
        (t) => t.status === JobStatus.PENDING || t.status === JobStatus.RUNNING
    ).length;

    // Retry all failed tasks
    const handleRetryAllFailed = async () => {
        if (isRetryingAll || failedTasksList.length === 0) return;
        
        setIsRetryingAll(true);
        try {
            const failedIds = failedTasksList.map(t => t.id);
            await retryAllFailedTasks(failedIds);
            
            // Invalidate queries to refresh data
            await queryClient.invalidateQueries({ queryKey: ["job", job?.id] });
            
            // Schedule follow-up refetches
            setTimeout(() => queryClient.invalidateQueries({ queryKey: ["job", job?.id] }), 1500);
            setTimeout(() => queryClient.invalidateQueries({ queryKey: ["job", job?.id] }), 4000);
            
            onRetryAllFailed?.();
        } finally {
            setIsRetryingAll(false);
        }
    };

    // Retry single task inline
    const handleRetryTask = async (taskId: number) => {
        if (retryingTaskIds.has(taskId)) return;
        
        setRetryingTaskIds(prev => new Set(prev).add(taskId));
        try {
            await retryImageTask(taskId);
            await queryClient.invalidateQueries({ queryKey: ["job", job?.id] });
            setTimeout(() => queryClient.invalidateQueries({ queryKey: ["job", job?.id] }), 1500);
        } finally {
            setRetryingTaskIds(prev => {
                const newSet = new Set(prev);
                newSet.delete(taskId);
                return newSet;
            });
        }
    };

    return (
        <div className="space-y-4">
            {/* Overall Progress Card */}
            {shouldShowOverallProgress && (
                <Card>
                    <CardContent className="pt-6">
                        <div className="space-y-4">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    {getStatusIcon(job.status)}
                                    <div>
                                        <h3 className="font-semibold">{t('overallProgress')}</h3>
                                        <p className="text-sm text-muted-foreground capitalize">
                                            {job.status.toLowerCase().replace("_", " ")}
                                        </p>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <span className="text-2xl font-bold">{overallProgress}%</span>
                                </div>
                            </div>
                            <Progress value={overallProgress} className={progressCardPattern.progressBarClasses} />
                            {/* Task summary badges - uses progressCardPattern from design system */}
                            <div className={progressCardPattern.summaryContainerClasses}>
                                {completedTasks > 0 && (
                                    <Badge variant="default" className="gap-1">
                                        <CheckCircle2 className="h-3 w-3" />
                                        {t('completedCount', { count: completedTasks })}
                                    </Badge>
                                )}
                                {pendingTasks > 0 && (
                                    <Badge variant="secondary" className="gap-1">
                                        <Loader2 className="h-3 w-3 animate-spin" />
                                        {t('inProgressCount', { count: pendingTasks })}
                                    </Badge>
                                )}
                                {failedTasks > 0 && (
                                    <div className="flex items-center gap-2">
                                        <Badge variant="destructive" className="gap-1">
                                            <XCircle className="h-3 w-3" />
                                            {t('failedCount', { count: failedTasks })}
                                        </Badge>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={handleRetryAllFailed}
                                            disabled={isRetryingAll || hasActiveTasks}
                                            title={hasActiveTasks ? t('waitForRunningTasks') : t('retryAllFailedTasks')}
                                            className="h-6 text-xs gap-1 border-red-200 text-red-600 hover:bg-red-50 hover:text-red-700 dark:border-red-800 dark:text-red-400 dark:hover:bg-red-950 disabled:opacity-50"
                                        >
                                            {isRetryingAll ? (
                                                <Loader2 className="h-3 w-3 animate-spin" />
                                            ) : (
                                                <RotateCcw className="h-3 w-3" />
                                            )}
                                            {t('retryAll')}
                                        </Button>
                                    </div>
                                )}
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Individual Task Progress */}
            {imageTasks.length > 0 && (
                <div className="space-y-3">
                    <div className="flex items-center gap-2">
                        <ImageIcon className="h-4 w-4 text-muted-foreground" />
                        <h3 className="font-medium text-sm text-muted-foreground">
                            {t('imageTasks', { count: imageTasks.length })}
                        </h3>
                    </div>
                    <div className="grid gap-2">
                        {/* Task items - uses taskItemPattern from design system */}
                        {imageTasks.map((task) => {
                            const isRetrying = retryingTaskIds.has(task.id);
                            const isFailed = task.status === JobStatus.FAILED;
                            const canRetryNow = isFailed && !hasActiveTasks;
                            
                            return (
                                <div
                                    key={task.id}
                                    className={cn(
                                        taskItemPattern.baseClasses,
                                        task.status === JobStatus.RUNNING && taskItemPattern.runningClasses,
                                        task.status === JobStatus.SUCCESS && taskItemPattern.successClasses,
                                        task.status === JobStatus.FAILED && taskItemPattern.failedClasses
                                    )}
                                >
                                    <div className="shrink-0">{getStatusIcon(task.status)}</div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center justify-between gap-2">
                                            <span className="font-medium text-sm truncate">
                                                {task.algorithm_key
                                                    .split("_")
                                                    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                                                    .join(" ")}
                                            </span>
                                            <div className="flex items-center gap-2 shrink-0">
                                                {/* Show retry button for failed tasks, disable while active tasks running */}
                                                {isFailed && (
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => handleRetryTask(task.id)}
                                                        disabled={isRetrying || !canRetryNow}
                                                        title={hasActiveTasks ? t('waitForRunning') : t('retryThisTask')}
                                                        className="h-5 px-2 text-[10px] text-red-600 hover:text-red-700 hover:bg-red-100 dark:text-red-400 dark:hover:bg-red-950 disabled:opacity-50"
                                                    >
                                                        {isRetrying ? (
                                                            <Loader2 className="h-3 w-3 animate-spin" />
                                                        ) : (
                                                            <RotateCcw className="h-3 w-3" />
                                                        )}
                                                        <span className="ml-1">{t('retry')}</span>
                                                    </Button>
                                                )}
                                                <span className="text-xs text-muted-foreground tabular-nums">
                                                    {task.progress}%
                                                </span>
                                                <Badge
                                                    variant={
                                                        task.status === JobStatus.SUCCESS
                                                            ? "default"
                                                            : task.status === JobStatus.FAILED
                                                              ? "destructive"
                                                              : "secondary"
                                                    }
                                                    className="text-[10px] h-5"
                                                >
                                                    {task.status}
                                                </Badge>
                                            </div>
                                        </div>
                                        {task.status === JobStatus.RUNNING && (
                                            <Progress value={Number(task.progress) || 0} className="h-1 mt-2" />
                                        )}
                                        {task.error_message && (
                                            <p className="text-xs text-red-500 mt-1 truncate" title={task.error_message}>
                                                {task.error_message}
                                            </p>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
};
