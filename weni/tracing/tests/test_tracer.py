"""
Tests for the tracing module.
"""

import pytest
from unittest.mock import patch
from typing import Any, Mapping
from weni.tracing import (
    TracedAgent,
    trace,
    ExecutionTrace,
    ExecutionStep,
    StepStatus,
)
from weni.tool import Tool
from weni.context import Context
from weni.responses import TextResponse, ResponseObject
from weni.preprocessor import PreProcessor, ProcessedData
from weni.context.preprocessor_context import PreProcessorContext


def clear_tracer(instance: TracedAgent) -> None:
    """Helper to clear tracer state."""
    if hasattr(instance, "_execution_trace"):
        del instance._execution_trace
    instance._tracer_initialized = False


class TestTracedTool(TracedAgent, Tool):
    """Test Tool with tracing enabled."""

    def execute(self, context: Context) -> ResponseObject:
        result = self._process_data(context)
        response: ResponseObject = TextResponse(data=result)  # type: ignore
        data, format = response
        # Trace is automatically returned separately by Tool.__new__
        return data, format

    @trace()
    def _process_data(self, context: Context) -> dict:
        return {"processed": True, "value": 42}


class TestTracedPreProcessor(TracedAgent, PreProcessor):
    """Test PreProcessor with tracing enabled."""

    def process(self, context: PreProcessorContext) -> ProcessedData:
        validated = self._validate(context)
        data = {"data": validated}
        # Trace is automatically returned separately by PreProcessor.__new__
        return ProcessedData("test-urn", data)

    @trace()
    def _validate(self, context: PreProcessorContext) -> Mapping[Any, Any]:
        return context.payload


def test_trace_decorator_basic():
    """Test basic trace decorator functionality."""
    tool = object.__new__(TestTracedTool)
    tool._auto_init_tracer()

    result = tool._process_data(
        Context(
            credentials={},
            parameters={},
            globals={},
            contact={},
            project={},
            constants={},
        )
    )

    assert result == {"processed": True, "value": 42}
    assert hasattr(tool, "_execution_trace")
    assert len(tool._execution_trace.steps) >= 2  # STARTED and COMPLETED

    # Check that we have both STARTED and COMPLETED steps
    started_steps = [s for s in tool._execution_trace.steps if s.status == StepStatus.STARTED]
    completed_steps = [s for s in tool._execution_trace.steps if s.status == StepStatus.COMPLETED]

    assert len(started_steps) > 0
    assert len(completed_steps) > 0


def test_trace_with_error():
    """Test trace decorator captures errors."""

    class FailingTool(TracedAgent, Tool):
        @trace()
        def _failing_method(self):
            raise ValueError("Test error")

    tool = object.__new__(FailingTool)
    tool._auto_init_tracer()

    with pytest.raises(ValueError):
        tool._failing_method()

    assert hasattr(tool, "_execution_trace")
    failed_steps = [s for s in tool._execution_trace.steps if s.status == StepStatus.FAILED]
    assert len(failed_steps) > 0
    assert tool._execution_trace.status == "failed"
    assert "ValueError" in tool._execution_trace.error_summary


def test_trace_capture_input_output():
    """Test trace captures input and output."""

    class TestTool(TracedAgent, Tool):
        @trace(capture_input=True, capture_output=True)
        def _test_method(self, arg1: str, arg2: int = 10) -> dict:
            return {"result": f"{arg1}_{arg2}"}

    tool = object.__new__(TestTool)
    tool._auto_init_tracer()

    result = tool._test_method("test", arg2=20)

    assert result == {"result": "test_20"}
    
    # Find the step by index (STARTED and COMPLETED share the same step_index)
    started_steps = [s for s in tool._execution_trace.steps if s.status == StepStatus.STARTED]
    completed_steps = [s for s in tool._execution_trace.steps if s.status == StepStatus.COMPLETED]
    
    assert len(started_steps) > 0
    assert len(completed_steps) > 0
    
    # Input data is in STARTED step
    started_step = started_steps[0]
    assert started_step.input_data is not None
    assert "arg1" in started_step.input_data
    assert started_step.input_data["arg1"] == "test"
    assert "arg2" in started_step.input_data
    assert started_step.input_data["arg2"] == 20
    
    # Output data is in COMPLETED step
    completed_step = completed_steps[0]
    assert completed_step.output_data is not None
    assert completed_step.output_data == {"result": "test_20"}


