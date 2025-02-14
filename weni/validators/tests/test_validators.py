import pytest
from weni.components.component import ListMessage, QuickReplies
from weni.validators import validate_components
from weni.components import Component, Text, Header, Footer


def test_validate_components_valid():
    """Test validation passes with valid components"""
    assert validate_components([Text, Header, Footer]) is True


def test_validate_third_party_component():
    """Test that using a third-party component raises ValueError"""

    class ThirdPartyComponent(Component):
        pass

    with pytest.raises(ValueError) as exc:
        validate_components([ThirdPartyComponent])
    assert "is not an official component" in str(exc.value)


def test_validate_modified_string_attribute():
    """Test that modifying a string attribute (even with another string) raises ValueError"""
    original_description = Text._description
    try:
        Text._description = "New description"  # type: ignore
        with pytest.raises(ValueError) as exc:
            validate_components([Text])
        assert "has been modified" in str(exc.value)
        assert "Original value" in str(exc.value)
        assert "Current value" in str(exc.value)
    finally:
        Text._description = original_description  # type: ignore


def test_validate_modified_list_attribute():
    """Test that modifying a list attribute raises ValueError"""
    original_rules = Text._rules.copy()
    try:
        Text._rules = ["New rule"]  # type: ignore
        with pytest.raises(ValueError) as exc:
            validate_components([Text])
        assert "has been modified" in str(exc.value)
    finally:
        Text._rules = original_rules  # type: ignore


def test_validate_modified_component_lists():
    """Test that modifying component lists raises ValueError"""
    original_required = Text._required_components.copy()
    try:
        Text._required_components = [Header]  # type: ignore
        with pytest.raises(ValueError) as exc:
            validate_components([Text])
        assert "has been modified" in str(exc.value)
    finally:
        Text._required_components = original_required  # type: ignore


def test_empty_component_list():
    """Test validation with empty component list"""
    assert validate_components([]) is True


def test_multiple_components_validation():
    """Test validation with multiple components at once"""
    assert validate_components([Text, Header, Footer]) is True


def test_validate_modified_mutable_list():
    """Test that modifying a mutable list attribute (without reassignment) raises ValueError"""
    original_rules = Text._rules.copy()
    try:
        Text._rules.append("New rule")  # type: ignore
        with pytest.raises(ValueError) as exc:
            validate_components([Text])
        assert "has been modified" in str(exc.value)
    finally:
        Text._rules = original_rules  # type: ignore


def test_validate_nested_component_modification():
    """Test that modifying nested component attributes raises ValueError"""
    original_required = Text._required_components.copy()
    original_header_desc = Header._description
    try:
        Text._required_components = [Header]  # type: ignore
        Header._description = "Modified Header"  # type: ignore
        with pytest.raises(ValueError) as exc:
            validate_components([Text, Header])
        assert "has been modified" in str(exc.value)
    finally:
        Text._required_components = original_required  # type: ignore
        Header._description = original_header_desc  # type: ignore


def test_validate_none_attribute():
    """Test that setting an attribute to None raises ValueError"""
    original_description = Text._description
    try:
        Text._description = None  # type: ignore
        with pytest.raises(ValueError) as exc:
            validate_components([Text])
        assert "has been modified" in str(exc.value)
    finally:
        Text._description = original_description  # type: ignore


def test_validate_circular_reference():
    """Test that circular references in components are handled properly"""
    original_allowed = Text._allowed_components.copy()
    original_required = Header._required_components.copy()
    try:
        Text._allowed_components = [Header]  # type: ignore
        Header._required_components = [Text]  # type: ignore
        with pytest.raises(ValueError) as exc:
            validate_components([Text, Header])
        assert "has been modified" in str(exc.value)
    finally:
        Text._allowed_components = original_allowed  # type: ignore
        Header._required_components = original_required  # type: ignore


def test_validate_deep_copy_modification():
    """Test that using a deep copy of a component with modifications is caught"""
    import copy

    class ModifiedComponent(Component):
        _description = Text._description
        _rules = copy.deepcopy(Text._rules)
        _required_components = copy.deepcopy(Text._required_components)

    ModifiedComponent._rules.append("New rule")  # type: ignore

    with pytest.raises(ValueError) as exc:
        validate_components([ModifiedComponent])
    assert "is not an official component" in str(exc.value)


def test_validate_list_clear():
    """Test that clearing a list raises ValueError"""
    original_rules = ListMessage._rules.copy()
    try:
        ListMessage._rules.clear()  # type: ignore
        with pytest.raises(ValueError) as exc:
            validate_components([ListMessage])
        assert "has been modified" in str(exc.value)
    finally:
        ListMessage._rules = original_rules  # type: ignore


def test_validate_whitespace_modification():
    """Test that modifying whitespace in strings raises ValueError"""
    original_description = Text._description
    try:
        Text._description = Text._description.strip() + " "  # type: ignore
        with pytest.raises(ValueError) as exc:
            validate_components([Text])
        assert "has been modified" in str(exc.value)
    finally:
        Text._description = original_description  # type: ignore


def test_validate_case_modification():
    """Test that modifying string case raises ValueError"""
    original_description = Text._description
    try:
        Text._description = Text._description.upper()  # type: ignore
        with pytest.raises(ValueError) as exc:
            validate_components([Text])
        assert "has been modified" in str(exc.value)
    finally:
        Text._description = original_description  # type: ignore


def test_validate_list_element_modification():
    """Test that modifying individual list elements raises ValueError"""
    original_rules = QuickReplies._rules.copy()
    try:
        if QuickReplies._rules:  # Ensure there's at least one rule
            QuickReplies._rules[0] = QuickReplies._rules[0].upper()  # type: ignore
        with pytest.raises(ValueError) as exc:
            validate_components([QuickReplies])
        assert "has been modified" in str(exc.value)
    finally:
        QuickReplies._rules = original_rules  # type: ignore


def test_validate_list_slice_modification():
    """Test that modifying list slices raises ValueError"""
    original_rules = ListMessage._rules.copy()
    try:
        if len(ListMessage._rules) >= 2:
            ListMessage._rules[0:2] = ListMessage._rules[0:2][::-1]  # type: ignore
        with pytest.raises(ValueError) as exc:
            validate_components([ListMessage])
        assert "has been modified" in str(exc.value)
    finally:
        ListMessage._rules = original_rules  # type: ignore


def test_validate_unicode_modification():
    """Test that modifying strings with unicode equivalents raises ValueError"""
    original_description = Text._description
    try:
        # Replace 'a' with its unicode equivalent 'а' (Cyrillic)
        Text._description = Text._description.replace("a", "а")  # type: ignore
        with pytest.raises(ValueError) as exc:
            validate_components([Text])
        assert "has been modified" in str(exc.value)
    finally:
        Text._description = original_description  # type: ignore
