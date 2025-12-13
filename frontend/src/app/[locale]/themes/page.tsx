
import { PageHeader } from "@/shared/ui/PageHeader";
import { StateBlock } from "@/shared/ui/StateBlock";
import { Construction } from "lucide-react";

export default function ThemesPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Themes & Styling" />
      <StateBlock
        variant="default"
        title="Under Construction"
        description="Theme management is coming soon."
        icon={<Construction className="w-12 h-12 text-muted-foreground" />}
      />
    </div>
  );
}
