from datetime import datetime
from typing import Any, Dict, List, Optional

from typing_extensions import deprecated


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
    @deprecated("Event.register() will be removed soon. Use self.register_event(event) inside your Tool instead.")
    def register(cls, event: "Event") -> None:
        cls.registry.append(event)

    @classmethod
    @deprecated("Event.get_events() will be removed soon. Events are now collected automatically by Tool.")
    def get_events(cls) -> List[Dict[str, Any]]:
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
