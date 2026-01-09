import { getTranslations } from "next-intl/server";
import { PageHeader } from "@/shared/ui/PageHeader";
import { GalleryGrid } from "@/shared/ui/GalleryGrid";
import { ImageCard } from "@/shared/ui/ImageCard";
import { StatsCard } from "@/shared/ui/StatsCard";
import { EmptyState } from "@/shared/ui/EmptyState";
import { features } from "@/shared/lib/flags";
import { MOCK_IMAGE_TASKS } from "@/shared/mock/mockJob";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { PlusCircle, Search, Image as ImageIcon, CheckCircle, Clock, Sparkles } from "lucide-react";
import Link from "next/link";

export default async function DashboardPage() {
  const t = await getTranslations("dashboard");
  const useMocks = features.useMocks;

  // In a real app, fetch data here
  const jobs = useMocks ? MOCK_IMAGE_TASKS : [];

  // Calculate stats
  const totalJobs = jobs.length;
  const completedJobs = jobs.filter(job => job.status === 'SUCCESS' || job.status === 'COMPLETED').length;
  const runningJobs = jobs.filter(job => job.status === 'RUNNING').length;
  const successRate = totalJobs > 0 ? Math.round((completedJobs / totalJobs) * 100) : 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("title")}
        subtitle={t("welcome")}
        actions={
          <Link href="/generate">
            <Button size="lg">
              <PlusCircle className="mr-2 h-4 w-4" />
              New Generation
            </Button>
          </Link>
        }
      />

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Total Generations"
          value={totalJobs}
          description="All time generations"
          icon={Sparkles}
          variant="primary"
        />
        <StatsCard
          title="Completed"
          value={completedJobs}
          description={`${successRate}% success rate`}
          icon={CheckCircle}
          variant="success"
          trend={
            totalJobs > 0
              ? {
                  value: successRate,
                  isPositive: successRate >= 80,
                  label: "vs target",
                }
              : undefined
          }
        />
        <StatsCard
          title="In Progress"
          value={runningJobs}
          description="Currently running"
          icon={Clock}
          variant="warning"
        />
        <StatsCard
          title="Images Generated"
          value={completedJobs}
          description="Total images created"
          icon={ImageIcon}
          variant="default"
        />
      </div>

      {/* Search and Filter Bar */}
      {jobs.length > 0 && (
        <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
          <div className="relative w-full sm:w-auto sm:min-w-[300px]">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search generations..."
              className="pl-10"
            />
          </div>
          <div className="flex gap-2">
            {/* Quick filters could go here */}
          </div>
        </div>
      )}

      {/* Gallery or Empty State */}
      {jobs.length > 0 ? (
        <GalleryGrid>
          {jobs.map((task) => (
            <ImageCard
              key={task.id}
              title={task.algorithm_key}
              status={task.status}
              imageUrl={task.artifact_png_url}
              subtitle={`Task ID: ${task.id}`}
            />
          ))}
        </GalleryGrid>
      ) : (
        <EmptyState
          title="No images generated yet"
          description="Start by creating a new generation job to visualize your data."
          icon={<Sparkles className="h-12 w-12 text-muted-foreground" />}
          action={{
            label: "Create New Generation",
            href: "/generate",
            variant: "default",
          }}
        />
      )}
    </div>
  );
}
