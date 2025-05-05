from weni.preprocessor.preprocessor import ProcessedData
from typing import Any, Dict

class Rule:
    """
    Base class for implementing rules.
    """
    template: str = ""
    
    def execute(self, data: ProcessedData) -> bool:
        """
        Execute the rule's main functionality.
        """
        raise NotImplementedError("Subclasses must implement the execute method")
    
    def get_template_variables(self, data: Any) -> Dict:
        raise NotImplementedError("Subclasses must implement the get_template_variables method")
