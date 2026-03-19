from .component import (
    Component,
    Text,
    Header,
    Footer,
    Attachments,
    QuickReplies,
    ListMessage,
    CTAMessage,
    Location,
    OrderDetails,
)


__all__ = [
    "Component",
    "Text",
    "Header",
    "Footer",
    "Attachments",
    "QuickReplies",
    "ListMessage",
    "CTAMessage",
    "Location",
    "OrderDetails",
    "FinalResponse",
]


def __getattr__(name: str):
    if name == "FinalResponse":
        from weni.responses.responses import FinalResponse
        return FinalResponse
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
