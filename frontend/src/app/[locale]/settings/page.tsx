
import { PageHeader } from "@/shared/ui/PageHeader";
import { StateBlock } from "@/shared/ui/StateBlock";
import { Construction } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Settings" />
      <StateBlock
        variant="default"
        title="Configuration"
        description="System settings will appear here."
        icon={<Construction className="w-12 h-12 text-muted-foreground" />}
      />
    </div>
  );
}
