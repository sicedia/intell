import { useState } from "react";
import React from "react";
import { useTranslations } from "next-intl";
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
import { Loader2, RotateCcw, X, Download, ChevronDown, BookmarkPlus, BookmarkCheck, Sparkles, Eye, Edit } from "lucide-react";
import { UserInfo } from "@/shared/ui/UserInfo";
import { ImageCard } from "@/shared/ui/ImageCard";
import { Switch } from "@/shared/components/ui/switch";
import { Label } from "@/shared/components/ui/label";
import { env } from "@/shared/lib/env";
import { cn } from "@/shared/lib/utils";
import { retryImageTask, cancelImageTask, downloadJobZip, ZipFormat } from "../api/jobs";
import { usePublishImage } from "@/features/images/hooks/useImages";
import { useQueryClient } from "@tanstack/react-query";
import { isConnectionError, isCancelledError, getConnectionErrorMessage } from "@/shared/lib/api-client";
import { createLogger } from "@/shared/lib/logger";
import { useAutoDescribeAndPublish } from "../hooks/useAutoDescribeAndPublish";
import { AIDescriptionDialog } from "@/features/images/ui/AIDescriptionDialog";
import { ImageDetailDialog } from "@/features/images/ui/ImageDetailDialog";
import { Progress } from "@/shared/components/ui/progress";

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
    const [autoDescribeAndPublish, setAutoDescribeAndPublish] = useState(false);
    const queryClient = useQueryClient();
    const t = useTranslations('generate.results');
    const tCommon = useTranslations('common');
    
    // Check if all images are complete but job is still RUNNING or PENDING
    // This can happen if finalize_job didn't run or was delayed
    // This is a safety check to detect inconsistencies
    const allImagesComplete = job.images && job.images.length > 0 && 
        job.images.every(img => 
            img.status === JobStatus.SUCCESS || 
            img.status === JobStatus.FAILED || 
            img.status === JobStatus.CANCELLED
        );
    
    const shouldBeFinished = allImagesComplete && 
        (job.status === JobStatus.RUNNING || job.status === JobStatus.PENDING);
    
    // Force refetch if job should be finished but isn't
    // Use a debounced approach to avoid excessive refetches
    React.useEffect(() => {
        if (shouldBeFinished) {
            // Add a small delay to allow backend to update
            const timeoutId = setTimeout(() => {
                // Invalidate and refetch to get updated job status
                // The backend should have updated it via _check_and_update_job_status
                queryClient.invalidateQueries({ 
                    queryKey: ["job", job.id],
                    refetchType: "all"
                });
            }, 1000); // Wait 1 second before refetching
            
            return () => clearTimeout(timeoutId);
        }
    }, [shouldBeFinished, job.id, job.status, queryClient]);

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
                <p>{t('noImagesGenerated')}</p>
                {job.status === JobStatus.RUNNING && (
                    <p className="text-sm mt-2">{t('imagesStillBeingGenerated')}</p>
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
                            {t('generatedImagesCount', { count: successfulImages.length })}
                        </h3>
                        <div className="flex items-center gap-4">
                            <div className="flex items-center gap-2">
                                <Switch
                                    id="auto-describe"
                                    checked={autoDescribeAndPublish}
                                    onCheckedChange={setAutoDescribeAndPublish}
                                />
                                <Label htmlFor="auto-describe" className="text-sm cursor-pointer">
                                    {t('autoDescribeAndPublish')}
                                </Label>
                            </div>
                            <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button size="sm" variant="outline" disabled={isDownloading}>
                                    {isDownloading ? (
                                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                    ) : (
                                        <Download className="h-4 w-4 mr-2" />
                                    )}
                                    {t('downloadAll')}
                                    <ChevronDown className="h-4 w-4 ml-1" />
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                                <DropdownMenuItem onClick={() => handleDownloadAll("both")}>
                                    {t('allFormats')}
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => handleDownloadAll("png")}>
                                    {t('pngOnly')}
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => handleDownloadAll("svg")}>
                                    {t('svgOnly')}
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                        </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {successfulImages.map((task) => (
                            <TaskResultCard 
                                key={task.id} 
                                task={task} 
                                jobId={job.id}
                                autoDescribeAndPublish={autoDescribeAndPublish}
                                jobSourceType={job.source_type}
                            />
                        ))}
                    </div>
                </div>
            )}

            {pendingImages.length > 0 && (
                <div>
                    <h3 className="text-lg font-medium mb-4">
                        {t('inProgressCount', { count: pendingImages.length })}
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
                        {t('cancelledCount', { count: cancelledImages.length })}
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

const TaskResultCard = ({ 
    task, 
    jobId,
    autoDescribeAndPublish = false,
    jobSourceType
}: { 
    task: ImageTask; 
    jobId: number;
    autoDescribeAndPublish?: boolean;
    jobSourceType?: string;
}) => {
    const [isRetrying, setIsRetrying] = useState(false);
    const [isCancelling, setIsCancelling] = useState(false);
    const [showDescriptionDialog, setShowDescriptionDialog] = useState(false);
    const [showImageDetailDialog, setShowImageDetailDialog] = useState(false);
    const [imageDetailDialogTab, setImageDetailDialogTab] = useState<"view" | "edit" | "ai">("view");
    const queryClient = useQueryClient();
    const publishImage = usePublishImage();
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
    
    // Check if task can be published (must be SUCCESS)
    const canPublish = task.status === JobStatus.SUCCESS;
    const isPublished = task.is_published || false;
    
    // Auto-describe and publish hook
    const { isProcessing: isAutoProcessing, descriptionTask, descriptionProgress } = useAutoDescribeAndPublish(
        task,
        autoDescribeAndPublish && canPublish && !isPublished,
        jobSourceType,
        jobId
    );
    
    // Check if image already has AI description (has user_description)
    const hasAIDescription = !!(task.user_description && task.user_description.trim());
    
    // Convert ImageTask to ImageTask format for AIDescriptionDialog
    const imageTaskForDialog = canPublish ? {
        id: task.id,
        job: jobId,
        algorithm_key: task.algorithm_key,
        algorithm_version: "1.0",
        params: {},
        output_format: "both" as const,
        status: "SUCCESS" as const,
        progress: 100,
        artifact_png_url: pngUrl || null,
        artifact_svg_url: svgUrl || null,
        chart_data: task.chart_data || null,
        error_code: null,
        error_message: null,
        trace_id: null,
        title: task.title || null,
        user_description: task.user_description || null,
        group: null,
        tags: [],
        is_published: isPublished,
        published_at: task.published_at || null,
        created_at: task.created_at,
        updated_at: task.updated_at,
    } : null;
    
    // Handle describe button click - check if already has AI description
    const handleDescribeClick = () => {
        if (hasAIDescription) {
            // If already has description, open ImageDetailDialog in edit tab
            setImageDetailDialogTab("edit");
            setShowImageDetailDialog(true);
        } else {
            // If no description, open AIDescriptionDialog
            setShowDescriptionDialog(true);
        }
    };
    
    // Handle view button click
    const handleViewClick = () => {
        setImageDetailDialogTab("view");
        setShowImageDetailDialog(true);
    };
    
    // Handle edit button click
    const handleEditClick = () => {
        setImageDetailDialogTab("edit");
        setShowImageDetailDialog(true);
    };
    
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
    
    const handlePublish = async () => {
        if (!canPublish || publishImage.isPending) return;
        
        try {
            await publishImage.mutateAsync({
                imageId: task.id,
                publish: !isPublished,
            });
            
            // Invalidate job queries to refresh the task status
            await queryClient.invalidateQueries({ 
                queryKey: ["job", jobId],
                refetchType: "all"
            });
        } catch (error) {
            // Error handled by hook (toast)
        }
    };

    return (
        <>
            <Card className="overflow-hidden">
            <CardContent className="p-0">
                {task.status === JobStatus.SUCCESS && hasImages ? (
                    <div className="relative">
                        {isAutoProcessing && (
                            <div className="absolute top-2 left-2 z-20 bg-primary/90 text-primary-foreground px-3 py-1.5 rounded-md text-xs font-medium flex items-center gap-2 shadow-lg">
                                <Sparkles className="h-3 w-3 animate-pulse" />
                                {t('generatingDescription')}
                            </div>
                        )}
                        {descriptionTask && descriptionTask.status === "RUNNING" && (
                            <div className="absolute top-2 right-2 z-20 bg-background/95 border px-3 py-1.5 rounded-md text-xs">
                                <div className="flex items-center gap-2">
                                    <Loader2 className="h-3 w-3 animate-spin" />
                                    <span>{descriptionProgress}%</span>
                                </div>
                                <Progress value={descriptionProgress} className="h-1 mt-1 w-24" />
                            </div>
                        )}
                        <ImageCard
                            title={formatAlgorithmKey(task.algorithm_key)}
                            imageUrl={pngUrl || undefined}
                            svgUrl={svgUrl || undefined}
                            status={task.status}
                            subtitle={task.title || undefined}
                            variant="detailed"
                            showDownload={true}
                            createdBy={task.created_by}
                            createdByUsername={task.created_by_username}
                            createdByEmail={task.created_by_email}
                            className="border-0 shadow-none rounded-none"
                            onView={handleViewClick}
                            onEdit={handleEditClick}
                            onGenerateDescription={handleDescribeClick}
                        />
                    </div>
                ) : task.status === JobStatus.RUNNING || task.status === JobStatus.PENDING ? (
                    <div className="h-[300px] flex items-center justify-center p-6 text-center text-muted-foreground flex-col gap-2">
                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                        <p>{t('generatingImage')}</p>
                        <p className="text-xs">{t('progress')}: {task.progress}%</p>
                        {(task.progress === 0 && canRetry) && (
                            <p className="text-xs text-amber-500 mt-2">
                                {t('taskMayBeStuck')}
                            </p>
                        )}
                    </div>
                ) : task.status === JobStatus.CANCELLED ? (
                    <div className="h-[300px] flex items-center justify-center p-6 text-center text-muted-foreground flex-col gap-2">
                        <p className="font-medium">{t('generationCancelled')}</p>
                        {canRetry && (
                            <p className="text-xs text-muted-foreground">
                                {t('canRetryTask')}
                            </p>
                        )}
                    </div>
                ) : (
                    <div className="h-[300px] flex items-center justify-center p-6 text-center text-muted-foreground flex-col gap-2">
                        <p className="font-medium">{t('generationFailed')}</p>
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
                    {t('taskId')}: {task.id}
                </div>
                <div className="flex gap-2 flex-wrap">
                    {canPublish && (
                        <>
                            <Button
                                size="sm"
                                variant="outline"
                                onClick={handleViewClick}
                                className="gap-2"
                                title={t('viewImageTooltip')}
                            >
                                <Eye className="h-3 w-3" />
                                {t('viewImage')}
                            </Button>
                            <Button
                                size="sm"
                                variant="outline"
                                onClick={handleEditClick}
                                className="gap-2"
                                title={t('editMetadataTooltip')}
                            >
                                <Edit className="h-3 w-3" />
                                {t('editMetadata')}
                            </Button>
                            <Button
                                size="sm"
                                variant="outline"
                                onClick={handleDescribeClick}
                                disabled={isAutoProcessing}
                                className="gap-2"
                                title={hasAIDescription ? t('editDescriptionTooltip') : t('describeWithAITooltip')}
                            >
                                <Sparkles className="h-3 w-3" />
                                {hasAIDescription ? t('editDescription') : t('describeWithAI')}
                            </Button>
                            <Button
                                size="sm"
                                variant={isPublished ? "default" : "outline"}
                                onClick={handlePublish}
                                disabled={publishImage.isPending || isAutoProcessing}
                                className="gap-2"
                                title={isPublished ? t('inLibraryTooltip') : t('saveToLibraryTooltip')}
                            >
                                {publishImage.isPending ? (
                                    <>
                                        <Loader2 className="h-3 w-3 animate-spin" />
                                        {isPublished ? t('unpublishing') : t('publishing')}
                                    </>
                                ) : isPublished ? (
                                    <>
                                        <BookmarkCheck className="h-3 w-3" />
                                        {t('inLibrary')}
                                    </>
                                ) : (
                                    <>
                                        <BookmarkPlus className="h-3 w-3" />
                                        {t('saveToLibrary')}
                                    </>
                                )}
                            </Button>
                        </>
                    )}
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
                                    {t('cancelling')}
                                </>
                            ) : (
                                <>
                                    <X className="h-3 w-3" />
                                    {tCommon('cancel')}
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
                                    {t('retrying')}
                                </>
                            ) : (
                                <>
                                    <RotateCcw className="h-3 w-3" />
                                    {t('retry')}
                                </>
                            )}
                        </Button>
                    )}
                </div>
            </CardFooter>
        </Card>
        {imageTaskForDialog && (
            <>
                <AIDescriptionDialog
                    image={imageTaskForDialog}
                    open={showDescriptionDialog}
                    onOpenChange={setShowDescriptionDialog}
                    onDescriptionSaved={() => {
                        queryClient.invalidateQueries({ queryKey: ["job", jobId] });
                    }}
                />
                <ImageDetailDialog
                    imageId={task.id}
                    open={showImageDetailDialog}
                    onOpenChange={setShowImageDetailDialog}
                    initialTab={imageDetailDialogTab}
                    autoPublishOnSave={true}
                    onSave={() => {
                        // Invalidate job queries to refresh the task status
                        queryClient.invalidateQueries({ queryKey: ["job", jobId] });
                    }}
                />
            </>
        )}
        </>
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
