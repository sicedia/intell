"use client";

import { GenerateWizard } from "@/features/generation/ui/GenerateWizard";

export default function GeneratePage() {
  return (
    <div className="container mx-auto py-8">
      <div className="mb-8 text-center sm:text-left">
        <h1 className="text-3xl font-bold tracking-tight">Generate Visualizations</h1>
        <p className="text-muted-foreground mt-2">
          Upload patent data and choose algorithms to generate visual insights.
        </p>
      </div>

      <GenerateWizard />
    </div>
  );
}
