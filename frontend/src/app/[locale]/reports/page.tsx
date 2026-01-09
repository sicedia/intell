import { PageHeader } from "@/shared/ui/PageHeader";
import { EmptyState } from "@/shared/ui/EmptyState";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/components/ui/select";
import { DataTable } from "@/shared/ui/DataTable";
import { Badge } from "@/shared/components/ui/badge";
import { FileText, Download, Plus, Calendar, Filter } from "lucide-react";
import Link from "next/link";

// Mock data type
type Report = {
  id: string;
  name: string;
  generatedAt: string;
  status: string;
  type: string;
  size: string;
};

export default function ReportsPage() {
  // Mock data
  const hasReports = false; // Change to true to see table view
  const mockReports: Report[] = [
    {
      id: "rpt-001",
      name: "Q1 2024 Analytics Report",
      generatedAt: "2024-03-31",
      status: "completed",
      type: "PDF",
      size: "2.4 MB",
    },
  ];

  const columns = [
    {
      key: "name" as const,
      header: "Report Name",
      render: (value: string, row: Report) => (
        <div>
          <div className="font-medium">{value}</div>
          <div className="text-xs text-muted-foreground">Type: {row.type}</div>
        </div>
      ),
    },
    {
      key: "generatedAt" as const,
      header: "Generated",
      render: (value: string) => (
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-muted-foreground" />
          {new Date(value).toLocaleDateString()}
        </div>
      ),
    },
    {
      key: "status" as const,
      header: "Status",
      render: (value: string) => (
        <Badge variant={value === "completed" ? "default" : "secondary"}>
          {value}
        </Badge>
      ),
    },
    {
      key: "size" as const,
      header: "Size",
    },
    {
      key: "id" as const,
      header: "Actions",
      render: (_: string, row: Report) => (
        <Button variant="outline" size="sm">
          <Download className="mr-2 h-4 w-4" />
          Download
        </Button>
      ),
      className: "text-right",
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Reports"
        subtitle="Generate and manage analytics reports"
        actions={
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Generate Report
          </Button>
        }
      />

      {hasReports ? (
        <>
          {/* Filters */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col sm:flex-row gap-4">
                <Input placeholder="Search reports..." className="flex-1" />
                <Select defaultValue="all">
                  <SelectTrigger className="w-full sm:w-[180px]">
                    <Filter className="mr-2 h-4 w-4" />
                    <SelectValue placeholder="Filter by type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Types</SelectItem>
                    <SelectItem value="pdf">PDF</SelectItem>
                    <SelectItem value="excel">Excel</SelectItem>
                    <SelectItem value="html">HTML</SelectItem>
                  </SelectContent>
                </Select>
                <Select defaultValue="all">
                  <SelectTrigger className="w-full sm:w-[180px]">
                    <SelectValue placeholder="Filter by status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                    <SelectItem value="generating">Generating</SelectItem>
                    <SelectItem value="failed">Failed</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Reports Table */}
          <DataTable
            data={mockReports}
            columns={columns}
            searchable={true}
            sortable={true}
            emptyMessage="No reports found"
          />
        </>
      ) : (
        <EmptyState
          title="No reports generated yet"
          description="Create comprehensive reports from your generated visualizations. Export to PDF, Excel, or HTML formats."
          icon={<FileText className="h-12 w-12 text-muted-foreground" />}
          action={{
            label: "Generate Your First Report",
            onClick: () => {
              // Handle report generation
            },
            variant: "default",
          }}
        />
      )}
    </div>
  );
}
