# Responses

## Overview

Responses in the Weni Agents Toolkit are containers for data that will be used by the AI agent to generate appropriate text responses. Each response type is designed to provide context for different kinds of interactions.

## Response Types

### Text Response

Simple text context:

```python
from weni.responses import TextResponse

response = TextResponse(
    data={
        "weather": "sunny",
        "temperature": "25°C",
        "location": "New York"
    }
)
```

### Quick Reply Response

Context for interactive decisions:

```python
from weni.responses import QuickReplyResponse

response = QuickReplyResponse(
    data={
        "user_preference": "vegetarian",
        "available_restaurants": [
            "Green Garden",
            "Veggie House",
            "Fresh Bites"
        ],
        "meal_time": "lunch"
    }
)
```

### List Message Response

Context for multiple options:

```python
from weni.responses import ListMessageResponse

response = ListMessageResponse(
    data={
        "product_category": "smartphones",
        "price_range": "500-1000",
        "available_items": [
            {
                "name": "Phone Model A",
                "price": 599,
                "specs": {"ram": "8GB", "storage": "128GB"}
            },
            {
                "name": "Phone Model B",
                "price": 799,
                "specs": {"ram": "12GB", "storage": "256GB"}
            }
        ]
    }
)
```

## Best Practices

### 1. Provide Rich Context

Include relevant information that helps the AI generate better responses:

```python
response = TextResponse(
    data={
        "user_name": "John",
        "user_history": ["previous_purchases", "browsing_preferences"],
        "current_intent": "product_recommendation",
        "product_category": "electronics"
    }
)
```

### 2. Type Safety

Use type hints:

```python
from typing import Dict, Any

def create_response(context_data: Dict[str, Any]) -> TextResponse:
    return TextResponse(data=context_data)
```

### 3. Data Structure

Keep data structured and organized:

```python
response = TextResponse(
    data={
        "user": {
            "name": "Alice",
            "preferences": ["books", "music"],
            "language": "en"
        },
        "query": {
            "type": "recommendation",
            "category": "books",
            "filters": {
                "genre": "science fiction",
                "max_price": 20
            }
        }
    }
)
```

### 4. Immutability

Responses are immutable after creation:

```python
response = TextResponse(data={"context": "initial"})
response.data = {}  # Error: can't modify response
```

## Important Notes

!!! note
    The `data` attribute is the only required field for responses. This data serves as context for the AI agent to generate appropriate text responses.

!!! tip
    Provide as much relevant context as possible in the `data` attribute to help the AI generate more accurate and contextual responses.

!!! warning
    The response object itself doesn't contain the final text - it provides the context for the AI to generate the text. 