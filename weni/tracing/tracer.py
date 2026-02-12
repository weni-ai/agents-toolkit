"""
Execution Tracer Module.

Provides automatic tracing for method execution flow.
Just inherit from TracedAgent and use @trace decorator on methods.

Usage:
    class MyPreProcessor(TracedAgent, PreProcessor):

        @trace()
        def _my_method(self, data):
            return {"processed": True}

    class MyTool(TracedAgent, Tool):

        @trace()
        def execute(self, context: Context) -> ResponseObject:
            return TextResponse(data={"result": "success"})

The trace is automatically added to ProcessedData results or Response data.
"""

import functools
import inspect
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TypeVar
from dataclasses import dataclass, field
from enum import Enum


class StepStatus(str, Enum):
    """Status of an execution step."""

    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ExecutionStep:
    """Represents a single execution step in the trace."""

    class_name: str
    method_name: str
    status: StepStatus
    step_index: int = 0
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None


@dataclass
class ExecutionTrace:
    """Container for all execution steps."""

    agent_name: str = ""
    started_at: str = ""
    status: str = "pending"
    steps: List[ExecutionStep] = field(default_factory=list)
    error_summary: Optional[str] = None


def _serialize_value(value: Any, max_depth: int = 3, max_length: int = 1000) -> Any:
    """Safely serialize a value for logging."""
    if max_depth <= 0:
        return "<max_depth_exceeded>"

    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        if isinstance(value, str) and len(value) > max_length:
            return f"{value[:max_length]}...<truncated>"
        return value

    if isinstance(value, (list, tuple)):
        if len(value) > 50:
            serialized = [
                _serialize_value(v, max_depth - 1, max_length) for v in value[:50]
            ]
            return serialized + [f"<{len(value) - 50} more items>"]
        return [_serialize_value(v, max_depth - 1, max_length) for v in value]

    if isinstance(value, dict):
        if len(value) > 50:
            items = list(value.items())[:50]
            result = {
                k: _serialize_value(v, max_depth - 1, max_length) for k, v in items
            }
            result["<truncated>"] = f"{len(value) - 50} more keys"
            return result
        return {
            k: _serialize_value(v, max_depth - 1, max_length) for k, v in value.items()
        }

    if hasattr(value, "__dict__"):
        return f"<{type(value).__name__}>"

    return str(value)[:max_length]


def _extract_args(func: Callable, args: tuple, kwargs: dict) -> Dict[str, Any]:
    """Extract function arguments as a serialized dictionary."""
    try:
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        result = {}
        
        # Track position in args (skip self/cls)
        args_index = 0

        for param_name in params:
            if param_name in ("self", "cls"):
                # Skip self/cls in args
                if args_index < len(args):
                    args_index += 1
                continue

            # Check if argument is provided positionally
            if args_index < len(args):
                result[param_name] = _serialize_value(args[args_index])
                args_index += 1
            # Otherwise check if provided as keyword argument
            elif param_name in kwargs:
                result[param_name] = _serialize_value(kwargs[param_name])

        return result
    except Exception:
        return {"args": _serialize_value(args[1:])}


F = TypeVar("F", bound=Callable[..., Any])


