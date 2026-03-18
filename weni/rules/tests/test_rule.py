import pytest
from typing import Any, Dict

from weni.rules.rule import Rule
from weni.preprocessor.preprocessor import ProcessedData
from weni.tracing import Traced, trace


def test_rule_without_implementation():
    """Test Rule class without implementing required methods"""
    
    rule = Rule()
    
    # Test that execute raises NotImplementedError
    with pytest.raises(NotImplementedError) as excinfo:
        rule.execute(ProcessedData("test-urn", {}))
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
    
    # Test execute method with data that should pass - returns only bool
    processed_data = ProcessedData("test-urn", {"test_key": "value"})
    result = rule.execute(processed_data)
    assert result is True
    
    # Test execute method with data that should fail - returns only bool
    processed_data = ProcessedData("test-urn", {"other_key": "value"})
    result = rule.execute(processed_data)
    assert result is False
    
    # Test using Rule(data) directly - returns (bool, traces)
    processed_data = ProcessedData("test-urn", {"test_key": "value"})
    result, traces = TestRule(processed_data)
    assert result is True
    assert traces == {}
    
    # Test get_template_variables method
    test_data = {"value": "test_value"}
    template_vars = rule.get_template_variables(test_data)
    assert template_vars == {"variable": "test_value"}
    
    # Test with missing data
    empty_data = {}
    template_vars = rule.get_template_variables(empty_data)
    assert template_vars == {"variable": ""}


def test_rule_with_traced_returns_tuple():
    """Test that Rule with Traced returns tuple (result, traces) when @trace() is used"""
    
    class TracedRule(Traced, Rule):
        template = "Test template"
        
        def execute(self, data: ProcessedData) -> bool:
            # Call a traced method to initialize the tracer
            return self._validate_data(data)
        
        @trace()
        def _validate_data(self, data: ProcessedData) -> bool:
            # Simple rule logic
            return "test_key" in data.data and data.data["test_key"] == "value"
        
        def get_template_variables(self, data: Any) -> Dict:
            return {"variable": data.get("value", "")}
    
    processed_data = ProcessedData("test-urn", {"test_key": "value"})
    
    # Using Rule(data) directly - should return tuple (bool, traces)
    result = TracedRule(processed_data)
    
    # Should return tuple (bool, traces)
    assert isinstance(result, tuple)
    assert len(result) == 2
    bool_result, traces = result
    
    # Verify boolean result
    assert bool_result is True
    
    # Verify traces structure
    assert isinstance(traces, dict)
    assert "name" in traces
    assert traces["name"] == "TracedRule"
    assert "steps" in traces
    assert len(traces["steps"]) > 0  # Should have steps from _validate_data
    assert "started_at" in traces
    assert "status" in traces


def test_rule_with_traced_false_result():
    """Test that Rule with Traced returns tuple even when result is False"""
    
    class TracedRule(Traced, Rule):
        template = "Test template"
        
        def execute(self, data: ProcessedData) -> bool:
            # Call a traced method to initialize the tracer
            return self._check_data(data)
        
        @trace()
        def _check_data(self, data: ProcessedData) -> bool:
            return False
        
        def get_template_variables(self, data: Any) -> Dict:
            return {}
    
    processed_data = ProcessedData("test-urn", {})
    
    # Using Rule(data) directly - should return tuple (bool, traces)
    result = TracedRule(processed_data)
    
    # Should return tuple (bool, traces)
    assert isinstance(result, tuple)
    assert len(result) == 2
    bool_result, traces = result
    
    # Verify boolean result is False
    assert bool_result is False
    
    # Verify traces are still returned
    assert isinstance(traces, dict)
    assert "name" in traces
    assert traces["name"] == "TracedRule"
    assert "steps" in traces
    assert len(traces["steps"]) > 0  # Should have steps from _check_data


def test_rule_with_traced_no_trace_decorator():
    """Test that Rule with Traced but no @trace() decorator returns tuple with empty traces"""
    
    class TracedRuleWithoutTrace(Traced, Rule):
        template = "Test template"
        
        def execute(self, data: ProcessedData) -> bool:
            # No @trace() decorator on any method
            return "test_key" in data.data
        
        def get_template_variables(self, data: Any) -> Dict:
            return {}
    
    processed_data = ProcessedData("test-urn", {"test_key": "value"})
    
    # Using Rule(data) directly - should return tuple (bool, traces)
    result = TracedRuleWithoutTrace(processed_data)
    
    # Should return tuple (bool, traces) even when no @trace() methods are called
    assert isinstance(result, tuple)
    assert len(result) == 2
    bool_result, traces = result
    assert isinstance(bool_result, bool)
    assert bool_result is True
    # Traces should be empty dict when no @trace() decorator is used
    assert traces == {}
