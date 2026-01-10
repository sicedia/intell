import { useWizardStore } from "../stores/useWizardStore";
import { ALGORITHMS, AlgorithmConfig } from "../constants/algorithms";
import {
    COLOR_PALETTE_OPTIONS,
    FONT_SIZE_OPTIONS,
    ColorPalette,
    FontSize,
} from "../constants/visualization";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/shared/components/ui/card";
import { Checkbox } from "@/shared/components/ui/checkbox";
import { Label } from "@/shared/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/shared/components/ui/radio-group";
import { cn } from "@/shared/lib/utils";

interface VisualizationStepProps {
    onNext: () => void;
    onBack: () => void;
}

export const VisualizationStep = ({ onNext, onBack }: VisualizationStepProps) => {
    const {
        selectedAlgorithms,
        setSelectedAlgorithms,
        visualizationConfig,
        setVisualizationConfig,
    } = useWizardStore();

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

    const handlePaletteChange = (value: string) => {
        setVisualizationConfig({
            ...visualizationConfig,
            color_palette: value as ColorPalette,
        });
    };

    const handleFontSizeChange = (value: string) => {
        setVisualizationConfig({
            ...visualizationConfig,
            font_size: value as FontSize,
        });
    };

    return (
        <div className="space-y-6">
            {/* Algorithm Selection */}
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

            {/* Visualization Options */}
            <Card>
                <CardHeader>
                    <CardTitle>Chart Style</CardTitle>
                    <CardDescription>
                        Customize the appearance of all generated charts.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    {/* Color Palette */}
                    <div className="space-y-3">
                        <Label className="text-sm font-medium">Color Palette</Label>
                        <RadioGroup
                            value={visualizationConfig.color_palette}
                            onValueChange={handlePaletteChange}
                            className="grid grid-cols-2 md:grid-cols-3 gap-3"
                        >
                            {COLOR_PALETTE_OPTIONS.map((palette) => (
                                <Label
                                    key={palette.value}
                                    htmlFor={`palette-${palette.value}`}
                                    className={cn(
                                        "flex flex-col items-start gap-2 rounded-lg border p-3 cursor-pointer transition-all hover:bg-accent",
                                        visualizationConfig.color_palette === palette.value &&
                                            "border-primary bg-primary/5"
                                    )}
                                >
                                    <div className="flex items-center gap-2">
                                        <RadioGroupItem
                                            value={palette.value}
                                            id={`palette-${palette.value}`}
                                        />
                                        <span className="font-medium text-sm">{palette.label}</span>
                                    </div>
                                    <p className="text-xs text-muted-foreground">
                                        {palette.description}
                                    </p>
                                    <div className="flex gap-1">
                                        {palette.colors.map((color, idx) => (
                                            <div
                                                key={idx}
                                                className="w-5 h-5 rounded-full border border-border"
                                                style={{ backgroundColor: color }}
                                            />
                                        ))}
                                    </div>
                                </Label>
                            ))}
                        </RadioGroup>
                    </div>

                    {/* Font Size */}
                    <div className="space-y-3">
                        <Label className="text-sm font-medium">Font Size</Label>
                        <RadioGroup
                            value={visualizationConfig.font_size}
                            onValueChange={handleFontSizeChange}
                            className="flex flex-wrap gap-3"
                        >
                            {FONT_SIZE_OPTIONS.map((size) => (
                                <Label
                                    key={size.value}
                                    htmlFor={`size-${size.value}`}
                                    className={cn(
                                        "flex items-center gap-2 rounded-lg border px-4 py-2 cursor-pointer transition-all hover:bg-accent",
                                        visualizationConfig.font_size === size.value &&
                                            "border-primary bg-primary/5"
                                    )}
                                >
                                    <RadioGroupItem
                                        value={size.value}
                                        id={`size-${size.value}`}
                                    />
                                    <div>
                                        <span className="font-medium text-sm">{size.label}</span>
                                        <p className="text-xs text-muted-foreground">
                                            {size.description}
                                        </p>
                                    </div>
                                </Label>
                            ))}
                        </RadioGroup>
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
