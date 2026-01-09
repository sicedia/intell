"use client";

import { useEffect } from "react";
import { Button } from "@/shared/components/ui/button";
import { AlertCircle } from "lucide-react";

interface ErrorProps {
    error: Error & { digest?: string };
    reset: () => void;
}

export default function Error({ error, reset }: ErrorProps) {
    useEffect(() => {
        // Log error to error reporting service
        console.error("Application error:", error);
    }, [error]);

    return (
        <div className="container mx-auto py-8 flex items-center justify-center min-h-[60vh]">
            <div className="text-center space-y-4 max-w-md">
                <AlertCircle className="h-12 w-12 text-destructive mx-auto" />
                <h2 className="text-2xl font-bold">Something went wrong!</h2>
                <p className="text-muted-foreground">
                    {error.message || "An unexpected error occurred. Please try again."}
                </p>
                {error.digest && (
                    <p className="text-xs text-muted-foreground font-mono">
                        Error ID: {error.digest}
                    </p>
                )}
                <div className="flex gap-2 justify-center">
                    <Button onClick={reset}>Try again</Button>
                    <Button variant="outline" onClick={() => window.location.href = "/"}>
                        Go home
                    </Button>
                </div>
            </div>
        </div>
    );
}
