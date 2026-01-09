"use client";

import { useWizardStore } from "../stores/useWizardStore";
import { SourceStep } from "./SourceStep";
import { VisualizationStep } from "./VisualizationStep";
import { RunStep } from "./RunStep";
import { Stepper } from "@/shared/ui/Stepper";
import { cn } from "@/shared/lib/utils";

const STEPS = [
  { id: "source", label: "Data Source", description: "Upload your data" },
  { id: "visualization", label: "Visualizations", description: "Choose algorithms" },
  { id: "run", label: "Generate", description: "Run and monitor" },
];

export const GenerateWizard = () => {
  const { currentStep, setStep, reset } = useWizardStore();

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
