import React from 'react';
import { cn } from "@/shared/lib/utils";
import { Label } from "@/shared/components/ui/label";

export interface FormFieldProps {
  label?: string;
  hint?: string;
  error?: string;
  required?: boolean;
  className?: string;
  children: React.ReactNode;
  id?: string;
  htmlFor?: string;
}

export function FormField({
  label,
  hint,
  error,
  required,
  className,
  children,
  id,
  htmlFor,
}: FormFieldProps) {
  const fieldId = id || (typeof children === 'object' && children && 'props' in children && (children.props as { id?: string })?.id) || undefined;
  const labelFor = htmlFor || fieldId;

  return (
    <div className={cn("space-y-2", className)}>
      {label && (
        <Label htmlFor={labelFor} className={cn(error && "text-destructive")}>
          {label}
          {required && <span className="text-destructive ml-1">*</span>}
        </Label>
      )}
      {children}
      {hint && !error && (
        <p className="text-sm text-muted-foreground">{hint}</p>
      )}
      {error && (
        <p className="text-sm text-destructive font-medium">{error}</p>
      )}
    </div>
  );
}
