"use client";

import React, { useState, useEffect } from "react";
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
      setEditableDescription(descriptionTask.result_text);
      setViewMode("result"); // Switch to result view when description is ready
      // Store the context that was used for this generation
      if (userContext.trim() && !originalContext) {
        setOriginalContext(userContext.trim());
      }
    }
  }, [descriptionTask, userContext, originalContext]);

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
    // Keep current context for editing
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
    if (!editableDescription.trim()) return;

    try {
      await updateImage.mutateAsync({
        imageId: image.id,
        data: { user_description: editableDescription.trim() },
      });
      onDescriptionSaved?.();
      onOpenChange(false);
    } catch (error) {
      // Error handled by hook
    }
  };

  const contextLength = userContext.length;
  const hasDescription = descriptionTask?.status === "SUCCESS" && editableDescription;
  const canRegenerate = hasDescription && !isGenerating;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            Generar descripción con IA
          </DialogTitle>
          <DialogDescription>
            Proporciona contexto sobre esta imagen para generar una descripción detallada usando
            inteligencia artificial.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Input Mode: Context and Provider Selection */}
          {(viewMode === "input" || !hasDescription) && (
            <>
              {/* Context Input */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="context">
                    {isRefiningContext ? "Refinar contexto" : "Contexto (opcional)"}
                  </Label>
                  <span className="text-xs text-muted-foreground">
                    {contextLength} caracteres
                  </span>
                </div>
                <Textarea
                  id="context"
                  placeholder="Describe el contexto de esta imagen. Por ejemplo: 'Este gráfico muestra las tendencias de patentes en inteligencia artificial durante los últimos 5 años. Los datos provienen de la base de datos de patentes de la EPO y representan publicaciones acumulativas por año...' (Opcional - puedes dejar vacío para usar contexto automático)"
                  value={userContext}
                  onChange={(e) => setUserContext(e.target.value)}
                  rows={6}
                  className="resize-none"
                />
                <p className="text-xs text-muted-foreground">
                  El contexto es opcional. Si no proporcionas contexto, se usará información automática basada en el algoritmo y tipo de datos.
                </p>
              </div>

              {/* Provider Selection */}
              <div className="space-y-2">
                <Label htmlFor="provider">Proveedor de IA</Label>
                <Select
                  value={providerPreference || "auto"}
                  onValueChange={(value) => setProviderPreference(value === "auto" ? undefined : value as AIProvider)}
                >
                  <SelectTrigger id="provider">
                    <SelectValue placeholder="Automático (mejor disponible)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="auto">Automático (mejor disponible)</SelectItem>
                    <SelectItem value="openai">OpenAI (GPT-4)</SelectItem>
                    <SelectItem value="anthropic">Anthropic (Claude)</SelectItem>
                    <SelectItem value="mock">Mock (solo pruebas)</SelectItem>
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
                        Regenerando...
                      </>
                    ) : (
                      <>
                        <Sparkles className="mr-2 h-4 w-4" />
                        Regenerar con contexto refinado
                      </>
                    )}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setIsRefiningContext(false);
                      setViewMode("result");
                    }}
                    disabled={isGenerating}
                  >
                    Cancelar
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
                      Generando descripción...
                    </>
                  ) : (
                    <>
                      <Sparkles className="mr-2 h-4 w-4" />
                      Generar descripción automática con IA
                    </>
                  )}
                </Button>
              )}

              {/* Progress Indicator */}
              {isGenerating && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Progreso</span>
                    <span className="text-muted-foreground">{progress}%</span>
                  </div>
                  <Progress value={progress} />
                  {descriptionTask?.status === "RUNNING" && (
                    <p className="text-xs text-muted-foreground">
                      Procesando con {descriptionTask.provider_used || "proveedor automático"}...
                    </p>
                  )}
                </div>
              )}

              {/* Error Display */}
              {descriptionTask?.status === "FAILED" && (
                <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                  <p className="font-medium">Error al generar descripción</p>
                  <p className="mt-1">{descriptionTask.error_message || "Error desconocido"}</p>
                </div>
              )}
            </>
          )}

          {/* Result Mode: Show Generated Description */}
          {viewMode === "result" && hasDescription && (
            <>
              <Card>
                <CardContent className="pt-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="description" className="text-base font-semibold">
                        Descripción generada
                      </Label>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={handleRefineContext}
                          disabled={isGenerating}
                        >
                          <Edit2 className="h-3 w-3 mr-1" />
                          Refinar contexto
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={handleRegenerate}
                          disabled={isGenerating}
                        >
                          <RotateCcw className="h-3 w-3 mr-1" />
                          Regenerar
                        </Button>
                      </div>
                    </div>
                    <Textarea
                      id="description"
                      value={editableDescription}
                      onChange={(e) => setEditableDescription(e.target.value)}
                      rows={12}
                      className="resize-none font-mono text-sm"
                    />
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span>
                        Generado con {descriptionTask.provider_used || "proveedor automático"} (
                        {descriptionTask.model_used || "modelo desconocido"})
                      </span>
                      <span>{editableDescription.length} caracteres</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Show Original Context Info */}
              {originalContext && (
                <div className="text-xs text-muted-foreground p-2 bg-muted rounded-md">
                  <p className="font-medium mb-1">Contexto utilizado:</p>
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
                  Ver/Editar contexto
                </Button>
                <Button
                  onClick={handleSave}
                  disabled={updateImage.isPending || !editableDescription.trim()}
                  className="flex-1"
                >
                  {updateImage.isPending ? (
                    <>
                      <Spinner className="mr-2 h-4 w-4" />
                      Guardando...
                    </>
                  ) : (
                    <>
                      <Save className="mr-2 h-4 w-4" />
                      Guardar descripción
                    </>
                  )}
                </Button>
              </div>
            </>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {hasDescription ? "Cerrar" : "Cancelar"}
          </Button>
          {hasDescription && viewMode === "result" && (
            <Button onClick={handleSave} disabled={updateImage.isPending || !editableDescription.trim()}>
              {updateImage.isPending ? (
                <>
                  <Spinner className="mr-2 h-4 w-4" />
                  Guardando...
                </>
              ) : (
                <>
                  <Save className="mr-2 h-4 w-4" />
                  Guardar y cerrar
                </>
              )}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
