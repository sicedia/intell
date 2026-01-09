import { Skeleton } from "@/shared/components/ui/skeleton";

export default function GenerateLoading() {
    return (
        <div className="container mx-auto py-8 space-y-6">
            <div className="space-y-2">
                <Skeleton className="h-10 w-64" />
                <Skeleton className="h-4 w-96" />
            </div>
            <div className="max-w-4xl mx-auto space-y-8">
                {/* Step indicator skeleton */}
                <div className="flex items-center justify-between mb-8">
                    {[0, 1, 2].map((step) => (
                        <Skeleton key={step} className="flex-1 h-2 rounded-full mx-1" />
                    ))}
                </div>
                {/* Content skeleton */}
                <Skeleton className="h-[400px] w-full rounded-lg" />
            </div>
        </div>
    );
}
