import { useTranslations } from "next-intl";
import { PageHeader } from "@/shared/ui/PageHeader";
import { EmptyState } from "@/shared/ui/EmptyState";
import { Wrench } from "lucide-react";

export default function ReportsPage() {
  const t = useTranslations('reports');

  return (
    <div className="space-y-6">
      <PageHeader
        title={t('title')}
        subtitle={t('description')}
      />

      <EmptyState
        title="Under Construction"
        description="This feature is currently being developed. Please check back soon."
        icon={<Wrench className="h-12 w-12 text-muted-foreground" />}
      />
    </div>
  );
}
