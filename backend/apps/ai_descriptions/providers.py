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
        timeout: int = 30
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
    
    def _build_prompt(self, chart_data: Dict[str, Any], user_context: Optional[str]) -> str:
        """
        Build prompt from chart_data and user_context.
        
        This is a shared implementation used by all AI providers.
        
        Args:
            chart_data: Structured chart data
            user_context: User-provided context
            
        Returns:
            Formatted prompt string
        """
        prompt = f"Describe this chart:\n\n"
        prompt += f"Chart Type: {chart_data.get('type', 'unknown')}\n"
        prompt += f"Title: {chart_data.get('title', 'Untitled')}\n"
        
        if 'series' in chart_data:
            prompt += f"Series: {len(chart_data['series'])} data series\n"
        
        if 'totals' in chart_data:
            totals = chart_data['totals']
            for key, value in totals.items():
                if value is not None:
                    prompt += f"{key}: {value}\n"
        
        if user_context:
            prompt += f"\nUser Context: {user_context}\n"
        
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
        timeout: int = 30
    ) -> str:
        """Generate description using OpenAI."""
        try:
            from langchain.prompts import ChatPromptTemplate
            
            # Build prompt
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", "You are a data visualization expert. Describe charts clearly and concisely."),
                ("human", self._build_prompt(chart_data, user_context))
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
        timeout: int = 30
    ) -> str:
        """Generate description using Anthropic."""
        try:
            from langchain.prompts import ChatPromptTemplate
            
            # Build prompt
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", "You are a data visualization expert. Describe charts clearly and concisely."),
                ("human", self._build_prompt(chart_data, user_context))
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
    """Mock provider for MVP - returns hardcoded text."""
    
    def generate_description(
        self, 
        chart_data: Dict[str, Any], 
        user_context: Optional[str] = None,
        timeout: int = 30
    ) -> str:
        """Generate mock description."""
        chart_type = chart_data.get('type', 'chart')
        title = chart_data.get('title', 'Chart')
        
        description = f"This is a {chart_type} chart titled '{title}'. "
        
        if 'totals' in chart_data:
            totals = chart_data['totals']
            if 'total_publications' in totals:
                description += f"It shows {totals['total_publications']} total publications. "
        
        if user_context:
            description += f"User context: {user_context}. "
        
        description += "This is a mock description for MVP testing."
        
        return description


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
        provider_preference: Optional[str] = None
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
                    description = provider.generate_description(chart_data, user_context, timeout)
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

