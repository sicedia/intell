import { useWizardStore } from "../stores/useWizardStore";
import { SourceStep } from "./SourceStep";
import { VisualizationStep } from "./VisualizationStep";
import { RunStep } from "./RunStep";

export const GenerateWizard = () => {
    const { currentStep, setStep, reset } = useWizardStore();

    const handleNext = () => setStep(currentStep + 1);
    const handleBack = () => setStep(currentStep - 1);
    const handleReset = () => reset();

    return (
        <div className="max-w-4xl mx-auto p-6 space-y-8">
            {/* Steps Indicator could go here */}
            <div className="flex items-center justify-between mb-8">
                {[0, 1, 2].map((step) => (
                    <div
                        key={step}
                        className={`flex-1 h-2 rounded-full mx-1 transition-colors ${step <= currentStep ? "bg-primary" : "bg-muted"
                            }`}
                    />
                ))}
            </div>

            <div className="min-h-[400px]">
                {currentStep === 0 && <SourceStep onNext={handleNext} />}
                {currentStep === 1 && <VisualizationStep onNext={handleNext} onBack={handleBack} />}
                {currentStep === 2 && <RunStep onReset={handleReset} />}
            </div>
        </div>
    );
};
