"""
AI provider implementations for chart descriptions.
Supports OpenAI, Anthropic, and Mock (for MVP).
Includes router with fallback and retry logic.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time
import logging

logger = logging.getLogger(__name__)


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
        visualization_type: Optional[str] = None
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
        visualization_type: Optional[str] = None
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
        
        # User context (required, minimum 200 chars already validated)
        if user_context:
            prompt += f"\nUser Context (important background information):\n{user_context}\n"
        
        prompt += "\nPlease provide a comprehensive, professional description of this chart."
        
        return prompt


class OpenAIProvider(AIProvider):
    """OpenAI provider using LangChain."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key (from settings if not provided)
            model: Model name
        """
        self.api_key = api_key
        self.model = model
        self._client = None
    
    def _get_client(self):
        """Get OpenAI client (lazy initialization)."""
        if self._client is None:
            try:
                from langchain_openai import ChatOpenAI
                from django.conf import settings
                api_key = self.api_key or getattr(settings, 'OPENAI_API_KEY', None)
                if not api_key:
                    raise ValueError("OpenAI API key not configured")
                self._client = ChatOpenAI(
                    model_name=self.model,
                    openai_api_key=api_key,
                    temperature=0.7
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
        visualization_type: Optional[str] = None
    ) -> str:
        """Generate description using OpenAI."""
        try:
            from langchain.prompts import ChatPromptTemplate
            
            # Build prompt
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", "You are a data visualization expert. Describe charts clearly and concisely."),
                ("human", self._build_prompt(
                    chart_data, user_context, algorithm_key, source_type, visualization_type
                ))
            ])
            
            client = self._get_client()
            chain = prompt_template | client
            
            # Execute with timeout
            start_time = time.time()
            result = chain.invoke({})
            
            if time.time() - start_time > timeout:
                raise TimeoutError("OpenAI request timed out")
            
            return result.content if hasattr(result, 'content') else str(result)
            
        except Exception as e:
            logger.error(f"OpenAI provider error: {e}")
            raise


class AnthropicProvider(AIProvider):
    """Anthropic provider using LangChain."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-opus-20240229"):
        """
        Initialize Anthropic provider.
        
        Args:
            api_key: Anthropic API key (from settings if not provided)
            model: Model name
        """
        self.api_key = api_key
        self.model = model
        self._client = None
    
    def _get_client(self):
        """Get Anthropic client (lazy initialization)."""
        if self._client is None:
            try:
                from langchain_anthropic import ChatAnthropic
                from django.conf import settings
                api_key = self.api_key or getattr(settings, 'ANTHROPIC_API_KEY', None)
                if not api_key:
                    raise ValueError("Anthropic API key not configured")
                self._client = ChatAnthropic(
                    model=self.model,
                    anthropic_api_key=api_key,
                    temperature=0.7
                )
            except ImportError:
                raise ImportError("langchain-anthropic not installed")
        return self._client
    
    def generate_description(
        self, 
        chart_data: Dict[str, Any], 
        user_context: Optional[str] = None,
        timeout: int = 30,
        algorithm_key: Optional[str] = None,
        source_type: Optional[str] = None,
        visualization_type: Optional[str] = None
    ) -> str:
        """Generate description using Anthropic."""
        try:
            from langchain.prompts import ChatPromptTemplate
            
            # Build prompt
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", "You are a data visualization expert. Describe charts clearly and concisely."),
                ("human", self._build_prompt(
                    chart_data, user_context, algorithm_key, source_type, visualization_type
                ))
            ])
            
            client = self._get_client()
            chain = prompt_template | client
            
            # Execute with timeout
            start_time = time.time()
            result = chain.invoke({})
            
            if time.time() - start_time > timeout:
                raise TimeoutError("Anthropic request timed out")
            
            return result.content if hasattr(result, 'content') else str(result)
            
        except Exception as e:
            logger.error(f"Anthropic provider error: {e}")
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
        visualization_type: Optional[str] = None
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
    Order: OpenAI → Anthropic → Mock
    """
    
    def __init__(self):
        """Initialize router with providers."""
        self.providers = []
        
        # Try to initialize OpenAI
        try:
            self.providers.append(('openai', OpenAIProvider()))
        except Exception as e:
            logger.warning(f"OpenAI provider not available: {e}")
        
        # Try to initialize Anthropic
        try:
            self.providers.append(('anthropic', AnthropicProvider()))
        except Exception as e:
            logger.warning(f"Anthropic provider not available: {e}")
        
        # Always add Mock as fallback
        self.providers.append(('mock', MockProvider()))
    
    def generate_description(
        self,
        chart_data: Dict[str, Any],
        user_context: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        provider_preference: Optional[str] = None,
        algorithm_key: Optional[str] = None,
        source_type: Optional[str] = None,
        visualization_type: Optional[str] = None
    ) -> tuple[str, str]:
        """
        Generate description with fallback.
        
        Args:
            chart_data: Structured chart data
            user_context: User-provided context
            timeout: Timeout per provider
            max_retries: Maximum retries per provider
            provider_preference: Preferred provider name ('openai', 'anthropic', 'mock')
                                If provided, starts from that provider
            algorithm_key: Algorithm identifier
            source_type: Data source type
            visualization_type: Type of visualization
            
        Returns:
            Tuple of (description_text, provider_name)
        """
        # If provider_preference is specified, reorder providers to start with it
        providers_to_try = self.providers.copy()
        if provider_preference:
            # Find preferred provider and move it to the front
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
                logger.warning(f"Provider preference '{provider_preference}' not available, using default order")
        
        for provider_name, provider in providers_to_try:
            # Retry logic with exponential backoff
            for attempt in range(max_retries):
                try:
                    description = provider.generate_description(
                        chart_data, user_context, timeout,
                        algorithm_key, source_type, visualization_type
                    )
                    return description, provider_name
                except Exception as e:
                    logger.warning(
                        f"Provider {provider_name} attempt {attempt + 1} failed: {e}"
                    )
                    if attempt < max_retries - 1:
                        # Exponential backoff
                        wait_time = 2 ** attempt
                        time.sleep(wait_time)
                    else:
                        # Move to next provider
                        break
        
        # Should never reach here (Mock always succeeds)
        raise Exception("All providers failed (including Mock)")

