# Context System

The Context system is a fundamental part of the Weni Agents Toolkit, providing a secure and immutable way for skills to access data they need during execution.

## Overview

When a skill's `execute` method is called, it receives a Context object containing three main sections:
- **credentials**: Secure storage for sensitive data like API keys
- **parameters**: Skill-specific input parameters
- **globals**: Project-wide configuration values

## Using Context in Skills

### Basic Context Usage

```python
from weni import Skill
from weni.context import Context
from weni.responses import TextResponse

class WeatherSkill(Skill):
    def execute(self, context: Context) -> TextResponse:
        # Access API credentials securely
        api_key = context.credentials.get("weather_api_key", "")
        
        # Get user parameters
        city = context.parameters.get("city", "")
        units = context.parameters.get("units", "metric")
        
        # Get global configuration
        api_url = context.globals.get("weather_api_url")
        
        # Use the data to fetch weather information
        weather_data = self._fetch_weather(api_url, city, api_key, units)
        
        return TextResponse(data=weather_data)
```

## Accessing Context Data

### Safe Data Access

Always use the `get()` method to safely access data with defaults:

```python
class OrderSkill(Skill):
    def execute(self, context: Context) -> TextResponse:
        # Safe access with defaults
        user_id = context.parameters.get("user_id", "anonymous")
        api_key = context.credentials.get("api_key", "")
        base_url = context.globals.get("api_url", "https://default-url.com")
```

### Type Hints

Use type hints for better code safety:

```python
from typing import Optional, Dict, Any

class ProfileSkill(Skill):
    def execute(self, context: Context) -> TextResponse:
        user_id: str = context.parameters.get("user_id", "")
        settings: Dict[str, Any] = context.globals.get("settings", {})
        api_key: Optional[str] = context.credentials.get("api_key")
```