def test_trace_no_capture():
    """Test trace without capturing input/output."""

    class TestTool(TracedAgent, Tool):
        @trace(capture_input=False, capture_output=False)
        def _test_method(self, sensitive_data: str) -> str:
            return "secret_token"

    tool = object.__new__(TestTool)
    tool._auto_init_tracer()

    result = tool._test_method("password123")

    assert result == "secret_token"
    started_steps = [s for s in tool._execution_trace.steps if s.status == StepStatus.STARTED]
    completed_steps = [s for s in tool._execution_trace.steps if s.status == StepStatus.COMPLETED]

    if started_steps:
        assert started_steps[0].input_data is None
    if completed_steps:
        assert completed_steps[0].output_data is None


def test_traced_agent_auto_init():
    """Test automatic tracer initialization."""

    class TestTool(TracedAgent, Tool):
        @trace()
        def _test_method(self):
            return "ok"

    tool = object.__new__(TestTool)
    # Don't manually init, let @trace do it
    result = tool._test_method()

    assert result == "ok"
    assert tool._tracer_initialized
    assert hasattr(tool, "_execution_trace")


def test_traced_agent_custom_name():
    """Test custom name."""

    class TestTool(TracedAgent, Tool):
        NAME = "CustomName"

        @trace()
        def _test_method(self):
            return "ok"

    tool = object.__new__(TestTool)
    tool._auto_init_tracer()

    assert tool._execution_trace.name == "CustomName"


def test_traced_agent_default_name():
    """Test default name (class name)."""

    class MyCustomTool(TracedAgent, Tool):
        @trace()
        def _test_method(self):
            return "ok"

    tool = object.__new__(MyCustomTool)
    tool._auto_init_tracer()

    assert tool._execution_trace.name == "MyCustomTool"


def test_get_trace_summary():
    """Test trace summary generation."""

    class TestTool(TracedAgent, Tool):
        @trace()
        def _step1(self):
            return "step1_result"

        @trace()
        def _step2(self):
            return "step2_result"

    tool = object.__new__(TestTool)
    tool._auto_init_tracer()

    tool._step1()
    tool._step2()

    summary = tool._get_trace_summary()

    assert "name" in summary
    assert "started_at" in summary
    assert "completed_at" in summary
    assert "total_duration_ms" in summary
    assert "status" in summary
    assert "total_steps" in summary
    assert "steps" in summary
    assert len(summary["steps"]) == 2


def test_inject_trace():
    """Test trace injection into data."""

    class TestTool(TracedAgent, Tool):
        @trace()
        def _test_method(self):
            return {"data": "value"}

    tool = object.__new__(TestTool)
    tool._auto_init_tracer()

    tool._test_method()
    data = {"result": "test"}
    result = tool._inject_trace(data)

    assert "_execution_trace" in result
    assert result["_execution_trace"]["name"] == "TestTool"


def test_inject_trace_not_dict():
    """Test trace injection with non-dict data."""

    class TestTool(TracedAgent, Tool):
        @trace()
        def _test_method(self):
            return "string_result"

    tool = object.__new__(TestTool)
    tool._auto_init_tracer()

    tool._test_method()
    result = tool._inject_trace("not_a_dict")

    assert result == "not_a_dict"
    assert "_execution_trace" not in result


def test_reset_tracer():
    """Test tracer reset."""

    class TestTool(TracedAgent, Tool):
        @trace()
        def _test_method(self):
            return "ok"

    tool = object.__new__(TestTool)
    tool._auto_init_tracer()
    tool._test_method()

    assert tool._tracer_initialized
    assert hasattr(tool, "_execution_trace")

    tool._reset_tracer()

    assert not tool._tracer_initialized
    assert not hasattr(tool, "_execution_trace")


def test_traced_tool_integration():
    """Test TracedAgent with Tool integration."""

    context = Context(
        credentials={},
        parameters={},
        globals={},
        contact={},
        project={},
        constants={},
    )

    # Use Tool.__new__ to test the actual integration with trace return
    result = TestTracedTool(context)
    
    # Tool with Traced returns (result, format, events, traces)
    assert len(result) == 4
    data, format, events, traces = result

    # Trace should be returned separately, not injected in data
    assert "_execution_trace" not in data
    assert data["processed"] is True
    assert isinstance(traces, dict)
    assert "name" in traces
    assert traces["name"] == "TestTracedTool"
    assert "steps" in traces


