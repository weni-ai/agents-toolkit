# Tracing Module

The `tracing` module provides execution tracking capabilities for Tools, PreProcessors, Rules, and other classes.

## Features

- ✅ Automatic method tracking with `@trace()` decorator
- ✅ Captures input, output, duration, and errors
- ✅ Works with Tools, PreProcessors, and Rules
- ✅ Automatic trace return as separate variable
- ✅ Generic naming (`Traced`) to support all types

## Basic Usage

### With Tool

```python
from weni import Tool
from weni.tracing import Traced, trace
from weni.context import Context
from weni.responses import TextResponse, ResponseObject

class MyTool(Traced, Tool):
    def execute(self, context: Context) -> ResponseObject:
        # Process data
        result = self._process_data(context)
        
        # Create response
        data, format = TextResponse(data=result)
        
        return data, format

    @trace()
    def _process_data(self, context: Context) -> dict:
        # Your logic here
        return {"result": "success", "value": 42}
```

When executed, the Tool will always return `(result, format, events, traces)`. If tracing is enabled (Traced is used and @trace() decorator is called), traces will contain execution data. Otherwise, traces will be an empty dictionary.

### With PreProcessor

```python
from weni.preprocessor import PreProcessor, ProcessedData
from weni.tracing import Traced, trace
from weni.context.preprocessor_context import PreProcessorContext

class MyPreProcessor(Traced, PreProcessor):
    def process(self, context: PreProcessorContext) -> ProcessedData:
        # Validate data
        validated_data = self._validate(context)
        
        # Prepare data
        data = {"data": validated_data}
        
        return ProcessedData("example-urn", data)

    @trace()
    def _validate(self, context: PreProcessorContext) -> dict:
        # Your validation logic here
        return context.payload
```

When executed, the PreProcessor will always return `(ProcessedData, traces)`. If tracing is enabled (Traced is used and @trace() decorator is called), traces will contain execution data. Otherwise, traces will be an empty dictionary.

## `@trace()` Decorator Options

```python
@trace(capture_input=True, capture_output=True)  # Default: captures everything
def my_method(self, data: dict) -> dict:
    return process(data)

@trace(capture_output=False)  # Don't capture output (sensitive data)
def authenticate(self, credentials: dict) -> str:
    return secret_token

@trace(capture_input=False)  # Don't capture input
def process_sensitive(self, password: str) -> dict:
    return {"status": "ok"}
```

## Custom Name

```python
class MyTool(Traced, Tool):
    NAME = "MyCustomName"  # Override default name
    
    @trace()
    def execute(self, context: Context) -> ResponseObject:
        # ...
```

## Trace Structure

The trace returned has the following structure:

```python
{
    "name": "MyTool",
    "started_at": "2024-01-01T12:00:00.000Z",
    "completed_at": "2024-01-01T12:00:01.500Z",
    "total_duration_ms": 1500.0,
    "status": "completed",  # or "failed"
    "total_steps": 2,
    "steps": [
        {
            "order": 1,
            "class": "MyTool",
            "method": "_process_data",
            "status": "ok",  # or "failed"
            "input": {...},
            "output": {...},
            "duration_ms": 100.5
        }
    ],
    "error_summary": "..."  # Only if there's an error
}
```

## Backwards Compatibility

For backwards compatibility, the following aliases are available:

```python
from weni.tracing import TracedAgent  # Alias for Traced
from weni.tracing import TracedProcessor  # Alias for Traced
from weni.tracing import ExecutionTracerMixin  # Alias for Traced
```

## Reset Tracer

To reset the tracer between executions:

```python
tool._reset_tracer()
```

## Advanced Examples

### Multiple Tracked Methods

```python
class ComplexTool(Traced, Tool):
    def execute(self, context: Context) -> ResponseObject:
        data = self._extract_data(context)
        validated = self._validate(data)
        processed = self._process(validated)
        
        data, format = TextResponse(data=processed)
        return data, format

    @trace()
    def _extract_data(self, context: Context) -> dict:
        return context.parameters

    @trace()
    def _validate(self, data: dict) -> dict:
        # Validation
        return data

    @trace()
    def _process(self, data: dict) -> dict:
        # Processing
        return {"result": data}
```

### Error Handling

```python
class ToolWithError(Traced, Tool):
    @trace()
    def _method_with_error(self):
        raise ValueError("Test error")
        # The trace automatically captures the error
```

The trace will include:
- Status: "failed"
- error_summary: "ValueError: Test error"
- Step with "failed" status and error details
