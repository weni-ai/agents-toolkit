import warnings
from datetime import datetime
from typing import Any, Dict, List, Optional


class Event:
    """
    Data Transfer Object (DTO) for events sent to the Weni Datalake.

    Attributes:
        event_name (str): Event name.
        key (str): Unique key for the event.
        date (str): Event date and time in ISO 8601 format.
        value_type (str): Value type (ex: 'string', 'int', etc).
        value (Any): Event value.
        metadata (Optional[Dict[str, Any]]): Additional event metadata.
    """

    registry: List["Event"] = []

    @classmethod
    def register(cls, event: "Event") -> None:
        """
        Deprecated: Use self.register_event(event) inside your Tool instead.
        Will be removed in version 3.0.0.
        """
        warnings.warn(
            "Event.register() is deprecated and will be removed in version 3.0.0. "
            "Use self.register_event(event) inside your Tool instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        cls.registry.append(event)

    @classmethod
    def get_events(cls) -> List[Dict[str, Any]]:
        """
        Deprecated: Events are now collected automatically by Tool.
        Will be removed in version 3.0.0.
        """
        warnings.warn(
            "Event.get_events() is deprecated and will be removed in version 3.0.0. "
            "Events are now collected automatically by Tool.",
            DeprecationWarning,
            stacklevel=2,
        )
        return [event.to_dict() for event in cls.registry]

    def __init__(
        self,
        event_name: str,
        key: str,
        value_type: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None,
        date: Optional[str] = None,
    ):
        self.event_name = event_name
        self.key = key
        self.date = date or datetime.now().isoformat()
        self.value_type = value_type
        self.value = value
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert the DTO to a dictionary compatible with the Weni Datalake SDK."""
        return {
            "event_name": self.event_name,
            "key": self.key,
            "date": self.date,
            "value_type": self.value_type,
            "value": self.value,
            "metadata": self.metadata,
        }
