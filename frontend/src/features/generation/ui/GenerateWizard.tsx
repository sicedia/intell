"use client";

import { useTranslations } from "next-intl";
import { useWizardStore } from "../stores/useWizardStore";
import { SourceStep } from "./SourceStep";
import { VisualizationStep } from "./VisualizationStep";
import { RunStep } from "./RunStep";
import { Stepper } from "@/shared/ui/Stepper";
import { Button } from "@/shared/components/ui/button";
import { RefreshCw } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { cn } from "@/shared/lib/utils";

export const GenerateWizard = () => {
  const t = useTranslations('generate.wizard');
  const tSteps = useTranslations('generate.wizard.steps');
  const { currentStep, setStep, reset, isJobCompleted, jobId } = useWizardStore();
  const queryClient = useQueryClient();

  const STEPS = [
    { id: "source", label: tSteps('source.label'), description: tSteps('source.description') },
    { id: "visualization", label: tSteps('visualization.label'), description: tSteps('visualization.description') },
    { id: "run", label: tSteps('run.label'), description: tSteps('run.description') },
  ];

  const handleNext = () => setStep(currentStep + 1);
  const handleBack = () => setStep(currentStep - 1);
  const handleReset = () => {
    // Clear job-related queries from cache
    if (jobId) {
      queryClient.removeQueries({ queryKey: ["job", jobId] });
      queryClient.removeQueries({ queryKey: ["job", jobId, "events"] });
    }
    // Reset wizard state
    reset();
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      {/* Header with Reset button */}
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">{t('title')}</h1>
        <Button 
          onClick={handleReset} 
          variant="outline" 
          size="sm"
          title={t('resetTooltip')}
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          {t('reset')}
        </Button>
      </div>

      {/* Stepper */}
      <div className="mb-8">
        <Stepper
          steps={STEPS}
          currentStep={currentStep}
          orientation="horizontal"
          allCompleted={isJobCompleted}
        />
      </div>

      {/* Step Content with Transition */}
      <div className="relative min-h-[400px]">
        <div
          key={currentStep}
          className={cn(
            "animate-in fade-in slide-in-from-right-4 duration-300",
            currentStep === 0 && "slide-in-from-left-4"
          )}
        >
          {currentStep === 0 && <SourceStep onNext={handleNext} />}
          {currentStep === 1 && (
            <VisualizationStep onNext={handleNext} onBack={handleBack} />
          )}
          {currentStep === 2 && <RunStep onReset={handleReset} />}
        </div>
      </div>
    </div>
  );
};
