import pytest
from typing import Any, Dict

from weni.rules.rule import Rule
from weni.preprocessor.preprocessor import ProcessedData


def test_rule_without_implementation():
    """Test Rule class without implementing required methods"""
    
    rule = Rule()
    
    # Test that execute raises NotImplementedError
    with pytest.raises(NotImplementedError) as excinfo:
        rule.execute(ProcessedData("test-urn", "en", {}))
    assert "Subclasses must implement the execute method" in str(excinfo.value)
    
    # Test that get_template_variables raises NotImplementedError
    with pytest.raises(NotImplementedError) as excinfo:
        rule.get_template_variables({})
    assert "Subclasses must implement the get_template_variables method" in str(excinfo.value)


def test_rule_implementation():
    """Test a concrete implementation of the Rule class"""
    
    class TestRule(Rule):
        template = "This is a template with {variable}"
        
        def execute(self, data: ProcessedData) -> bool:
            # Simple rule that checks if a key exists in the data
            if "test_key" not in data.data:
                return False
            return data.data["test_key"] == "value"
        
        def get_template_variables(self, data: Any) -> Dict:
            return {"variable": data.get("value", "")}
    
    # Create an instance of our concrete implementation
    rule = TestRule()
    
    # Test the template attribute
    assert rule.template == "This is a template with {variable}"
    
    # Test execute method with data that should pass
    processed_data = ProcessedData("test-urn", "en", {"test_key": "value"})
    assert rule.execute(processed_data) is True
    
    # Test execute method with data that should fail
    processed_data = ProcessedData("test-urn", "en", {"other_key": "value"})
    assert rule.execute(processed_data) is False
    
    # Test get_template_variables method
    test_data = {"value": "test_value"}
    template_vars = rule.get_template_variables(test_data)
    assert template_vars == {"variable": "test_value"}
    
    # Test with missing data
    empty_data = {}
    template_vars = rule.get_template_variables(empty_data)
    assert template_vars == {"variable": ""}
