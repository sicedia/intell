"""
Views for AI descriptions app.
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from .providers import LITELLM_MODELS


# Model information with estimated costs (per 1K tokens)
# Costs are estimates and may vary
MODEL_INFO = {
    'openai/gpt-5.2-chat-latest': {
        'name': 'GPT-5.2 Chat Latest',
        'provider': 'openai',
        'category': 'gpt',
        'cost_per_1k_input': 0.015,
        'cost_per_1k_output': 0.045,
        'description': 'Latest GPT-5.2 model with advanced reasoning capabilities',
    },
    'openai/gpt-5-mini': {
        'name': 'GPT-5 Mini',
        'provider': 'openai',
        'category': 'gpt',
        'cost_per_1k_input': 0.003,
        'cost_per_1k_output': 0.009,
        'description': 'Fast and efficient GPT-5 model optimized for speed',
    },
    'openai/gpt-4.1': {
        'name': 'GPT-4.1',
        'provider': 'openai',
        'category': 'gpt',
        'cost_per_1k_input': 0.03,
        'cost_per_1k_output': 0.06,
        'description': 'Enhanced GPT-4 model with improved performance',
    },
    'openai/gpt-4.1-mini-2025-04-14': {
        'name': 'GPT-4.1 Mini',
        'provider': 'openai',
        'category': 'gpt',
        'cost_per_1k_input': 0.006,
        'cost_per_1k_output': 0.012,
        'description': 'Compact GPT-4.1 model for faster responses',
    },
    'gemini/gemini-3-flash-preview': {
        'name': 'Gemini 3 Flash Preview',
        'provider': 'google',
        'category': 'gemini',
        'cost_per_1k_input': 0.00025,
        'cost_per_1k_output': 0.001,
        'description': 'Fast Gemini 3 model optimized for speed',
    },
    'gemini/gemini-3-pro-preview': {
        'name': 'Gemini 3 Pro Preview',
        'provider': 'google',
        'category': 'gemini',
        'cost_per_1k_input': 0.00125,
        'cost_per_1k_output': 0.005,
        'description': 'Advanced Gemini 3 model with enhanced capabilities',
    },
    'gemini/gemini-2.5-flash': {
        'name': 'Gemini 2.5 Flash',
        'provider': 'google',
        'category': 'gemini',
        'cost_per_1k_input': 0.0002,
        'cost_per_1k_output': 0.0008,
        'description': 'Fast Gemini 2.5 model',
    },
    'gemini/gemini-2.5-pro': {
        'name': 'Gemini 2.5 Pro',
        'provider': 'google',
        'category': 'gemini',
        'cost_per_1k_input': 0.001,
        'cost_per_1k_output': 0.004,
        'description': 'Advanced Gemini 2.5 model',
    },
    'deepseek-v3.2': {
        'name': 'DeepSeek V3.2',
        'provider': 'deepseek',
        'category': 'deepseek',
        'cost_per_1k_input': 0.0007,
        'cost_per_1k_output': 0.0028,
        'description': 'DeepSeek V3.2 model with strong reasoning',
    },
    'qwen3-next-80b-thinking': {
        'name': 'Qwen3 Next 80B Thinking',
        'provider': 'qwen',
        'category': 'qwen',
        'cost_per_1k_input': 0.001,
        'cost_per_1k_output': 0.004,
        'description': 'Qwen3 model with advanced thinking capabilities',
    },
    'qwen3-next-80b-instruct': {
        'name': 'Qwen3 Next 80B Instruct',
        'provider': 'qwen',
        'category': 'qwen',
        'cost_per_1k_input': 0.001,
        'cost_per_1k_output': 0.004,
        'description': 'Qwen3 instruction-tuned model',
    },
    'qwen3-coder': {
        'name': 'Qwen3 Coder',
        'provider': 'qwen',
        'category': 'qwen',
        'cost_per_1k_input': 0.001,
        'cost_per_1k_output': 0.004,
        'description': 'Qwen3 model specialized for code generation',
    },
    'gpt-oss-120b': {
        'name': 'GPT-OSS 120B',
        'provider': 'open-source',
        'category': 'oss',
        'cost_per_1k_input': 0.0005,
        'cost_per_1k_output': 0.002,
        'description': 'Open-source GPT model (120B parameters)',
    },
    'gpt-oss-20b': {
        'name': 'GPT-OSS 20B',
        'provider': 'open-source',
        'category': 'oss',
        'cost_per_1k_input': 0.0002,
        'cost_per_1k_output': 0.0008,
        'description': 'Open-source GPT model (20B parameters)',
    },
}


@extend_schema(
    summary='Obtener modelos disponibles',
    description='Obtiene la lista de modelos LiteLLM disponibles con información de costos estimados.',
    tags=['AI'],
    responses={
        200: {
            'description': 'Lista de modelos disponibles',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'models': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'id': {'type': 'string'},
                                        'name': {'type': 'string'},
                                        'provider': {'type': 'string'},
                                        'category': {'type': 'string'},
                                        'cost_per_1k_input': {'type': 'number'},
                                        'cost_per_1k_output': {'type': 'number'},
                                        'fallback_order': {'type': 'integer'},
                                        'description': {'type': 'string'},
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
    },
)
@api_view(['GET'])
def get_available_models(request):
    """
    Get list of available LiteLLM models with cost information.
    """
    models = []
    
    for index, model_id in enumerate(LITELLM_MODELS, start=1):
        model_info = MODEL_INFO.get(model_id, {
            'name': model_id.replace('/', ' ').replace('-', ' ').title(),
            'provider': model_id.split('/')[0] if '/' in model_id else 'unknown',
            'category': model_id.split('/')[0] if '/' in model_id else 'unknown',
            'cost_per_1k_input': 0.01,  # Default estimate
            'cost_per_1k_output': 0.03,  # Default estimate
            'description': f'{model_id} model',
        })
        
        models.append({
            'id': model_id,
            'name': model_info['name'],
            'provider': model_info['provider'],
            'category': model_info['category'],
            'cost_per_1k_input': model_info['cost_per_1k_input'],
            'cost_per_1k_output': model_info['cost_per_1k_output'],
            'fallback_order': index,
            'description': model_info['description'],
        })
    
    return Response({'models': models})
