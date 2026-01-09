import { PageHeader } from "@/shared/ui/PageHeader";
import { EmptyState } from "@/shared/ui/EmptyState";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/components/ui/select";
import { Image as ImageIcon, Search, Filter, Download, Grid, List } from "lucide-react";
import Link from "next/link";

export default function ImagesPage() {
  // Mock data for demonstration
  const hasImages = false; // Change to true to see gallery view

  return (
    <div className="space-y-6">
      <PageHeader
        title="Image Library"
        subtitle="Browse and manage all generated visualizations"
        actions={
          <Link href="/generate">
            <Button>
              <ImageIcon className="mr-2 h-4 w-4" />
              Generate New
            </Button>
          </Link>
        }
      />

      {hasImages ? (
        <>
          {/* Filters and Search */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search images by name, algorithm, or ID..."
                    className="pl-10"
                  />
                </div>
                <Select defaultValue="all">
                  <SelectTrigger className="w-full sm:w-[180px]">
                    <Filter className="mr-2 h-4 w-4" />
                    <SelectValue placeholder="Filter by status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="success">Success</SelectItem>
                    <SelectItem value="running">Running</SelectItem>
                    <SelectItem value="failed">Failed</SelectItem>
                  </SelectContent>
                </Select>
                <div className="flex gap-2">
                  <Button variant="outline" size="icon">
                    <Grid className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" size="icon">
                    <List className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Image Grid would go here */}
          <div className="text-center py-12 text-muted-foreground">
            Image gallery coming soon...
          </div>
        </>
      ) : (
        <EmptyState
          title="No images in your library"
          description="Generate visualizations from your data to see them appear here. You can organize, search, and download your generated images."
          icon={<ImageIcon className="h-12 w-12 text-muted-foreground" />}
          action={{
            label: "Generate Your First Image",
            href: "/generate",
            variant: "default",
          }}
        />
      )}
    </div>
  );
}
