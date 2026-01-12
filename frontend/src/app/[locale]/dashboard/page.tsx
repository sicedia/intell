"use client";

import { PageHeader } from "@/shared/ui/PageHeader";
import { GalleryGrid } from "@/shared/ui/GalleryGrid";
import { ImageCard } from "@/shared/ui/ImageCard";
import { StatsCard } from "@/shared/ui/StatsCard";
import { EmptyState } from "@/shared/ui/EmptyState";
import { Button } from "@/shared/components/ui/button";
import { 
  PlusCircle, 
  Image as ImageIcon, 
  Sparkles, 
  TrendingUp,
  FileImage
} from "lucide-react";
import Link from "next/link";
import { useDashboardStats, useLatestPublishedImages } from "@/features/dashboard/hooks/useDashboard";
import { useTranslations } from "next-intl";
import { ImageLibraryItem } from "@/features/images/types";
import { useRouter } from "next/navigation";

export default function DashboardPage() {
  const t = useTranslations("dashboard");
  const router = useRouter();
  
  const { data: stats, isLoading: statsLoading } = useDashboardStats();
  const { data: latestImages, isLoading: imagesLoading } = useLatestPublishedImages(8);

  const handleImageClick = (image: ImageLibraryItem) => {
    router.push(`/images?imageId=${image.id}`);
  };

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
          title="Total Images Generated"
          value={statsLoading ? "..." : stats?.total_images ?? 0}
          description="Successfully generated images"
          icon={ImageIcon}
          variant="primary"
        />
        <StatsCard
          title="Published Images"
          value={statsLoading ? "..." : stats?.total_published_images ?? 0}
          description={`${stats?.published_this_month ?? 0} published this month`}
          icon={FileImage}
          variant="success"
        />
        <StatsCard
          title="Active Users This Month"
          value={statsLoading ? "..." : stats?.total_active_users_this_month ?? 0}
          description="Users who created content this month"
          icon={Sparkles}
          variant="default"
        />
        <StatsCard
          title="AI Described Images"
          value={statsLoading ? "..." : stats?.total_ai_described_images ?? 0}
          description={`${stats?.images_this_month ?? 0} images this month`}
          icon={TrendingUp}
          variant="primary"
        />
      </div>

      {/* Latest Published Images Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Latest Published Images</h2>
            <p className="text-muted-foreground">
              Recently published images from your library
            </p>
          </div>
          <Link href="/images">
            <Button variant="outline">
              View All
            </Button>
          </Link>
        </div>

        {imagesLoading ? (
          <GalleryGrid isLoading={true} itemCount={8} />
        ) : latestImages && latestImages.length > 0 ? (
          <GalleryGrid>
            {latestImages.map((image) => (
              <ImageCard
                key={image.id}
                title={image.title || image.algorithm_key || "Untitled"}
                status={image.status}
                imageUrl={image.artifact_png_url}
                subtitle={image.algorithm_key}
                onView={() => handleImageClick(image)}
              />
            ))}
          </GalleryGrid>
        ) : (
          <EmptyState
            title="No published images yet"
            description="Publish images from your gallery to see them here."
            icon={<FileImage className="h-12 w-12 text-muted-foreground" />}
            action={{
              label: "View Gallery",
              href: "/images",
              variant: "default",
            }}
          />
        )}
      </div>
    </div>
  );
}
