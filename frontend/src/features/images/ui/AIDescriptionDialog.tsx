"use client";

import React, { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/shared/components/ui/dialog";
import { Button } from "@/shared/components/ui/button";
import { Textarea } from "@/shared/components/ui/textarea";
import { Label } from "@/shared/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/components/ui/select";
import { Progress } from "@/shared/components/ui/progress";
import { Spinner } from "@/shared/components/ui/spinner";
import { useAIDescription } from "../hooks/useAIDescription";
import { useImageUpdate } from "../hooks/useImages";
import { ImageTask, AIProvider } from "../types";
import { Sparkles, Save, RotateCcw, Edit2, Eye } from "lucide-react";
import { Card, CardContent } from "@/shared/components/ui/card";

interface AIDescriptionDialogProps {
  image: ImageTask;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onDescriptionSaved?: () => void;
}

type ViewMode = "input" | "result";

export function AIDescriptionDialog({
  image,
  open,
  onOpenChange,
  onDescriptionSaved,
}: AIDescriptionDialogProps) {
  const [userContext, setUserContext] = useState("");
  const [originalContext, setOriginalContext] = useState(""); // Store original context for regeneration
  const [providerPreference, setProviderPreference] = useState<AIProvider | undefined>("mock"); // Default to mock for testing
  const [editableDescription, setEditableDescription] = useState("");
  const [viewMode, setViewMode] = useState<ViewMode>("input");
  const [isRefiningContext, setIsRefiningContext] = useState(false);
  const { generateDescription, descriptionTask, isGenerating, progress, reset: resetDescription } = useAIDescription();
  const updateImage = useImageUpdate();
  const t = useTranslations('aiDescription');
  const tCommon = useTranslations('common');

  // Reset when dialog opens/closes
  useEffect(() => {
    if (open) {
      setUserContext("");
      setOriginalContext("");
      setProviderPreference("mock"); // Default to mock for testing
      setEditableDescription("");
      setViewMode("input");
      setIsRefiningContext(false);
      resetDescription();
    } else {
      // Reset when closing
      setUserContext("");
      setOriginalContext("");
      setProviderPreference("mock");
      setEditableDescription("");
      setViewMode("input");
      setIsRefiningContext(false);
    }
  }, [open, resetDescription]);

  // Update editable description when task completes
  useEffect(() => {
    if (descriptionTask?.status === "SUCCESS" && descriptionTask.result_text) {
      // Update description if result_text is available
      const resultText = descriptionTask.result_text.trim();
      if (resultText) {
        setEditableDescription(resultText);
        setViewMode("result"); // Switch to result view when description is ready
      }
      // Store the context that was used for this generation
      if (userContext.trim() && !originalContext) {
        setOriginalContext(userContext.trim());
      }
    }
  }, [descriptionTask?.status, descriptionTask?.result_text, userContext, originalContext]);

  const handleGenerate = () => {
    // Store original context on first generation
    if (!originalContext && userContext.trim()) {
      setOriginalContext(userContext.trim());
    }

    generateDescription({
      image_task_id: image.id,
      user_context: userContext.trim() || "",
      provider_preference: providerPreference,
    });
  };

  const handleRegenerate = () => {
    // Regenerate with original context (restore if it was changed)
    if (originalContext && userContext !== originalContext) {
      setUserContext(originalContext);
    }
    resetDescription();
    handleGenerate();
  };

  const handleRefineContext = () => {
    setIsRefiningContext(true);
    setViewMode("input");
    // Restore original context for editing if available
    if (originalContext) {
      setUserContext(originalContext);
    }
  };

  const handleRefineAndRegenerate = () => {
    // Update original context with refined version
    if (userContext.trim()) {
      setOriginalContext(userContext.trim());
    }
    setIsRefiningContext(false);
    resetDescription();
    handleGenerate();
  };

  const handleViewOriginalContext = () => {
    setViewMode("input");
    setIsRefiningContext(false);
    // Restore original context for viewing/editing
    if (originalContext) {
      setUserContext(originalContext);
    }
  };

  const handleSave = async () => {
    const descriptionToSave = displayDescription || editableDescription;
    if (!descriptionToSave.trim()) return;

    try {
      await updateImage.mutateAsync({
        imageId: image.id,
        data: { user_description: descriptionToSave.trim() },
      });
      onDescriptionSaved?.();
      onOpenChange(false);
    } catch (error) {
      // Error handled by hook
    }
  };

  const contextLength = userContext.length;
  // Check if we have a description (either from task result or already saved)
  const hasDescription = (descriptionTask?.status === "SUCCESS" && descriptionTask.result_text) || 
                         (editableDescription && editableDescription.trim().length > 0);
  const canRegenerate = hasDescription && !isGenerating;
  
  // Use result_text directly if available, otherwise use editableDescription
  const displayDescription = descriptionTask?.result_text || editableDescription;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            {t('generateDescriptionWithAI')}
          </DialogTitle>
          <DialogDescription>
            {t('provideContextDescription')}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Input Mode: Context and Provider Selection */}
          {(viewMode === "input" || isRefiningContext) && (
            <>
              {/* Context Input */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="context">
                    {isRefiningContext ? t('refineContext') : t('contextOptional')}
                  </Label>
                  <span className="text-xs text-muted-foreground">
                    {t('characters', { count: contextLength })}
                  </span>
                </div>
                <Textarea
                  id="context"
                  placeholder={t('contextPlaceholder')}
                  value={userContext}
                  onChange={(e) => setUserContext(e.target.value)}
                  rows={6}
                  className="resize-none"
                />
                <p className="text-xs text-muted-foreground">
                  {t('contextOptionalInfo')}
                </p>
              </div>

              {/* Provider Selection */}
              <div className="space-y-2">
                <Label htmlFor="provider">{t('aiProvider')}</Label>
                <Select
                  value={providerPreference || "auto"}
                  onValueChange={(value) => setProviderPreference(value === "auto" ? undefined : value as AIProvider)}
                >
                  <SelectTrigger id="provider">
                    <SelectValue placeholder={t('automaticBestAvailable')} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="auto">{t('automaticBestAvailable')}</SelectItem>
                    <SelectItem value="openai">{t('openaiGpt4')}</SelectItem>
                    <SelectItem value="anthropic">{t('anthropicClaude')}</SelectItem>
                    <SelectItem value="mock">{t('mockTestingOnly')}</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Generate/Refine Button */}
              {isRefiningContext ? (
                <div className="flex gap-2">
                  <Button
                    onClick={handleRefineAndRegenerate}
                    disabled={isGenerating}
                    className="flex-1"
                    size="lg"
                  >
                    {isGenerating ? (
                      <>
                        <Spinner className="mr-2 h-4 w-4" />
                        {t('generatingDescription')}
                      </>
                    ) : (
                      <>
                        <Sparkles className="mr-2 h-4 w-4" />
                        {t('regenerateWithRefinedContext')}
                      </>
                    )}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setIsRefiningContext(false);
                      if (hasDescription) {
                        setViewMode("result");
                      }
                    }}
                    disabled={isGenerating}
                  >
                    {tCommon('cancel')}
                  </Button>
                </div>
              ) : (
                <Button
                  onClick={handleGenerate}
                  disabled={isGenerating}
                  className="w-full"
                  size="lg"
                >
                  {isGenerating ? (
                    <>
                      <Spinner className="mr-2 h-4 w-4" />
                      {t('generatingDescription')}
                    </>
                  ) : (
                    <>
                      <Sparkles className="mr-2 h-4 w-4" />
                      {t('generateAutomaticDescription')}
                    </>
                  )}
                </Button>
              )}

              {/* Progress Indicator */}
              {isGenerating && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">{t('progress')}</span>
                    <span className="text-muted-foreground">{progress}%</span>
                  </div>
                  <Progress value={progress} />
                  {descriptionTask?.status === "RUNNING" && (
                    <p className="text-xs text-muted-foreground">
                      {t('processingWithProvider', { provider: descriptionTask.provider_used || t('unknownProvider') })}
                    </p>
                  )}
                </div>
              )}

              {/* Error Display */}
              {descriptionTask?.status === "FAILED" && (
                <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                  <p className="font-medium">{t('errorGeneratingDescription')}</p>
                  <p className="mt-1">{descriptionTask.error_message || t('unknownError')}</p>
                </div>
              )}
            </>
          )}

          {/* Result Mode: Show Generated Description */}
          {hasDescription && !isRefiningContext && (
            <>
              <Card>
                <CardContent className="pt-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="description" className="text-base font-semibold">
                        {t('generatedDescription')}
                      </Label>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={handleRefineContext}
                          disabled={isGenerating}
                        >
                          <Edit2 className="h-3 w-3 mr-1" />
                          {t('refineContext')}
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={handleRegenerate}
                          disabled={isGenerating}
                        >
                          <RotateCcw className="h-3 w-3 mr-1" />
                          {t('regenerate')}
                        </Button>
                      </div>
                    </div>
                    <Textarea
                      id="description"
                      value={displayDescription || ""}
                      onChange={(e) => setEditableDescription(e.target.value)}
                      rows={12}
                      className="resize-none font-mono text-sm"
                      placeholder="La descripción se está cargando..."
                    />
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span>
                        {t('generatedWith', { provider: descriptionTask?.provider_used || t('unknownProvider'), model: descriptionTask?.model_used || t('unknownModel') })}
                      </span>
                      <span>{t('characters', { count: displayDescription.length })}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Show Original Context Info */}
              {originalContext && (
                <div className="text-xs text-muted-foreground p-2 bg-muted rounded-md">
                  <p className="font-medium mb-1">{t('contextUsed')}</p>
                  <p className="line-clamp-2">{originalContext}</p>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={handleViewOriginalContext}
                  className="flex-1"
                >
                  <Eye className="h-4 w-4 mr-2" />
                  {t('viewEditContext')}
                </Button>
                <Button
                  onClick={handleSave}
                  disabled={updateImage.isPending || !displayDescription.trim()}
                  className="flex-1"
                >
                  {updateImage.isPending ? (
                    <>
                      <Spinner className="mr-2 h-4 w-4" />
                      {t('saving')}
                    </>
                  ) : (
                    <>
                      <Save className="mr-2 h-4 w-4" />
                      {t('saveDescription')}
                    </>
                  )}
                </Button>
              </div>
            </>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {hasDescription ? tCommon('close') : tCommon('cancel')}
          </Button>
          {hasDescription && (
            <Button onClick={handleSave} disabled={updateImage.isPending || !displayDescription?.trim()}>
              {updateImage.isPending ? (
                <>
                  <Spinner className="mr-2 h-4 w-4" />
                  {t('saving')}
                </>
              ) : (
                <>
                  <Save className="mr-2 h-4 w-4" />
                  {t('saveAndClose')}
                </>
              )}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
