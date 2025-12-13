
import { getTranslations } from "next-intl/server";
import { PageHeader } from "@/shared/ui/PageHeader";
import { GenerateWizard } from "@/features/generate/GenerateWizard";

export default async function GeneratePage() {
  const t = await getTranslations("generate");

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("title") || "New Generation"}
        subtitle={t("subtitle") || "Configure and run a new analysis job."}
      />
      <GenerateWizard />
    </div>
  );
}
