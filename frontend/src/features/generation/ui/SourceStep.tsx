import { useState, useCallback } from "react";
import { useWizardStore } from "../stores/useWizardStore";
import { useDropzone } from "react-dropzone";
import * as XLSX from "xlsx";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/shared/components/ui/card";
// Assuming ui components exist based on package structure "shared/components/ui"

interface SourceStepProps {
    onNext: () => void;
}

export const SourceStep = ({ onNext }: SourceStepProps) => {
    const { setSourceFile, sourceFile, sourceType, setSourceType } = useWizardStore();
    const [previewData, setPreviewData] = useState<any[]>([]);
    const [error, setError] = useState<string | null>(null);

    const onDrop = useCallback((acceptedFiles: File[]) => {
        const file = acceptedFiles[0];
        if (!file) return;

        // Validate file type
        if (!file.name.match(/\.(xlsx|xls)$/)) {
            setError("Please upload a valid Excel file (.xlsx or .xls)");
            return;
        }

        setSourceFile(file);
        setError(null);

        // Read file for preview
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const bstr = e.target?.result;
                const wb = XLSX.read(bstr, { type: "binary" });
                const wsname = wb.SheetNames[0];
                const ws = wb.Sheets[wsname];
                // Get header and first 10 rows
                const allData = XLSX.utils.sheet_to_json(ws, { header: 1 });
                setPreviewData(allData.slice(0, 11));
            } catch (err) {
                console.error("Error reading file", err);
                setError("Failed to read Excel file. Please ensure it is a valid format.");
            }
        };
        reader.readAsBinaryString(file);
    }, [setSourceFile]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
            'application/vnd.ms-excel': ['.xls']
        },
        maxFiles: 1
    });

    return (
        <div className="space-y-6">
            <div className="flex gap-4">
                <Button
                    variant={sourceType === "espacenet_excel" ? "default" : "outline"}
                    onClick={() => setSourceType("espacenet_excel")}
                >
                    Espacenet Excel
                </Button>
                <Button
                    variant={sourceType === "lens_query" ? "default" : "outline"}
                    onClick={() => setSourceType("lens_query")}
                    disabled
                    title="Not implemented yet"
                >
                    Lens Query (Coming Soon)
                </Button>
            </div>

            {sourceType === "espacenet_excel" && (
                <Card>
                    <CardHeader>
                        <CardTitle>Upload Patent Data</CardTitle>
                        <CardDescription>Upload an Excel file exported from Espacenet.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div
                            {...getRootProps()}
                            className={`border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition-colors
                ${isDragActive ? "border-primary bg-primary/10" : "border-gray-300 hover:border-primary"}
              `}
                        >
                            <input {...getInputProps()} />
                            {sourceFile ? (
                                <p className="text-sm font-medium">Selected: {sourceFile.name}</p>
                            ) : (
                                <p className="text-sm text-muted-foreground">
                                    Drag & drop an Excel file here, or click to select one
                                </p>
                            )}
                        </div>

                        {error && (
                            <div className="p-3 bg-red-100 text-red-800 rounded-md text-sm">
                                {error}
                            </div>
                        )}

                        {previewData.length > 0 && (
                            <div className="overflow-x-auto border rounded-md">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="bg-muted">
                                            {/* Render Headers */
                                                (previewData[0] as any[]).map((cell: any, i: number) => (
                                                    <th key={i} className="p-2 border-b text-left font-medium">{cell}</th>
                                                ))}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {/* Render Rows */
                                            previewData.slice(1).map((row: any[], i: number) => (
                                                <tr key={i} className="hover:bg-muted/50">
                                                    {row.map((cell: any, j: number) => (
                                                        <td key={j} className="p-2 border-b">{cell}</td>
                                                    ))}
                                                </tr>
                                            ))}
                                    </tbody>
                                </table>
                                <p className="text-xs text-muted-foreground mt-2 p-2">
                                    Showing first {previewData.length - 1} rows.
                                </p>
                            </div>
                        )}
                    </CardContent>
                </Card>
            )}

            <div className="flex justify-end">
                <Button onClick={onNext} disabled={!sourceFile}>
                    Next: Choose Visualizations
                </Button>
            </div>
        </div>
    );
};
