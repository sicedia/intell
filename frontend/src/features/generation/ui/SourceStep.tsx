import { useState, useCallback } from "react";
import { useTranslations } from "next-intl";
import { useWizardStore } from "../stores/useWizardStore";
import { useDropzone } from "react-dropzone";
import * as XLSX from "xlsx";
import { Button } from "@/shared/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/shared/components/ui/card";
import { FormField } from "@/shared/ui/FormField";
import { env } from "@/shared/lib/env";
import { getCsrfToken } from "@/shared/lib/csrf";
import { Loader2 } from "lucide-react";

interface SourceStepProps {
    onNext: () => void;
}

// Type for Excel row data (array of cells)
type ExcelRow = (string | number | boolean | null | undefined)[];

export const SourceStep = ({ onNext }: SourceStepProps) => {
    const { setSourceFile, sourceFile, sourceType, setSourceType } = useWizardStore();
    const [previewData, setPreviewData] = useState<ExcelRow[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [isValidating, setIsValidating] = useState(false);
    const [isValid, setIsValid] = useState<boolean | null>(null);
    const t = useTranslations('generate.source');

    const validateExcelFile = useCallback(async (file: File): Promise<boolean> => {
        setIsValidating(true);
        setError(null);
        setIsValid(null);

        try {
            const formData = new FormData();
            formData.append('file', file);

            const apiUrl = env.NEXT_PUBLIC_API_BASE_URL;
            const csrfToken = getCsrfToken();
            
            const headers: HeadersInit = {};
            if (csrfToken) {
                headers['X-CSRFToken'] = csrfToken;
            }

            const response = await fetch(`${apiUrl}/validate-excel/`, {
                method: 'POST',
                headers,
                credentials: 'include',
                body: formData,
            });

            const data = await response.json();

            if (data.is_valid) {
                setIsValid(true);
                setError(null);
                return true;
            } else {
                setIsValid(false);
                setError(data.message || t('excelValidationFailed'));
                return false;
            }
        } catch (err) {
            console.error("Error validating Excel file", err);
            setIsValid(false);
            const errorMessage = err instanceof Error 
                ? err.message 
                : t('excelValidationError');
            setError(errorMessage);
            return false;
        } finally {
            setIsValidating(false);
        }
    }, [t]);

    const onDrop = useCallback(async (acceptedFiles: File[]) => {
        const file = acceptedFiles[0];
        if (!file) return;

        // Validate file type
        if (!file.name.match(/\.(xlsx|xls)$/)) {
            setError(t('pleaseUploadValidExcel'));
            setIsValid(false);
            return;
        }

        // Validate Excel structure before setting it
        const isValid = await validateExcelFile(file);
        
        if (!isValid) {
            // Don't set the file if validation fails
            setSourceFile(null);
            setPreviewData([]);
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
                const allData = XLSX.utils.sheet_to_json(ws, { header: 1 }) as ExcelRow[];
                setPreviewData(allData.slice(0, 11));
            } catch (err) {
                console.error("Error reading file", err);
                setError(t('failedToReadExcel'));
            }
        };
        reader.readAsBinaryString(file);
    }, [setSourceFile, validateExcelFile, t]);

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
                    {t('espacenetExcel')}
                </Button>
                <Button
                    variant={sourceType === "lens_query" ? "default" : "outline"}
                    onClick={() => setSourceType("lens_query")}
                    disabled
                    title={t('notImplementedYet')}
                >
                    {t('lensQuery')}
                </Button>
            </div>

            {sourceType === "espacenet_excel" && (
                <Card>
                    <CardHeader>
                        <CardTitle>{t('uploadPatentData')}</CardTitle>
                        <CardDescription>{t('uploadExcelDescription')}</CardDescription>
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
                                <p className="text-sm font-medium">{t('selected')}: {sourceFile.name}</p>
                            ) : (
                                <p className="text-sm text-muted-foreground">
                                    {t('dragDropOrClick')}
                                </p>
                            )}
                        </div>

                        {isValidating && (
                            <div className="p-3 bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300 rounded-md text-sm border border-blue-200 dark:border-blue-800 flex items-center gap-2">
                                <Loader2 className="h-4 w-4 animate-spin" />
                                {t('validatingExcel')}
                            </div>
                        )}

                        {error && (
                            <div className="p-3 bg-destructive/10 text-destructive rounded-md text-sm border border-destructive/20">
                                <div className="mb-2">{error}</div>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => {
                                        setSourceFile(null);
                                        setError(null);
                                        setIsValid(null);
                                        setPreviewData([]);
                                    }}
                                    className="mt-2"
                                >
                                    {t('clearAndTryAgain')}
                                </Button>
                            </div>
                        )}

                        {isValid === true && !isValidating && (
                            <div className="p-3 bg-green-50 dark:bg-green-950 text-green-700 dark:text-green-300 rounded-md text-sm border border-green-200 dark:border-green-800">
                                {t('excelValid')}
                            </div>
                        )}

                        {previewData.length > 0 && (
                            <div className="overflow-x-auto border rounded-md">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="bg-muted">
                                            {previewData[0]?.map((cell, i) => (
                                                <th key={i} className="p-2 border-b text-left font-medium">
                                                    {String(cell ?? "")}
                                                </th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {previewData.slice(1).map((row, i) => (
                                            <tr key={i} className="hover:bg-muted/50">
                                                {row.map((cell, j) => (
                                                    <td key={j} className="p-2 border-b">
                                                        {String(cell ?? "")}
                                                    </td>
                                                ))}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                                <p className="text-xs text-muted-foreground mt-2 p-2">
                                    {t('showingFirstRows', { count: previewData.length - 1 })}
                                </p>
                            </div>
                        )}
                    </CardContent>
                </Card>
            )}

            <div className="flex justify-between items-center">
                {/* Test button - only in development - loads test file from backend */}
                {process.env.NODE_ENV === 'development' && !sourceFile && (
                    <Button
                        variant="outline"
                        onClick={async () => {
                            try {
                                setError(null);
                                // Load test file from backend endpoint
                                const apiUrl = env.NEXT_PUBLIC_API_BASE_URL;
                                const response = await fetch(`${apiUrl}/test-excel/`);
                                if (!response.ok) {
                                    const errorText = await response.text();
                                    throw new Error(`Failed to load test file: ${response.status} ${response.statusText} - ${errorText}`);
                                }
                                const blob = await response.blob();
                                const file = new File([blob], 'Filters_20250331_1141.xlsx', { 
                                    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
                                });
                                await onDrop([file]);
                            } catch (err) {
                                console.error('Error loading test file:', err);
                                const errorMessage = err instanceof Error 
                                    ? err.message 
                                    : 'Could not load test file. Please upload manually.';
                                setError(errorMessage);
                            }
                        }}
                    >
                        {t('loadTestFile')}
                    </Button>
                )}
                <Button 
                    onClick={onNext} 
                    disabled={!sourceFile || !isValid || isValidating}
                >
                    {t('nextChooseVisualizations')}
                </Button>
            </div>
        </div>
    );
};
