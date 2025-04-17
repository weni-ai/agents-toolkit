# Tools

## Overview

Tools are the core executable units in the Weni Agents Toolkit. They encapsulate specific functionality and can be combined to create complex conversational flows.

## Creating a Tool

```python
from weni import Tool
from weni.context import Context
from weni.responses import TextResponse
from typing import Optional

class CustomTool(Tool):
    def execute(self, context: Context) -> TextResponse:
        # Implementation here
        pass
```

## Tool Lifecycle

1. **Initialization**: Tool instance is created
2. **Context Reception**: Tool receives execution context
3. **Execution**: Business logic is processed
4. **Response Generation**: Tool generates appropriate response

## Best Practices

### 1. Type Safety

Always use type hints:

```python
from typing import Any

class WeatherTool(Tool):
    def execute(self, context: Context) -> Response:
        location: str = context.parameters.get("location", "")
        return TextResponse(data=self._get_weather(location))

    def _get_weather(self, location: str) -> dict[str, Any]:
        # Implementation
        pass
```

### 2. Error Handling

Always return a response, even if it's an error response, this will allow the AI to continue the conversation:

```python
from weni.exceptions import ToolError

class APITool(Tool):
    def execute(self, context: Context) -> Response:
        try:
            # API call
            pass
        except Exception as e:
            return TextResponse(data={"error": "API call failed"})
```
