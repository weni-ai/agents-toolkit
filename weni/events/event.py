from datetime import datetime
from typing import Any, Dict, List, Optional

class Event:
    """
    Data Transfer Object (DTO) para representar os dados de um evento a ser enviado ao Weni Datalake.

    Attributes:
        event_name (str): Event name.
        key (str): Unique key for the event.
        date (str): Event date and time in ISO 8601 format.
        contact_urn (str): Contact URN (ex: whatsapp:+55123456789).
        value_type (str): Value type (ex: 'string', 'int', etc).
        value (Any): Event value.
        metadata (Optional[Dict[str, Any]]): Additional event metadata.
    """
    registry: List["Event"] = []

    @classmethod
    def register(cls, event: "Event") -> None:
        cls.registry.append(event)
    
    @classmethod
    def get_events(cls) -> List[Dict]:
        return [event.to_dict() for event in cls.registry]

    def __init__(
        self,
        event_name: str,
        key: str,
        contact_urn: str,
        value_type: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None,
        date: Optional[str] = None,
    ):
        self.event_name = event_name
        self.key = key
        self.date = date or datetime.now().isoformat()
        self.contact_urn = contact_urn
        self.value_type = value_type
        self.value = value
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the DTO to a dictionary compatible with the Weni Datalake SDK.
        """
        return {
            "event_name": self.event_name,
            "key": self.key,
            "date": self.date,
            "contact_urn": self.contact_urn,
            "value_type": self.value_type,
            "value": self.value,
            "metadata": self.metadata,
        }
