"use client";

import React, { useState, useEffect, useMemo } from "react";
import { useTranslations } from "next-intl";
import { useQuery } from "@tanstack/react-query";
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
import { Input } from "@/shared/components/ui/input";
import { Badge } from "@/shared/components/ui/badge";
import { useAIDescription } from "../hooks/useAIDescription";
import { useImageUpdate } from "../hooks/useImages";
import { ImageTask, AIProvider, ModelInfo } from "../types";
import { getAvailableModels } from "../api/descriptions";
import { estimateCost, formatCost, getCategoryName } from "../constants/models";
import { Sparkles, Save, RotateCcw, Edit2, Eye, AlertCircle, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { Card, CardContent } from "@/shared/components/ui/card";
import { Separator } from "@/shared/components/ui/separator";

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
  const [modelPreference, setModelPreference] = useState<string | undefined>(undefined); // Specific model or "auto"
  const [editableDescription, setEditableDescription] = useState("");
  const [viewMode, setViewMode] = useState<ViewMode>("input");
  const [isRefiningContext, setIsRefiningContext] = useState(false);
  const { 
    generateDescription, 
    descriptionTask, 
    isGenerating, 
    progress, 
    reset: resetDescription,
    realTimeEvents,
    currentModel,
    modelAttempts,
  } = useAIDescription();
  const updateImage = useImageUpdate();
  const t = useTranslations('aiDescription');
  const tCommon = useTranslations('common');

  // Fetch available models
  const { data: modelsData, isLoading: modelsLoading } = useQuery({
    queryKey: ["ai-models"],
    queryFn: getAvailableModels,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });

  // Group models by category
  const groupedModels = useMemo(() => {
    if (!modelsData?.models) return {};

    const grouped: Record<string, ModelInfo[]> = {};
    modelsData.models.forEach((model) => {
      if (!grouped[model.category]) {
        grouped[model.category] = [];
      }
      grouped[model.category].push(model);
    });

    return grouped;
  }, [modelsData]);

  // Estimate cost for selected model
  const estimatedCost = useMemo(() => {
    if (!modelPreference || modelPreference === "auto" || !modelsData?.models) return null;
    const model = modelsData.models.find((m) => m.id === modelPreference);
    if (!model) return null;
    // Estimate: ~2000 input tokens (prompt + dataset sample), ~500 output tokens
    return estimateCost(modelPreference, 2000, 500);
  }, [modelPreference, modelsData]);

  // Reset when dialog opens/closes
  useEffect(() => {
    if (open) {
      setUserContext("");
      setOriginalContext("");
      setModelPreference(undefined); // Auto by default
      setEditableDescription("");
      setViewMode("input");
      setIsRefiningContext(false);
      resetDescription();
    } else {
      // Reset when closing
      setUserContext("");
      setOriginalContext("");
      setModelPreference(undefined);
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
      model_preference: modelPreference && modelPreference !== "auto" ? modelPreference : undefined,
      provider_preference: modelPreference === "auto" || !modelPreference ? "litellm" : undefined,
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

              {/* Model Selection */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="model">{t('selectModel')}</Label>
                  {estimatedCost && (
                    <span className="text-xs text-muted-foreground">
                      {t('estimatedCost')}: ~${estimatedCost.toFixed(4)}
                    </span>
                  )}
                </div>
                
                {modelsLoading ? (
                  <div className="flex items-center justify-center p-4">
                    <Spinner className="h-4 w-4 mr-2" />
                    <span className="text-sm text-muted-foreground">{t('loadingModels')}</span>
                  </div>
                ) : (
                  <>
                    <Select
                      value={modelPreference || "auto"}
                      onValueChange={(value) => setModelPreference(value === "auto" ? undefined : value)}
                    >
                      <SelectTrigger id="model" className="w-full">
                        <SelectValue placeholder={t('automaticBestAvailable')} />
                      </SelectTrigger>
                      <SelectContent className="max-h-[400px]">
                        <SelectItem value="auto">{t('automaticBestAvailable')}</SelectItem>
                        <Separator className="my-1" />
                        {Object.entries(groupedModels).map(([category, models]) => (
                          <div key={category}>
                            <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
                              {getCategoryName(category)}
                            </div>
                            {models.map((model) => {
                              const inputCost = formatCost(model.cost_per_1k_input);
                              const outputCost = formatCost(model.cost_per_1k_output);
                              return (
                                <SelectItem key={model.id} value={model.id}>
                                  <div className="flex flex-col">
                                    <span className="font-medium">{model.name}</span>
                                    <span className="text-xs text-muted-foreground">
                                      {inputCost} / {outputCost}
                                    </span>
                                  </div>
                                </SelectItem>
                              );
                            })}
                          </div>
                        ))}
                      </SelectContent>
                    </Select>
                    
                    {/* Search for models (optional, can be added later) */}
                    {modelPreference && modelPreference !== "auto" && (
                      <p className="text-xs text-muted-foreground">
                        {modelsData?.models.find((m) => m.id === modelPreference)?.description}
                      </p>
                    )}
                  </>
                )}
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

              {/* Progress Indicator with Real-time Feedback */}
              {isGenerating && (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">{t('progress')}</span>
                      <span className="text-muted-foreground">{progress}%</span>
                    </div>
                    <Progress value={progress} />
                    {currentModel && (
                      <p className="text-xs text-muted-foreground flex items-center gap-1">
                        <Loader2 className="h-3 w-3 animate-spin" />
                        {t('processingWithModel', { model: currentModel })}
                      </p>
                    )}
                  </div>

                  {/* Real-time Model Attempts Timeline */}
                  {modelAttempts.length > 0 && (
                    <Card>
                      <CardContent className="pt-4">
                        <div className="space-y-2">
                          <Label className="text-sm font-semibold">{t('modelAttempts')}</Label>
                          <div className="space-y-2 max-h-32 overflow-y-auto">
                            {modelAttempts.map((attempt, index) => (
                              <div
                                key={`${attempt.model}-${index}`}
                                className="flex items-center gap-2 text-xs"
                              >
                                {attempt.status === "attempting" && (
                                  <>
                                    <Loader2 className="h-3 w-3 animate-spin text-blue-500" />
                                    <span className="text-muted-foreground">
                                      {t('attemptingModel', { model: attempt.model })}
                                    </span>
                                  </>
                                )}
                                {attempt.status === "failed" && (
                                  <>
                                    <XCircle className="h-3 w-3 text-destructive" />
                                    <span className="text-destructive">
                                      {t('modelFailed', { model: attempt.model })}
                                    </span>
                                    {attempt.error && (
                                      <Badge variant="outline" className="text-xs">
                                        {attempt.error.substring(0, 30)}...
                                      </Badge>
                                    )}
                                  </>
                                )}
                                {attempt.status === "success" && (
                                  <>
                                    <CheckCircle2 className="h-3 w-3 text-green-500" />
                                    <span className="text-green-600">
                                      {t('modelSuccess', { model: attempt.model })}
                                    </span>
                                  </>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </div>
              )}

              {/* Error Display with Model Failure Details */}
              {descriptionTask?.status === "FAILED" && (
                <Card className="border-destructive">
                  <CardContent className="pt-4">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-destructive">
                        <AlertCircle className="h-4 w-4" />
                        <p className="font-medium">{t('errorGeneratingDescription')}</p>
                      </div>
                      <p className="text-sm text-destructive">
                        {descriptionTask.error_message || t('unknownError')}
                      </p>
                      {modelAttempts.length > 0 && (
                        <div className="mt-2 pt-2 border-t border-destructive/20">
                          <p className="text-xs font-medium text-destructive mb-1">
                            {t('modelsAttempted')}:
                          </p>
                          <div className="space-y-1">
                            {modelAttempts.map((attempt, index) => (
                              <div key={`failed-${attempt.model}-${index}`} className="text-xs text-muted-foreground">
                                • {attempt.model} {attempt.status === "failed" && attempt.error && `(${attempt.error.substring(0, 50)}...)`}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
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
                        {(() => {
                          // Debug: log descriptionTask to see what we have
                          if (descriptionTask?.status === "SUCCESS") {
                            console.log("DescriptionTask on SUCCESS:", {
                              model_used: descriptionTask.model_used,
                              provider_used: descriptionTask.provider_used,
                              status: descriptionTask.status
                            });
                          }
                          
                          if (descriptionTask?.model_used) {
                            return t('generatedWith', { 
                              provider: descriptionTask.provider_used || 'litellm', 
                              model: descriptionTask.model_used 
                            });
                          } else if (descriptionTask?.provider_used) {
                            return t('generatedWith', { 
                              provider: descriptionTask.provider_used, 
                              model: t('unknownModel') 
                            });
                          } else {
                            return t('generatedWith', { 
                              provider: t('unknownProvider'), 
                              model: t('unknownModel') 
                            });
                          }
                        })()}
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
