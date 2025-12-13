import { Job, ImageTask, JobStatus } from "../constants/job";
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/shared/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/components/ui/tabs";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import { Download, ExternalLink } from "lucide-react";

// Helper to construct full URL if backend returns relative path
const getFullUrl = (path?: string) => {
    if (!path) return undefined;
    if (path.startsWith("http")) return path;
    // If undefined NEXT_PUBLIC_API_BASE_URL, fallback
    const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
    // If base ends with /api, we might need to be careful. 
    // Typically backend media URLs are root-relative e.g. /media/...
    // We want http://localhost:8000/media/...
    // We can strip /api from base if present to find root, or assume BASE_URL is root of API not server.
    // Let's assume passed env var is server root or close to it.

    // Actually, usually Django returns full absolute URL if configured well, OR /media/ path.
    // We'll safely join.
    const origin = new URL(base).origin;
    return `${origin}${path.startsWith('/') ? '' : '/'}${path}`;
};

export const JobResults = ({ job }: { job: Job }) => {
    if (!job.images || job.images.length === 0) {
        return <div className="text-center text-muted-foreground">No images generated.</div>;
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {job.images.map((task) => (
                <TaskResultCard key={task.id} task={task} />
            ))}
        </div>
    );
};

const TaskResultCard = ({ task }: { task: ImageTask }) => {
    const pngUrl = getFullUrl(task.result_urls.png);
    const svgUrl = getFullUrl(task.result_urls.svg);

    return (
        <Card className="overflow-hidden">
            <CardHeader className="py-4 bg-muted/30">
                <div className="flex justify-between items-center">
                    <CardTitle className="text-base font-medium truncate" title={task.algorithm_key}>
                        {task.algorithm_key}
                    </CardTitle>
                    <StatusBadge status={task.status} />
                </div>
            </CardHeader>
            <CardContent className="p-0">
                {task.status === JobStatus.SUCCESS ? (
                    <Tabs defaultValue={svgUrl ? "svg" : "png"} className="w-full">
                        <div className="p-4 bg-checkered min-h-[300px] flex items-center justify-center bg-gray-50 dark:bg-gray-900 border-b">
                            <TabsContent value="png" className="mt-0 w-full flex justify-center">
                                {pngUrl ? (
                                    <img src={pngUrl} alt="Result" className="max-h-[300px] object-contain" />
                                ) : (
                                    <span className="text-sm text-muted-foreground">No PNG available</span>
                                )}
                            </TabsContent>
                            <TabsContent value="svg" className="mt-0 w-full flex justify-center">
                                {svgUrl ? (
                                    <object data={svgUrl} type="image/svg+xml" className="max-h-[300px] max-w-full">
                                        <img src={svgUrl} alt="Fallback" />
                                    </object>
                                ) : (
                                    <span className="text-sm text-muted-foreground">No SVG available</span>
                                )}
                            </TabsContent>
                        </div>

                        {(pngUrl && svgUrl) && (
                            <TabsList className="w-full rounded-none border-b">
                                <TabsTrigger value="svg" className="flex-1">SVG</TabsTrigger>
                                <TabsTrigger value="png" className="flex-1">PNG</TabsTrigger>
                            </TabsList>
                        )}
                    </Tabs>
                ) : (
                    <div className="h-[300px] flex items-center justify-center p-6 text-center text-muted-foreground flex-col gap-2">
                        <p>Generation Failed</p>
                        {task.error_message && (
                            <p className="text-xs text-red-500 bg-red-50 p-2 rounded">{task.error_message}</p>
                        )}
                    </div>
                )}
            </CardContent>
            <CardFooter className="flex justify-between p-4 bg-muted/10">
                <div className="text-xs text-muted-foreground">
                    ID: {task.id}
                </div>
                <div className="flex gap-2">
                    {pngUrl && (
                        <Button size="sm" variant="outline" asChild>
                            <a href={pngUrl} target="_blank" rel="noopener noreferrer">
                                Open PNG
                            </a>
                        </Button>
                    )}
                    {svgUrl && (
                        <Button size="sm" variant="outline" asChild>
                            <a href={svgUrl} target="_blank" rel="noopener noreferrer">
                                Open SVG
                            </a>
                        </Button>
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
