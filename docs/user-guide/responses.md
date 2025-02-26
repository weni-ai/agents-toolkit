# Responses

## Overview

Responses in the Weni Agents Toolkit are containers for data that will be used by the AI agent to generate appropriate text responses. Each response type is designed to provide context for different kinds of interactions and features a specific set of components (like text, buttons, attachments) that determine how the content will be displayed.


## Header Types

For some responses that support headers, you can specify the type of header using the `HeaderType` enum:

```python
from weni.responses import HeaderType

# Available header types
HeaderType.TEXT        # Text-based header
HeaderType.ATTACHMENTS # Attachment-based header (images, files, etc.)
HeaderType.NONE        # No header (default)
```

## Response Types

### Text Response

Simple text response with a single text component:

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

**Parameters:**
- `data`: Dictionary containing context information for the agent to generate a response

### Attachment Response

Response with media attachments such as images, documents, or videos:

```python
from weni.responses import AttachmentResponse

response = AttachmentResponse(
    data={
        "attachments": [{
            "type": "image",
            "url": "https://example.com/image.jpg"
        }],
    },
    text=True,   # Include a text component
    footer=True  # Include a footer component
)
```

**Parameters:**
- `data`: Dictionary containing context information for the agent to generate a response
- `text` (bool): Whether to include a text component (default: False)
- `footer` (bool): Whether to include a footer component (default: False)

### Quick Reply Response

Interactive response with quick reply buttons:

```python
from weni.responses import QuickReplyResponse, HeaderType

response = QuickReplyResponse(
    data={
        "user_preference": "vegetarian",
        "available_restaurants": [
            "Green Garden",
            "Veggie House",
            "Fresh Bites"
        ]
    },
    header_type=HeaderType.TEXT, # Include a text header component
    footer=True # Include a footer component
)
```

**Parameters:**
- `data`: Dictionary containing context information for the agent to generate a response
- `header_type` (HeaderType): Type of header to display (default: HeaderType.NONE)
- `footer` (bool): Whether to include a footer (default: False)

### List Message Response

Response with a structured list of items:

```python
from weni.responses import ListMessageResponse, HeaderType

response = ListMessageResponse(
    data={
        "product_category": "smartphones",
        "price_range": "500-1000"
    },
    header_type=HeaderType.ATTACHMENTS, # Include an attachment header component
    footer=True # Include a footer component
)
```

**Parameters:**
- `data`: Dictionary containing context information for the agent to generate a response
- `header_type` (HeaderType): Type of header to display (default: HeaderType.NONE)
- `footer` (bool): Whether to include a footer (default: False)

### CTA Message Response

Response with call-to-action buttons:

```python
from weni.responses import CTAMessageResponse

response = CTAMessageResponse(
    data={
        "text": "Would you like to proceed with your order?",
        "buttons": [
            {"title": "Yes, confirm", "payload": "confirm_order"},
            {"title": "No, cancel", "payload": "cancel_order"}
        ],
        "header": {"type": "text", "content": "Order Confirmation"},
        "footer": {"text": "Your order total is $45.99"}
    },
    header=True, # Include a header component
    footer=True # Include a footer component
)
```

**Parameters:**
- `data`: Dictionary containing context information for the agent to generate a response
- `header` (bool): Whether to include a header component (default: False)
- `footer` (bool): Whether to include a footer component (default: False)

### Order Details Response

Response with structured order information:

```python
from weni.responses import OrderDetailsResponse

response = OrderDetailsResponse(
    data={
        "order_id": "ORD-12345",
        "items": [
            {"name": "Product A", "quantity": 2, "price": 19.99},
            {"name": "Product B", "quantity": 1, "price": 9.99}
        ],
        "total": 49.97,
        "status": "Processing",
        "customer_info": {
            "name": "John Doe",
            "address": "123 Main St, City"
        }
    },
    attachments=True, # Include an attachment component
    footer=True # Include a footer component
)
```

**Parameters:**
- `data`: Dictionary containing context information for the agent to generate a response
- `attachments` (bool): Whether to include attachments (default: False)
- `footer` (bool): Whether to include a footer (default: False)

### Location Response

Response requesting location information:

```python
from weni.responses import LocationResponse

response = LocationResponse(
    data={
        "location_request": {
            "required": True,
        }
    }
)
```

**Parameters:**
- `data`: Dictionary containing context information for the agent to generate a response

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

Use type hints to improve code quality and IDE support:

```python
from typing import Dict, Any
from weni.responses import TextResponse

def create_response(context_data: Dict[str, Any]) -> TextResponse:
    return TextResponse(data=context_data)
```

### 3. Structured Data Organization

Keep data structured and organized for better AI comprehension:

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

### 4. Component Configuration

Configure components based on the requirements of your interaction:

```python
# For a rich interactive experience
response = QuickReplyResponse(
    data={...},
    header_type=HeaderType.ATTACHMENTS,  # Include an image header
    footer=True                          # Include a footer
)

# For a simpler experience
response = QuickReplyResponse(
    data={...},
    header_type=HeaderType.NONE,         # No header
    footer=False                         # No footer
)
```

## Important Notes

!!! note
    The `data` attribute is the only required field for responses. This data serves as context for the AI agent to generate appropriate text responses.

!!! tip
    Provide as much relevant context as possible in the `data` attribute to help the AI generate more accurate and contextual responses.

!!! warning
    The response object itself doesn't contain the final text - it provides the context for the AI to generate the text.
