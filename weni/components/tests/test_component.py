import pytest
from weni.components import Component, Text, Header, Footer, QuickReplies


def test_parse_method_cannot_be_overridden():
    """Test that parse method cannot be overridden by child classes"""
    with pytest.raises(TypeError) as exc_info:

        class ChildComponent(Component):
            def parse(self):  # type: ignore
                pass

    assert "Cannot override final method 'parse'" in str(exc_info.value)


def test_parse_method_can_be_called():
    """Test that parse method can be called from both parent and child classes"""

    class ValidChildComponent(Component):
        pass

    # Should not raise any exceptions
    Component.parse()
    ValidChildComponent.parse()


def test_parse_empty_component():
    """Test parsing a component with no attributes set"""

    class EmptyComponent(Component):
        pass

    result = EmptyComponent.parse()
    assert result == ""


def test_parse_component_with_description():
    """Test parsing a component with only description"""

    class DescriptionComponent(Component):
        _description = "A Test description"

    result = DescriptionComponent.parse()
    assert result == "[DescriptionComponent] is: A Test description"


def test_parse_component_with_rules():
    """Test parsing a component with only rules"""

    class RulesComponent(Component):
        _rules = ["Rule 1", "Rule 2"]

    result = RulesComponent.parse()
    assert result == "[RulesComponent] Component Rules: ['Rule 1', 'Rule 2']"


def test_parse_component_with_required_components():
    """Test parsing a component with required components"""

    class RequiredComponent(Component):
        _required_components = [Text]

    result = RequiredComponent.parse()
    assert "Required components: [" in result
    assert Text._description in result


def test_parse_component_with_allowed_components():
    """Test parsing a component with allowed components"""

    class AllowedComponent(Component):
        _allowed_components = [Header, Footer]

    result = AllowedComponent.parse()
    assert "Allowed components: [" in result
    assert Header._description in result
    assert Footer._description in result


def test_parse_component_with_all_attributes():
    """Test parsing a component with all attributes set"""

    class CompleteComponent(Component):
        _description = "Complete component"
        _rules = ["Rule 1", "Rule 2"]
        _required_components = [Text]
        _allowed_components = [Header, Footer]
        _format = {"msg": {"text": "<text>"}}
        _example = {"msg": {"text": "Hello"}}

    result = CompleteComponent.parse()

    assert "Complete component" in result
    assert "Component Rules: ['Rule 1', 'Rule 2']" in result
    assert "Required components: [" in result
    assert "Allowed components: [" in result
    assert Text._description in result
    assert Header._description in result
    assert Footer._description in result
    assert "Format: " in result
    assert "Example: " in result


def test_parse_real_component():
    """Test parsing a real component (QuickReplies) to verify integration"""
    result = QuickReplies.parse()

    assert QuickReplies._description in result
    assert "Component Rules: [" in result
    assert QuickReplies._rules[0] in result
    assert "Required components: [" in result
    assert Text._description in result
    assert "Allowed components: [" in result
    assert Header._description in result
    assert Footer._description in result


def test_parse_nested_components_no_escaping():
    """Test that nested component parsing has no escaped characters"""

    class NestedComponent(Component):
        _description = "Test component"
        _rules = ["Rule 1", "Rule 2"]
        _required_components = [Text]
        _allowed_components = [Header]

    result = NestedComponent.parse()

    expected_parts = [
        f"[NestedComponent] is: {NestedComponent._description}",
        f"[NestedComponent] Component Rules: {NestedComponent._rules}",
        f"[NestedComponent] Required components: [{Text.parse()}]",
        f"[NestedComponent] Allowed components: [{Header.parse()}]",
    ]

    expected = "\n".join(expected_parts)
    assert result == expected
    assert "\\" not in result  # No escape characters should be present


def test_parse_component_with_special_characters():
    """Test that special characters are handled without escaping"""

    class SpecialComponent(Component):
        _description = "Component with \"quotes\" and 'apostrophes'"
        _rules = ["Rule with 'quotes'", 'Rule with "double quotes"']

    result = SpecialComponent.parse()

    expected = (
        f"[SpecialComponent] is: {SpecialComponent._description}\n"
        + f"[SpecialComponent] Component Rules: {SpecialComponent._rules}"
    )

    assert result == expected
    assert "\\" not in result  # No escape characters should be present


def test_parse_component_string_representation():
    """Test that component string representation is clean and readable"""

    class SimpleComponent(Component):
        _description = "Simple component with 'quotes' and newlines\n"
        _rules = ["Rule with 'quotes'"]

    result = SimpleComponent.parse()

    # Verify quotes and newlines are handled properly
    assert "Simple component with 'quotes' and newlines" in result
    assert "Rule with 'quotes'" in result
    assert "\\n" not in result  # Should not contain escaped newlines
    assert '"\\n"' not in result  # Should not contain escaped quotes
