from datetime import datetime
from typing import Any, Dict, Optional
from weni_datalake_sdk.clients.client import send_event_data
from weni_datalake_sdk.paths.events_path import EventPath

class DatalakeEventDTO:
    """
    Data Transfer Object (DTO) para representar os dados de um evento a ser enviado ao Weni Datalake.

    Attributes:
        event_name (str): Event name.
        key (str): Unique key for the event.
        date (str): Event date and time in ISO 8601 format.
        project (str): Project UUID related to the event.
        contact_urn (str): Contact URN (ex: whatsapp:+55123456789).
        value_type (str): Value type (ex: 'string', 'int', etc).
        value (Any): Event value.
        metadata (Optional[Dict[str, Any]]): Additional event metadata.
    """
    def __init__(
        self,
        event_name: str,
        key: str,
        project: str,
        contact_urn: str,
        value_type: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None,
        date: Optional[str] = None,
    ):
        self.event_name = event_name
        self.key = key
        self.date = date or datetime.now().isoformat()
        self.project = project
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
            "project": self.project,
            "contact_urn": self.contact_urn,
            "value_type": self.value_type,
            "value": self.value,
            "metadata": self.metadata,
        }

def send_datalake_event(event_dto: DatalakeEventDTO) -> Any:
    """
    Send an event to Weni Datalake using the official SDK.

    Args:
        event_dto (DatalakeEventDTO): Object containing the event data.

    Returns:
        Any: Response from the SDK after sending the event.

    Raises:
        Exception: Propagates SDK exceptions in case of event sending failure.
    """
    event_data = event_dto.to_dict()
    return send_event_data(EventPath, event_data)
