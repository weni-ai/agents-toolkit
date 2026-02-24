import pytest
from typing import Any, Mapping

from weni.preprocessor.preprocessor import PreProcessor, ProcessedData
from weni.context.preprocessor_context import PreProcessorContext
from weni.tracing import Traced, trace


def test_preprocessor_execution():
    """Test basic PreProcessor execution"""

    class TestPreProcessor(PreProcessor):
        def process(self, context: PreProcessorContext) -> ProcessedData:
            return ProcessedData("test-urn", {"test": "data"})

    context = PreProcessorContext(params={}, payload={}, credentials={}, project={})
    result = TestPreProcessor(context)

    assert result.urn == "test-urn"
    assert result.data == {"test": "data"}


def test_preprocessor_without_process_implementation():
    """Test PreProcessor without process implementation"""

    class EmptyPreProcessor(PreProcessor):
        pass

    context = PreProcessorContext(params={}, payload={}, credentials={}, project={})
    
    with pytest.raises(NotImplementedError) as excinfo:
        EmptyPreProcessor(context)
    
    assert "Subclasses must implement the process method" in str(excinfo.value)


def test_preprocessor_context_access():
    """Test PreProcessor access to context values"""

    class ContextAccessPreProcessor(PreProcessor):
        def process(self, context: PreProcessorContext) -> ProcessedData:
            return ProcessedData(
                "test-urn",
                {
                    "param": context.params.get("key"),
                    "payload": context.payload.get("data"),
                    "credential": context.credentials.get("api_key"),
                }
            )

    context = PreProcessorContext(
        params={"key": "value"},
        payload={"data": "content"},
        credentials={"api_key": "secret123"},
        project={"name": "Project 1", "uuid": "project-uuid"}
    )

    result = ContextAccessPreProcessor(context)
    
    assert result.urn == "test-urn"
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
            return ProcessedData("test-urn", {})

    context = PreProcessorContext(params={"key": "value"}, payload={}, credentials={}, project={})
    
    with pytest.raises(TypeError):
        MutablePreProcessor(context)

def test_processed_data_creation():
    """Test ProcessedData creation"""
    
    result = ProcessedData("test-urn", {"key": "value"})
    
    assert result.urn == "test-urn"
    assert result.data == {"key": "value"}


def test_preprocessor_with_traced_returns_tuple():
    """Test that PreProcessor with Traced returns tuple (ProcessedData, traces)"""
    
    class TracedPreProcessor(Traced, PreProcessor):
        def process(self, context: PreProcessorContext) -> ProcessedData:
            validated = self._validate(context)
            return ProcessedData("test-urn", {"data": validated})
        
        @trace()
        def _validate(self, context: PreProcessorContext) -> Mapping[Any, Any]:
            return context.payload
    
    context = PreProcessorContext(
        params={},
        payload={"test": "data"},
        credentials={},
        project={},
    )
    
    # PreProcessor with Traced should return tuple
    result = TracedPreProcessor(context)
    
    # Should return tuple (ProcessedData, traces)
    assert isinstance(result, tuple)
    assert len(result) == 2
    processed_data, traces = result
    
    # Verify ProcessedData
    assert isinstance(processed_data, ProcessedData)
    assert processed_data.urn == "test-urn"
    assert processed_data.data == {"data": {"test": "data"}}
    
    # Verify traces structure
    assert isinstance(traces, dict)
    assert "name" in traces
    assert traces["name"] == "TracedPreProcessor"
    assert "steps" in traces
    assert "started_at" in traces
    assert "status" in traces
    assert len(traces["steps"]) > 0  # Should have at least one step from _validate


def test_preprocessor_without_traced_returns_single_value():
    """Test that PreProcessor without Traced returns only ProcessedData"""
    
    class RegularPreProcessor(PreProcessor):
        def process(self, context: PreProcessorContext) -> ProcessedData:
            return ProcessedData("test-urn", {"test": "data"})
    
    context = PreProcessorContext(params={}, payload={}, credentials={}, project={})
    
    # PreProcessor without Traced should return only ProcessedData
    result = RegularPreProcessor(context)
    
    # Should return only ProcessedData, not a tuple
    assert not isinstance(result, tuple)
    assert isinstance(result, ProcessedData)
    assert result.urn == "test-urn"
    assert result.data == {"test": "data"}

