# Broadcasts

The Broadcasts module allows tools to send WhatsApp messages to contacts during execution via the Flows WhatsApp Broadcasts API.

## Quick Start

```python
from weni import Tool
from weni.context import Context
from weni.broadcasts import Text
from weni.responses import FinalResponse

class MyTool(Tool):
    def execute(self, context: Context):
        self.broadcasts.send(Text(text="Processing your request..."))
        return FinalResponse()
```

`self.broadcasts` is a `Broadcast` instance pre-bound to the tool. It is created on first access and cached for the duration of the execution.

## Calling Styles

All three styles are equivalent. Choose whichever fits your convention:

```python
# Namespaced (recommended) — available via self.<name> on any Tool
self.broadcasts.send(Text(text="Hello!"))
self.broadcasts.send_many([Text(text="Step 1"), Text(text="Step 2")])

# Shorthand — mirrors the old API, resolved through the same facade
self.send_broadcast(Text(text="Hello!"))

# Explicit — pass the tool instance yourself
from weni.broadcasts import Broadcast
Broadcast(self).send(Text(text="Hello!"))
```

## How It Works

```
   Tool.execute()                         SQS queue              Flows worker
   ──────────────                         ─────────              ────────────
   self.broadcasts.send(Text("Hello"))
        │
        ├── _register_operation("messages_sent", payload)
        │
        ▼
   BroadcastSender
   sends message to SQS ──────────────────────► consumer reads
                                                      │
                                                      ▼
                                               POST /api/v2/whatsapp_broadcasts.json
                                                      │
                                                      ▼
                                               Mailroom / Courier
                                                      │
                                                      ▼
                                               Message delivered to contact
```

1. `send()` registers the payload in the tool's `_pending_operations` log and enqueues it on SQS — execution continues immediately (non-blocking).
2. A Flows SQS consumer reads the queue and POSTs to the WhatsApp Broadcasts endpoint.
3. Flows queues delivery via Mailroom/Courier.

## Message Types

### Text

Simple text message.

```python
self.broadcasts.send(Text(text="Hello! How can I help you?"))
```

### QuickReply

Message with quick reply buttons.

```python
from weni.broadcasts import QuickReply

self.broadcasts.send(QuickReply(
    text="Do you want to continue?",
    options=["Yes", "No", "Maybe"],
    header="Question",    # optional
    footer="Tap to select"  # optional
))
```

### Attachment

Message with a media attachment.

```python
from weni.broadcasts import Attachment

self.broadcasts.send(Attachment(
    attachment="image/jpeg:https://example.com/photo.jpg",
    text="Here is your receipt",  # optional caption
))
```

### ListMessage

Interactive list picker.

```python
from weni.broadcasts import ListMessage

self.broadcasts.send(ListMessage(
    text="Select a category",
    button_text="Open list",
    list_items=[
        {"title": "Electronics", "description": "Phones, tablets"},
        {"title": "Clothing", "description": "Shirts, shoes"},
    ],
    header="Categories",  # optional
    footer="Scroll for more",  # optional
))
```

### WhatsAppCarousel

Horizontally scrollable card carousel.

```python
from weni.broadcasts import WhatsAppCarousel

self.broadcasts.send(WhatsAppCarousel(
    text="Choose a product",
    attachments=[],
    carousel=[
        {
            "header": {"type": "image", "image": {"link": "https://…/img.jpg"}},
            "body": {"text": "Product A"},
            "buttons": [{"type": "reply", "reply": {"id": "A", "title": "Select A"}}],
        },
    ],
))
```

### OneClickPayment

WhatsApp order-details message with a saved card.

```python
from weni.broadcasts import OneClickPayment

self.broadcasts.send(OneClickPayment(
    text="Confirm payment with your saved card ending in 1234?",
    reference_id="ORDER-001",
    total_amount=19990,
    items=[{"retailer_id": "SKU-1", "name": "T-shirt", "amount": {"value": 19990, "offset": 100}, "quantity": 1}],
    subtotal=19990,
    tax={"description": "Tax", "offset": 100, "value": 0},
    discount={"description": "Discount", "offset": 100, "value": 0},
    shipping={"description": "Shipping", "offset": 100, "value": 0},
    last_four_digits="1234",
    credential_id="cred-uuid",
))
```

### PixPayment

WhatsApp PIX payment message.

```python
from weni.broadcasts import PixPayment

self.broadcasts.send(PixPayment(
    text="Copy the PIX code below to complete payment.",
    footer="Thank you for your purchase",
    reference_id="ORDER-001",
    total_amount=34990,
    pix_key="7d4e8f2a-3b1c-4d5e-9f6a-8b7c2d1e0f3a",
    pix_key_type="EVP",
    merchant_name="My Store",
    pix_code="00020126…",
    items=[],
    subtotal=29990,
    tax={"description": "Tax", "offset": 100, "value": 0},
    discount={"description": "Discount", "offset": 100, "value": 1500},
    shipping={"description": "Shipping", "offset": 100, "value": 6500},
))
```

### WhatsAppFlows

Opens a WhatsApp Flow screen in-conversation.

```python
from weni.broadcasts import WhatsAppFlows

self.broadcasts.send(WhatsAppFlows(
    text="You have a pending confirmation.",
    flow_id="1451561746318256",
    flow_cta="Confirm now",
    flow_screen="CONFIRM_SCREEN",
    flow_data={"order_value": "R$ 150.00"},
    flow_token="optional-token",  # optional
))
```

## Sending Multiple Messages

```python
self.broadcasts.send_many([
    Text(text="Step 1: Processing…"),
    Text(text="Step 2: Complete!"),
])
```

## Configuration

The sender reads configuration from the execution context automatically:

| Config | Source priority | Description |
|--------|----------------|-------------|
| `auth_token` | `project` | `Authorization: Bearer` header |
| `flows_url` | project / credentials / globals / env `FLOWS_BASE_URL` | Flows API base URL |
| `channel_uuid` | project / credentials / contact / globals / env | WhatsApp channel UUID |
| Contact URN | `contact.urns` → `contact.urn` → `parameters.contact_urn` | Message recipient |

## Isolation

Each tool execution gets its own `_pending_operations` dict. Because `Broadcast` receives `self` (the tool instance), messages from one Lambda invocation never leak into another, even on warm starts.

## Response Shape

`Tool.__new__()` always includes `messages_sent` in the result:

```python
{
    "result": <data>,
    "messages_sent": [<broadcast payload>, …]
}
```

The list is empty when no broadcast was sent.

## Error Handling

```python
from weni.broadcasts.sender import BroadcastSenderError, BroadcastSenderConfigError

try:
    self.broadcasts.send(Text(text="Hello!"))
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
