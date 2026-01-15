/**
 * TypeScript types for Image Library feature
 */

export type ImageTaskStatus = 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED' | 'CANCELLED';
export type DescriptionTaskStatus = 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED' | 'CANCELLED';
export type AIProvider = 'litellm' | 'openai' | 'anthropic' | 'mock';

export interface Tag {
  id: number;
  name: string;
  color: string;
  created_by: number | null;
  created_at: string;
}

export interface ImageGroup {
  id: number;
  name: string;
  description: string | null;
  created_by: number;
  image_count?: number;
  created_at: string;
  updated_at: string;
}

export interface ImageTask {
  id: number;
  job: number;
  created_by: number | null;
  created_by_username?: string | null;
  created_by_email?: string | null;
  algorithm_key: string;
  algorithm_version: string;
  params: Record<string, unknown>;
  output_format: 'png' | 'svg' | 'both';
  status: ImageTaskStatus;
  progress: number;
  artifact_png_url: string | null;
  artifact_svg_url: string | null;
  chart_data: Record<string, unknown> | null;
  error_code: string | null;
  error_message: string | null;
  trace_id: string | null;
  title: string | null;
  user_description: string | null;
  ai_context: string | null;
  group: number | null;
  tags: number[];
  is_published: boolean;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ImageTaskUpdate {
  title?: string;
  user_description?: string;
  group?: number | null;
  tags?: number[];
}

export interface ImageLibraryItem {
  id: number;
  job_id: number;
  created_by: number | null;
  created_by_username?: string | null;
  created_by_email?: string | null;
  title: string | null;
  algorithm_key: string;
  status: ImageTaskStatus;
  artifact_png_url: string | null;
  artifact_svg_url: string | null;
  user_description: string | null;
  ai_context: string | null;
  tags: Tag[];
  group: number | null;
  group_name: string | null;
  is_published: boolean;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface DescriptionTask {
  id: number;
  image_task: number;
  user_context: string | null;
  provider_used: AIProvider | null;
  model_used: string | null;
  status: DescriptionTaskStatus;
  progress: number;
  result_text: string | null;
  prompt_snapshot: Record<string, unknown> | null;
  error_code: string | null;
  error_message: string | null;
  trace_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  category: string;
  cost_per_1k_input: number;
  cost_per_1k_output: number;
  fallback_order: number;
  description: string;
}

export interface AvailableModelsResponse {
  models: ModelInfo[];
}

export interface AIDescriptionRequest {
  image_task_id: number;
  user_context: string;
  provider_preference?: AIProvider;
  model_preference?: string; // Specific model ID (e.g., 'openai/gpt-5.2-chat-latest')
}

export interface AIDescriptionResponse {
  description_task_id: number;
  status: DescriptionTaskStatus;
  message: string;
  provider_preference?: AIProvider;
  model_preference?: string;
  job_id: number; // Job ID for WebSocket connection
}

export interface DescriptionTaskEvent {
  job_id?: number;
  entity_type?: string;
  entity_id?: number | string;
  event_type: 'START' | 'PROGRESS' | 'MODEL_ATTEMPT' | 'MODEL_FAILED' | 'MODEL_SUCCESS' | 'FALLBACK' | 'DONE' | 'ERROR' | 'AI_PROVIDER_ERROR';
  level: 'INFO' | 'WARNING' | 'ERROR';
  message: string;
  progress?: number;
  payload?: {
    model?: string;
    from_model?: string;
    to_model?: string;
    error?: string;
    failed_models?: string;
    description_task_id?: number;
    [key: string]: unknown;
  };
  trace_id?: string;
  created_at?: string;
}

export interface ImageFilters {
  status?: ImageTaskStatus;
  tags?: number[];
  group?: number;
  search?: string;
  date_from?: string;
  date_to?: string;
  published?: boolean; // Filter by published status (only used when not in library mode)
  group_by?: "job"; // Group images by Job (for grouped view)
  page?: number; // Page number for pagination (1-indexed)
  pageSize?: number; // Page size for pagination
}

// Paginated response from API
export interface PaginatedImageResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// Pagination metadata for UI
export interface PaginationMetadata {
  currentPage: number;
  pageSize: number;
  totalCount: number;
  totalPages: number;
  hasNext: boolean;
  hasPrevious: boolean;
}
