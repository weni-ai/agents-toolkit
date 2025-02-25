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
    original_format = Text._format_example.copy()
    try:
        Text._format_example = {"text": "New text value"}
        with pytest.raises(ValueError) as exc:
            validate_components([Text])
        assert "has been modified" in str(exc.value)
        assert "Original value" in str(exc.value)
        assert "Current value" in str(exc.value)
    finally:
        Text._format_example = original_format


def test_validate_modified_list_attribute():
    """Test that modifying a list attribute raises ValueError"""
    original_format = QuickReplies._format_example.copy()
    try:
        # Modify a list inside the format example
        QuickReplies._format_example = {"quick_replies": ["Modified", "List"]}
        with pytest.raises(ValueError) as exc:
            validate_components([QuickReplies])
        assert "has been modified" in str(exc.value)
    finally:
        QuickReplies._format_example = original_format


def test_validate_modified_component_lists():
    """Test that modifying nested dict values raises ValueError"""
    original_format = Header._format_example.copy()
    try:
        Header._format_example = {"header": {"type": "image", "text": "Modified header"}}
        with pytest.raises(ValueError) as exc:
            validate_components([Header])
        assert "has been modified" in str(exc.value)
    finally:
        Header._format_example = original_format


def test_empty_component_list():
    """Test validation with empty component list"""
    assert validate_components([]) is True


def test_multiple_components_validation():
    """Test validation with multiple components at once"""
    assert validate_components([Text, Header, Footer]) is True


def test_validate_modified_mutable_list():
    """Test that modifying a mutable list attribute (without reassignment) raises ValueError"""
    original_format = QuickReplies._format_example.copy()
    try:
        QuickReplies._format_example["quick_replies"].append("New option")
        with pytest.raises(ValueError) as exc:
            validate_components([QuickReplies])
        assert "has been modified" in str(exc.value)
    finally:
        QuickReplies._format_example = original_format


def test_validate_nested_component_modification():
    """Test that modifying nested component attributes raises ValueError"""
    original_text_format = Text._format_example.copy()
    original_header_format = Header._format_example.copy()
    try:
        # Modify two components
        Text._format_example = {"text": "Modified text"}
        Header._format_example = {"header": {"type": "text", "text": "Modified header"}}
        with pytest.raises(ValueError) as exc:
            validate_components([Text, Header])
        assert "has been modified" in str(exc.value)
    finally:
        Text._format_example = original_text_format
        Header._format_example = original_header_format


def test_validate_none_attribute():
    """Test that setting an attribute to None raises ValueError"""
    original_format = Text._format_example.copy()
    try:
        Text._format_example = None  # type: ignore
        with pytest.raises(ValueError) as exc:
            validate_components([Text])
        assert "has been modified" in str(exc.value)
    finally:
        Text._format_example = original_format


def test_validate_circular_reference():
    """Test that circular references in components are handled properly"""
    # Since we don't have component references anymore, we'll just test modifying two components
    original_text = Text._format_example.copy()
    original_header = Header._format_example.copy()
    try:
        Text._format_example = {"text": "Text references header"}
        Header._format_example = {"header": {"type": "text", "text": "Header references text"}}
        with pytest.raises(ValueError) as exc:
            validate_components([Text, Header])
        assert "has been modified" in str(exc.value)
    finally:
        Text._format_example = original_text
        Header._format_example = original_header


def test_validate_deep_copy_modification():
    """Test that using a deep copy of a component with modifications is caught"""
    import copy

    class ModifiedComponent(Component):
        _format_example = copy.deepcopy(Text._format_example)

    # Modify the copy
    ModifiedComponent._format_example["text"] = "Modified text"

    with pytest.raises(ValueError) as exc:
        validate_components([ModifiedComponent])
    assert "is not an official component" in str(exc.value)


def test_validate_list_clear():
    """Test that clearing a list raises ValueError"""
    original_format = ListMessage._format_example.copy()
    try:
        # Clear the list items in the format example
        ListMessage._format_example["list_message"]["list_items"] = []
        with pytest.raises(ValueError) as exc:
            validate_components([ListMessage])
        assert "has been modified" in str(exc.value)
    finally:
        ListMessage._format_example = original_format


def test_validate_whitespace_modification():
    """Test that modifying whitespace in strings raises ValueError"""
    original_format = Text._format_example.copy()
    try:
        Text._format_example = {"text": Text._format_example["text"] + " "}
        with pytest.raises(ValueError) as exc:
            validate_components([Text])
        assert "has been modified" in str(exc.value)
    finally:
        Text._format_example = original_format


def test_validate_case_modification():
    """Test that modifying string case raises ValueError"""
    original_format = Text._format_example.copy()
    try:
        Text._format_example = {"text": Text._format_example["text"].upper()}
        with pytest.raises(ValueError) as exc:
            validate_components([Text])
        assert "has been modified" in str(exc.value)
    finally:
        Text._format_example = original_format


def test_validate_list_element_modification():
    """Test that modifying individual list elements raises ValueError"""
    original_format = QuickReplies._format_example.copy()
    try:
        if QuickReplies._format_example["quick_replies"]:  # Ensure there's at least one reply
            QuickReplies._format_example["quick_replies"][0] = QuickReplies._format_example["quick_replies"][0].upper()
        with pytest.raises(ValueError) as exc:
            validate_components([QuickReplies])
        assert "has been modified" in str(exc.value)
    finally:
        QuickReplies._format_example = original_format


def test_validate_list_slice_modification():
    """Test that modifying list slices raises ValueError"""
    original_format = QuickReplies._format_example.copy()
    try:
        quick_replies = QuickReplies._format_example["quick_replies"]
        if len(quick_replies) >= 2:
            QuickReplies._format_example["quick_replies"] = quick_replies[::-1]  # Reverse the list
        with pytest.raises(ValueError) as exc:
            validate_components([QuickReplies])
        assert "has been modified" in str(exc.value)
    finally:
        QuickReplies._format_example = original_format


def test_validate_unicode_modification():
    """Test that modifying strings with unicode equivalents raises ValueError"""
    original_format = Text._format_example.copy()
    try:
        # Replace 'a' with its unicode equivalent 'а' (Cyrillic)
        Text._format_example = {"text": Text._format_example["text"].replace("a", "а")}
        with pytest.raises(ValueError) as exc:
            validate_components([Text])
        assert "has been modified" in str(exc.value)
    finally:
        Text._format_example = original_format
