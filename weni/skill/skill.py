import json
from typing import Any, Type

from weni.components import Component
from weni.context import Context
from weni.validators import validate_components


class Response:
    """
    A response from a skill.
    """

    _data: dict = {}
    _components: list[Type[Component]] = []

    def __init__(self, data: dict, components: list[Type[Component]]):
        # Validate components using the existing validator
        try:
            validate_components(components)
        except ValueError as e:
            raise TypeError(f"Invalid components: {str(e)}")

        # Ensure data and components are immutable
        self._data = data.copy()
        self._components = components.copy()

    def __str__(self):
        # Get parsed components without additional JSON encoding
        parsed_components = [component.parse() for component in self._components]

        # Create the response structure
        response = {"data": self._data, "components": parsed_components}

        # Single JSON encoding
        return json.dumps(response)


class Skill:
    """
    Base class for implementing skills.

    A skill represents a specific capability or functionality that can be executed within the platform.
    Skills receive a Context object containing credentials, parameters and global variables, and must
    return a Response object with the execution result and the components that should be used to
    display it.

    Example:
        ```python
        class GetWeather(Skill):
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

    The skill execution flow is:
    1. The skill receives a Context object with credentials, parameters and globals
    2. The execute() method is called with the context
    3. The skill performs its business logic using the context data
    4. The skill returns a Response with the result data and display components
    """

    def __new__(cls, context: Context):
        instance = super().__new__(cls)
        result = instance.execute(context)

        if not isinstance(result, Response):
            raise TypeError(f"Execute method must return a Response object, got {type(result)}")

        return result

    def execute(self, context: Context) -> Response:
        return Response(data={}, components=[])
