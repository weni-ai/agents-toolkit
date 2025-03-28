import pytest

from weni.context import Context
from weni.skill import Skill
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


def test_skill_execution():
    """Test basic Skill execution"""

    class TestSkill(Skill):
        def execute(self, context: Context) -> ResponseObject:
            return TextResponse(data={"test": "data"})  # type: ignore

    context = Context(credentials={}, parameters={}, globals={})
    result, format = TestSkill(context)

    assert result == {"test": "data"}
    assert format == {"msg": {"text": "Hello, how can I help you today?"}}


def test_skill_context_access():
    """Test Skill access to context values"""

    class TestSkill(Skill):
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

    result, format = TestSkill(context)
    assert result == {"credential": "secret123", "param": "user456", "global": "production"}
    assert format == {
        "msg": {
            "text": "Hello, how can I help you today?",
            "quick_replies": ["Yes", "No"],
            "header": {"type": "text", "text": "Important Message"},
        }
    }


def test_skill_without_execute_implementation():
    """Test Skill without execute implementation"""

    class EmptySkill(Skill):
        pass

    context = Context(credentials={}, parameters={}, globals={})
    result, format = EmptySkill(context)

    assert result == {}
    assert format == {"msg": {"text": "Hello, how can I help you today?"}}


def test_skill_with_invalid_format():
    """Test Skill where the format value (second return value) is not a dict"""

    class InvalidFormatSkill(Skill):
        def execute(self, context: Context) -> ResponseObject:  # type: ignore
            # The first value can be any type (a dictionary here),
            # but the second value (format) must be a dictionary - not a string
            return {}, "not a dictionary"  # type: ignore

    context = Context(credentials={}, parameters={}, globals={})

    with pytest.raises(TypeError) as excinfo:
        InvalidFormatSkill(context)

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


def test_skill_context_immutability():
    """Test Context immutability in Skill"""

    class MutableSkill(Skill):
        def execute(self, context: Context) -> ResponseObject:
            # Try to modify context
            context.credentials["new_key"] = "value"  # type: ignore
            return TextResponse(data={})  # type: ignore

    context = Context(credentials={"key": "value"}, parameters={}, globals={})
    original_credentials = context.credentials.copy()

    with pytest.raises(TypeError):
        MutableSkill(context)

    assert context.credentials == original_credentials


def test_skill_execution_order():
    """Test Skill execution order and single execution"""
    execution_count = 0

    class CountedSkill(Skill):
        def execute(self, context: Context) -> ResponseObject:
            nonlocal execution_count
            execution_count += 1
            return TextResponse(data={"count": execution_count})  # type: ignore

    context = Context(credentials={}, parameters={}, globals={})
    result, format = CountedSkill(context)

    assert execution_count == 1
    assert result == {"count": 1}
    assert format == {"msg": {"text": "Hello, how can I help you today?"}}

    result, format = CountedSkill(context)

    assert execution_count == 2
    assert result == {"count": 2}
    assert format == {"msg": {"text": "Hello, how can I help you today?"}}


def test_skill_with_complex_response():
    """Test Skill with complex response configuration"""

    class ComplexSkill(Skill):
        def execute(self, context: Context) -> ResponseObject:
            return QuickReplyResponse(
                data={"message": "Choose an option"}, header_type=HeaderType.TEXT, footer=True
            )  # type: ignore

    context = Context(credentials={}, parameters={}, globals={})
    result, format = ComplexSkill(context)

    assert result == {"message": "Choose an option"}
    assert format == {
        "msg": {
            "text": "Hello, how can I help you today?",
            "quick_replies": ["Yes", "No"],
            "header": {"type": "text", "text": "Important Message"},
            "footer": "Powered by Weni",
        }
    }


def test_skill_with_non_dict_response():
    """Test Skill execution with non-dictionary response data"""

    class ListDataSkill(Skill):
        def execute(self, context: Context) -> ResponseObject:
            return TextResponse(data=["item1", "item2", "item3"])  # type: ignore

    context = Context(credentials={}, parameters={}, globals={})
    result, format = ListDataSkill(context)

    assert result == ["item1", "item2", "item3"]
    assert format == {"msg": {"text": "Hello, how can I help you today?"}}

    class StringDataSkill(Skill):
        def execute(self, context: Context) -> ResponseObject:
            return TextResponse(data="simple string response")  # type: ignore

    result, format = StringDataSkill(context)

    assert result == "simple string response"
    assert format == {"msg": {"text": "Hello, how can I help you today?"}}

    class NumberDataSkill(Skill):
        def execute(self, context: Context) -> ResponseObject:
            return TextResponse(data=42)  # type: ignore

    result, format = NumberDataSkill(context)

    assert result == 42
    assert format == {"msg": {"text": "Hello, how can I help you today?"}}
