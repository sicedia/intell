import Link from "next/link";
import { Button } from "@/shared/components/ui/button";
import { FileQuestion } from "lucide-react";

export default function NotFound() {
    return (
        <div className="container mx-auto py-8 flex items-center justify-center min-h-[60vh]">
            <div className="text-center space-y-4 max-w-md">
                <FileQuestion className="h-12 w-12 text-muted-foreground mx-auto" />
                <h2 className="text-2xl font-bold">Page not found</h2>
                <p className="text-muted-foreground">
                    The page you&apos;re looking for doesn&apos;t exist or has been moved.
                </p>
                <Button asChild>
                    <Link href="/dashboard">Go to Dashboard</Link>
                </Button>
            </div>
        </div>
    );
}
