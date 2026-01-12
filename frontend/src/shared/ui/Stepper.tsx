import React from 'react';
import { cn } from "@/shared/lib/utils";
import { Check } from "lucide-react";

export interface Step {
  id: string;
  label: string;
  description?: string;
}

export interface StepperProps {
  steps: Step[];
  currentStep: number;
  className?: string;
  orientation?: 'horizontal' | 'vertical';
  allCompleted?: boolean;
}

export function Stepper({ steps, currentStep, className, orientation = 'horizontal', allCompleted = false }: StepperProps) {
  if (orientation === 'vertical') {
    return (
      <div className={cn("flex flex-col gap-4", className)}>
        {steps.map((step, index) => {
          const isActive = index === currentStep && !allCompleted;
          const isCompleted = index < currentStep || allCompleted;
          const isUpcoming = index > currentStep && !allCompleted;

          return (
            <div key={step.id} className="flex gap-4">
              <div className="flex flex-col items-center">
                <div
                  className={cn(
                    "h-10 w-10 rounded-full flex items-center justify-center border-2 font-semibold text-sm transition-all",
                    {
                      "bg-primary text-primary-foreground border-primary": isActive,
                      "bg-success text-success-foreground border-success": isCompleted,
                      "bg-muted text-muted-foreground border-muted": isUpcoming,
                    }
                  )}
                >
                  {isCompleted ? (
                    <Check className="h-5 w-5" />
                  ) : (
                    <span>{index + 1}</span>
                  )}
                </div>
                {index < steps.length - 1 && (
                  <div
                    className={cn(
                      "w-0.5 h-full min-h-8 mt-2 transition-colors",
                      isCompleted ? "bg-success" : "bg-muted"
                    )}
                  />
                )}
              </div>
              <div className="flex-1 pb-8">
                <div
                  className={cn(
                    "font-medium transition-colors",
                    isActive && "text-primary",
                    isCompleted && "text-foreground",
                    isUpcoming && "text-muted-foreground"
                  )}
                >
                  {step.label}
                </div>
                {step.description && (
                  <div className="text-sm text-muted-foreground mt-1">
                    {step.description}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  return (
    <div className={cn("w-full", className)}>
      <div className="flex items-center justify-between">
        {steps.map((step, index) => {
          const isActive = index === currentStep && !allCompleted;
          const isCompleted = index < currentStep || allCompleted;
          const isUpcoming = index > currentStep && !allCompleted;

          return (
            <React.Fragment key={step.id}>
              <div className="flex flex-col items-center flex-1">
                <div className="flex items-center w-full">
                  <div className="flex flex-col items-center flex-1">
                    <div
                      className={cn(
                        "h-10 w-10 rounded-full flex items-center justify-center border-2 font-semibold text-sm transition-all relative z-10",
                        {
                          "bg-primary text-primary-foreground border-primary shadow-md": isActive,
                          "bg-success text-success-foreground border-success": isCompleted,
                          "bg-muted text-muted-foreground border-muted": isUpcoming,
                        }
                      )}
                    >
                      {isCompleted ? (
                        <Check className="h-5 w-5" />
                      ) : (
                        <span>{index + 1}</span>
                      )}
                    </div>
                    <div className="mt-2 text-center">
                      <div
                        className={cn(
                          "text-sm font-medium transition-colors",
                          isActive && "text-primary",
                          isCompleted && "text-foreground",
                          isUpcoming && "text-muted-foreground"
                        )}
                      >
                        {step.label}
                      </div>
                      {step.description && (
                        <div className="text-xs text-muted-foreground mt-1 max-w-[120px] mx-auto">
                          {step.description}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
              {index < steps.length - 1 && (
                <div className="flex-1 h-0.5 mx-4 relative -top-5">
                  <div
                    className={cn(
                      "h-full transition-all duration-300",
                      isCompleted ? "bg-success" : "bg-muted"
                    )}
                  />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