def test_traced_preprocessor_integration():
    """Test TracedAgent with PreProcessor integration."""

    context = PreProcessorContext(
        params={},
        payload={"test": "data"},
        credentials={},
        project={},
    )

    # Use PreProcessor.__new__ to test the actual integration with trace return
    result = TestTracedPreProcessor(context)

    # PreProcessor with Traced returns (ProcessedData, traces)
    assert isinstance(result, tuple)
    assert len(result) == 2
    processed_data, traces = result

    # Trace should be returned separately, not injected in data
    assert "_execution_trace" not in processed_data.data
    assert processed_data.data["data"] == {"test": "data"}
    assert isinstance(traces, dict)
    assert "name" in traces
    assert traces["name"] == "TestTracedPreProcessor"
    assert "steps" in traces


def test_backwards_compatibility_aliases():
    """Test that backwards compatibility aliases exist."""
    from weni.tracing import TracedProcessor, ExecutionTracerMixin

    assert TracedProcessor is TracedAgent
    assert ExecutionTracerMixin is TracedAgent


def test_serialize_value_none():
    """Test _serialize_value with None."""
    from weni.tracing.tracer import _serialize_value

    assert _serialize_value(None) is None


def test_serialize_value_primitives():
    """Test _serialize_value with primitive types."""
    from weni.tracing.tracer import _serialize_value

    assert _serialize_value("test") == "test"
    assert _serialize_value(42) == 42
    assert _serialize_value(3.14) == 3.14
    assert _serialize_value(True) is True
    assert _serialize_value(False) is False


def test_serialize_value_long_string():
    """Test _serialize_value with long string (truncation)."""
    from weni.tracing.tracer import _serialize_value

    long_string = "a" * 2000
    result = _serialize_value(long_string, max_length=1000)
    assert len(result) == 1014  # 1000 + "...<truncated>" (14 chars)
    assert result.endswith("...<truncated>")


def test_serialize_value_list():
    """Test _serialize_value with list."""
    from weni.tracing.tracer import _serialize_value

    result = _serialize_value([1, 2, 3])
    assert result == [1, 2, 3]


def test_serialize_value_long_list():
    """Test _serialize_value with long list (truncation)."""
    from weni.tracing.tracer import _serialize_value

    long_list = list(range(100))
    result = _serialize_value(long_list, max_length=1000)
    assert len(result) == 51  # 50 items + "<50 more items>"
    assert "<50 more items>" in result


def test_serialize_value_dict():
    """Test _serialize_value with dict."""
    from weni.tracing.tracer import _serialize_value

    result = _serialize_value({"key": "value", "num": 42})
    assert result == {"key": "value", "num": 42}


def test_serialize_value_long_dict():
    """Test _serialize_value with long dict (truncation)."""
    from weni.tracing.tracer import _serialize_value

    long_dict = {f"key_{i}": f"value_{i}" for i in range(100)}
    result = _serialize_value(long_dict, max_length=1000)
    assert len(result) == 51  # 50 items + "<truncated>" key
    assert "<truncated>" in result


def test_serialize_value_max_depth():
    """Test _serialize_value with max_depth exceeded."""
    from weni.tracing.tracer import _serialize_value

    nested = {"level1": {"level2": {"level3": "deep"}}}
    result = _serialize_value(nested, max_depth=2)
    # Should still serialize but with limited depth
    assert isinstance(result, dict)


def test_serialize_value_max_depth_zero():
    """Test _serialize_value with max_depth=0."""
    from weni.tracing.tracer import _serialize_value

    result = _serialize_value({"key": "value"}, max_depth=0)
    assert result == "<max_depth_exceeded>"


def test_serialize_value_object_with_dict():
    """Test _serialize_value with object that has __dict__."""
    from weni.tracing.tracer import _serialize_value

    class TestObj:
        def __init__(self):
            self.value = "test"

    obj = TestObj()
    result = _serialize_value(obj)
    assert result == "<TestObj>"


