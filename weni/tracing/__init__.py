"""
Tracing module for Weni Agents Toolkit.

Provides execution tracing capabilities for both active agents (Tools) and
passive agents (PreProcessors, Rules, etc.).
"""

from .tracer import (
    ExecutionStep,
    ExecutionTrace,
    StepStatus,
    TracedAgent,
    TracedProcessor,  # Backwards compatibility alias
    ExecutionTracerMixin,  # Backwards compatibility alias
    trace,
)

__all__ = [
    "ExecutionStep",
    "ExecutionTrace",
    "StepStatus",
    "TracedAgent",
    "TracedProcessor",  # Backwards compatibility
    "ExecutionTracerMixin",  # Backwards compatibility
    "trace",
]
