# Weni Agents Toolkit

[![CI](https://github.com/weni-ai/agents-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/weni-ai/agents-toolkit/actions/workflows/ci.yml)
[![CD](https://github.com/weni-ai/agents-toolkit/actions/workflows/cd.yml/badge.svg)](https://github.com/weni-ai/agents-toolkit/actions/workflows/cd.yml)
[![PyPI version](https://badge.fury.io/py/weni-agents-toolkit.svg)](https://badge.fury.io/py/weni-agents-toolkit)
[![Python Versions](https://img.shields.io/pypi/pyversions/weni-agents-toolkit.svg)](https://pypi.org/project/weni-agents-toolkit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python library for creating and managing agent skills for the Weni platform. Build powerful conversational agents with type-safe components and a robust skill system.

## Installation

```bash
pip install weni-agents-toolkit
```

Or with Poetry:
```bash
poetry add weni-agents-toolkit
```

## Quick Start

### Creating a Skill

```python
import requests
from weni import Skill
from weni.context import Context
from weni.components import Text, QuickReplies
from weni.data import register_result

class GetAddress(Skill):

    def execute(self, context: Context):
        # This is how we would retrieve credentials or sensitive information from context
        token = context.credentials.get("X-App-Token")

        # This is how we would retrieve parameters for this agent tool
        cep = context.parameters.get("cep")

        # This is how we would retrieve global constants for this project
        api_url = context.globals.get("cep_api_url")

        # This block is the business logic for the sake of this example on retrieving an address based on the received CEP
        base_url = f"{api_url}/{cep}"
        response = requests.get(base_url, headers={"Authorization": f"Bearer {token}"})

        result = response.json()

        # This block is where data is registered for further analysis in the future
        register_result("address", result.get("street"))

        # This example I'm respoonding allowing quick replies message or a location
        return TextResponse(data=result)
```

## Core Concepts

### Context System

The context system provides secure access to:
```python
context = Context(
    credentials={"api_key": "secret123"},     # Sensitive data
    parameters={"user_id": "123"},            # Skill parameters
    globals={"env": "production"}             # Global configuration
)
```

### Available Components

- `Text`: Basic text messages
- `QuickReplies`: Interactive quick reply buttons
- `ListMessage`: Interactive list menus
- `CTAMessage`: Call-to-action messages
- `Location`: Location request messages
- `OrderDetails`: Order information messages
- `Attachments`: File attachments
- `Header`: Message headers
- `Footer`: Message footers

### Response Types

- `TextResponse`: Simple text messages
- `QuickReplyResponse`: Messages with quick reply buttons
- `ListMessageResponse`: Interactive list menus
- `CTAMessageResponse`: Call-to-action messages
- `LocationResponse`: Location-based messages
- `OrderDetailsResponse`: Order information displays

## Development

### Prerequisites

- Python 3.9+
- Poetry

### Setup

1. Clone the repository:
```bash
git clone https://github.com/weni-ai/agents-toolkit.git
cd agents-toolkit
```

2. Install dependencies:
```bash
poetry install
```

3. Run tests:
```bash
poetry run pytest
```

### Code Quality

We use several tools to ensure code quality:

- `pytest` for testing
- `mypy` for type checking
- `ruff` for linting

Run all checks:
```bash
poetry run pytest
poetry run mypy weni
poetry run ruff check .
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
