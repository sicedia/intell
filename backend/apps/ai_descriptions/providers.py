"""
AI provider implementations for chart descriptions.
Supports LiteLLM (via CEDIA), OpenAI, Anthropic, and Mock (for MVP).
Includes router with fallback and retry logic.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time
import logging

logger = logging.getLogger(__name__)

# List of available LiteLLM models with fallback order
LITELLM_MODELS = [
    'openai/gpt-5.2-chat-latest',
    'openai/gpt-5-mini',
    'openai/gpt-4.1',
    'openai/gpt-4.1-mini-2025-04-14',
    'gemini/gemini-3-flash-preview',
    'gemini/gemini-3-pro-preview',
    'gemini/gemini-2.5-flash',
    'gemini/gemini-2.5-pro',
    'deepseek-v3.2',
    'qwen3-next-80b-thinking',
    'qwen3-next-80b-instruct',
    'qwen3-coder',
    'gpt-oss-120b',
    'gpt-oss-20b',
]


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    def generate_description(
        self, 
        chart_data: Dict[str, Any], 
        user_context: Optional[str] = None,
        timeout: int = 30,
        algorithm_key: Optional[str] = None,
        source_type: Optional[str] = None,
        visualization_type: Optional[str] = None,
        dataset_content: Optional[str] = None
    ) -> str:
        """
        Generate description for chart.
        
        Args:
            chart_data: Structured chart data
            user_context: User-provided context
            timeout: Timeout in seconds
            
        Returns:
            Generated description text
        """
        pass
    
    def _build_prompt(
        self, 
        chart_data: Dict[str, Any], 
        user_context: Optional[str],
        algorithm_key: Optional[str] = None,
        source_type: Optional[str] = None,
        visualization_type: Optional[str] = None,
        dataset_content: Optional[str] = None
    ) -> str:
        """
        Build prompt from chart_data and user_context with enriched context.
        
        This is a shared implementation used by all AI providers.
        
        Args:
            chart_data: Structured chart data
            user_context: User-provided context
            algorithm_key: Algorithm identifier (e.g., 'patent_trends_cumulative')
            source_type: Data source type (e.g., 'lens', 'espacenet_excel')
            visualization_type: Type of visualization (from chart_data or algorithm)
            
        Returns:
            Formatted prompt string
        """
        prompt = "You are a data visualization expert. Describe this chart in detail, focusing on:\n"
        prompt += "- The main trends and patterns visible\n"
        prompt += "- Key data points and metrics\n"
        prompt += "- The significance of the visualization\n"
        prompt += "- Any notable insights or observations\n\n"
        prompt += "Chart Information:\n"
        prompt += f"Chart Type: {chart_data.get('type', visualization_type or 'unknown')}\n"
        
        # Title from chart_data or use algorithm-based title
        title = chart_data.get('title')
        if not title and algorithm_key:
            # Generate a readable title from algorithm_key
            title = algorithm_key.replace('_', ' ').title()
        prompt += f"Title: {title or 'Untitled'}\n"
        
        # Algorithm and source context
        if algorithm_key:
            prompt += f"Algorithm: {algorithm_key}\n"
        if source_type:
            prompt += f"Data Source: {source_type}\n"
        
        # Axis labels
        if 'x_axis' in chart_data:
            prompt += f"X-Axis: {chart_data['x_axis']}\n"
        if 'y_axis' in chart_data or 'y_axis_1' in chart_data:
            y_axis = chart_data.get('y_axis') or chart_data.get('y_axis_1', '')
            prompt += f"Y-Axis: {y_axis}\n"
        if 'y_axis_2' in chart_data:
            prompt += f"Y-Axis 2 (Secondary): {chart_data['y_axis_2']}\n"
        
        # Series information
        if 'series' in chart_data:
            series = chart_data['series']
            prompt += f"\nData Series: {len(series)} data points\n"
            # Include sample of first few data points if available
            if isinstance(series, list) and len(series) > 0:
                sample_size = min(3, len(series))
                prompt += f"Sample data points (first {sample_size}):\n"
                for i, point in enumerate(series[:sample_size]):
                    prompt += f"  - {point}\n"
        
        # Totals and summary metrics
        if 'totals' in chart_data:
            totals = chart_data['totals']
            prompt += "\nSummary Metrics:\n"
            for key, value in totals.items():
                if value is not None:
                    prompt += f"  {key}: {value}\n"
        
        # Additional totals at root level
        for key in ['total_cumulative', 'total_publications', 'max_value', 'min_value']:
            if key in chart_data and chart_data[key] is not None:
                prompt += f"  {key}: {chart_data[key]}\n"
        
        # Date/time ranges
        if 'years_range' in chart_data:
            years = chart_data['years_range']
            if isinstance(years, dict):
                start = years.get('start')
                end = years.get('end')
                if start and end:
                    prompt += f"\nTime Period: {start} - {end}\n"
        
        # Warnings or notes
        if 'warnings' in chart_data and chart_data['warnings']:
            prompt += f"\nNotes/Warnings: {', '.join(chart_data['warnings'])}\n"
        
        # Dataset content (raw data context)
        if dataset_content:
            # Truncate if too large (limit to ~5000 chars to avoid token limits)
            max_dataset_length = 5000
            if len(dataset_content) > max_dataset_length:
                prompt += f"\nDataset Content (first {max_dataset_length} characters):\n{dataset_content[:max_dataset_length]}...\n"
                prompt += f"\nNote: Dataset was truncated. Total length: {len(dataset_content)} characters.\n"
            else:
                prompt += f"\nDataset Content (raw data):\n{dataset_content}\n"
        
        # User context (required, minimum 200 chars already validated)
        if user_context:
            prompt += f"\nUser Context (important background information):\n{user_context}\n"
        
        prompt += "\nPlease provide a comprehensive, professional description of this chart."
        
        return prompt


# Legacy providers (OpenAI and Anthropic) removed - using LiteLLM only
# These providers are no longer used as we rely on LiteLLM for all AI operations

class LiteLLMProvider(AIProvider):
    """LiteLLM provider using ChatOpenAI with custom base_url for CEDIA API."""
    
    def __init__(self, api_key: str = "sk-iAriFxLhR71i7NTlUKXw6Q", base_url: str = "https://api.cedia.org.ec/v1", model: str = "openai/gpt-5.2-chat-latest"):
        """
        Initialize LiteLLM provider.
        
        Args:
            api_key: API key for LiteLLM
            base_url: Base URL for LiteLLM API
            model: Model name to use
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self._client = None
    
    def _get_client(self):
        """Get LiteLLM client (lazy initialization)."""
        if self._client is None:
            try:
                from langchain_openai import ChatOpenAI
                self._client = ChatOpenAI(
                    model=self.model,
                    temperature=0,
                    max_tokens=None,
                    timeout=None,
                    max_retries=2,
                    base_url=self.base_url,
                    api_key=self.api_key,
                )
            except ImportError:
                raise ImportError("langchain-openai not installed")
        return self._client
    
    def generate_description(
        self, 
        chart_data: Dict[str, Any], 
        user_context: Optional[str] = None,
        timeout: int = 30,
        algorithm_key: Optional[str] = None,
        source_type: Optional[str] = None,
        visualization_type: Optional[str] = None,
        dataset_content: Optional[str] = None
    ) -> str:
        """Generate description using LiteLLM."""
        try:
            # Use direct messages instead of ChatPromptTemplate to avoid issues with
            # curly braces in dataset content being interpreted as template variables
            prompt_text = self._build_prompt(
                chart_data, user_context, algorithm_key, source_type, visualization_type, dataset_content
            )
            client = self._get_client()
            
            # Use direct messages format - this avoids ChatPromptTemplate interpreting
            # JSON content with curly braces as template variables
            messages = [
                ("system", "You are a data visualization expert. Describe charts clearly and concisely."),
                ("human", prompt_text)
            ]
            
            start_time = time.time()
            result = client.invoke(messages)
            elapsed_time = time.time() - start_time
            
            if elapsed_time > timeout:
                raise TimeoutError(f"LiteLLM request timed out after {elapsed_time:.2f}s")
            
            return result.content if hasattr(result, 'content') else str(result)
        except Exception as e:
            logger.error(f"LiteLLM provider error (model: {self.model}): {e}")
            raise


