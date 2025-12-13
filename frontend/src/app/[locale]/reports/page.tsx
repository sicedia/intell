
import { PageHeader } from "@/shared/ui/PageHeader";
import { StateBlock } from "@/shared/ui/StateBlock";
import { Construction } from "lucide-react";

export default function ReportsPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Reports" />
      <StateBlock
        variant="default"
        title="Report Generator"
        description="This feature is not yet available."
        icon={<Construction className="w-12 h-12 text-muted-foreground" />}
      />
    </div>
  );
}
