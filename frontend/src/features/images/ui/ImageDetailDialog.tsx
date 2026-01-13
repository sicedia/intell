"use client";

import React, { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/shared/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/components/ui/tabs";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { Textarea } from "@/shared/components/ui/textarea";
import { useImageDetail, useImageUpdate, usePublishImage, useDeleteImage } from "../hooks/useImages";
import { useQueryClient } from "@tanstack/react-query";
import { TagSelector } from "./TagSelector";
import { GroupSelector } from "./GroupSelector";
import { AIDescriptionDialog } from "./AIDescriptionDialog";
import { ImageTask } from "../types";
import { Save, Sparkles, BookmarkPlus, BookmarkCheck, Trash2, X } from "lucide-react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/shared/components/ui/alert-dialog";
import { Spinner } from "@/shared/components/ui/spinner";
import { Badge } from "@/shared/components/ui/badge";
import { UserInfo } from "@/shared/ui/UserInfo";

interface ImageDetailDialogProps {
  imageId: number | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  initialTab?: "view" | "edit" | "ai";
  autoPublishOnSave?: boolean;
  onSave?: () => void;
}

export function ImageDetailDialog({ imageId, open, onOpenChange, initialTab = "view", autoPublishOnSave = false, onSave }: ImageDetailDialogProps) {
  const { data: image, isLoading, refetch } = useImageDetail(imageId);
  const updateImage = useImageUpdate();
  const publishImage = usePublishImage();
  const deleteImage = useDeleteImage();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState(initialTab);
  const [isAIDialogOpen, setIsAIDialogOpen] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const t = useTranslations('images');
  const tCommon = useTranslations('common');
  const tAI = useTranslations('aiDescription');

  // Update active tab when initialTab changes or dialog opens
  useEffect(() => {
    if (open) {
      setActiveTab(initialTab);
    }
  }, [open, initialTab]);

  // Form state
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [selectedTags, setSelectedTags] = useState<number[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<number | null>(null);

  // Initialize form when image loads
  useEffect(() => {
    if (image) {
      setTitle(image.title || "");
      setDescription(image.user_description || "");
      setSelectedTags(image.tags || []);
      setSelectedGroup(image.group);
    }
  }, [image]);

  const handleSave = async () => {
    if (!image) return;

    try {
      await updateImage.mutateAsync({
        imageId: image.id,
        data: {
          title: title.trim() || undefined,
          user_description: description.trim() || undefined,
          tags: selectedTags,
          group: selectedGroup,
        },
      });
      
      // Auto-publish if enabled and image is not already published
      if (autoPublishOnSave && !image.is_published) {
        try {
          await publishImage.mutateAsync({
            imageId: image.id,
            publish: true,
          });
        } catch (error) {
          // Error handled by hook, but don't prevent dialog from closing
        }
      }
      
      // Invalidate job queries if we have a job context (from generate page)
      // This ensures the job status updates in JobResults
      if (image.job) {
        queryClient.invalidateQueries({ queryKey: ["job", image.job] });
      }
      
      // Call onSave callback if provided
      onSave?.();
      
      onOpenChange(false);
    } catch (error) {
      // Error handled by hook
    }
  };

  const hasChanges =
    image &&
    (title !== (image.title || "") ||
      description !== (image.user_description || "") ||
      JSON.stringify(selectedTags.sort()) !== JSON.stringify((image.tags || []).sort()) ||
      selectedGroup !== image.group);

  if (isLoading || !image) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>{t('loadingImage')}</DialogTitle>
          </DialogHeader>
          <div className="flex items-center justify-center py-12">
            <Spinner size="lg" />
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-4xl max-h-[90vh] p-0 flex flex-col">
          {/* Fixed close button in top right corner */}
          <Button
            variant="ghost"
            size="icon"
            className="absolute right-4 top-4 z-50 h-8 w-8 rounded-full bg-background/80 backdrop-blur-sm hover:bg-background border shadow-sm"
            onClick={() => onOpenChange(false)}
            aria-label={t('closeDialog')}
          >
            <X className="h-4 w-4" />
          </Button>
          
          {/* Header - fixed */}
          <div className="px-6 pt-6 pb-4 border-b">
            <DialogHeader>
              <DialogTitle>
                {image.title || t('imageTitle', { id: image.id })} - {image.algorithm_key}
              </DialogTitle>
            </DialogHeader>
          </div>

          {/* Scrollable content */}
          <div className="flex-1 overflow-y-auto px-6 py-4">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="view">{t('view')}</TabsTrigger>
              <TabsTrigger value="edit">{t('editMetadata')}</TabsTrigger>
              <TabsTrigger value="ai">{t('aiDescription')}</TabsTrigger>
            </TabsList>

            {/* View Tab */}
            <TabsContent value="view" className="space-y-4 mt-4">
              <div className="relative w-full aspect-video bg-muted rounded-lg overflow-hidden">
                {image.artifact_png_url ? (
                  // Use native img for external URLs to avoid Next.js Image optimization issues
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={image.artifact_png_url}
                    alt={image.title || `Image ${image.id}`}
                    className="absolute inset-0 w-full h-full object-contain"
                  />
                ) : (
                  <div className="flex items-center justify-center h-full text-muted-foreground">
                    {t('imageNotAvailable')}
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <div>
                  <Label className="text-muted-foreground">{t('title')}</Label>
                  <p className="text-sm font-medium">{image.title || t('noTitle')}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">{t('algorithm')}</Label>
                  <p className="text-sm">{image.algorithm_key} v{image.algorithm_version}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">{t('generatedBy')}</Label>
                  <div className="mt-1">
                    <UserInfo
                      username={image.created_by_username}
                      email={image.created_by_email}
                      userId={image.created_by}
                      variant="default"
                      showIcon={true}
                    />
                  </div>
                </div>
                {image.user_description && (
                  <div>
                    <Label className="text-muted-foreground">{t('description')}</Label>
                    <p className="text-sm whitespace-pre-wrap">{image.user_description}</p>
                  </div>
                )}
                <div>
                  <Label className="text-muted-foreground">{tCommon('status')}</Label>
                  <div className="flex items-center gap-2">
                    <p className="text-sm">{image.status}</p>
                    <Badge variant={image.is_published ? "default" : "secondary"}>
                      {image.is_published ? t('published') : t('draft')}
                    </Badge>
                  </div>
                </div>
                {image.is_published && image.published_at && (
                  <div>
                    <Label className="text-muted-foreground">{t('publishedOn')}</Label>
                    <p className="text-sm">{new Date(image.published_at).toLocaleString()}</p>
                  </div>
                )}
                <div>
                  <Label className="text-muted-foreground">{tCommon('created')}</Label>
                  <p className="text-sm">{new Date(image.created_at).toLocaleString()}</p>
                </div>
                {image.status === "SUCCESS" && (
                  <div className="pt-4 border-t space-y-2">
                    <Button
                      variant={image.is_published ? "outline" : "default"}
                      onClick={async () => {
                        try {
                          await publishImage.mutateAsync({
                            imageId: image.id,
                            publish: !image.is_published,
                          });
                          refetch();
                        } catch (error) {
                          // Error handled by hook
                        }
                      }}
                      disabled={publishImage.isPending}
                      className="w-full"
                    >
                          {publishImage.isPending ? (
                            <>
                              <Spinner className="mr-2 h-4 w-4" />
                              {image.is_published ? t('unpublishing') : t('publishing')}
                            </>
                          ) : image.is_published ? (
                            <>
                              <BookmarkCheck className="mr-2 h-4 w-4" />
                              {t('unpublishToDraft')}
                            </>
                          ) : (
                            <>
                              <BookmarkPlus className="mr-2 h-4 w-4" />
                              {t('publishToLibrary')}
                            </>
                          )}
                        </Button>
                        <Button
                          variant="destructive"
                          onClick={() => setShowDeleteConfirm(true)}
                          disabled={deleteImage.isPending}
                          className="w-full"
                        >
                          {deleteImage.isPending ? (
                            <>
                              <Spinner className="mr-2 h-4 w-4" />
                              {t('deleting')}
                            </>
                          ) : (
                            <>
                              <Trash2 className="mr-2 h-4 w-4" />
                              {t('deleteImage')}
                            </>
                          )}
                        </Button>
                  </div>
                )}
              </div>
            </TabsContent>

            {/* Edit Tab */}
            <TabsContent value="edit" className="space-y-4 mt-4">
              <div className="space-y-4">
                {/* Show info if description was AI-generated */}
                {image.user_description && (
                  <div className="rounded-lg border bg-blue-50 dark:bg-blue-950/20 p-3 space-y-1">
                    <div className="flex items-center gap-2">
                      <Sparkles className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                      <Label className="text-sm font-medium text-blue-900 dark:text-blue-100">
                        {t('aiGeneratedDescription')}
                      </Label>
                    </div>
                    <p className="text-xs text-blue-700 dark:text-blue-300">
                      {t('aiGeneratedDescriptionInfo')}
                    </p>
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="title">{t('title')}</Label>
                  <Input
                    id="title"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder={t('titlePlaceholder')}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">{t('description')}</Label>
                  <Textarea
                    id="description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder={t('descriptionPlaceholder')}
                    rows={4}
                  />
                  {image.user_description && (
                    <p className="text-xs text-muted-foreground">
                      {t('canEditDescription')}
                    </p>
                  )}
                </div>

                <TagSelector
                  selectedTags={selectedTags}
                  onTagsChange={setSelectedTags}
                />

                <GroupSelector
                  selectedGroup={selectedGroup}
                  onGroupChange={setSelectedGroup}
                />
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t">
                <Button variant="outline" onClick={() => onOpenChange(false)}>
                  {tCommon('cancel')}
                </Button>
                <Button onClick={handleSave} disabled={!hasChanges || updateImage.isPending}>
                  {updateImage.isPending ? (
                    <>
                      <Spinner className="mr-2 h-4 w-4" />
                      {t('saving')}
                    </>
                  ) : (
                    <>
                      <Save className="mr-2 h-4 w-4" />
                      {t('saveChanges')}
                    </>
                  )}
                </Button>
              </div>
            </TabsContent>

            {/* AI Description Tab */}
            <TabsContent value="ai" className="space-y-4 mt-4">
              <div className="space-y-4">
                <div className="rounded-lg border p-4 space-y-2">
                  <h3 className="font-medium">{t('generateDescriptionWithAI')}</h3>
                  <p className="text-sm text-muted-foreground">
                    {t('provideContext')}
                  </p>
                  <Button onClick={() => setIsAIDialogOpen(true)} className="w-full">
                    <Sparkles className="mr-2 h-4 w-4" />
                    {t('requestAIDescription')}
                  </Button>
                </div>

                {/* Show AI Context if available */}
                {image.ai_context && (
                  <div className="space-y-2">
                    <Label>{t('contextUsedForAIDescription')}</Label>
                    <div className="rounded-md border p-3 bg-blue-50 dark:bg-blue-950/20">
                      <p className="text-sm whitespace-pre-wrap text-blue-900 dark:text-blue-100">
                        {image.ai_context}
                      </p>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {t('contextUsedInfo')}
                    </p>
                  </div>
                )}

                {image.user_description && (
                  <div className="space-y-2">
                    <Label>{t('currentDescription')}</Label>
                    <div className="rounded-md border p-3 bg-muted/50">
                      <p className="text-sm whitespace-pre-wrap">{image.user_description}</p>
                    </div>
                  </div>
                )}
              </div>
            </TabsContent>
          </Tabs>
          </div>
        </DialogContent>
      </Dialog>

      {/* AI Description Dialog */}
      {image && (
        <AIDescriptionDialog
          image={image}
          open={isAIDialogOpen}
          onOpenChange={setIsAIDialogOpen}
          onDescriptionSaved={() => {
            setIsAIDialogOpen(false);
            setActiveTab("view");
            // Refresh image data
            refetch();
          }}
        />
      )}

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t('deleteImageConfirm')}</AlertDialogTitle>
            <AlertDialogDescription>
              {t('deleteImageConfirmDescription', { title: image?.title || t('imageTitle', { id: image?.id || 0 }) })}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{tCommon('cancel')}</AlertDialogCancel>
            <AlertDialogAction
              onClick={async () => {
                if (!image) return;
                try {
                  await deleteImage.mutateAsync(image.id);
                  setShowDeleteConfirm(false);
                  onOpenChange(false);
                } catch (error) {
                  // Error handled by hook
                }
              }}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {t('delete')}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
