"use client"

import React, { useState } from 'react';
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from "@/shared/components/ui/card";
import { ProgressPanel } from "@/shared/ui/ProgressPanel";
import { EventTimeline, TimelineEvent } from "@/shared/ui/EventTimeline";
import { StateBlock } from "@/shared/ui/StateBlock";
import { features } from "@/shared/lib/flags";
import { MOCK_EVENTS } from "@/shared/mock/mockJob";
import { EventLogPayload } from "@/features/generation/constants/job";
import { CheckCircle2, FileSpreadsheet, Database } from "lucide-react";
import { cn } from "@/shared/lib/utils";

const STEPS = [
    { number: 1, title: "Source" },
    { number: 2, title: "Visualizations" },
    { number: 3, title: "Execute" },
];

export function GenerateWizard() {
    const [step, setStep] = useState(1);
    const [source, setSource] = useState<'lens' | 'excel' | null>(null);
    const [selectedAlgos, setSelectedAlgos] = useState<string[]>([]);
    const [isExecuting, setIsExecuting] = useState(false);
    const [events, setEvents] = useState<TimelineEvent[]>([]);
    const [progress, setProgress] = useState(0);

    const mockExecution = () => {
        setIsExecuting(true);
        setEvents([]);
        setProgress(0);

        if (features.useMocks) {
            let currentProgress = 0;
            let eventIndex = 0;

            const interval = setInterval(() => {
                currentProgress += 10;
                setProgress(Math.min(currentProgress, 100));

                // Add mock event occasionally
                if (currentProgress % 30 === 0 && eventIndex < MOCK_EVENTS.length) {
                    const mockEvent: EventLogPayload = MOCK_EVENTS[eventIndex];
                    setEvents(prev => [...prev, {
                        id: String(Date.now()),
                        timestamp: new Date().toISOString(),
                        level: mockEvent.level,
                        message: mockEvent.message,
                        progress: currentProgress
                    }]);
                    eventIndex++;
                }

                if (currentProgress >= 100) {
                    clearInterval(interval);
                    setIsExecuting(false);
                }
            }, 800);
        }
    };

    const handleNext = () => {
        if (step === 3) {
            mockExecution();
        } else {
            setStep(prev => prev + 1);
        }
    };

    const handleBack = () => {
        if (step > 1 && !isExecuting) setStep(prev => prev - 1);
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            {/* Steps Indicator */}
            <div className="flex items-center justify-center space-x-4">
                {STEPS.map((s) => (
                    <div key={s.number} className="flex items-center gap-2">
                        <div className={cn(
                            "flex items-center justify-center w-8 h-8 rounded-full border text-sm font-medium",
                            step >= s.number ? "bg-primary text-primary-foreground border-primary" : "text-muted-foreground border-muted-foreground"
                        )}>
                            {step > s.number ? <CheckCircle2 className="w-5 h-5" /> : s.number}
                        </div>
                        <span className={cn("text-sm", step >= s.number ? "font-medium text-foreground" : "text-muted-foreground")}>{s.title}</span>
                        {s.number < STEPS.length && <div className="w-12 h-px bg-border" />}
                    </div>
                ))}
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>{STEPS[step - 1].title}</CardTitle>
                    <CardDescription>Step {step} of {STEPS.length}</CardDescription>
                </CardHeader>
                <CardContent className="min-h-[300px]">
                    {step === 1 && (
                        <div className="grid grid-cols-2 gap-4">
                            <Button
                                variant={source === 'lens' ? 'default' : 'outline'}
                                className="h-32 flex flex-col gap-2"
                                onClick={() => setSource('lens')}
                            >
                                <Database className="w-8 h-8" />
                                <span>Use Lens Integration</span>
                            </Button>
                            <Button
                                variant={source === 'excel' ? 'default' : 'outline'}
                                className="h-32 flex flex-col gap-2"
                                onClick={() => setSource('excel')}
                            >
                                <FileSpreadsheet className="w-8 h-8" />
                                <span>Upload Excel</span>
                            </Button>
                        </div>
                    )}

                    {step === 2 && (
                        <div className="space-y-4">
                            <p className="text-sm text-muted-foreground">Select algorithms to run:</p>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                {['Clustering (K-Means)', 'Regression (Linear)', 'Classification (Random Forest)', 'Anomaly Detection'].map(algo => (
                                    <div
                                        key={algo}
                                        className={cn(
                                            "p-4 rounded-lg border cursor-pointer transition-colors",
                                            selectedAlgos.includes(algo) ? "border-primary bg-primary/5" : "hover:bg-muted"
                                        )}
                                        onClick={() => {
                                            if (selectedAlgos.includes(algo)) setSelectedAlgos(prev => prev.filter(a => a !== algo));
                                            else setSelectedAlgos(prev => [...prev, algo]);
                                        }}
                                    >
                                        <div className="flex items-center gap-2">
                                            <div className={cn("w-4 h-4 rounded border flex items-center justify-center", selectedAlgos.includes(algo) && "bg-primary border-primary")}>
                                                {selectedAlgos.includes(algo) && <CheckCircle2 className="w-3 h-3 text-primary-foreground" />}
                                            </div>
                                            <span className="text-sm font-medium">{algo}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {step === 3 && (
                        <div className="space-y-6">
                            {!isExecuting && progress === 0 ? (
                                <StateBlock
                                    title="Ready to Execute"
                                    description={`Source: ${source?.toUpperCase() || 'None'} | Algorithms: ${selectedAlgos.length}`}
                                    icon={<CheckCircle2 className="w-12 h-12 text-green-500" />}
                                />
                            ) : (
                                <div className="space-y-6">
                                    <ProgressPanel progress={progress} step="Processing data..." className="w-full" />
                                    <div className="border rounded-lg p-4 bg-muted/20 max-h-[300px] overflow-y-auto">
                                        <h4 className="text-sm font-medium mb-2">Event Log</h4>
                                        <EventTimeline events={events} />
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </CardContent>
                <CardFooter className="flex justify-between">
                    <Button variant="outline" onClick={handleBack} disabled={step === 1 || isExecuting}>Previous</Button>
                    <Button
                        onClick={handleNext}
                        disabled={
                            (step === 1 && !source) ||
                            (step === 2 && selectedAlgos.length === 0) ||
                            (step === 3 && (isExecuting || progress === 100))
                        }
                    >
                        {step === 3 ? (isExecuting ? 'Running...' : (progress === 100 ? 'Completed' : 'Execute Job')) : 'Next'}
                    </Button>
                </CardFooter>
            </Card>
        </div>
    );
}
