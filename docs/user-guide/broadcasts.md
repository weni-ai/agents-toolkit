# Broadcasts

The Broadcasts module provides message types and functionality for sending WhatsApp messages asynchronously during tool execution.

## Quick Start

```python
from weni.broadcasts import Broadcast, Text, Attachment

class MyTool(Tool):
    def execute(self, context: Context):
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

## How It Works

1. **During Tool Execution**: Messages sent via `Broadcast.send()` are queued in `BroadcastEvent`
2. **After Tool Execution**: Queued messages are processed and sent to the contact asynchronously
3. **No Blocking**: The tool continues executing without waiting for messages to be delivered

This allows you to send progress updates to the user while performing long-running operations.

## Message Payload Format

Each message type implements `format_message()` which returns the appropriate payload for the WhatsApp API:

```python
msg = Text(text="Hello!")
payload = msg.format_message()
# Returns: {"type": "text", "text": "Hello!"}

msg = Attachment(text="Image", image="https://example.com/img.png")
payload = msg.format_message()
# Returns: {
#     "type": "attachment",
#     "text": "Image",
#     "attachments": ["image/png:https://example.com/img.png"]
# }
```
