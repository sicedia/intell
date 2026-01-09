import { JobEvent, Job, JobStatus } from "../constants/job";
import { Badge } from "@/shared/components/ui/badge";
import { Progress } from "@/shared/components/ui/progress";
import { CheckCircle2, XCircle, Loader2, Clock } from "lucide-react";
import { cn } from "@/shared/lib/utils";

interface JobProgressProps {
    events: JobEvent[];
    job?: Job;
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

export const JobProgress = ({ events, job }: JobProgressProps) => {
    const imageTasks = job?.images ?? [];
    
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
    const hasActiveTasks = imageTasks.some(task => 
        task.status === JobStatus.RUNNING || task.status === JobStatus.PENDING
    );
    
    // Show overall progress if job is running, has active tasks, or is completed
    const isCompleted = job?.status === JobStatus.SUCCESS || 
                        job?.status === JobStatus.FAILED || 
                        job?.status === JobStatus.PARTIAL_SUCCESS;
    const shouldShowOverallProgress = job && (
        hasActiveTasks || 
        job.status === JobStatus.RUNNING || 
        (isCompleted && overallProgress >= 100)
    );

    return (
        <div className="space-y-6">
            {/* Overall Progress - Show if running or completed */}
            {shouldShowOverallProgress && (
                <div className="space-y-2">
                    <div className="flex items-center justify-between">
                        <h3 className="text-lg font-medium">Overall Progress</h3>
                        <span className="text-sm font-medium text-muted-foreground">
                            {overallProgress}%
                        </span>
                    </div>
                    <Progress value={overallProgress} className="h-3" />
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        {getStatusIcon(job.status)}
                        <span className="capitalize">{job.status.toLowerCase().replace('_', ' ')}</span>
                    </div>
                </div>
            )}

            {/* Individual Task Progress */}
            {imageTasks.length > 0 && (
                <div className="space-y-4">
                    <h3 className="text-lg font-medium">Image Generation Tasks</h3>
                    <div className="space-y-3">
                        {imageTasks.map((task) => (
                            <div
                                key={task.id}
                                className="border rounded-lg p-4 space-y-2 bg-card"
                            >
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        {getStatusIcon(task.status)}
                                        <span className="font-medium text-sm">
                                            {task.algorithm_key.replace(/_/g, ' ')}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <span className="text-xs text-muted-foreground">
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
                                            className="text-[10px]"
                                        >
                                            {task.status}
                                        </Badge>
                                    </div>
                                </div>
                                <Progress value={Number(task.progress) || 0} className="h-2" />
                                {task.error_message && (
                                    <p className="text-xs text-red-500 mt-1">
                                        {task.error_message}
                                    </p>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Activity Log */}
            <div className="space-y-2">
                <h3 className="text-lg font-medium">Activity Log</h3>
                {events.length === 0 ? (
                    <div className="text-center p-4 text-muted-foreground border rounded-lg bg-muted/20">
                        Waiting for events...
                    </div>
                ) : (
                    <div className="h-[300px] border rounded-lg p-4 bg-black/5 dark:bg-white/5 overflow-y-auto">
                        <div className="space-y-3">
                            {[...events]
                                .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
                                .map((event, i) => (
                                    <div
                                        key={i}
                                        className={cn(
                                            "flex flex-col space-y-1 pb-2 border-b border-border/50 last:border-0 last:pb-0",
                                            event.level === "ERROR" && "bg-red-50/50 dark:bg-red-950/20 rounded p-2"
                                        )}
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center space-x-2">
                                                <Badge
                                                    variant={
                                                        event.level === "ERROR"
                                                            ? "destructive"
                                                            : event.level === "WARNING"
                                                            ? "outline"
                                                            : "secondary"
                                                    }
                                                    className="text-[10px] px-1 py-0 h-5"
                                                >
                                                    {event.level}
                                                </Badge>
                                                <span className="text-xs font-mono text-muted-foreground">
                                                    {new Date(event.created_at).toLocaleTimeString()}
                                                </span>
                                            </div>
                                            {Number(event.progress) > 0 && (
                                                <span className="text-xs font-bold">{event.progress}%</span>
                                            )}
                                        </div>
                                        <p className="text-sm">{event.message}</p>
                                    </div>
                                ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
