from datetime import datetime
from typing import Any, Dict, Optional


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
