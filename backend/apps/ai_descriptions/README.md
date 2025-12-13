# AI Descriptions App

AI-powered chart description generation using LangChain with provider routing and fallback.

## Modules

### `providers.py`
AI provider implementations:
- `AIProvider`: Abstract base class
  - Method: `generate_description(chart_data, user_context, timeout) -> str`
- `OpenAIProvider`: OpenAI via LangChain
  - Uses `langchain_openai.ChatOpenAI`
  - Configurable model and timeout
- `AnthropicProvider`: Anthropic via LangChain
  - Uses `langchain_anthropic.ChatAnthropic`
  - Configurable model and timeout
- `MockProvider`: Mock for MVP
  - Returns hardcoded description text
- `AIProviderRouter`: Router with fallback
  - Order: OpenAI → Anthropic → Mock
  - Retry logic: max 3 attempts with exponential backoff per provider
  - Timeout: 30s per call (configurable)
  - Returns: `(description_text, provider_name)`

### `tasks.py`
Celery task:
- `generate_description_task(description_task_id)`: Generates AI description
  - Gets `chart_data` from `ImageTask`
  - Uses `AIProviderRouter` with retries/backoff
  - Updates `DescriptionTask` with result
  - Uses `emit_event()` for tracing
  - Checks cancellation

## Usage

Generate description:
```python
from apps.ai_descriptions.providers import AIProviderRouter

router = AIProviderRouter()
description, provider = router.generate_description(
    chart_data={"type": "bar", "series": [...]},
    user_context="Describe this chart",
    timeout=30,
    max_retries=3
)
```

Enqueue task:
```python
from apps.ai_descriptions.tasks import generate_description_task
generate_description_task.delay(description_task_id)
```

