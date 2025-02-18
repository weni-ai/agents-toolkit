from weni.context import Context
from weni.responses import Response, TextResponse


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
        return TextResponse(data={})
