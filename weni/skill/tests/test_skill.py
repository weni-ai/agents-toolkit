import json
import pytest

from weni.context import Context
from weni.skill import Skill
from weni.responses import (
    Response,
    HeaderType,
    TextResponse,
    QuickReplyResponse,
    ListMessageResponse,
)
from weni.components import (
    Text,
    Header,
    Footer,
    QuickReplies,
    ListMessage,
)


def test_response_initialization():
    """Test Response class initialization"""
    data = {"key": "value"}
    components = [Text]
    response = TextResponse(data=data)

    assert response._data == data
    assert response._components == components


def test_response_str_representation():
    """Test Response string representation"""
    data = {"key": "value"}
    response = TextResponse(data=data)

    expected = json.dumps({"data": {"key": "value"}, "components": [Text.parse()]})

    assert str(response) == expected


def test_response_with_empty_data():
    """Test Response with empty data"""
    response = TextResponse(data={})

    expected = json.dumps({"data": {}, "components": [Text.parse()]})

    assert str(response) == expected


def test_response_with_complex_data():
    """Test Response with nested data structure"""
    data = {"nested": {"key": "value", "list": [1, 2, 3], "bool": True}}
    response = TextResponse(data=data)

    assert response._data == data
    assert response._components == [Text]


def test_skill_execution():
    """Test basic Skill execution"""

    class TestSkill(Skill):
        def execute(self, context: Context) -> Response:
            return TextResponse(data={"test": "data"})

    context = Context(credentials={}, parameters={}, globals={})
    result = TestSkill(context)

    assert isinstance(result, TextResponse)
    assert result._data == {"test": "data"}
    assert result._components == [Text]


def test_skill_context_access():
    """Test Skill access to context values"""

    class TestSkill(Skill):
        def execute(self, context: Context) -> Response:
            return QuickReplyResponse(
                data={
                    "credential": context.credentials.get("api_key"),
                    "param": context.parameters.get("user_id"),
                    "global": context.globals.get("env"),
                },
                header_type=HeaderType.TEXT,
            )

    context = Context(
        credentials={"api_key": "secret123"}, parameters={"user_id": "user456"}, globals={"env": "production"}
    )

    result = TestSkill(context)
    assert result._data == {"credential": "secret123", "param": "user456", "global": "production"}
    assert set(result._components) == {Text, QuickReplies, Header}


def test_skill_without_execute_implementation():
    """Test Skill without execute implementation"""

    class EmptySkill(Skill):
        pass

    context = Context(credentials={}, parameters={}, globals={})
    result = EmptySkill(context)

    assert isinstance(result, TextResponse)
    assert result._data == {}
    assert result._components == [Text]


def test_skill_with_invalid_response():
    """Test Skill with invalid response type"""

    class InvalidSkill(Skill):
        def execute(self, context: Context) -> Response:  # type: ignore
            return {"invalid": "response"}  # type: ignore

    context = Context(credentials={}, parameters={}, globals={})
    with pytest.raises(TypeError):
        InvalidSkill(context)


def test_response_immutability():
    """Test Response immutability after creation"""
    data = {"key": "value"}
    response = TextResponse(data=data)

    # Modify original data
    data["new_key"] = "new_value"

    # Response should maintain original values
    assert "new_key" not in response._data


def test_skill_context_immutability():
    """Test Context immutability in Skill"""

    class MutableSkill(Skill):
        def execute(self, context: Context) -> Response:
            # Try to modify context
            context.credentials["new_key"] = "value"  # type: ignore
            return TextResponse(data={})

    context = Context(credentials={"key": "value"}, parameters={}, globals={})
    original_credentials = context.credentials.copy()

    with pytest.raises(TypeError):
        MutableSkill(context)

    assert context.credentials == original_credentials


def test_skill_execution_order():
    """Test Skill execution order and single execution"""
    execution_count = 0

    class CountedSkill(Skill):
        def execute(self, context: Context) -> Response:
            nonlocal execution_count
            execution_count += 1
            return ListMessageResponse(data={"count": execution_count})

    context = Context(credentials={}, parameters={}, globals={})
    result = CountedSkill(context)

    assert execution_count == 1
    assert result._data == {"count": 1}
    assert set(result._components) == {Text, ListMessage}


def test_skill_with_complex_response():
    """Test Skill with complex response configuration"""

    class ComplexSkill(Skill):
        def execute(self, context: Context) -> Response:
            return QuickReplyResponse(data={"message": "Choose an option"}, header_type=HeaderType.TEXT, footer=True)

    context = Context(credentials={}, parameters={}, globals={})
    result = ComplexSkill(context)

    assert isinstance(result, QuickReplyResponse)
    assert result._data == {"message": "Choose an option"}
    assert set(result._components) == {Text, QuickReplies, Header, Footer}