def test_serialize_value_other_types():
    """Test _serialize_value with other types (fallback to str)."""
    from weni.tracing.tracer import _serialize_value

    # Test with a set (not in the specific cases)
    result = _serialize_value({1, 2, 3}, max_length=10)
    assert isinstance(result, str)
    assert len(result) <= 10


def test_extract_args_exception():
    """Test _extract_args when exception occurs."""
    from weni.tracing.tracer import _extract_args

    # Create a function that will cause an exception in signature inspection
    def test_func(self, arg1):
        pass

    # Force an exception by patching inspect.signature in the tracer module
    with patch("weni.tracing.tracer.inspect.signature", side_effect=Exception("Test exception")):
        result = _extract_args(test_func, (object(), "test"), {})
        # Should fall back to exception handler
        assert "args" in result
        assert isinstance(result["args"], list)


def test_trace_without_auto_init_tracer():
    """Test trace decorator when object doesn't have _auto_init_tracer."""

    class TestTool:
        @trace()
        def _test_method(self):
            return "ok"

    tool = TestTool()
    # Should not raise error, just execute normally
    result = tool._test_method()
    assert result == "ok"


def test_trace_without_execution_trace():
    """Test trace decorator when object doesn't have _execution_trace."""

    class TestTool:
        def _auto_init_tracer(self):
            # Don't create _execution_trace
            pass

        @trace()
        def _test_method(self):
            return "ok"

    tool = TestTool()
    result = tool._test_method()
    assert result == "ok"


def test_get_trace_summary_no_execution_trace():
    """Test _get_trace_summary when _execution_trace doesn't exist."""

    class TestTool(TracedAgent, Tool):
        pass

    tool = object.__new__(TestTool)
    summary = tool._get_trace_summary()
    assert summary == {}


def test_get_trace_summary_with_failed_step():
    """Test _get_trace_summary includes failed steps (covers branch 335->316)."""

    class TestTool(TracedAgent, Tool):
        @trace()
        def _failing_method(self):
            raise ValueError("Test error")

    tool = object.__new__(TestTool)
    tool._auto_init_tracer()

    try:
        tool._failing_method()
    except ValueError:
        pass

    # Verify that we have both STARTED and FAILED steps
    started_steps = [s for s in tool._execution_trace.steps if s.status == StepStatus.STARTED]
    failed_steps = [s for s in tool._execution_trace.steps if s.status == StepStatus.FAILED]
    
    assert len(started_steps) > 0
    assert len(failed_steps) > 0
    
    # Now get summary - this should process the FAILED step (branch 335->316)
    summary = tool._get_trace_summary()
    assert len(summary["steps"]) == 1
    assert summary["steps"][0]["status"] == "failed"
    assert "error" in summary["steps"][0]
    assert "duration_ms" in summary["steps"][0]
    # Ensure the FAILED branch (335->316) is covered
    assert summary["steps"][0]["error"] is not None
    assert summary["status"] == "failed"


def test_get_trace_summary_failed_step_branch_coverage():
    """Test _get_trace_summary with FAILED step to cover branch 335->316 specifically."""
    from weni.tracing import ExecutionStep, StepStatus

    class TestTool(TracedAgent, Tool):
        pass

    tool = object.__new__(TestTool)
    tool._auto_init_tracer()

    # Manually add a FAILED step to ensure branch 335->316 is covered
    # This directly tests the elif step.status == StepStatus.FAILED branch
    tool._execution_trace.steps.append(
        ExecutionStep(
            class_name="TestTool",
            method_name="_test_method",
            status=StepStatus.FAILED,
            step_index=0,
            error="Test error message",
            duration_ms=10.5,
        )
    )

    # Call _get_trace_summary - this will process the FAILED step (branch 335->316)
    summary = tool._get_trace_summary()
    
    # Verify the FAILED step was processed correctly
    assert len(summary["steps"]) == 1
    step = summary["steps"][0]
    assert step["status"] == "failed"
    assert step["error"] == "Test error message"
    assert step["duration_ms"] == 10.5
    assert step["class"] == "TestTool"
    assert step["method"] == "_test_method"


