import { useWizardStore } from "../stores/useWizardStore";
import { ALGORITHMS, AlgorithmConfig } from "../constants/algorithms";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/shared/components/ui/card";
import { Checkbox } from "@/shared/components/ui/checkbox";
import { cn } from "@/shared/lib/utils";

interface VisualizationStepProps {
    onNext: () => void;
    onBack: () => void;
}

export const VisualizationStep = ({ onNext, onBack }: VisualizationStepProps) => {
    const { selectedAlgorithms, setSelectedAlgorithms } = useWizardStore();

    const toggleAlgorithm = (algoKey: string) => {
        const exists = selectedAlgorithms.find((a) => a.algorithm_key === algoKey);

        if (exists) {
            setSelectedAlgorithms(selectedAlgorithms.filter((a) => a.algorithm_key !== algoKey));
        } else {
            const algoDef = ALGORITHMS.find((a) => a.key === algoKey);
            if (!algoDef) return;

            const newConfig: AlgorithmConfig = {
                algorithm_key: algoDef.key,
                algorithm_version: "1.0",
                params: { ...algoDef.defaultParams },
                output_format: "both",
            };
            setSelectedAlgorithms([...selectedAlgorithms, newConfig]);
        }
    };

    const isSelected = (key: string) => selectedAlgorithms.some((a) => a.algorithm_key === key);

    return (
        <div className="space-y-6">
            <Card>
                <CardHeader>
                    <CardTitle>Select Visualizations</CardTitle>
                    <CardDescription>Choose the analyses you want to perform on the data.</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {ALGORITHMS.map((algo) => (
                            <Card
                                key={algo.key}
                                className={cn(
                                    "cursor-pointer transition-all hover:shadow-md",
                                    isSelected(algo.key) && "border-primary bg-primary/5 shadow-sm"
                                )}
                                onClick={() => toggleAlgorithm(algo.key)}
                            >
                                <CardContent className="flex items-start space-x-3 p-4">
                                    <Checkbox
                                        checked={isSelected(algo.key)}
                                        onCheckedChange={() => toggleAlgorithm(algo.key)}
                                        className="mt-1"
                                    />
                                    <div className="space-y-1 flex-1">
                                        <h4 className="font-medium leading-none">{algo.label}</h4>
                                        <p className="text-xs text-muted-foreground">
                                            Generate {algo.label.toLowerCase()} chart
                                        </p>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </CardContent>
            </Card>

            <div className="flex justify-between">
                <Button variant="outline" onClick={onBack}>
                    Back
                </Button>
                <Button onClick={onNext} disabled={selectedAlgorithms.length === 0}>
                    Next: Generate
                </Button>
            </div>
        </div>
    );
};
