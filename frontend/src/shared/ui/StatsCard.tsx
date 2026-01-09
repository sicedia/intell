import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { cn } from "@/shared/lib/utils";
import { LucideIcon } from "lucide-react";

export interface StatsCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon?: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
    label?: string;
  };
  className?: string;
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'destructive';
}

export function StatsCard({
  title,
  value,
  description,
  icon: Icon,
  trend,
  className,
  variant = 'default',
}: StatsCardProps) {
  return (
    <Card className={cn(
      "relative overflow-hidden",
      {
        "border-primary/50 bg-primary/5": variant === 'primary',
        "border-success/50 bg-success/5": variant === 'success',
        "border-warning/50 bg-warning/5": variant === 'warning',
        "border-destructive/50 bg-destructive/5": variant === 'destructive',
      },
      className
    )}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        {Icon && (
          <div className={cn(
            "h-8 w-8 rounded-full flex items-center justify-center",
            {
              "bg-primary/10 text-primary": variant === 'primary',
              "bg-success/10 text-success": variant === 'success',
              "bg-warning/10 text-warning": variant === 'warning',
              "bg-destructive/10 text-destructive": variant === 'destructive',
              "bg-muted text-muted-foreground": variant === 'default',
            }
          )}>
            <Icon className="h-4 w-4" />
          </div>
        )}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground mt-1">{description}</p>
        )}
        {trend && (
          <p className={cn(
            "text-xs mt-2 flex items-center gap-1",
            trend.isPositive ? "text-success" : "text-destructive"
          )}>
            <span>{trend.isPositive ? '↑' : '↓'}</span>
            <span>{Math.abs(trend.value)}%</span>
            {trend.label && <span className="text-muted-foreground">{trend.label}</span>}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
