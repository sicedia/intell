import { create } from "zustand";
import { AlgorithmConfig } from "../constants/algorithms";

interface WizardState {
    currentStep: number;
    sourceType: "espacenet_excel" | "lens_query";
    sourceFile: File | null;
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

export const useWizardStore = create<WizardState>((set) => ({
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
}));
