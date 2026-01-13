"use client";

import { useTranslations } from "next-intl";
import { useWizardStore } from "../stores/useWizardStore";
import { SourceStep } from "./SourceStep";
import { VisualizationStep } from "./VisualizationStep";
import { RunStep } from "./RunStep";
import { Stepper } from "@/shared/ui/Stepper";
import { cn } from "@/shared/lib/utils";

export const GenerateWizard = () => {
  const t = useTranslations('generate.wizard.steps');
  const { currentStep, setStep, reset, isJobCompleted } = useWizardStore();

  const STEPS = [
    { id: "source", label: t('source.label'), description: t('source.description') },
    { id: "visualization", label: t('visualization.label'), description: t('visualization.description') },
    { id: "run", label: t('run.label'), description: t('run.description') },
  ];

  const handleNext = () => setStep(currentStep + 1);
  const handleBack = () => setStep(currentStep - 1);
  const handleReset = () => reset();

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
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
