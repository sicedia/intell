import { useState } from "react";
import { Job, ImageTask, JobStatus } from "../constants/job";
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/shared/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/components/ui/tabs";
import { Badge } from "@/shared/components/ui/badge";
import { Button, buttonVariants } from "@/shared/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/shared/components/ui/dropdown-menu";
import { Loader2, RotateCcw, X, Download, ChevronDown } from "lucide-react";
import { env } from "@/shared/lib/env";
import { cn } from "@/shared/lib/utils";
import { retryImageTask, cancelImageTask, downloadJobZip, ZipFormat } from "../api/jobs";
import { useQueryClient } from "@tanstack/react-query";
import { isConnectionError, isCancelledError, getConnectionErrorMessage } from "@/shared/lib/api-client";
import { createLogger } from "@/shared/lib/logger";

// Helper to construct full URL if backend returns relative path
const getFullUrl = (path?: string) => {
    if (!path) return undefined;
    if (path.startsWith("http")) return path;
    
    // Get base URL from env, remove /api if present to get server root
    const base = env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
    const baseUrl = base.replace(/\/api\/?$/, "");
    const origin = new URL(baseUrl).origin;
    return `${origin}${path.startsWith('/') ? '' : '/'}${path}`;
};

// Format algorithm key for display
const formatAlgorithmKey = (key: string): string => {
    return key
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
};

// Scoped loggers for different operations
const downloadLog = createLogger("DownloadZip");
const taskLog = createLogger("ImageTask");

