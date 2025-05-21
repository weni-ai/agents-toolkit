from weni.context.preprocessor_context import PreProcessorContext
from typing import Any

class ProcessedData:
    """
    The data that is processed by the preprocessor.
    """
    def __init__(self, urn: str, data: Any):
        self.urn = urn
        self.data = data


class PreProcessor:
    """
    The base class for implementing preprocessors.
    
    Preprocessors are used to preprocess the input data before it is processed by the rules.
    They can be used to extract information from the input data, transform it, or even replace it.
    
    Example:
    ```python
    class MyPreProcessor(PreProcessor):
        def process(self, context: PreProcessorContext) -> ProcessedData:
            return ProcessedData(context.urn, context.data)
    ```
    
    The preprocessor execution flow is:
    1. The preprocessor receives a PreProcessorContext object with the input data
    2. The process() method is called with the context
    3. The preprocessor performs its business logic using the context data
    4. The preprocessor returns a ProcessedData object with the processed data
    """
    def __new__(cls, context: PreProcessorContext) -> ProcessedData:  # type: ignore
        instance = super().__new__(cls)
        return instance.process(context)

    def process(self, context: PreProcessorContext) -> ProcessedData:
        """
        Process the input context and return a new context with the processed data.
        
        Args:
            context (PreProcessorContext): The input context to process

        Returns:
            ProcessedData: The processed data
            
        Example:
        ```python
        class MyPreProcessor(PreProcessor):
            def process(self, context: PreProcessorContext) -> ProcessedData:
                return ProcessedData(context.urn, context.data)
        ```
        """
        raise NotImplementedError("Subclasses must implement the process method")

