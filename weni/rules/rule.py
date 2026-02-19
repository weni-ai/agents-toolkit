from weni.preprocessor.preprocessor import ProcessedData
from typing import Any, Dict, Union

class Rule:
    """
    Base class for implementing rules.
    
    Note: When using Traced, the execute() method will automatically return
    a tuple (result, traces) instead of just the result. Code should handle both cases.
    """
    template: str = ""
    
    def execute(self, data: ProcessedData) -> Union[bool, tuple[bool, Dict[str, Any]]]:
        """
        Execute the rule's main functionality.
        
        Subclasses should override this method to implement their rule logic.
        
        Returns:
            bool: The result of the rule execution (True/False) when not using Traced
            tuple[bool, Dict[str, Any]]: If the class inherits from Traced and tracing is enabled,
                                        returns a tuple of (result, traces)
        
        Note:
            When using Traced, the return type changes to a tuple. Code should handle both cases:
            ```python
            result = rule.execute(data)
            if isinstance(result, tuple):
                bool_result, traces = result
            else:
                bool_result = result
            ```
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
    
    def _wrap_execute_result(self, result: bool) -> Union[bool, tuple[bool, Dict[str, Any]]]:
        """
        Wraps the execute result with trace information if Traced is used.
        
        Subclasses that override execute() directly should call this method to ensure
        trace support works correctly:
        
        ```python
        def execute(self, data: ProcessedData):
            result = self._my_logic(data)
            return self._wrap_execute_result(result)
        ```
        """
        # Se a instância herda de Traced e o trace está inicializado, retorna tupla com traces
        if hasattr(self, '_get_trace_summary') and hasattr(self, '_tracer_initialized'):
            if self._tracer_initialized:
                traces = self._get_trace_summary()
                return result, traces
        
        return result
    
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