class MockProvider(AIProvider):
    """Mock provider for MVP - returns realistic mock descriptions."""
    
    def generate_description(
        self, 
        chart_data: Dict[str, Any], 
        user_context: Optional[str] = None,
        timeout: int = 30,
        algorithm_key: Optional[str] = None,
        source_type: Optional[str] = None,
        visualization_type: Optional[str] = None,
        dataset_content: Optional[str] = None
    ) -> str:
        """Generate realistic mock description."""
        import time
        # Simulate processing time
        time.sleep(1)
        
        chart_type = chart_data.get('type', visualization_type or 'chart')
        title = chart_data.get('title', algorithm_key or 'Chart')
        
        # Build a more realistic description
        description_parts = []
        
        # Introduction
        if algorithm_key:
            algo_name = algorithm_key.replace('_', ' ').title()
            description_parts.append(f"Este gráfico de tipo {chart_type} muestra un análisis de {algo_name}.")
        else:
            description_parts.append(f"Este gráfico de tipo {chart_type} presenta una visualización de datos.")
        
        # Data source context
        if source_type == 'lens':
            description_parts.append("Los datos provienen de la base de datos de patentes Lens API, proporcionando una perspectiva global sobre las tendencias de patentes.")
        elif source_type == 'espacenet_excel':
            description_parts.append("Los datos han sido extraídos de un archivo Excel de Espacenet, representando información estructurada de patentes.")
        else:
            description_parts.append("Los datos representan información procesada y estructurada para su visualización.")
        
        # Chart-specific details
        if 'totals' in chart_data:
            totals = chart_data['totals']
            if 'total_publications' in totals:
                count = totals['total_publications']
                description_parts.append(f"El gráfico muestra un total de {count} publicaciones de patentes, lo que indica un volumen significativo de actividad de innovación.")
        
        # Time range
        if 'years_range' in chart_data:
            years = chart_data['years_range']
            if isinstance(years, dict):
                start = years.get('start')
                end = years.get('end')
                if start and end:
                    description_parts.append(f"El período de análisis abarca desde {start} hasta {end}, permitiendo observar la evolución temporal de las tendencias.")
        
        # User context integration
        if user_context and user_context.strip():
            description_parts.append(f"Según el contexto proporcionado: {user_context}")
        
        # Key insights
        description_parts.append("El análisis revela patrones importantes en la distribución y evolución de los datos, destacando tendencias significativas que pueden ser útiles para la toma de decisiones estratégicas.")
        
        # Conclusion
        description_parts.append("Esta visualización facilita la comprensión de los datos complejos mediante una representación gráfica clara y accesible.")
        
        return " ".join(description_parts)