def test_get_trace_summary_datetime_parse_error():
    """Test _get_trace_summary handles datetime parse errors."""

    class TestTool(TracedAgent, Tool):
        @trace()
        def _test_method(self):
            return "ok"

    tool = object.__new__(TestTool)
    tool._auto_init_tracer()
    tool._test_method()

    # Corrupt the started_at to cause parse error
    tool._execution_trace.started_at = "invalid-date"

    summary = tool._get_trace_summary()
    # Should still work, just with duration 0.0
    assert "total_duration_ms" in summary
    assert summary["total_duration_ms"] == 0.0


def test_get_trace_summary_with_error_summary():
    """Test _get_trace_summary includes error_summary when present."""

    class TestTool(TracedAgent, Tool):
        @trace()
        def _failing_method(self):
            raise ValueError("Test error")

    tool = object.__new__(TestTool)
    tool._auto_init_tracer()

    try:
        tool._failing_method()
    except ValueError:
        pass

    summary = tool._get_trace_summary()
    assert "error_summary" in summary
    assert "ValueError" in summary["error_summary"]


def test_inject_trace_not_initialized():
    """Test _inject_trace when tracer not initialized."""

    class TestTool(TracedAgent, Tool):
        pass

    tool = object.__new__(TestTool)
    # Don't initialize tracer
    tool._tracer_initialized = False

    data = {"key": "value"}
    result = tool._inject_trace(data)

    # Should not inject trace
    assert "_execution_trace" not in result
    assert result == data

def test_inject_trace_not_dict_multiple_types():
    """Test _inject_trace with non-dict data (already tested, but ensuring coverage)."""

    class TestTool(TracedAgent, Tool):
        @trace()
        def _test_method(self):
            return "ok"

    tool = object.__new__(TestTool)
    tool._auto_init_tracer()
    tool._test_method()

    # Test with list
    result = tool._inject_trace([1, 2, 3])
    assert result == [1, 2, 3]

    # Test with string
    result = tool._inject_trace("string")
    assert result == "string"

    # Test with None
    result = tool._inject_trace(None)
    assert result is None


def test_reset_tracer_without_execution_trace():
    """Test _reset_tracer when _execution_trace doesn't exist."""

    class TestTool(TracedAgent, Tool):
        pass

    tool = object.__new__(TestTool)
    tool._tracer_initialized = True
    # Don't create _execution_trace

    tool._reset_tracer()

    assert not tool._tracer_initialized
    assert not hasattr(tool, "_execution_trace")


def test_step_status_enum():
    """Test StepStatus enum values."""
    assert StepStatus.STARTED == "started"
    assert StepStatus.COMPLETED == "completed"
    assert StepStatus.FAILED == "failed"


def test_execution_step_defaults():
    """Test ExecutionStep with default values."""
    step = ExecutionStep(
        class_name="TestClass",
        method_name="test_method",
        status=StepStatus.STARTED,
    )
    assert step.step_index == 0
    assert step.input_data is None
    assert step.output_data is None
    assert step.error is None
    assert step.duration_ms is None


def test_execution_trace_defaults():
    """Test ExecutionTrace with default values."""
    trace = ExecutionTrace()
    assert trace.name == ""
    assert trace.started_at == ""
    assert trace.status == "pending"
    assert trace.steps == []
    assert trace.error_summary is None


def test_trace_with_cls_parameter():
    """Test _extract_args with cls parameter (classmethod)."""

    class TestTool(TracedAgent, Tool):
        @trace()
        @classmethod
        def _class_method(cls, arg1: str) -> str:
            return f"class_{arg1}"

    tool = object.__new__(TestTool)
    tool._auto_init_tracer()

    # Note: classmethod won't work the same way, but test the extraction logic
    from weni.tracing.tracer import _extract_args

    def test_func(cls, arg1: str):
        pass

    result = _extract_args(test_func, (TestTool, "test"), {})
    assert "arg1" in result
    assert result["arg1"] == "test"


def test_get_trace_summary_with_started_only():
    """Test _get_trace_summary when only STARTED step exists (edge case)."""

    class TestTool(TracedAgent, Tool):
        pass

    tool = object.__new__(TestTool)
    tool._auto_init_tracer()

    # Manually add only a STARTED step
    from weni.tracing import ExecutionStep, StepStatus

    tool._execution_trace.steps.append(
        ExecutionStep(
            class_name="TestTool",
            method_name="_test",
            status=StepStatus.STARTED,
            step_index=0,
        )
    )

    summary = tool._get_trace_summary()
    # Steps without status (only STARTED, no COMPLETED/FAILED) should not appear
    assert len(summary["steps"]) == 0


