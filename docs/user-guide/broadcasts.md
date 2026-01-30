# Broadcasts

The Broadcasts module provides message types and functionality for sending WhatsApp messages asynchronously during tool execution.

Messages are sent to an **SQS queue** and processed by a Flows worker, providing:
- **Near-zero latency** (~5-10ms to enqueue)
- **100% delivery guarantee** (SQS persists the message)
- **No blocking** of tool execution

## Quick Start

```python
from weni.broadcasts import Broadcast, Text, Attachment

class MyTool(Tool):
    def execute(self, context: Context):
        # Configure the broadcast sender (required once)
        Broadcast.configure(context)
        
        # Send immediate feedback to user
        Broadcast.send(Text(text="Processing your request..."))
        
        # Do some work...
        result = some_api_call()
        
        # Send an attachment
        Broadcast.send(Attachment(
            text="Here's the result",
            image="https://example.com/image.png"
        ))
        
        return FinalResponse()
```

## Configuration

Before using `Broadcast.send()`, you must call `Broadcast.configure(context)` to initialize the sender.

The sender reads configuration from the Context in this priority:
1. `context.project`
2. `context.credentials`
3. `context.globals`
4. Environment variables

### Required Configuration

| Key | Environment Variable | Description |
|-----|---------------------|-------------|
| `sqs_queue_url` | `BROADCAST_SQS_QUEUE_URL` | The SQS queue URL for broadcast messages |
| `flows_url` | `FLOWS_BASE_URL` | The Flows API base URL |

### Optional Configuration

| Key | Description |
|-----|-------------|
| `flows_jwt` or `jwt` | JWT token for Flows API authentication |
| `project_uuid` | Project UUID for identification |

### Example Context Configuration

```python
context = Context(
    project={
        "sqs_queue_url": "https://sqs.us-east-1.amazonaws.com/123456789/broadcast-queue",
        "flows_url": "https://flows.weni.ai",
        "flows_jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "project_uuid": "550e8400-e29b-41d4-a716-446655440000",
    },
    contact={
        "urns": ["whatsapp:5511999999999"],
        "name": "John Doe",
    },
    credentials={},
    parameters={},
    globals={},
)
```

## Message Types

### Text

Simple text message.

```python
from weni.broadcasts import Text

msg = Text(text="Hello! How can I help you?")
Broadcast.send(msg)
```

### Attachment

Message with media (image, document, video, audio).

```python
from weni.broadcasts import Attachment

# With image
msg = Attachment(
    text="Here's the image",
    image="https://example.com/image.png"
)

# With document
msg = Attachment(
    text="Download the PDF",
    document="https://example.com/file.pdf"
)

# With video
msg = Attachment(
    text="Watch this",
    video="https://example.com/video.mp4"
)
```

### QuickReply

Message with quick reply buttons.

```python
from weni.broadcasts import QuickReply

msg = QuickReply(
    text="Do you want to continue?",
    options=["Yes", "No", "Maybe"],
    header="Question",  # optional
    footer="Tap to select"  # optional
)
Broadcast.send(msg)
```

### ListMessage

Interactive list with selectable items.

```python
from weni.broadcasts import ListMessage, ListItem

msg = ListMessage(
    text="Select an option:",
    button_text="View options",
    items=[
        ListItem(title="Option 1", description="First option"),
        ListItem(title="Option 2", description="Second option"),
        ListItem(title="Option 3", description="Third option"),
    ],
    header="Menu",  # optional
    footer="Tap to view"  # optional
)
Broadcast.send(msg)
```

### CTAMessage

Call-to-Action message with URL button.

```python
from weni.broadcasts import CTAMessage

msg = CTAMessage(
    text="Visit our website for more information",
    url="https://example.com",
    display_text="Open Website",
    header="More Info",  # optional
    footer="External link"  # optional
)
Broadcast.send(msg)
```

### Location

Location request message.

```python
from weni.broadcasts import Location

msg = Location(text="Please share your location")
Broadcast.send(msg)
```

### OrderDetails

Order details with payment information.

```python
from weni.broadcasts import OrderDetails, OrderItem

msg = OrderDetails(
    text="Your order details:",
    reference_id="ORDER-123",
    items=[
        OrderItem(
            retailer_id="SKU-001",
            name="Product A",
            value=1000,  # in cents
            quantity=2
        ),
        OrderItem(
            retailer_id="SKU-002",
            name="Product B",
            value=500,
            quantity=1
        ),
    ],
    total_amount=2500,
    subtotal=2500,
    payment_type="pix",
    pix_key="12345678900",
    pix_key_type="cpf",
    merchant_name="My Store"
)
Broadcast.send(msg)
```

### Catalog

Catalog message for product browsing.

```python
from weni.broadcasts import Catalog

msg = Catalog(
    text="Browse our products",
    thumbnail_product_retailer_id="FEATURED-PRODUCT"  # optional
)
Broadcast.send(msg)
```

## Sending Multiple Messages

Use `send_many()` for more efficient batch sending:

```python
from weni.broadcasts import Broadcast, Text

Broadcast.configure(context)

# Send multiple messages in a single batch
Broadcast.send_many([
    Text(text="Step 1: Processing..."),
    Text(text="Step 2: Validating..."),
    Text(text="Step 3: Complete!"),
])
```

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                     MESSAGE FLOW                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Tool Lambda                                                   │
│   ───────────                                                   │
│   Broadcast.configure(context)                                  │
│   Broadcast.send(Text("Hello!"))  ──► SQS Queue (~5-10ms)      │
│   ... continue execution ...                                    │
│                                                                 │
│                                           │                     │
│                                           ▼                     │
│                                                                 │
│   Flows Worker (reads from SQS)                                │
│   ─────────────────────────────                                │
│   Receives message from queue                                   │
│   POST /api/v2/internals/whatsapp_broadcasts                   │
│   Message delivered to WhatsApp                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

1. **Tool Execution**: `Broadcast.configure()` initializes the sender with SQS configuration
2. **Message Queuing**: `Broadcast.send()` sends the message payload to SQS (~5-10ms)
3. **Async Processing**: A Flows worker reads from SQS and calls the WhatsApp Broadcasts API
4. **Delivery**: The message is delivered to the contact via WhatsApp

## SQS Message Payload

The payload sent to SQS contains all information needed by the Flows worker:

```json
{
    "msg": {
        "text": "Hello!",
        "quick_replies": ["Yes", "No"]
    },
    "urns": ["whatsapp:5511999999999"],
    "flows_url": "https://flows.weni.ai",
    "jwt_token": "eyJhbGciOiJIUzI1NiIs...",
    "project_uuid": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Error Handling

The `BroadcastSender` raises specific exceptions:

```python
from weni.broadcasts import (
    Broadcast,
    BroadcastSenderError,
    BroadcastSenderConfigError,
)

try:
    Broadcast.configure(context)
    Broadcast.send(Text(text="Hello!"))
except BroadcastSenderConfigError as e:
    # Missing required configuration (sqs_queue_url, flows_url)
    print(f"Configuration error: {e}")
except BroadcastSenderError as e:
    # Failed to send to SQS
    print(f"Send error: {e}")
```

## Backward Compatibility

If `Broadcast.configure()` is not called, messages are still registered in `BroadcastEvent` for later processing. This allows gradual migration and testing.

```python
# Without configure - messages are only registered, not sent to SQS
Broadcast.send(Text(text="Hello!"))

# Later, retrieve and process manually
pending = BroadcastEvent.pop_pending()
for msg in pending:
    # Process manually...
    pass
```
