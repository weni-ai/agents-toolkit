import warnings
from datetime import datetime

from weni.events.event import Event


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


def test_deprecated_register_emits_warning():
    Event.registry = []
    event = Event(event_name="e", key="k", value_type="string", value="v")

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        Event.register(event)

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "removed" in str(w[0].message).lower()

    assert len(Event.registry) == 1


def test_deprecated_get_events_emits_warning():
    Event.registry = [Event(event_name="e", key="k", value_type="string", value="v")]

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        events = Event.get_events()

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)

    assert len(events) == 1
    assert events[0]["event_name"] == "e"