def test_get_trace_summary_multiple_steps_same_index():
    """Test _get_trace_summary with multiple steps having same index (shouldn't happen but test edge case)."""

    class TestTool(TracedAgent, Tool):
        @trace()
        def _test1(self):
            return "ok"

        @trace()
        def _test2(self):
            return "ok"

    tool = object.__new__(TestTool)
    tool._auto_init_tracer()

    tool._test1()
    tool._test2()

    summary = tool._get_trace_summary()
    assert len(summary["steps"]) == 2
    assert summary["steps"][0]["order"] == 1
    assert summary["steps"][1]["order"] == 2


def test_auto_init_tracer_when_already_initialized():
    """Test _auto_init_tracer when already initialized."""

    class TestTool(TracedAgent, Tool):
        @trace()
        def _test_method(self):
            return "ok"

    tool = object.__new__(TestTool)
    tool._auto_init_tracer()
    first_trace = tool._execution_trace

    # Call again
    tool._auto_init_tracer()
    # Should be the same trace object
    assert tool._execution_trace is first_trace


def test_serialize_value_tuple():
    """Test _serialize_value with tuple."""
    from weni.tracing.tracer import _serialize_value

    result = _serialize_value((1, 2, 3))
    assert result == [1, 2, 3]  # Tuples are converted to lists


def test_serialize_value_long_tuple():
    """Test _serialize_value with long tuple (truncation)."""
    from weni.tracing.tracer import _serialize_value

    long_tuple = tuple(range(100))
    result = _serialize_value(long_tuple, max_length=1000)
    assert len(result) == 51  # 50 items + "<50 more items>"
    assert "<50 more items>" in result


def test_extract_args_with_cls():
    """Test _extract_args with cls parameter (classmethod scenario)."""
    from weni.tracing.tracer import _extract_args

    def class_method(cls, arg1: str, arg2: int = 10):
        pass

    # Simulate classmethod call: ClassName.method("test", arg2=20)
    result = _extract_args(class_method, (type, "test"), {"arg2": 20})
    assert "arg1" in result
    assert result["arg1"] == "test"
    assert "arg2" in result
    assert result["arg2"] == 20


def test_extract_args_only_kwargs():
    """Test _extract_args with only keyword arguments."""
    from weni.tracing.tracer import _extract_args

    def test_func(self, arg1: str, arg2: int = 10):
        pass

    # Only kwargs, no positional args (except self)
    result = _extract_args(test_func, (object(),), {"arg1": "test", "arg2": 20})
    assert result["arg1"] == "test"
    assert result["arg2"] == 20


def test_extract_args_self_without_args():
    """Test _extract_args when self/cls is in params but args_index >= len(args) (branch 116->118)."""
    from weni.tracing.tracer import _extract_args

    def test_func(self, arg1: str):
        pass

    # Call with empty args tuple - this covers the branch where
    # args_index (0) >= len(args) (0) when processing self/cls
    # The condition `if args_index < len(args)` will be False, so it won't increment
    result = _extract_args(test_func, (), {})
    # Should handle gracefully, self won't be in result
    assert isinstance(result, dict)
    # arg1 won't be in result either since no args provided
    assert "arg1" not in result


def test_extract_args_missing_parameter():
    """Test _extract_args when parameter is not in args or kwargs (branch 125->113)."""
    from weni.tracing.tracer import _extract_args

    def test_func(self, arg1: str, arg2: int = 10, arg3: str = "default"):
        pass

    # Provide only arg1 positionally, arg2 and arg3 have defaults but are not provided
    # When processing arg2: args_index=1, len(args)=2, so 1 < 2 is True, but arg2 is at index 1
    # Wait, that's not right. Let me think...
    # Actually: args = (self_obj, "test"), so args_index after self = 1
    # When processing arg1: args_index=1, len(args)=2, so we use args[1] = "test" ✓
    # When processing arg2: args_index=2, len(args)=2, so 2 < 2 is False
    # Then: elif arg2 in kwargs is False (kwargs is empty)
    # So it continues to next iteration - this is branch 125->113
    result = _extract_args(test_func, (object(), "test"), {})
    # arg1 should be captured
    assert "arg1" in result
    assert result["arg1"] == "test"
    # arg2 and arg3 won't be in result since they're not provided (covers branch 125->113)
    assert "arg2" not in result
    assert "arg3" not in result


