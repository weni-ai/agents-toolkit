"""
Tests for broadcast message types.
"""

from weni.broadcasts.messages import (
    Text,
    Attachment,
    QuickReply,
    ListMessage,
    ListItem,
    CTAMessage,
    Location,
    OrderDetails,
    OrderItem,
    Catalog,
    _get_mime_type,
)


class TestGetMimeType:
    """Tests for _get_mime_type helper function."""

    def test_jpeg_extension(self):
        """Test JPEG image detection."""
        mime = _get_mime_type("https://example.com/photo.jpg", "image/png")
        assert mime == "image/jpeg"

    def test_jpeg_extension_uppercase(self):
        """Test JPEG with uppercase extension."""
        mime = _get_mime_type("https://example.com/photo.JPEG", "image/png")
        assert mime == "image/jpeg"

    def test_png_extension(self):
        """Test PNG image detection."""
        mime = _get_mime_type("https://example.com/image.png", "image/png")
        assert mime == "image/png"

    def test_gif_extension(self):
        """Test GIF image detection."""
        mime = _get_mime_type("https://example.com/animation.gif", "image/png")
        assert mime == "image/gif"

    def test_webp_extension(self):
        """Test WebP image detection."""
        mime = _get_mime_type("https://example.com/image.webp", "image/png")
        assert mime == "image/webp"

    def test_pdf_extension(self):
        """Test PDF document detection."""
        mime = _get_mime_type("https://example.com/document.pdf", "application/pdf")
        assert mime == "application/pdf"

    def test_mp4_extension(self):
        """Test MP4 video detection."""
        mime = _get_mime_type("https://example.com/video.mp4", "video/mp4")
        assert mime == "video/mp4"

    def test_webm_extension(self):
        """Test WebM video detection."""
        mime = _get_mime_type("https://example.com/video.webm", "video/mp4")
        assert mime == "video/webm"

    def test_mp3_extension(self):
        """Test MP3 audio detection."""
        mime = _get_mime_type("https://example.com/audio.mp3", "audio/mpeg")
        assert mime == "audio/mpeg"

    def test_wav_extension(self):
        """Test WAV audio detection."""
        mime = _get_mime_type("https://example.com/audio.wav", "audio/mpeg")
        assert mime == "audio/x-wav"

    def test_url_with_query_params(self):
        """Test URL with query parameters."""
        mime = _get_mime_type("https://example.com/photo.jpg?token=abc123", "image/png")
        assert mime == "image/jpeg"

    def test_no_extension_uses_default(self):
        """Test URL without extension uses default."""
        mime = _get_mime_type("https://example.com/image", "image/png")
        assert mime == "image/png"

    def test_unknown_extension_uses_default(self):
        """Test unknown extension uses default."""
        mime = _get_mime_type("https://example.com/file.xyz123", "application/pdf")
        assert mime == "application/pdf"


class TestTextMessage:
    """Tests for Text message."""

    def test_format_message(self):
        """Test Text message formatting."""
        msg = Text(text="Hello, world!")
        payload = msg.format_message()

        assert payload["type"] == "text"
        assert payload["text"] == "Hello, world!"


class TestAttachmentMessage:
    """Tests for Attachment message."""

    def test_format_with_image_png(self):
        """Test Attachment with PNG image."""
        msg = Attachment(text="Check this out", image="https://example.com/img.png")
        payload = msg.format_message()

        assert payload["type"] == "attachment"
        assert payload["text"] == "Check this out"
        assert "image/png:https://example.com/img.png" in payload["attachments"]

    def test_format_with_image_jpeg(self):
        """Test Attachment with JPEG image uses correct MIME type."""
        msg = Attachment(text="Photo", image="https://example.com/photo.jpg")
        payload = msg.format_message()

        assert "image/jpeg:https://example.com/photo.jpg" in payload["attachments"]

    def test_format_with_image_gif(self):
        """Test Attachment with GIF image uses correct MIME type."""
        msg = Attachment(image="https://example.com/animation.gif")
        payload = msg.format_message()

        assert "image/gif:https://example.com/animation.gif" in payload["attachments"]

    def test_format_with_image_webp(self):
        """Test Attachment with WebP image uses correct MIME type."""
        msg = Attachment(image="https://example.com/image.webp")
        payload = msg.format_message()

        assert "image/webp:https://example.com/image.webp" in payload["attachments"]

    def test_format_with_document(self):
        """Test Attachment with document."""
        msg = Attachment(document="https://example.com/doc.pdf")
        payload = msg.format_message()

        assert "application/pdf:https://example.com/doc.pdf" in payload["attachments"]

    def test_format_with_video_mp4(self):
        """Test Attachment with MP4 video."""
        msg = Attachment(video="https://example.com/video.mp4")
        payload = msg.format_message()

        assert "video/mp4:https://example.com/video.mp4" in payload["attachments"]

    def test_format_with_video_webm(self):
        """Test Attachment with WebM video uses correct MIME type."""
        msg = Attachment(video="https://example.com/video.webm")
        payload = msg.format_message()

        assert "video/webm:https://example.com/video.webm" in payload["attachments"]

    def test_format_with_audio_mp3(self):
        """Test Attachment with MP3 audio."""
        msg = Attachment(audio="https://example.com/audio.mp3")
        payload = msg.format_message()

        assert "audio/mpeg:https://example.com/audio.mp3" in payload["attachments"]

    def test_format_with_audio_wav(self):
        """Test Attachment with WAV audio uses correct MIME type."""
        msg = Attachment(audio="https://example.com/audio.wav")
        payload = msg.format_message()

        assert "audio/x-wav:https://example.com/audio.wav" in payload["attachments"]

    def test_format_without_text(self):
        """Test Attachment without text."""
        msg = Attachment(image="https://example.com/img.png")
        payload = msg.format_message()

        assert "text" not in payload

    def test_format_with_no_extension_uses_default(self):
        """Test Attachment with URL without extension uses default MIME type."""
        msg = Attachment(image="https://example.com/image")
        payload = msg.format_message()

        assert "image/png:https://example.com/image" in payload["attachments"]


