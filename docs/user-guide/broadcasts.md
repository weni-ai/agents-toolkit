# Broadcasts

The Broadcasts module allows tools to send WhatsApp messages to contacts during execution via the Flows WhatsApp Broadcasts API.

## Quick Start

```python
from weni import Tool
from weni.context import Context
from weni.broadcasts import Broadcast, Text
from weni.responses import FinalResponse

class MyTool(Tool):
    def execute(self, context: Context):
        Broadcast.send(Text(text="Processing your request..."))
        result = do_work()
        return FinalResponse()
```

No manual configuration needed. `Tool.__new__()` automatically configures the broadcast sender using the execution context.

## How It Works

```
   Tool Lambda                          Flows API                WhatsApp
   ───────────                          ─────────                ────────
   Broadcast.send(Text("Hello"))
        │
        ▼
   BroadcastSender
   POST /api/v2/whatsapp_broadcasts.json ──────► Creates Broadcast
        │                                              │
        │                                              ▼
        │                                        Mailroom/Courier
        │                                              │
        ▼                                              ▼
   return FinalResponse()                     Message delivered
```

1. `Broadcast.send()` makes an HTTP POST to the Flows WhatsApp Broadcasts API
2. Flows creates the broadcast and queues it via Mailroom
3. Courier delivers the message to the contact via WhatsApp

## Message Types

### Text

Simple text message.

```python
from weni.broadcasts import Text

Broadcast.send(Text(text="Hello! How can I help you?"))
```

### QuickReply

Message with quick reply buttons.

```python
from weni.broadcasts import QuickReply

Broadcast.send(QuickReply(
    text="Do you want to continue?",
    options=["Yes", "No", "Maybe"],
    header="Question",   # optional
    footer="Tap to select"  # optional
))
```

## Sending Multiple Messages

```python
Broadcast.send_many([
    Text(text="Step 1: Processing..."),
    Text(text="Step 2: Complete!"),
])
```

## Configuration

The sender reads configuration from the Context automatically:

| Config | Source | Description |
|--------|--------|-------------|
| `auth_token` | `context.project` | Bearer token for Flows API |
| `flows_url` | context or `FLOWS_BASE_URL` env var | Flows API base URL |
| `channel_uuid` | context (project/credentials/contact) | WhatsApp channel UUID |
| Contact URN | `contact.urns` > `contact.urn` > `parameters.contact_urn` | Recipient URN |

### Config Resolution Priority

`project > credentials > contact > globals > environment variables`

## Response Types

### With FinalResponse

```python
class MyTool(Tool):
    def execute(self, context: Context):
        Broadcast.send(Text(text="Hello!"))
        return FinalResponse()
# Result: {"is_final_output": true, "messages": [{"text": "Hello!"}]}
```

### With TextResponse (or any other Response)

Broadcasts are automatically included in the result when present:

```python
class MyTool(Tool):
    def execute(self, context: Context):
        Broadcast.send(Text(text="Processing..."))
        return TextResponse(data="done")
# Result: {"result": "done", "messages": [{"text": "Processing..."}]}
```

## Error Handling

```python
from weni.broadcasts import BroadcastSenderError, BroadcastSenderConfigError

try:
    Broadcast.send(Text(text="Hello!"))
except BroadcastSenderConfigError as e:
    print(f"Configuration error: {e}")
except BroadcastSenderError as e:
    print(f"Send error: {e}")
```

If the sender is not configured (e.g., missing credentials), `Broadcast.send()` silently registers the message without sending. The tool continues to work normally.

## Test Definition

For testing via `weni run`, pass config through `project` and `contact`:

```yaml
tests:
    test_broadcast:
        parameters:
            text: "Hello from broadcast"
        project:
            auth_token: "your-token-here"
        contact:
            urn: "whatsapp:5584988242399"
            channel_uuid: "your-channel-uuid"
```
