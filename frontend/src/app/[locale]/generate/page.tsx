"use client";

import { useTranslations } from "next-intl";
import { GenerateWizard } from "@/features/generation/ui/GenerateWizard";

export default function GeneratePage() {
  const t = useTranslations('generate');

  return (
    <div className="container mx-auto py-8">
      <div className="mb-8 text-center sm:text-left">
        <h1 className="text-3xl font-bold tracking-tight">{t('title')}</h1>
        <p className="text-muted-foreground mt-2">
          {t('description')}
        </p>
      </div>

      <GenerateWizard />
    </div>
  );
}
