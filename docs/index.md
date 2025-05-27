# Weni Agents Toolkit

A Python library for creating and managing agent tools for the Weni platform. Build powerful conversational agents with type-safe components and a robust tool system.

## Features

- 🔒 **Type-safe Tools**: Build reliable tools with type checking and validation
- 🛡️ **Immutable Context**: Secure handling of credentials and configuration
- 🧩 **Modular Architecture**: Easily extend and customize tools
- 📝 **Rich Context**: Comprehensive data structures for AI understanding
- ✨ **Built-in Validation**: Automatic validation of responses and data
- 🔌 **Response System**: Simple and intuitive context creation

## Installation

=== "pip"
    ```bash
    pip install weni-agents-toolkit
    ```

=== "Poetry"
    ```bash
    poetry add weni-agents-toolkit
    ```

## Quick Example

```python
from weni import Tool
from weni.context import Context
from weni.responses import TextResponse

class GreetingTool(Tool):
    def execute(self, context: Context) -> TextResponse:
        # Get user information from context
        name = context.parameters.get("name", "Guest")
        language = context.parameters.get("language", "en")
        
        # Return context for the AI to generate an appropriate greeting
        return TextResponse(data={
            "user": {
                "name": name,
                "language": language,
            },
            "time_context": {
                "time_of_day": self._get_time_of_day(),
                "user_timezone": "UTC-3",
                "is_business_hours": True
            },
            "available_actions": [
                "start_conversation",
                "show_help",
                "view_profile"
            ]
        })
```

## Project Status

[![CI](https://github.com/weni-ai/agents-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/weni-ai/agents-toolkit/actions/workflows/ci.yml)
[![CD](https://github.com/weni-ai/agents-toolkit/actions/workflows/cd.yml/badge.svg)](https://github.com/weni-ai/agents-toolkit/actions/workflows/cd.yml)
[![PyPI version](https://badge.fury.io/py/weni-agents-toolkit.svg)](https://badge.fury.io/py/weni-agents-toolkit)
[![Python Versions](https://img.shields.io/pypi/pyversions/weni-agents-toolkit.svg)](https://pypi.org/project/weni-agents-toolkit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) 