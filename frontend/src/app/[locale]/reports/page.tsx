import { PageHeader } from "@/shared/ui/PageHeader";
import { EmptyState } from "@/shared/ui/EmptyState";
import { Wrench } from "lucide-react";

export default function ReportsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Reports"
        subtitle="Generate and manage analytics reports"
      />

      <EmptyState
        title="Under Construction"
        description="This feature is currently being developed. Please check back soon."
        icon={<Wrench className="h-12 w-12 text-muted-foreground" />}
      />
    </div>
  );
}