def test_get_trace_summary_running_status():
    """Test _get_trace_summary converts 'running' status to 'completed'."""

    class TestTool(TracedAgent, Tool):
        @trace()
        def _test_method(self):
            return "ok"

    tool = object.__new__(TestTool)
    tool._auto_init_tracer()
    tool._test_method()

    # Status should be "running" initially
    assert tool._execution_trace.status == "running"

    summary = tool._get_trace_summary()
    # Should convert "running" to "completed"
    assert summary["status"] == "completed"


def test_get_trace_summary_empty_started_at():
    """Test _get_trace_summary with empty started_at."""

    class TestTool(TracedAgent, Tool):
        @trace()
        def _test_method(self):
            return "ok"

    tool = object.__new__(TestTool)
    tool._auto_init_tracer()
    tool._test_method()

    # Set empty started_at
    tool._execution_trace.started_at = ""

    summary = tool._get_trace_summary()
    # Should still work, just with duration 0.0
    assert summary["total_duration_ms"] == 0.0


def test_get_trace_summary_no_started_at():
    """Test _get_trace_summary when started_at is None/empty."""

    class TestTool(TracedAgent, Tool):
        pass

    tool = object.__new__(TestTool)
    tool._auto_init_tracer()
    tool._execution_trace.started_at = None

    summary = tool._get_trace_summary()
    assert summary["total_duration_ms"] == 0.0


def test_serialize_value_nested_structures():
    """Test _serialize_value with nested structures."""
    from weni.tracing.tracer import _serialize_value

    nested = {
        "list": [1, 2, {"nested": "value"}],
        "dict": {"key": [1, 2, 3]},
    }
    result = _serialize_value(nested)
    assert isinstance(result, dict)
    assert "list" in result
    assert "dict" in result


def test_serialize_value_with_custom_max_length():
    """Test _serialize_value with custom max_length."""
    from weni.tracing.tracer import _serialize_value

    long_string = "a" * 100
    result = _serialize_value(long_string, max_length=50)
    assert len(result) == 64  # 50 + "...<truncated>" (14 chars)
    assert result.endswith("...<truncated>")


def test_trace_decorator_preserves_function_metadata():
    """Test that trace decorator preserves function metadata."""

    class TestTool(TracedAgent, Tool):
        @trace()
        def _test_method(self, arg1: str) -> str:
            """Test docstring."""
            return "ok"

    tool = object.__new__(TestTool)
    # Check that function metadata is preserved
    assert tool._test_method.__name__ == "_test_method"
    assert "Test docstring" in tool._test_method.__doc__


def test_execution_step_with_all_fields():
    """Test ExecutionStep with all fields populated."""
    from weni.tracing import ExecutionStep, StepStatus

    step = ExecutionStep(
        class_name="TestClass",
        method_name="test_method",
        status=StepStatus.COMPLETED,
        step_index=1,
        input_data={"arg": "value"},
        output_data={"result": "ok"},
        error=None,
        duration_ms=10.5,
    )

    assert step.class_name == "TestClass"
    assert step.method_name == "test_method"
    assert step.status == StepStatus.COMPLETED
    assert step.step_index == 1
    assert step.input_data == {"arg": "value"}
    assert step.output_data == {"result": "ok"}
    assert step.error is None
    assert step.duration_ms == 10.5


def test_execution_trace_with_all_fields():
    """Test ExecutionTrace with all fields populated."""
    from weni.tracing import ExecutionTrace, ExecutionStep, StepStatus

    trace = ExecutionTrace(
        name="TestAgent",
        started_at="2024-01-01T00:00:00Z",
        status="completed",
        steps=[ExecutionStep("Test", "method", StepStatus.COMPLETED)],
        error_summary="Test error",
    )

    assert trace.name == "TestAgent"
    assert trace.started_at == "2024-01-01T00:00:00Z"
    assert trace.status == "completed"
    assert len(trace.steps) == 1
    assert trace.error_summary == "Test error"
