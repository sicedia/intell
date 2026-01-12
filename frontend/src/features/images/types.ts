/**
 * TypeScript types for Image Library feature
 */

export type ImageTaskStatus = 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED' | 'CANCELLED';
export type DescriptionTaskStatus = 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED' | 'CANCELLED';
export type AIProvider = 'openai' | 'anthropic' | 'mock';

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

export interface AIDescriptionRequest {
  image_task_id: number;
  user_context: string;
  provider_preference?: AIProvider;
}

export interface AIDescriptionResponse {
  description_task_id: number;
  status: DescriptionTaskStatus;
  message: string;
  provider_preference?: AIProvider;
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
}