def trace(
    capture_input: bool = True,
    capture_output: bool = True,
) -> Callable[[F], F]:
    """
    Decorator to trace method execution.

    This decorator automatically tracks method execution, including input arguments,
    output values, execution time, and errors. It requires the class to inherit
    from TracedAgent.

    Args:
        capture_input: Whether to capture input arguments.
        capture_output: Whether to capture return value.

    Example:
        ```python
        class MyAgent(TracedAgent, Tool):
            @trace()
            def execute(self, context: Context) -> ResponseObject:
                return TextResponse(data={"result": "success"})

            @trace(capture_output=False)  # Don't log sensitive output
            def _authenticate(self, credentials: dict) -> str:
                return token
        ```

    Returns:
        Decorated function with tracing enabled.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # Auto-initialize tracer if needed
            if hasattr(self, "_auto_init_tracer"):
                self._auto_init_tracer()

            if not hasattr(self, "_execution_trace"):
                return func(self, *args, **kwargs)

            class_name = self.__class__.__name__
            method_name = func.__name__
            start_time = datetime.utcnow()
            step_index = len(self._execution_trace.steps)

            input_data = (
                _extract_args(func, (self,) + args, kwargs) if capture_input else None
            )

            self._execution_trace.steps.append(
                ExecutionStep(
                    class_name=class_name,
                    method_name=method_name,
                    status=StepStatus.STARTED,
                    step_index=step_index,
                    input_data=input_data,
                )
            )

            try:
                result = func(self, *args, **kwargs)

                duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                output_data = _serialize_value(result) if capture_output else None

                self._execution_trace.steps.append(
                    ExecutionStep(
                        class_name=class_name,
                        method_name=method_name,
                        status=StepStatus.COMPLETED,
                        step_index=step_index,
                        output_data=output_data,
                        duration_ms=duration_ms,
                    )
                )

                return result

            except Exception as exc:
                duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                error_msg = f"{type(exc).__name__}: {str(exc)}"

                self._execution_trace.steps.append(
                    ExecutionStep(
                        class_name=class_name,
                        method_name=method_name,
                        status=StepStatus.FAILED,
                        step_index=step_index,
                        error=error_msg,
                        duration_ms=duration_ms,
                    )
                )

                self._execution_trace.status = "failed"
                self._execution_trace.error_summary = error_msg
                raise

        return wrapper  # type: ignore

    return decorator


class TracedAgent:
    """
    Base class that provides automatic execution tracing.

    This class can be used as a mixin with Tool or PreProcessor classes to enable
    automatic execution tracing. Just inherit from this class and use @trace decorator
    on methods you want to track.

    The trace is automatically added to any dict result that goes through the execution.
    For Tools, the trace is injected into the response data.
    For PreProcessors, the trace is injected into the ProcessedData.

    Attributes:
        AGENT_NAME (str): Override this class variable to set a custom agent name.
                         Defaults to the class name if not set.

    Example:
        ```python
        from weni import Tool
        from weni.tracing import TracedAgent, trace
        from weni.context import Context
        from weni.responses import TextResponse

        class MyTool(TracedAgent, Tool):
            def execute(self, context: Context) -> ResponseObject:
                result = self._process_data(context)
                data, format = TextResponse(data=result)
                # Trace is automatically injected into data
                return data, format

            @trace()
            def _process_data(self, context: Context) -> dict:
                return {"processed": True}
        ```

        ```python
        from weni.preprocessor import PreProcessor, ProcessedData
        from weni.tracing import TracedAgent, trace
        from weni.context.preprocessor_context import PreProcessorContext

        class MyPreProcessor(TracedAgent, PreProcessor):
            def process(self, context: PreProcessorContext) -> ProcessedData:
                validated = self._validate(context)
                data = {"data": validated}
                # Trace is automatically injected into data
                return ProcessedData("urn", data)

            @trace()
            def _validate(self, context: PreProcessorContext) -> dict:
                return context.payload
        ```
    """

    _execution_trace: ExecutionTrace
    _tracer_initialized: bool = False

    # Override this in your class to set a custom agent name
    AGENT_NAME: str = ""

    def _auto_init_tracer(self) -> None:
        """Auto-initialize tracer on first traced method call."""
        if not self._tracer_initialized:
            agent_name = self.AGENT_NAME or self.__class__.__name__
            self._execution_trace = ExecutionTrace(
                agent_name=agent_name,
                started_at=datetime.utcnow().isoformat() + "Z",
                status="running",
            )
            self._tracer_initialized = True

    def _get_trace_summary(self) -> Dict[str, Any]:
        """Build the execution trace summary."""
        if not hasattr(self, "_execution_trace"):
            return {}

        steps_by_index: Dict[int, Dict[str, Any]] = {}

        for step in self._execution_trace.steps:
            idx = step.step_index

            if idx not in steps_by_index:
                steps_by_index[idx] = {
                    "class": step.class_name,
                    "method": step.method_name,
                }

            if step.status == StepStatus.STARTED:
                steps_by_index[idx]["input"] = step.input_data

            elif step.status == StepStatus.COMPLETED:
                steps_by_index[idx]["output"] = step.output_data
                steps_by_index[idx]["duration_ms"] = (
                    round(step.duration_ms, 2) if step.duration_ms else 0
                )
                steps_by_index[idx]["status"] = "ok"

            elif step.status == StepStatus.FAILED:
                steps_by_index[idx]["error"] = step.error
                steps_by_index[idx]["duration_ms"] = (
                    round(step.duration_ms, 2) if step.duration_ms else 0
                )
                steps_by_index[idx]["status"] = "failed"

        summary = []
        order = 1
        for idx in sorted(steps_by_index.keys()):
            step_data = steps_by_index[idx]
            if "status" in step_data:
                step_data["order"] = order
                summary.append(step_data)
                order += 1

        # Calculate duration and completed_at
        duration = 0.0
        completed_at = datetime.utcnow().isoformat() + "Z"

        if self._execution_trace.started_at:
            try:
                start = datetime.fromisoformat(
                    self._execution_trace.started_at.replace("Z", "")
                )
                duration = round((datetime.utcnow() - start).total_seconds() * 1000, 2)
            except Exception:
                pass

        trace_data = {
            "agent_name": self._execution_trace.agent_name,
            "started_at": self._execution_trace.started_at,
            "completed_at": completed_at,
            "total_duration_ms": duration,
            "status": (
                "completed"
                if self._execution_trace.status == "running"
                else self._execution_trace.status
            ),
            "total_steps": len(summary),
            "steps": summary,
        }

        if self._execution_trace.error_summary:
            trace_data["error_summary"] = self._execution_trace.error_summary

        return trace_data

    def _inject_trace(self, data: Any) -> Any:
        """Inject trace into data if it's a dict."""
        if isinstance(data, dict) and self._tracer_initialized:
            data["_execution_trace"] = self._get_trace_summary()
        return data

    def _reset_tracer(self) -> None:
        """Reset tracer for next execution."""
        self._tracer_initialized = False
        if hasattr(self, "_execution_trace"):
            del self._execution_trace


# Alias for backwards compatibility
TracedProcessor = TracedAgent
ExecutionTracerMixin = TracedAgent
