"use client";

import { useState, useCallback } from "react";
import { PageHeader } from "@/shared/ui/PageHeader";
import { GalleryGrid } from "@/shared/ui/GalleryGrid";
import { ImageCard } from "@/shared/ui/ImageCard";
import { StatsCard } from "@/shared/ui/StatsCard";
import { EmptyState } from "@/shared/ui/EmptyState";
import { ImageDetailDialog } from "@/features/images/ui/ImageDetailDialog";
import { AIDescriptionDialog } from "@/features/images/ui/AIDescriptionDialog";
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
import { ImageLibraryItem, ImageTask } from "@/features/images/types";
import { useQueryClient } from "@tanstack/react-query";

export default function DashboardPage() {
  const t = useTranslations("dashboard");
  const queryClient = useQueryClient();
  
  const { data: stats, isLoading: statsLoading } = useDashboardStats();
  const { data: latestImages, isLoading: imagesLoading } = useLatestPublishedImages(8);

  const [selectedImageId, setSelectedImageId] = useState<number | null>(null);
  const [isDetailDialogOpen, setIsDetailDialogOpen] = useState(false);
  const [isAIDialogOpen, setIsAIDialogOpen] = useState(false);
  const [aiImage, setAiImage] = useState<ImageTask | null>(null);

  const handleViewImage = useCallback((imageId: number) => {
    setSelectedImageId(imageId);
    setIsDetailDialogOpen(true);
  }, []);

  const handleEditImage = useCallback((imageId: number) => {
    setSelectedImageId(imageId);
    setIsDetailDialogOpen(true);
  }, []);

  // Helper function to convert ImageLibraryItem to ImageTask
  const convertLibraryItemToTask = useCallback((image: ImageLibraryItem): ImageTask => {
    return {
      id: image.id,
      job: image.job_id,
      created_by: image.created_by,
      created_by_username: image.created_by_username,
      created_by_email: image.created_by_email,
      algorithm_key: image.algorithm_key,
      algorithm_version: "1.0",
      params: {},
      output_format: "both",
      status: image.status,
      progress: 100,
      artifact_png_url: image.artifact_png_url,
      artifact_svg_url: image.artifact_svg_url,
      chart_data: null,
      error_code: null,
      error_message: null,
      trace_id: null,
      title: image.title,
      user_description: image.user_description,
      ai_context: image.ai_context,
      group: image.group,
      tags: image.tags.map((t) => t.id),
      is_published: image.is_published,
      published_at: image.published_at,
      created_at: image.created_at,
      updated_at: image.updated_at,
    };
  }, []);

  const handleGenerateDescription = useCallback((image: ImageLibraryItem | ImageTask) => {
    // Convert ImageLibraryItem to ImageTask format if needed
    const imageTask: ImageTask = "job_id" in image 
      ? convertLibraryItemToTask(image as ImageLibraryItem)
      : (image as ImageTask);
    
    setAiImage(imageTask);
    setIsAIDialogOpen(true);
  }, [convertLibraryItemToTask]);

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("title")}
        subtitle={t("welcome")}
        actions={
          <Link href="/generate">
            <Button size="lg">
              <PlusCircle className="mr-2 h-4 w-4" />
              {t("newGeneration")}
            </Button>
          </Link>
        }
      />

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title={t("totalImagesGenerated")}
          value={statsLoading ? "..." : stats?.total_images ?? 0}
          description={t("successfullyGeneratedImages")}
          icon={ImageIcon}
          variant="primary"
        />
        <StatsCard
          title={t("publishedImages")}
          value={statsLoading ? "..." : stats?.total_published_images ?? 0}
          description={`${stats?.published_this_month ?? 0} ${t("publishedThisMonth")}`}
          icon={FileImage}
          variant="success"
        />
        <StatsCard
          title={t("activeUsersThisMonth")}
          value={statsLoading ? "..." : stats?.total_active_users_this_month ?? 0}
          description={t("usersWhoCreatedContent")}
          icon={Sparkles}
          variant="default"
        />
        <StatsCard
          title={t("aiDescribedImages")}
          value={statsLoading ? "..." : stats?.total_ai_described_images ?? 0}
          description={`${stats?.images_this_month ?? 0} ${t("imagesThisMonth")}`}
          icon={TrendingUp}
          variant="primary"
        />
      </div>

      {/* Latest Published Images Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">{t("latestPublishedImages")}</h2>
            <p className="text-muted-foreground">
              {t("recentlyPublishedImages")}
            </p>
          </div>
          <Link href="/images">
            <Button variant="outline">
              {t("viewAll")}
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
                svgUrl={image.artifact_svg_url}
                subtitle={image.algorithm_key}
                createdBy={image.created_by}
                createdByUsername={image.created_by_username}
                createdByEmail={image.created_by_email}
                showFormatToggle={true}
                showDownload={true}
                onView={() => handleViewImage(image.id)}
                onEdit={() => handleEditImage(image.id)}
                onGenerateDescription={() => handleGenerateDescription(image)}
              />
            ))}
          </GalleryGrid>
        ) : (
          <EmptyState
            title={t("noPublishedImagesYet")}
            description={t("publishImagesFromGallery")}
            icon={<FileImage className="h-12 w-12 text-muted-foreground" />}
            action={{
              label: t("viewGallery"),
              href: "/images",
              variant: "default",
            }}
          />
        )}
      </div>

      {/* Detail Dialog */}
      <ImageDetailDialog
        imageId={selectedImageId}
        open={isDetailDialogOpen}
        onOpenChange={setIsDetailDialogOpen}
      />

      {/* AI Description Dialog */}
      {aiImage && (
        <AIDescriptionDialog
          image={aiImage}
          open={isAIDialogOpen}
          onOpenChange={(open) => {
            setIsAIDialogOpen(open);
            if (!open) {
              setAiImage(null);
            }
          }}
          onDescriptionSaved={() => {
            // Refresh images list
            queryClient.invalidateQueries({ queryKey: ["images"] });
            queryClient.invalidateQueries({ queryKey: ["dashboard", "latest-images"] });
            if (aiImage) {
              queryClient.invalidateQueries({ queryKey: ["image", aiImage.id] });
            }
          }}
        />
      )}
    </div>
  );
}
