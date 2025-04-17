# Core Concepts

## Tools

Tools are the fundamental building blocks of the Weni Agents Toolkit. Each tool is a self-contained unit of functionality that can:

- Process user input
- Execute business logic
- Generate appropriate responses with context for the AI agent

```python
from weni import Tool
from weni.context import Context
from weni.responses import TextResponse

class WeatherTool(Tool):
    def execute(self, context: Context) -> TextResponse:
        # Tool implementation that returns context for the AI agent
        city = context.parameters.get("city", "")
        weather_data = self._fetch_weather(city)
        
        return TextResponse(data={
            "city": city,
            "temperature": weather_data["temp"],
            "conditions": weather_data["conditions"],
            "forecast": weather_data["next_24h"]
        })
```

## Context System

The Context system provides a secure, immutable container for passing data to tools:

```python
context = Context(
    credentials={"api_key": "secret123"},     # Sensitive data
    parameters={"city": "New York"},          # Tool parameters
    globals={"api_url": "https://api.example.com"}  # Global configuration
)
```

## Responses

Responses encapsulate the context data that will be used by the AI agent to generate appropriate responses:

```python
from weni.responses import QuickReplyResponse

# The data contains context about a user's order confirmation
response = QuickReplyResponse(
    data={
        "order_id": "12345",
        "items": [
            {"name": "Product A", "quantity": 2, "price": 29.99},
            {"name": "Product B", "quantity": 1, "price": 49.99}
        ],
        "total": 109.97,
        "shipping_method": "express",
        "estimated_delivery": "2024-02-15"
    }
)
```

## Key Principles

1. **Tools** are responsible for:
   - Processing inputs
   - Executing business logic
   - Gathering relevant context
   - Returning responses with context data

2. **Context** provides:
   - Secure credential storage
   - Tool-specific parameters
   - Global configuration
   - Immutable data access

3. **Responses** contain:
   - Rich context data for AI processing
   - Structured information
   - Relevant metadata
   - Business logic results

!!! note "Response Data"
    Remember that responses don't contain the final message text. Instead, they provide the context and data that the AI agent will use to generate appropriate responses for users.
