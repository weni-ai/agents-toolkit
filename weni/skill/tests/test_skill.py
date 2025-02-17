import json
import pytest

from weni.skill import Skill, Response
from weni.context import Context
from weni.components import (
    Text,
    Header,
    Footer,
    QuickReplies,
    ListMessage,
    CTAMessage,
    Location,
    OrderDetails,
)


def test_response_initialization():
    """Test Response class initialization"""
    data = {"key": "value"}
    components = [Text, Header]
    response = Response(data=data, components=components)

    assert response._data == data
    assert response._components == components


def test_response_str_representation():
    """Test Response string representation"""
    data = {"key": "value"}
    components = [Text, Header]
    response = Response(data=data, components=components)

    # Get the parsed components
    parsed_text = Text.parse()
    parsed_header = Header.parse()

    expected = json.dumps({"data": {"key": "value"}, "components": [parsed_text, parsed_header]})

    assert str(response) == expected


def test_response_with_empty_data():
    """Test Response with empty data"""
    response = Response(data={}, components=[])
    expected = '{"data": {}, "components": []}'
    assert str(response) == expected


def test_response_with_complex_data():
    """Test Response with nested data structure"""
    data = {"nested": {"key": "value", "list": [1, 2, 3], "bool": True}}
    response = Response(data=data, components=[Text])

    assert response._data == data
    assert response._components == [Text]


def test_skill_execution():
    """Test basic Skill execution"""

    class TestSkill(Skill):
        def execute(self, context: Context) -> Response:
            return Response(data={"test": "data"}, components=[Text])

    context = Context(credentials={}, parameters={}, globals={})
    result = TestSkill(context)

    assert isinstance(result, Response)
    assert result._data == {"test": "data"}
    assert result._components == [Text]


def test_skill_context_access():
    """Test Skill access to context values"""

    class TestSkill(Skill):
        def execute(self, context: Context) -> Response:
            return Response(
                data={
                    "credential": context.credentials.get("api_key"),
                    "param": context.parameters.get("user_id"),
                    "global": context.globals.get("env"),
                },
                components=[Text],
            )

    context = Context(
        credentials={"api_key": "secret123"}, parameters={"user_id": "user456"}, globals={"env": "production"}
    )

    result = TestSkill(context)
    assert result._data == {"credential": "secret123", "param": "user456", "global": "production"}


def test_skill_without_execute_implementation():
    """Test Skill without execute implementation"""

    class EmptySkill(Skill):
        pass

    context = Context(credentials={}, parameters={}, globals={})
    result = EmptySkill(context)

    assert isinstance(result, Response)
    assert result._data == {}
    assert result._components == []


def test_skill_with_invalid_response():
    """Test Skill with invalid response type"""

    class InvalidSkill(Skill):
        def execute(self, context: Context) -> Response:  # type: ignore
            return {"invalid": "response"}  # type: ignore

    context = Context(credentials={}, parameters={}, globals={})
    with pytest.raises(TypeError):
        InvalidSkill(context)


def test_skill_with_invalid_components():
    """Test Response with invalid component types"""

    class InvalidComponent:
        pass

    with pytest.raises(TypeError):
        Response(data={}, components=[InvalidComponent])  # type: ignore


def test_response_immutability():
    """Test Response immutability after creation"""
    data = {"key": "value"}
    components = [Text]
    response = Response(data=data, components=components)

    # Modify original data and components
    data["new_key"] = "new_value"
    components.append(Header)

    # Response should maintain original values
    assert "new_key" not in response._data
    assert Header not in response._components


def test_skill_context_immutability():
    """Test Context immutability in Skill"""

    class MutableSkill(Skill):
        def execute(self, context: Context) -> Response:
            # Try to modify context
            context.credentials["new_key"] = "value"  # type: ignore
            return Response(data={}, components=[])

    context = Context(credentials={"key": "value"}, parameters={}, globals={})
    original_credentials = context.credentials.copy()

    with pytest.raises(TypeError):
        MutableSkill(context)

    assert context.credentials == original_credentials


def test_response_with_all_component_types():
    """Test Response with various component types"""
    # Using only official components from the library
    components = [Text, Header, Footer, QuickReplies, ListMessage, CTAMessage, Location, OrderDetails]
    response = Response(data={}, components=components)

    assert response._components == components

    # Verify the string representation includes all components
    result = str(response)
    for component in components:
        assert json.dumps(component.parse()) in result


def test_skill_execution_order():
    """Test Skill execution order and single execution"""
    execution_count = 0

    class CountedSkill(Skill):
        def execute(self, context: Context) -> Response:
            nonlocal execution_count
            execution_count += 1
            return Response(data={"count": execution_count}, components=[])

    context = Context(credentials={}, parameters={}, globals={})
    result = CountedSkill(context)

    assert execution_count == 1
    assert result._data == {"count": 1}


def test_response_str_empty_components():
    """Test Response string representation with empty components"""
    data = {"key": "value"}
    response = Response(data=data, components=[])

    expected = json.dumps({"data": {"key": "value"}, "components": []})

    assert str(response) == expected


def test_response_str_empty_data():
    """Test Response string representation with empty data"""
    components = [Text]
    response = Response(data={}, components=components)

    expected = json.dumps({"data": {}, "components": [Text.parse()]})

    assert str(response) == expected
