import pytest

from weni.context import Context
from weni.tool import Tool
from weni.responses import (
    ResponseObject,
    HeaderType,
    TextResponse,
    QuickReplyResponse,
)


def test_response_initialization():
    """Test Response class initialization"""
    data = {"key": "value"}
    result, format = TextResponse(data=data)

    assert result == data
    assert format == {"msg": {"text": "Hello, how can I help you today?"}}


def test_response_str_representation():
    """Test Response string representation"""
    data = {"key": "value"}
    result, format = TextResponse(data=data)

    assert result == data
    assert format == {"msg": {"text": "Hello, how can I help you today?"}}


def test_response_with_empty_data():
    """Test Response with empty data"""
    result, format = TextResponse(data={})

    assert result == {}
    assert format == {"msg": {"text": "Hello, how can I help you today?"}}


def test_response_with_complex_data():
    """Test Response with nested data structure"""
    data = {"nested": {"key": "value", "list": [1, 2, 3], "bool": True}}
    result, format = TextResponse(data=data)

    assert result == data
    assert format == {"msg": {"text": "Hello, how can I help you today?"}}


def test_tool_execution():
    """Test basic Tool execution"""

    class TestTool(Tool):
        def execute(self, context: Context) -> ResponseObject:
            return TextResponse(data={"test": "data"})  # type: ignore

    context = Context(credentials={}, parameters={}, globals={})
    result, format = TestTool(context)

    assert result == {"test": "data"}
    assert format == {"msg": {"text": "Hello, how can I help you today?"}}


def test_tool_context_access():
    """Test Tool access to context values"""

    class TestTool(Tool):
        def execute(self, context: Context) -> ResponseObject:
            return QuickReplyResponse(
                data={
                    "credential": context.credentials.get("api_key"),
                    "param": context.parameters.get("user_id"),
                    "global": context.globals.get("env"),
                },
                header_type=HeaderType.TEXT,
            )  # type: ignore

    context = Context(
        credentials={"api_key": "secret123"}, parameters={"user_id": "user456"}, globals={"env": "production"}
    )

    result, format = TestTool(context)
    assert result == {"credential": "secret123", "param": "user456", "global": "production"}
    assert format == {
        "msg": {
            "text": "Hello, how can I help you today?",
            "quick_replies": ["Yes", "No"],
            "header": {"type": "text", "text": "Important Message"},
        }
    }


def test_tool_without_execute_implementation():
    """Test Tool without execute implementation"""

    class EmptyTool(Tool):
        pass

    context = Context(credentials={}, parameters={}, globals={})
    result, format = EmptyTool(context)

    assert result == {}
    assert format == {"msg": {"text": "Hello, how can I help you today?"}}


def test_tool_with_invalid_format():
    """Test Tool where the format value (second return value) is not a dict"""

    class InvalidFormatTool(Tool):
        def execute(self, context: Context) -> ResponseObject:  # type: ignore
            # The first value can be any type (a dictionary here),
            # but the second value (format) must be a dictionary - not a string
            return {}, "not a dictionary"  # type: ignore

    context = Context(credentials={}, parameters={}, globals={})

    with pytest.raises(TypeError) as excinfo:
        InvalidFormatTool(context)

    assert "Execute method must return a dictionary" in str(excinfo.value)


def test_response_immutability():
    """Test Response immutability after creation"""
    data = {"key": "value"}
    result, format = TextResponse(data=data)

    # Modify original data
    data["new_key"] = "new_value"

    # Response should maintain original values
    assert "new_key" not in result
    assert format == {"msg": {"text": "Hello, how can I help you today?"}}


def test_tool_context_immutability():
    """Test Context immutability in Tool"""

    class MutableTool(Tool):
        def execute(self, context: Context) -> ResponseObject:
            # Try to modify context
            context.credentials["new_key"] = "value"  # type: ignore
            return TextResponse(data={})  # type: ignore

    context = Context(credentials={"key": "value"}, parameters={}, globals={})
    original_credentials = context.credentials.copy()

    with pytest.raises(TypeError):
        MutableTool(context)

    assert context.credentials == original_credentials


def test_tool_execution_order():
    """Test Tool execution order and single execution"""
    execution_count = 0

    class CountedTool(Tool):
        def execute(self, context: Context) -> ResponseObject:
            nonlocal execution_count
            execution_count += 1
            return TextResponse(data={"count": execution_count})  # type: ignore

    context = Context(credentials={}, parameters={}, globals={})
    result, format = CountedTool(context)

    assert execution_count == 1
    assert result == {"count": 1}
    assert format == {"msg": {"text": "Hello, how can I help you today?"}}

    result, format = CountedTool(context)

    assert execution_count == 2
    assert result == {"count": 2}
    assert format == {"msg": {"text": "Hello, how can I help you today?"}}


def test_tool_with_complex_response():
    """Test Tool with complex response configuration"""

    class ComplexTool(Tool):
        def execute(self, context: Context) -> ResponseObject:
            return QuickReplyResponse(
                data={"message": "Choose an option"}, header_type=HeaderType.TEXT, footer=True
            )  # type: ignore

    context = Context(credentials={}, parameters={}, globals={})
    result, format = ComplexTool(context)

    assert result == {"message": "Choose an option"}
    assert format == {
        "msg": {
            "text": "Hello, how can I help you today?",
            "quick_replies": ["Yes", "No"],
            "header": {"type": "text", "text": "Important Message"},
            "footer": "Powered by Weni",
        }
    }


def test_tool_with_non_dict_response():
    """Test Tool execution with non-dictionary response data"""

    class ListDataTool(Tool):
        def execute(self, context: Context) -> ResponseObject:
            return TextResponse(data=["item1", "item2", "item3"])  # type: ignore

    context = Context(credentials={}, parameters={}, globals={})
    result, format = ListDataTool(context)

    assert result == ["item1", "item2", "item3"]
    assert format == {"msg": {"text": "Hello, how can I help you today?"}}

    class StringDataTool(Tool):
        def execute(self, context: Context) -> ResponseObject:
            return TextResponse(data="simple string response")  # type: ignore

    result, format = StringDataTool(context)

    assert result == "simple string response"
    assert format == {"msg": {"text": "Hello, how can I help you today?"}}

    class NumberDataTool(Tool):
        def execute(self, context: Context) -> ResponseObject:
            return TextResponse(data=42)  # type: ignore

    result, format = NumberDataTool(context)

    assert result == 42
    assert format == {"msg": {"text": "Hello, how can I help you today?"}}
