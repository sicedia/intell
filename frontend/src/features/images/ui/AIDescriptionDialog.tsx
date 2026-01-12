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
import { Sparkles, Save } from "lucide-react";
import { cn } from "@/shared/lib/utils";

interface AIDescriptionDialogProps {
  image: ImageTask;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onDescriptionSaved?: () => void;
}

const MIN_CONTEXT_LENGTH = 200;

export function AIDescriptionDialog({
  image,
  open,
  onOpenChange,
  onDescriptionSaved,
}: AIDescriptionDialogProps) {
  const [userContext, setUserContext] = useState("");
  const [providerPreference, setProviderPreference] = useState<AIProvider | undefined>();
  const [editableDescription, setEditableDescription] = useState("");
  const { generateDescription, descriptionTask, isGenerating, progress } = useAIDescription();
  const updateImage = useImageUpdate();

  // Reset when dialog opens/closes
  useEffect(() => {
    if (open) {
      setUserContext("");
      setProviderPreference(undefined);
      setEditableDescription("");
    } else {
      // Reset when closing
      setUserContext("");
      setProviderPreference(undefined);
      setEditableDescription("");
    }
  }, [open]);

  // Update editable description when task completes
  useEffect(() => {
    if (descriptionTask?.status === "SUCCESS" && descriptionTask.result_text) {
      setEditableDescription(descriptionTask.result_text);
    }
  }, [descriptionTask]);

  const handleGenerate = () => {
    if (userContext.length < MIN_CONTEXT_LENGTH) return;

    generateDescription({
      image_task_id: image.id,
      user_context: userContext,
      provider_preference: providerPreference,
    });
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
  const isValidContext = contextLength >= MIN_CONTEXT_LENGTH;
  const remainingChars = MIN_CONTEXT_LENGTH - contextLength;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
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
          {/* Context Input */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="context">Contexto (mínimo {MIN_CONTEXT_LENGTH} caracteres)</Label>
              <span
                className={cn(
                  "text-xs",
                  isValidContext ? "text-muted-foreground" : "text-destructive"
                )}
              >
                {contextLength} / {MIN_CONTEXT_LENGTH}
                {!isValidContext && ` (faltan ${remainingChars})`}
              </span>
            </div>
            <Textarea
              id="context"
              placeholder="Describe el contexto de esta imagen. Por ejemplo: 'Este gráfico muestra las tendencias de patentes en inteligencia artificial durante los últimos 5 años. Los datos provienen de la base de datos de patentes de la EPO y representan publicaciones acumulativas por año...'"
              value={userContext}
              onChange={(e) => setUserContext(e.target.value)}
              rows={6}
              className={cn(
                "resize-none",
                !isValidContext && contextLength > 0 && "border-destructive focus-visible:ring-destructive"
              )}
            />
            {!isValidContext && contextLength > 0 && (
              <p className="text-xs text-destructive">
                El contexto debe tener al menos {MIN_CONTEXT_LENGTH} caracteres para generar una
                descripción de calidad.
              </p>
            )}
          </div>

          {/* Provider Selection (Optional) */}
          <div className="space-y-2">
            <Label htmlFor="provider">Proveedor de IA (opcional)</Label>
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

          {/* Generate Button */}
          <Button
            onClick={handleGenerate}
            disabled={!isValidContext || isGenerating}
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

          {/* Result Display */}
          {descriptionTask?.status === "SUCCESS" && editableDescription && (
            <div className="space-y-2">
              <Label htmlFor="description">Descripción generada (editable)</Label>
              <Textarea
                id="description"
                value={editableDescription}
                onChange={(e) => setEditableDescription(e.target.value)}
                rows={8}
                className="resize-none"
              />
              <p className="text-xs text-muted-foreground">
                Generado con {descriptionTask.provider_used || "proveedor automático"} (
                {descriptionTask.model_used || "modelo desconocido"})
              </p>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          {descriptionTask?.status === "SUCCESS" && editableDescription && (
            <Button onClick={handleSave} disabled={updateImage.isPending || !editableDescription.trim()}>
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
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
