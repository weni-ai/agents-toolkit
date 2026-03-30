from weni.events.event import Event
from datetime import datetime


def test_event_creation_and_to_dict():
    event = Event(
        event_name="test_event",
        key="test_key",
        value_type="string",
        value="test_value",
        metadata={"foo": "bar"},
        date="2024-01-01T00:00:00Z"
    )
    event_dict = event.to_dict()
    assert event_dict["event_name"] == "test_event"
    assert event_dict["key"] == "test_key"
    assert event_dict["value_type"] == "string"
    assert event_dict["value"] == "test_value"
    assert event_dict["metadata"] == {"foo": "bar"}
    assert event_dict["date"] == "2024-01-01T00:00:00Z"


def test_event_metadata_default():
    event = Event(
        event_name="event2",
        key="key2",
        value_type="string",
        value="abc"
    )
    assert event.metadata == {}


def test_event_date_auto():
    event = Event(
        event_name="event3",
        key="key3",
        value_type="string",
        value="abc"
    )
    assert isinstance(event.date, str)
    dt = datetime.fromisoformat(event.date)
    assert abs((dt - datetime.now()).total_seconds()) < 5
