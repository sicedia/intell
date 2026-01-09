import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { AlgorithmConfig } from "../constants/algorithms";

interface WizardState {
    currentStep: number;
    sourceType: "espacenet_excel" | "lens_query";
    sourceFile: File | null; // Not persisted - File objects are not serializable
    selectedAlgorithms: AlgorithmConfig[];
    jobId: number | null;

    // Actions
    setStep: (step: number) => void;
    setSourceType: (type: "espacenet_excel" | "lens_query") => void;
    setSourceFile: (file: File | null) => void;
    setSelectedAlgorithms: (algorithms: AlgorithmConfig[]) => void;
    setJobId: (id: number | null) => void;
    reset: () => void;
}

// Persisted state (excludes sourceFile as it's not serializable)
type PersistedWizardState = Omit<WizardState, "sourceFile">;

export const useWizardStore = create<WizardState>()(
    persist(
        (set) => ({
            currentStep: 0,
            sourceType: "espacenet_excel",
            sourceFile: null,
            selectedAlgorithms: [],
            jobId: null,

            setStep: (step) => set({ currentStep: step }),
            setSourceType: (type) => set({ sourceType: type }),
            setSourceFile: (file) => set({ sourceFile: file }),
            setSelectedAlgorithms: (algorithms) => set({ selectedAlgorithms: algorithms }),
            setJobId: (id) => set({ jobId: id }),
            reset: () =>
                set({
                    currentStep: 0,
                    sourceType: "espacenet_excel",
                    sourceFile: null,
                    selectedAlgorithms: [],
                    jobId: null,
                }),
        }),
        {
            name: "wizard-store",
            storage: createJSONStorage(() => sessionStorage),
            // Only persist serializable fields
            partialize: (state): PersistedWizardState => ({
                currentStep: state.currentStep,
                sourceType: state.sourceType,
                selectedAlgorithms: state.selectedAlgorithms,
                jobId: state.jobId,
                setStep: state.setStep,
                setSourceType: state.setSourceType,
                setSourceFile: state.setSourceFile,
                setSelectedAlgorithms: state.setSelectedAlgorithms,
                setJobId: state.setJobId,
                reset: state.reset,
            }),
        }
    )
);
