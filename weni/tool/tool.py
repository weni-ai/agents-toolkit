from typing import Any

from weni.broadcasts.broadcast import Broadcast
from weni.broadcasts.messages import Message
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
            def execute(self, context: Context) -> Response:
                # Get API key from credentials
                api_key = context.credentials.get("weather_api_key")

                # Get city from parameters
                city = context.parameters.get("city")

                # Call weather API and get results
                weather_data = get_weather(api_key, city)

                # Return response with weather data and components to display it
                return Response(
                    data=weather_data,
                    components=[Text, QuickReplies]
                )
        ```
    
    The tool execution flow is:
    1. The tool receives a Context object with credentials, parameters and globals
    2. The execute() method is called with the context
    3. The tool performs its business logic using the context data
    4. The tool returns a Response with the result data and display components
    """

    _pending_broadcasts: list[dict[str, Any]]
    _pending_events: list[Event]
    context: Context

    def __new__(cls, context: Context):
        instance = super().__new__(cls)
        instance._pending_broadcasts = []
        instance._pending_events = []
        instance.context = context

        execute_result = instance.execute(context)
        events = [e.to_dict() for e in instance._pending_events]
        broadcasts = instance._pending_broadcasts

        result, format = execute_result
        if not isinstance(format, dict):
            raise TypeError(f"Execute method must return a dictionary, got {type(format)}")

        result = {"result": result, "messages_sent": broadcasts}

        traces = {}
        if hasattr(instance, '_get_trace_summary') and hasattr(instance, '_tracer_initialized'):
            if instance._tracer_initialized:
                traces = instance._get_trace_summary()

        return result, format, events, traces

    def execute(self, context: Context) -> ResponseObject:
        """
        Execute the tool's main functionality.

        Override this method to implement the tool's behavior.
        """
        return TextResponse(data={})  # type: ignore

    def send_broadcast(self, message: Message) -> None:
        Broadcast(self).send(message)

    def register_broadcast(self, broadcast: dict[str, Any]) -> None:
        self._pending_broadcasts.append(broadcast)

    def register_event(self, event: Event) -> None:
        self._pending_events.append(event)
