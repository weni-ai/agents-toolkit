from weni.preprocessor.preprocessor import ProcessedData
from typing import Any, Dict

class Rule:
    """
    Base class for implementing rules.
    
    Rules can be used in two ways:
    1. Direct execution: `result, traces = Rule(processed_data)` - returns (bool, traces)
    2. Instance execution: `rule = Rule()` then `result = rule.execute(processed_data)` - returns bool
    
    The execute() method should return only bool. The traces are automatically added by __new__()
    when called directly. When using execute() on an instance, it returns only the boolean result.
    """
    template: str = ""
    
    def __new__(cls, data: ProcessedData = None):  # type: ignore
        """
        If called with ProcessedData, executes the rule and returns (result, traces).
        Otherwise, returns a normal instance.
        """
        instance = super().__new__(cls)
        
        # If no data provided, return instance normally
        if data is None:
            return instance
        
        # Execute the rule - execute() returns only bool
        result = instance.execute(data)
        
        # Always returns traces. If the instance inherits from Traced and the trace is initialized,
        # retrieves the traces. Otherwise, returns an empty dictionary.
        traces = {}
        if hasattr(instance, '_get_trace_summary') and hasattr(instance, '_tracer_initialized'):
            if instance._tracer_initialized:
                traces = instance._get_trace_summary()
        
        return result, traces
    
    def execute(self, data: ProcessedData) -> bool:
        """
        Execute the rule's main functionality.
        
        Subclasses should override this method to implement their rule logic.
        The method should return only the boolean result. Traces are automatically added
        when using Rule(data) directly via __new__().
        
        Returns:
            bool: The result of the rule execution (True/False)
        
        Example:
            ```python
            def execute(self, data: ProcessedData) -> bool:
                # Simple rule logic - return only bool
                return "test_key" in data.data and data.data["test_key"] == "value"
            ```
        """
        raise NotImplementedError("Subclasses must implement the execute method")
    
    def get_template_variables(self, data: Any) -> Dict:
        """
        Get template variables from the data.
        
        Subclasses should override this method to extract template variables from the data.
        
        Args:
            data (Any): The data to extract template variables from
            
        Returns:
            Dict: Dictionary with template variable names as keys and their values
        """
        raise NotImplementedError("Subclasses must implement the get_template_variables method")
