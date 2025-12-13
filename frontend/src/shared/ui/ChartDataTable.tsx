
import React from 'react';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/shared/components/ui/table";
import { cn } from "@/shared/lib/utils";

// Minimal interface to match typical chart data structures
export interface ChartSeries {
    name: string;
    data: number[];
    color?: string;
}

export interface ChartData {
    categories: string[];
    series: ChartSeries[];
}

interface ChartDataTableProps {
    data: ChartData;
    className?: string;
}

export function ChartDataTable({ data, className }: ChartDataTableProps) {
    if (!data || !data.categories || !data.series) {
        return <div className="text-sm text-muted-foreground p-4">No chart data available.</div>;
    }

    return (
        <div className={cn("rounded-md border", className)}>
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead className="w-[150px]">Category</TableHead>
                        {data.series.map((series, i) => (
                            <TableHead key={i}>{series.name}</TableHead>
                        ))}
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {data.categories.map((category, catIndex) => (
                        <TableRow key={catIndex}>
                            <TableCell className="font-medium">{category}</TableCell>
                            {data.series.map((series, serIndex) => (
                                <TableCell key={serIndex}>
                                    {series.data[catIndex] !== undefined ? series.data[catIndex] : '-'}
                                </TableCell>
                            ))}
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
    );
}