class AIProviderRouter:
    """
    Router for AI providers with fallback and retry logic.
    Order: LiteLLM (with model fallback) → Mock
    """
    
    def __init__(self):
        """Initialize router with providers."""
        self.providers = []
        
        # Initialize LiteLLM providers for each model (will try in order)
        # We'll create them lazily when needed to avoid initialization errors
        self.litellm_models = LITELLM_MODELS.copy()
        
        # Always add Mock as fallback
        self.providers.append(('mock', MockProvider()))
    
    def generate_description(
        self,
        chart_data: Dict[str, Any],
        user_context: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        provider_preference: Optional[str] = None,
        model_preference: Optional[str] = None,
        algorithm_key: Optional[str] = None,
        source_type: Optional[str] = None,
        visualization_type: Optional[str] = None,
        dataset_content: Optional[str] = None,
        on_model_attempt: Optional[callable] = None,
        on_model_failed: Optional[callable] = None,
        on_model_success: Optional[callable] = None,
        on_fallback: Optional[callable] = None
    ) -> tuple[str, str]:
        """
        Generate description with fallback.
        
        Args:
            chart_data: Structured chart data
            user_context: User-provided context
            timeout: Timeout per provider
            max_retries: Maximum retries per provider
            provider_preference: Preferred provider name ('litellm', 'openai', 'anthropic', 'mock')
                                If provided, starts from that provider
            model_preference: Specific model to use (e.g., 'openai/gpt-5.2-chat-latest')
            algorithm_key: Algorithm identifier
            source_type: Data source type
            visualization_type: Type of visualization
            dataset_content: Raw dataset content as string
            on_model_attempt: Callback(model_name) called when attempting a model
            on_model_failed: Callback(model_name, error) called when a model fails
            on_model_success: Callback(model_name) called when a model succeeds
            on_fallback: Callback(from_model, to_model) called when falling back
            
        Returns:
            Tuple of (description_text, model_name)
        """
        # Build list of providers to try
        # Start with LiteLLM models (try each model in order)
        providers_to_try = []
        
        # If model_preference is specified, use only that model
        if model_preference and model_preference in self.litellm_models:
            try:
                provider = LiteLLMProvider(model=model_preference)
                providers_to_try.append((model_preference, provider))
            except Exception as e:
                logger.warning(f"Failed to initialize LiteLLM provider for model {model_preference}: {e}")
                # Fall through to default behavior if preferred model fails to initialize
                pass
        
        # Add LiteLLM models first (unless provider_preference is something else or model_preference was set)
        if not providers_to_try and (not provider_preference or provider_preference == 'litellm'):
            for model in self.litellm_models:
                # Skip if this is the preferred model (already added)
                if model_preference and model == model_preference:
                    continue
                try:
                    provider = LiteLLMProvider(model=model)
                    providers_to_try.append((model, provider))
                except Exception as e:
                    logger.warning(f"Failed to initialize LiteLLM provider for model {model}: {e}")
                    continue
        
        # Add fallback providers (Mock)
        providers_to_try.extend(self.providers)
        
        # If provider_preference is specified and not litellm, reorder
        # Note: 'litellm' is handled above by adding LiteLLM models to providers_to_try
        # So we only reorder if provider_preference is a specific provider name (e.g., 'mock')
        if provider_preference and provider_preference != 'litellm':
            preferred_provider = None
            remaining_providers = []
            for provider_name, provider in providers_to_try:
                if provider_name == provider_preference:
                    preferred_provider = (provider_name, provider)
                else:
                    remaining_providers.append((provider_name, provider))
            
            if preferred_provider:
                providers_to_try = [preferred_provider] + remaining_providers
            else:
                # Only warn if it's not 'litellm' or 'auto' (which are handled specially)
                if provider_preference not in ['litellm', 'auto']:
                    logger.warning(f"Provider preference '{provider_preference}' not available, using default order")
        
        # Track which models failed for error reporting
        failed_models = []
        previous_model = None
        
        for provider_name, provider in providers_to_try:
            # Emit fallback event if switching models
            if previous_model and previous_model != provider_name:
                if on_fallback:
                    try:
                        on_fallback(previous_model, provider_name)
                    except Exception as e:
                        logger.warning(f"Error in on_fallback callback: {e}")
            
            # Emit attempt event
            if on_model_attempt:
                try:
                    on_model_attempt(provider_name)
                except Exception as e:
                    logger.warning(f"Error in on_model_attempt callback: {e}")
            
            # Retry logic with exponential backoff
            for attempt in range(max_retries):
                try:
                    description = provider.generate_description(
                        chart_data, user_context, timeout,
                        algorithm_key, source_type, visualization_type, dataset_content
                    )
                    # Success! Emit success event and return
                    if on_model_success:
                        try:
                            on_model_success(provider_name)
                        except Exception as e:
                            logger.warning(f"Error in on_model_success callback: {e}")
                    return description, provider_name
                except Exception as e:
                    error_msg = str(e)
                    logger.warning(
                        f"Provider {provider_name} attempt {attempt + 1} failed: {error_msg}"
                    )
                    if attempt < max_retries - 1:
                        # Exponential backoff
                        wait_time = 2 ** attempt
                        time.sleep(wait_time)
                    else:
                        # All retries exhausted for this provider
                        failed_models.append(f"{provider_name} ({error_msg})")
                        # Emit failed event
                        if on_model_failed:
                            try:
                                on_model_failed(provider_name, error_msg)
                            except Exception as e:
                                logger.warning(f"Error in on_model_failed callback: {e}")
                        previous_model = provider_name
                        # Move to next provider
                        break
        
        # All providers failed - raise exception with details
        error_message = f"All providers failed. Failed models: {', '.join(failed_models)}"
        logger.error(error_message)
        raise Exception(error_message)

