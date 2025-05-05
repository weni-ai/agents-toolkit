import pytest

from weni.preprocessor.preprocessor import PreProcessor, ProcessedData
from weni.context.preprocessor_context import PreProcessorContext


def test_preprocessor_execution():
    """Test basic PreProcessor execution"""

    class TestPreProcessor(PreProcessor):
        def process(self, context: PreProcessorContext) -> ProcessedData:
            return ProcessedData("test-urn", "en", {"test": "data"})

    context = PreProcessorContext(params={}, payload={}, credentials={})
    result = TestPreProcessor(context)

    assert result.urn == "test-urn"
    assert result.language == "en"
    assert result.data == {"test": "data"}


def test_preprocessor_without_process_implementation():
    """Test PreProcessor without process implementation"""

    class EmptyPreProcessor(PreProcessor):
        pass

    context = PreProcessorContext(params={}, payload={}, credentials={})
    
    with pytest.raises(NotImplementedError) as excinfo:
        EmptyPreProcessor(context)
    
    assert "Subclasses must implement the process method" in str(excinfo.value)


def test_preprocessor_context_access():
    """Test PreProcessor access to context values"""

    class ContextAccessPreProcessor(PreProcessor):
        def process(self, context: PreProcessorContext) -> ProcessedData:
            return ProcessedData(
                "test-urn",
                "en",
                {
                    "param": context.params.get("key"),
                    "payload": context.payload.get("data"),
                    "credential": context.credentials.get("api_key"),
                }
            )

    context = PreProcessorContext(
        params={"key": "value"},
        payload={"data": "content"},
        credentials={"api_key": "secret123"}
    )

    result = ContextAccessPreProcessor(context)
    
    assert result.urn == "test-urn"
    assert result.language == "en"
    assert result.data == {
        "param": "value",
        "payload": "content",
        "credential": "secret123"
    }


def test_preprocessor_context_immutability():
    """Test Context immutability in PreProcessor"""

    class MutablePreProcessor(PreProcessor):
        def process(self, context: PreProcessorContext) -> ProcessedData:
            # Try to modify context
            context.params["new_key"] = "value"  # type: ignore[index]
            return ProcessedData("test-urn", "en", {})

    context = PreProcessorContext(params={"key": "value"}, payload={}, credentials={})
    
    with pytest.raises(TypeError):
        MutablePreProcessor(context)

def test_processed_data_creation():
    """Test ProcessedData creation"""
    
    result = ProcessedData("test-urn", "pt-br", {"key": "value"})
    
    assert result.urn == "test-urn"
    assert result.language == "pt-br"
    assert result.data == {"key": "value"}

