/**
 * Model information and cost estimates for LiteLLM models.
 * Costs are estimates per 1K tokens and may vary.
 */

export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  category: string;
  costPer1kInput: number;
  costPer1kOutput: number;
  fallbackOrder: number;
  description: string;
}

/**
 * Estimate cost for a description generation.
 * 
 * @param modelId - Model identifier
 * @param estimatedInputTokens - Estimated input tokens (prompt + dataset)
 * @param estimatedOutputTokens - Estimated output tokens (description)
 * @returns Estimated cost in USD
 */
export function estimateCost(
  modelId: string,
  estimatedInputTokens: number = 2000,
  estimatedOutputTokens: number = 500
): number {
  // This will be populated from the API, but we provide a default estimate
  // Default estimates (will be overridden by API data)
  const defaultCosts: Record<string, { input: number; output: number }> = {
    'openai/gpt-5.2-chat-latest': { input: 0.015, output: 0.045 },
    'openai/gpt-5-mini': { input: 0.003, output: 0.009 },
    'openai/gpt-4.1': { input: 0.03, output: 0.06 },
    'openai/gpt-4.1-mini-2025-04-14': { input: 0.006, output: 0.012 },
    'gemini/gemini-3-flash-preview': { input: 0.00025, output: 0.001 },
    'gemini/gemini-3-pro-preview': { input: 0.00125, output: 0.005 },
    'gemini/gemini-2.5-flash': { input: 0.0002, output: 0.0008 },
    'gemini/gemini-2.5-pro': { input: 0.001, output: 0.004 },
    'deepseek-v3.2': { input: 0.0007, output: 0.0028 },
    'qwen3-next-80b-thinking': { input: 0.001, output: 0.004 },
    'qwen3-next-80b-instruct': { input: 0.001, output: 0.004 },
    'qwen3-coder': { input: 0.001, output: 0.004 },
    'gpt-oss-120b': { input: 0.0005, output: 0.002 },
    'gpt-oss-20b': { input: 0.0002, output: 0.0008 },
  };

  const costs = defaultCosts[modelId] || { input: 0.01, output: 0.03 };
  
  const inputCost = (estimatedInputTokens / 1000) * costs.input;
  const outputCost = (estimatedOutputTokens / 1000) * costs.output;
  
  return inputCost + outputCost;
}

/**
 * Format cost for display.
 */
export function formatCost(cost: number): string {
  if (cost < 0.001) {
    return `~$${(cost * 1000).toFixed(2)} per 1K tokens`;
  }
  return `~$${cost.toFixed(4)} per 1K tokens`;
}

/**
 * Get category display name.
 */
export function getCategoryName(category: string): string {
  const categoryNames: Record<string, string> = {
    'gpt': 'GPT',
    'gemini': 'Gemini',
    'deepseek': 'DeepSeek',
    'qwen': 'Qwen',
    'oss': 'Open Source',
  };
  return categoryNames[category] || category;
}
