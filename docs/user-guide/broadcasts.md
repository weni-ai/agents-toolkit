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
        Broadcast(self).send(Text(text="Processing your request..."))
        return FinalResponse()
```

`Broadcast(self)` receives the tool instance, which provides the execution context and broadcast isolation between Lambda invocations.

## How It Works

```
   Tool.execute()                        Flows API                WhatsApp
   ──────────────                        ─────────                ────────
   Broadcast(self).send(Text("Hello"))
        │
        ├── register on tool._pending_broadcasts
        │
        ▼
   BroadcastSender
   POST /api/v2/whatsapp_broadcasts.json ──────► Creates Broadcast
                                                       │
                                                       ▼
                                                 Mailroom/Courier
                                                       │
                                                       ▼
   return FinalResponse()                      Message delivered
```

1. `Broadcast(self).send()` registers the message on the tool and POSTs to the Flows API
2. Flows creates the broadcast and queues it via Mailroom
3. Courier delivers the message to the contact via WhatsApp

## Message Types

### Text

Simple text message.

```python
Broadcast(self).send(Text(text="Hello! How can I help you?"))
```

### QuickReply

Message with quick reply buttons.

```python
from weni.broadcasts import QuickReply

Broadcast(self).send(QuickReply(
    text="Do you want to continue?",
    options=["Yes", "No", "Maybe"],
    header="Question",   # optional
    footer="Tap to select"  # optional
))
```

## Sending Multiple Messages

```python
Broadcast(self).send_many([
    Text(text="Step 1: Processing..."),
    Text(text="Step 2: Complete!"),
])
```

## Configuration

The sender reads configuration from the execution context automatically:

| Config | Source priority | Description |
|--------|----------------|-------------|
| `auth_token` | `project` | `Authorization: Bearer` header |
| `flows_url` | project / credentials / contact / globals / env `FLOWS_BASE_URL` | Flows API base URL |
| `channel_uuid` | project / credentials / contact / globals / env | WhatsApp channel UUID |
| Contact URN | `contact.urns` > `contact.urn` > `parameters.contact_urn` | Message recipient |

## Isolation

Each tool execution gets its own `_pending_broadcasts` list. The `Broadcast` class receives `self` (the tool instance), so broadcasts from one Lambda invocation never leak into another, even on warm starts.

## Response Types

### With FinalResponse

```python
class MyTool(Tool):
    def execute(self, context: Context):
        Broadcast(self).send(Text(text="Hello!"))
        return FinalResponse()
```

### With TextResponse (or any other Response)

Broadcasts are included in the result automatically:

```python
class MyTool(Tool):
    def execute(self, context: Context):
        Broadcast(self).send(Text(text="Processing..."))
        return TextResponse(data="done")
```

In both cases, `Tool.__new__()` wraps the result as `{"result": <data>, "messages_sent": [<broadcasts>]}`.

## Error Handling

```python
from weni.broadcasts import BroadcastSenderError, BroadcastSenderConfigError

try:
    Broadcast(self).send(Text(text="Hello!"))
except BroadcastSenderConfigError as e:
    print(f"Configuration error: {e}")
except BroadcastSenderError as e:
    print(f"Send error: {e}")
```

## Test Definition

For testing via `weni run`, pass config through `project` and `contact`:

```yaml
tests:
    test_broadcast:
        parameters:
            text: "Hello from broadcast"
        project:
            auth_token: "your-jwt-token"
        contact:
            urn: "whatsapp:5584988242399"
            channel_uuid: "your-channel-uuid"
```