export const JobResults = ({ job }: { job: Job }) => {
    const [isDownloading, setIsDownloading] = useState(false);

    const handleDownloadAll = async (format: ZipFormat) => {
        if (isDownloading) return;
        
        setIsDownloading(true);
        try {
            await downloadJobZip(job.id, format);
        } catch (error) {
            if (isCancelledError(error)) return;
            
            if (isConnectionError(error)) {
                downloadLog.warn(getConnectionErrorMessage(error));
            } else {
                downloadLog.error("Failed to download:", error);
            }
        } finally {
            setIsDownloading(false);
        }
    };

    if (!job.images || job.images.length === 0) {
        return (
            <div className="text-center text-muted-foreground p-8 border rounded-lg">
                <p>No images generated.</p>
                {job.status === JobStatus.RUNNING && (
                    <p className="text-sm mt-2">Images are still being generated...</p>
                )}
            </div>
        );
    }

    const successfulImages = job.images.filter(img => img.status === JobStatus.SUCCESS);
    const failedImages = job.images.filter(img => img.status === JobStatus.FAILED);
    const pendingImages = job.images.filter(img => img.status === JobStatus.PENDING || img.status === JobStatus.RUNNING);
    const cancelledImages = job.images.filter(img => img.status === JobStatus.CANCELLED);

    return (
        <div className="space-y-6">
            {successfulImages.length > 0 && (
                <div>
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="text-lg font-medium">
                            Generated Images ({successfulImages.length})
                        </h3>
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button size="sm" variant="outline" disabled={isDownloading}>
                                    {isDownloading ? (
                                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                    ) : (
                                        <Download className="h-4 w-4 mr-2" />
                                    )}
                                    Download All
                                    <ChevronDown className="h-4 w-4 ml-1" />
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                                <DropdownMenuItem onClick={() => handleDownloadAll("both")}>
                                    All Formats (PNG + SVG)
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => handleDownloadAll("png")}>
                                    PNG Only
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => handleDownloadAll("svg")}>
                                    SVG Only
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {successfulImages.map((task) => (
                            <TaskResultCard key={task.id} task={task} jobId={job.id} />
                        ))}
                    </div>
                </div>
            )}

            {pendingImages.length > 0 && (
                <div>
                    <h3 className="text-lg font-medium mb-4">
                        In Progress ({pendingImages.length})
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {pendingImages.map((task) => (
                            <TaskResultCard key={task.id} task={task} jobId={job.id} />
                        ))}
                    </div>
                </div>
            )}

            {failedImages.length > 0 && (
                <div>
                    <h3 className="text-lg font-medium mb-4 text-red-500">
                        Failed ({failedImages.length})
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {failedImages.map((task) => (
                            <TaskResultCard key={task.id} task={task} jobId={job.id} />
                        ))}
                    </div>
                </div>
            )}

            {cancelledImages.length > 0 && (
                <div>
                    <h3 className="text-lg font-medium mb-4 text-muted-foreground">
                        Cancelled ({cancelledImages.length})
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {cancelledImages.map((task) => (
                            <TaskResultCard key={task.id} task={task} jobId={job.id} />
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

const TaskResultCard = ({ task, jobId }: { task: ImageTask; jobId: number }) => {
    const [isRetrying, setIsRetrying] = useState(false);
    const [isCancelling, setIsCancelling] = useState(false);
    const queryClient = useQueryClient();
    const pngUrl = getFullUrl(task.result_urls.png);
    const svgUrl = getFullUrl(task.result_urls.svg);
    const hasImages = pngUrl || svgUrl;
    const hasBoth = pngUrl && svgUrl;
    
    // Check if task can be retried (FAILED, RUNNING, PENDING, or CANCELLED)
    const canRetry = task.status === JobStatus.FAILED || 
                     task.status === JobStatus.RUNNING || 
                     task.status === JobStatus.PENDING ||
                     task.status === JobStatus.CANCELLED;
    
    // Check if task can be cancelled (RUNNING or PENDING only)
    const canCancel = task.status === JobStatus.RUNNING || 
                      task.status === JobStatus.PENDING;
    
    const handleRetry = async () => {
        if (isRetrying || !canRetry) return;
        
        setIsRetrying(true);
        try {
            await retryImageTask(task.id);
            
            // Invalidate ALL job queries to refetch updated state
            // Use partial key match to cover both ["job", jobId] and ["job", jobId, "initial"]
            await queryClient.invalidateQueries({ 
                queryKey: ["job", jobId],
                // Force refetch even if query is stale
                refetchType: "all"
            });
            
            // Also invalidate poll query to ensure polling picks up the change
            await queryClient.invalidateQueries({
                queryKey: ["job", jobId, "poll"],
                refetchType: "all"
            });
            
            // Schedule additional refetches to catch the update
            // This helps when WebSocket is not working properly
            setTimeout(() => {
                queryClient.invalidateQueries({ queryKey: ["job", jobId] });
            }, 1500);
            
            setTimeout(() => {
                queryClient.invalidateQueries({ queryKey: ["job", jobId] });
            }, 4000);
            
        } catch (error) {
            // Ignorar cancelaciones (ej: usuario navegó a otra página)
            if (isCancelledError(error)) return;
            
            // Los errores de conexión ya son manejados globalmente (banner + toast)
            if (isConnectionError(error)) {
                taskLog.warn(`Retry task ${task.id}: ${getConnectionErrorMessage(error)}`);
            } else {
                taskLog.error(`Retry task ${task.id} failed:`, error);
            }
        } finally {
            setIsRetrying(false);
        }
    };
    
    const handleCancel = async () => {
        if (isCancelling || !canCancel) return;
        
        setIsCancelling(true);
        try {
            await cancelImageTask(task.id);
            
            // Invalidate ALL job queries to refetch updated state
            await queryClient.invalidateQueries({ 
                queryKey: ["job", jobId],
                refetchType: "all"
            });
            
            // Schedule a follow-up refetch
            setTimeout(() => {
                queryClient.invalidateQueries({ queryKey: ["job", jobId] });
            }, 1000);
            
        } catch (error) {
            // Ignorar cancelaciones (ej: usuario navegó a otra página)
            if (isCancelledError(error)) return;
            
            // Los errores de conexión ya son manejados globalmente (banner + toast)
            if (isConnectionError(error)) {
                taskLog.warn(`Cancel task ${task.id}: ${getConnectionErrorMessage(error)}`);
            } else {
                taskLog.error(`Cancel task ${task.id} failed:`, error);
            }
        } finally {
            setIsCancelling(false);
        }
    };

    return (
        <Card className="overflow-hidden">
            <CardHeader className="py-4 bg-muted/30">
                <div className="flex justify-between items-center">
                    <CardTitle className="text-base font-medium truncate" title={task.algorithm_key}>
                        {formatAlgorithmKey(task.algorithm_key)}
                    </CardTitle>
                    <StatusBadge status={task.status} />
                </div>
            </CardHeader>
            <CardContent className="p-0">
                {task.status === JobStatus.SUCCESS && hasImages ? (
                    <Tabs defaultValue={svgUrl ? "svg" : "png"} className="w-full">
                        <div className="p-4 bg-checkered min-h-[300px] flex items-center justify-center bg-gray-50 dark:bg-gray-900 border-b relative">
                            <TabsContent value="png" className="mt-0 w-full flex justify-center">
                                {pngUrl ? (
                                    <div className="relative w-full max-w-full h-[300px] flex items-center justify-center">
                                        {/* eslint-disable-next-line @next/next/no-img-element */}
                                        <img 
                                            src={pngUrl} 
                                            alt={`${formatAlgorithmKey(task.algorithm_key)} - PNG`} 
                                            className="max-h-[300px] max-w-full object-contain"
                                        />
                                    </div>
                                ) : (
                                    <span className="text-sm text-muted-foreground">No PNG available</span>
                                )}
                            </TabsContent>
                            <TabsContent value="svg" className="mt-0 w-full flex justify-center">
                                {svgUrl ? (
                                    <div className="relative w-full max-w-full h-[300px] flex items-center justify-center">
                                        {/* eslint-disable-next-line @next/next/no-img-element */}
                                        <img 
                                            src={svgUrl} 
                                            alt={`${formatAlgorithmKey(task.algorithm_key)} - SVG`} 
                                            className="max-h-[300px] max-w-full object-contain"
                                        />
                                    </div>
                                ) : (
                                    <span className="text-sm text-muted-foreground">No SVG available</span>
                                )}
                            </TabsContent>
                        </div>

                        {hasBoth && (
                            <TabsList className="w-full rounded-none border-b">
                                <TabsTrigger value="svg" className="flex-1">SVG</TabsTrigger>
                                <TabsTrigger value="png" className="flex-1">PNG</TabsTrigger>
                            </TabsList>
                        )}
                    </Tabs>
                ) : task.status === JobStatus.RUNNING || task.status === JobStatus.PENDING ? (
                    <div className="h-[300px] flex items-center justify-center p-6 text-center text-muted-foreground flex-col gap-2">
                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                        <p>Generating image...</p>
                        <p className="text-xs">Progress: {task.progress}%</p>
                        {(task.progress === 0 && canRetry) && (
                            <p className="text-xs text-amber-500 mt-2">
                                Task may be stuck. You can retry or cancel.
                            </p>
                        )}
                    </div>
                ) : task.status === JobStatus.CANCELLED ? (
                    <div className="h-[300px] flex items-center justify-center p-6 text-center text-muted-foreground flex-col gap-2">
                        <p className="font-medium">Generation Cancelled</p>
                        {canRetry && (
                            <p className="text-xs text-muted-foreground">
                                You can retry this task if needed.
                            </p>
                        )}
                    </div>
                ) : (
                    <div className="h-[300px] flex items-center justify-center p-6 text-center text-muted-foreground flex-col gap-2">
                        <p className="font-medium">Generation Failed</p>
                        {task.error_message && (
                            <p className="text-xs text-red-500 bg-red-50 dark:bg-red-950/20 p-2 rounded max-w-md">
                                {task.error_message}
                            </p>
                        )}
                    </div>
                )}
            </CardContent>
            <CardFooter className="flex justify-between p-4 bg-muted/10">
                <div className="text-xs text-muted-foreground">
                    Task ID: {task.id}
                </div>
                <div className="flex gap-2">
                    {canCancel && (
                        <Button
                            size="sm"
                            variant="outline"
                            onClick={handleCancel}
                            disabled={isCancelling || isRetrying}
                            className="gap-2"
                        >
                            {isCancelling ? (
                                <>
                                    <Loader2 className="h-3 w-3 animate-spin" />
                                    Cancelling...
                                </>
                            ) : (
                                <>
                                    <X className="h-3 w-3" />
                                    Cancel
                                </>
                            )}
                        </Button>
                    )}
                    {canRetry && (
                        <Button
                            size="sm"
                            variant="default"
                            onClick={handleRetry}
                            disabled={isRetrying || isCancelling}
                            className="gap-2"
                        >
                            {isRetrying ? (
                                <>
                                    <Loader2 className="h-3 w-3 animate-spin" />
                                    Retrying...
                                </>
                            ) : (
                                <>
                                    <RotateCcw className="h-3 w-3" />
                                    Retry
                                </>
                            )}
                        </Button>
                    )}
                    {pngUrl && (
                        <a
                            href={pngUrl}
                            download
                            target="_blank"
                            rel="noopener noreferrer"
                            className={cn(buttonVariants({ size: "sm", variant: "outline" }))}
                        >
                            Download PNG
                        </a>
                    )}
                    {svgUrl && (
                        <a
                            href={svgUrl}
                            download
                            target="_blank"
                            rel="noopener noreferrer"
                            className={cn(buttonVariants({ size: "sm", variant: "outline" }))}
                        >
                            Download SVG
                        </a>
                    )}
                </div>
            </CardFooter>
        </Card>
    );
};

const StatusBadge = ({ status }: { status: JobStatus }) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
        [JobStatus.SUCCESS]: "default", // or success if available? using default for now which is black/primary
        [JobStatus.FAILED]: "destructive",
        [JobStatus.PENDING]: "secondary",
        [JobStatus.RUNNING]: "outline", // animate this?
        [JobStatus.CANCELLED]: "secondary",
        [JobStatus.PARTIAL_SUCCESS]: "secondary", // maybe yellow?
    };

    return <Badge variant={variants[status] || "outline"}>{status}</Badge>;
};
