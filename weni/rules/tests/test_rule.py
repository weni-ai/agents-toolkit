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
    
    # Test execute method with data that should pass
    processed_data = ProcessedData("test-urn", {"test_key": "value"})
    assert rule.execute(processed_data) is True
    
    # Test execute method with data that should fail
    processed_data = ProcessedData("test-urn", {"other_key": "value"})
    assert rule.execute(processed_data) is False
    
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
        
        def _execute_impl(self, data: ProcessedData) -> bool:
            # Call a traced method to initialize the tracer
            validated = self._validate_data(data)
            return validated
        
        @trace()
        def _validate_data(self, data: ProcessedData) -> bool:
            # Simple rule logic
            return "test_key" in data.data and data.data["test_key"] == "value"
        
        def get_template_variables(self, data: Any) -> Dict:
            return {"variable": data.get("value", "")}
    
    rule = TracedRule()
    processed_data = ProcessedData("test-urn", {"test_key": "value"})
    
    # Execute should return tuple when Traced is used and @trace() methods are called
    result = rule.execute(processed_data)
    
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
        
        def _execute_impl(self, data: ProcessedData) -> bool:
            # Call a traced method to initialize the tracer
            return self._check_data(data)
        
        @trace()
        def _check_data(self, data: ProcessedData) -> bool:
            return False
        
        def get_template_variables(self, data: Any) -> Dict:
            return {}
    
    rule = TracedRule()
    processed_data = ProcessedData("test-urn", {})
    
    # Execute should return tuple when Traced is used and @trace() methods are called
    result = rule.execute(processed_data)
    
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
    """Test that Rule with Traced but no @trace() decorator returns only bool"""
    
    class TracedRuleWithoutTrace(Traced, Rule):
        template = "Test template"
        
        def _execute_impl(self, data: ProcessedData) -> bool:
            # No @trace() decorator on any method
            return "test_key" in data.data
        
        def get_template_variables(self, data: Any) -> Dict:
            return {}
    
    rule = TracedRuleWithoutTrace()
    processed_data = ProcessedData("test-urn", {"test_key": "value"})
    
    # Execute should return only bool when no @trace() methods are called
    result = rule.execute(processed_data)
    
    # Should return only bool, not a tuple
    assert not isinstance(result, tuple)
    assert isinstance(result, bool)
    assert result is True