class TestQuickReplyMessage:
    """Tests for QuickReply message."""

    def test_format_basic(self):
        """Test basic QuickReply."""
        msg = QuickReply(text="Choose one:", options=["Yes", "No"])
        payload = msg.format_message()

        assert payload["type"] == "quick_reply"
        assert payload["text"] == "Choose one:"
        assert payload["quick_replies"] == ["Yes", "No"]

    def test_format_with_header_footer(self):
        """Test QuickReply with header and footer."""
        msg = QuickReply(text="Choose one:", options=["A", "B"], header="Important", footer="Tap to select")
        payload = msg.format_message()

        assert payload["header"]["text"] == "Important"
        assert payload["footer"] == "Tap to select"


class TestListMessage:
    """Tests for ListMessage."""

    def test_format_basic(self):
        """Test basic ListMessage."""
        msg = ListMessage(
            text="Select an option:",
            button_text="View",
            items=[
                ListItem(title="Option 1", description="First"),
                ListItem(title="Option 2", description="Second"),
            ],
        )
        payload = msg.format_message()

        assert payload["type"] == "list"
        assert payload["text"] == "Select an option:"
        assert payload["list_message"]["button_text"] == "View"
        assert len(payload["list_message"]["list_items"]) == 2
        assert payload["list_message"]["list_items"][0]["title"] == "Option 1"


class TestCTAMessage:
    """Tests for CTAMessage."""

    def test_format_basic(self):
        """Test basic CTAMessage."""
        msg = CTAMessage(text="Visit our website", url="https://example.com", display_text="Open")
        payload = msg.format_message()

        assert payload["type"] == "cta_url"
        assert payload["cta_message"]["url"] == "https://example.com"
        assert payload["cta_message"]["display_text"] == "Open"


class TestLocationMessage:
    """Tests for Location message."""

    def test_format_basic(self):
        """Test basic Location."""
        msg = Location(text="Share your location")
        payload = msg.format_message()

        assert payload["type"] == "location"
        assert payload["text"] == "Share your location"
        assert payload["interactive_type"] == "location"


class TestOrderDetailsMessage:
    """Tests for OrderDetails message."""

    def test_format_basic(self):
        """Test basic OrderDetails."""
        msg = OrderDetails(
            text="Your order:",
            reference_id="ORDER-123",
            items=[OrderItem(retailer_id="SKU-1", name="Product A", value=1000, quantity=2)],
            total_amount=2000,
            subtotal=2000,
            payment_type="pix",
        )
        payload = msg.format_message()

        assert payload["type"] == "order_details"
        assert payload["order_details"]["reference_id"] == "ORDER-123"
        assert payload["order_details"]["total_amount"] == 2000
        assert len(payload["order_details"]["order"]["items"]) == 1


class TestCatalogMessage:
    """Tests for Catalog message."""

    def test_format_basic(self):
        """Test basic Catalog."""
        msg = Catalog(text="Browse products")
        payload = msg.format_message()

        assert payload["type"] == "catalog"
        assert payload["text"] == "Browse products"

    def test_format_with_thumbnail(self):
        """Test Catalog with thumbnail."""
        msg = Catalog(text="Products", thumbnail_product_retailer_id="PROD-1")
        payload = msg.format_message()

        assert payload["thumbnail_product_retailer_id"] == "PROD-1"
