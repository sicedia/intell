/**
 * Visualization configuration options for chart generation.
 * These match the backend's VisualizationConfig options.
 */

export type FontSize = "small" | "medium" | "large";
export type ColorPalette =
    | "professional"
    | "vibrant"
    | "earth"
    | "ocean"
    | "sunset"
    | "monochrome";

export interface VisualizationConfig {
    color_palette: ColorPalette;
    font_size: FontSize;
    custom_params?: Record<string, unknown>;
}

export const DEFAULT_VISUALIZATION_CONFIG: VisualizationConfig = {
    color_palette: "professional",
    font_size: "medium",
};

export const FONT_SIZE_OPTIONS: { value: FontSize; label: string; description: string }[] = [
    {
        value: "small",
        label: "Small",
        description: "Compact text for detailed charts",
    },
    {
        value: "medium",
        label: "Medium",
        description: "Balanced readability (recommended)",
    },
    {
        value: "large",
        label: "Large",
        description: "High visibility text",
    },
];

export const COLOR_PALETTE_OPTIONS: {
    value: ColorPalette;
    label: string;
    description: string;
    colors: string[];
}[] = [
    {
        value: "professional",
        label: "Professional",
        description: "Corporate style with blues and grays",
        colors: ["#2563eb", "#3b82f6", "#64748b", "#0891b2"],
    },
    {
        value: "vibrant",
        label: "Vibrant",
        description: "Bright, saturated colors for impact",
        colors: ["#8b5cf6", "#ec4899", "#f59e0b", "#10b981"],
    },
    {
        value: "earth",
        label: "Earth",
        description: "Natural, warm tones",
        colors: ["#b45309", "#65a30d", "#0d9488", "#78716c"],
    },
    {
        value: "ocean",
        label: "Ocean",
        description: "Blues and teals inspired by the sea",
        colors: ["#0284c7", "#0891b2", "#0d9488", "#7c3aed"],
    },
    {
        value: "sunset",
        label: "Sunset",
        description: "Warm oranges and reds",
        colors: ["#ea580c", "#dc2626", "#ca8a04", "#be185d"],
    },
    {
        value: "monochrome",
        label: "Monochrome",
        description: "Elegant grayscale with accent",
        colors: ["#374151", "#6b7280", "#9ca3af", "#2563eb"],
    },
];
