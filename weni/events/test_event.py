from weni.events.event import Event
from datetime import datetime

def teardown_function(function):
    # Clear the registry between tests
    Event.registry.clear()

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

def test_event_register_and_get_events():
    event = Event(
        event_name="event1",
        key="key1",
        value_type="int",
        value=42
    )
    Event.register(event)
    events = Event.get_events()
    assert len(events) == 1
    assert events[0]["event_name"] == "event1"
    assert events[0]["key"] == "key1"
    assert events[0]["value_type"] == "int"
    assert events[0]["value"] == 42
    assert events[0]["metadata"] == {}
    assert "date" in events[0]

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
    # Should be a string ISO 8601
    assert isinstance(event.date, str)
    # Should be approximately now
    dt = datetime.fromisoformat(event.date)
    assert abs((dt - datetime.now()).total_seconds()) < 5 