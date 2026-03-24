from typing import Any

from weni.context import Context
from weni.events.event import Event
from weni.responses import ResponseObject, TextResponse


class Tool:
    """
    Base class for implementing tools.

    Tools receive a Context object and must return a Response (tuple of data and format).
    Broadcasts are registered via Broadcast(self).send() and collected automatically.

    Example:
        ```python
        class GetWeather(Tool):
            def execute(self, context: Context) -> ResponseObject:
                weather_data = get_weather(context.parameters.get("city"))
                return TextResponse(data=weather_data)
        ```
    """

    def __new__(cls, context: Context):
        instance = super().__new__(cls)
        Event.registry.clear()
        instance._pending_broadcasts = []
        instance.context = context

        execute_result = instance.execute(context)
        events = Event.get_events()
        broadcasts = instance._pending_broadcasts

        result, format = execute_result
        if not isinstance(format, dict):
            raise TypeError(f"Execute method must return a dictionary, got {type(format)}")

        format["messages"] = broadcasts

        traces = {}
        if hasattr(instance, '_get_trace_summary') and hasattr(instance, '_tracer_initialized'):
            if instance._tracer_initialized:
                traces = instance._get_trace_summary()

        return result, format, events, traces, broadcasts

    def execute(self, context: Context) -> ResponseObject:
        """
        Execute the tool's main functionality.

        Override this method to implement the tool's behavior.
        """
        return TextResponse(data={})  # type: ignore

    def register_broadcast(self, broadcast: dict[str, Any]) -> None:
        self._pending_broadcasts.append(broadcast)
