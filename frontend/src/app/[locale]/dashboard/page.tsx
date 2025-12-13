
import { getTranslations } from "next-intl/server";
import { PageHeader } from "@/shared/ui/PageHeader";
import { GalleryGrid } from "@/shared/ui/GalleryGrid";
import { ImageCard } from "@/shared/ui/ImageCard";
import { features } from "@/shared/lib/flags";
import { MOCK_IMAGE_TASKS } from "@/shared/mock/mockJob";
import { Button } from "@/shared/components/ui/button";
import { PlusCircle } from "lucide-react";
import Link from "next/link";
import { StateBlock } from "@/shared/ui/StateBlock";

export default async function DashboardPage() {
  const t = await getTranslations("dashboard");
  const useMocks = features.useMocks;

  // In a real app, fetch data here
  const jobs = useMocks ? MOCK_IMAGE_TASKS : []; // Just mapping tasks as "jobs" for gallery view ease

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("title")}
        subtitle={t("welcome")}
        actions={
          <Link href="/generate">
            <Button>
              <PlusCircle className="mr-2 h-4 w-4" />
              New Generation
            </Button>
          </Link>
        }
      />

      {jobs.length > 0 ? (
        <GalleryGrid>
          {jobs.map((task) => (
            <ImageCard
              key={task.id}
              title={task.algorithm_key} // using Algo key as title for now
              status={task.status}
              imageUrl={task.artifact_png_url}
              subtitle={`Task ID: ${task.id}`}
            />
          ))}
        </GalleryGrid>
      ) : (
        <StateBlock
          variant="empty"
          title="No images generated yet"
          description="Start by creating a new generation job."
          action={{
            label: "Create New",
            href: "/generate"
          }}
        >
          <Link href="/generate" className="absolute inset-0 z-10" aria-label="Create new" />
        </StateBlock>
      )}
    </div>
  );
}
