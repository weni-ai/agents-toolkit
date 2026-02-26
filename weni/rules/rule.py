from weni.preprocessor.preprocessor import ProcessedData
from typing import Any, Dict

class Rule:
    """
    Base class for implementing rules.
    
    The execute() method always returns a tuple (result, traces).
    If Traced is used and tracing is enabled, traces will contain execution trace data.
    Otherwise, traces will be an empty dictionary.
    """
    template: str = ""
    
    def execute(self, data: ProcessedData) -> tuple[bool, Dict[str, Any]]:
        """
        Execute the rule's main functionality.
        
        Subclasses should override this method to implement their rule logic.
        
        Returns:
            tuple[bool, Dict[str, Any]]: Always returns a tuple of (result, traces).
                                        If the class inherits from Traced and tracing is enabled,
                                        traces will contain the execution trace data.
                                        Otherwise, traces will be an empty dictionary.
        """
        # Chama a implementação da subclasse
        # Se a subclasse sobrescreveu execute(), o Python vai chamar o método da subclasse
        # através do mecanismo de herança normal, então este método não será chamado.
        # Para que o trace funcione, subclasses que usam Traced devem chamar
        # super().execute(data) ou usar _wrap_execute_result() manualmente.
        result = self._execute_impl(data)
        return self._wrap_execute_result(result)
    
    def _execute_impl(self, data: ProcessedData) -> bool:
        """
        Internal implementation of execute. 
        
        Subclasses should override this method to implement their rule logic.
        The execute() method will automatically handle trace return if Traced is used.
        """
        raise NotImplementedError("Subclasses must implement the execute method")
    
    def _wrap_execute_result(self, result: bool) -> tuple[bool, Dict[str, Any]]:
        """
        Wraps the execute result with trace information.
        
        Always returns a tuple (result, traces). If Traced is used and tracing is enabled,
        traces will contain the execution trace data. Otherwise, traces will be an empty dictionary.
        
        Subclasses that override execute() directly should call this method to ensure
        trace support works correctly:
        
        ```python
        def execute(self, data: ProcessedData):
            result = self._my_logic(data)
            return self._wrap_execute_result(result)
        ```
        """
        # If the instance inherits from Traced and the trace is initialized, it obtains the traces.
        if hasattr(self, '_get_trace_summary') and hasattr(self, '_tracer_initialized'):
            if self._tracer_initialized:
                traces = self._get_trace_summary()
                return result, traces
        
        # Otherwise, it returns an empty dictionary.
        return result, {}
    
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
