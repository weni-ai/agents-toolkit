# Quick Start

## Creating Your First Tool

Let's create a simple greeting tool that provides user context:

```python
from weni import Tool
from weni.context import Context
from weni.responses import TextResponse

class GreetingTool(Tool):
    def execute(self, context: Context) -> TextResponse:
        name = context.parameters.get("name", "Guest")
        time_of_day = self._get_time_of_day()
        
        return TextResponse(data={
            "user_name": name,
            "time_of_day": time_of_day,
            "is_returning_user": name != "Guest",
            "available_actions": ["start_conversation", "show_menu", "get_help"]
        })
```

## Using Quick Replies

Here's how to create a tool that provides context for decision-making:

```python
from weni.responses import QuickReplyResponse

class ConfirmationTool(Tool):
    def execute(self, context: Context) -> QuickReplyResponse:
        order_id = context.parameters.get("order_id")
        order_details = self._get_order_details(order_id)
        
        return QuickReplyResponse(
            data={
                "order_id": order_id,
                "order_status": order_details["status"],
                "total_amount": order_details["total"],
                "items_count": len(order_details["items"]),
                "requires_confirmation": True,
                "confirmation_deadline": "2024-02-15T18:00:00Z",
                "user_preferences": {
                    "preferred_payment": "credit_card",
                    "previous_responses": ["confirmed", "on_time"]
                }
            }
        )
```

## Working with Context

The Context object provides access to:
- Credentials (API keys, tokens)
- Parameters (tool-specific inputs)
- Globals (project-wide settings)

```python
class WeatherTool(Tool):
    def execute(self, context: Context) -> TextResponse:
        # Access API key from credentials
        api_key = context.credentials.get("weather_api_key")
        
        # Get location from parameters
        city = context.parameters.get("city")
        
        # Get API URL from globals
        api_url = context.globals.get("weather_api_url")
        
        # Fetch weather data
        weather_data = self._fetch_weather_data(api_url, city, api_key)
        
        # Return context for the AI to generate a weather response
        return TextResponse(data={
            "location": {
                "city": city,
                "country": weather_data["country"],
                "timezone": weather_data["timezone"]
            },
            "current_conditions": {
                "temperature": weather_data["temp"],
                "feels_like": weather_data["feels_like"],
                "humidity": weather_data["humidity"],
                "wind_speed": weather_data["wind_speed"],
                "description": weather_data["description"]
            },
            "forecast": weather_data["next_24h"],
            "alerts": weather_data.get("alerts", []),
            "last_updated": weather_data["timestamp"]
        })
```

## Next Steps

- Learn more about [Core Concepts](core-concepts.md)
- Explore available [Response Types](../user-guide/responses.md)
- Understand the [Context System](../user-guide/context.md)

!!! tip "Context is Key"
    Remember that tools should provide rich, structured context data that helps the AI agent generate appropriate responses. The more relevant context you provide, the better the AI can understand the situation and respond accordingly. 