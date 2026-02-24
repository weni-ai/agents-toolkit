import pytest

from weni.context import Context
from weni.tool import Tool
from weni.responses import (
	ResponseObject,
	HeaderType,
	TextResponse,
	QuickReplyResponse,
)
from weni.events.event import Event
from weni.tracing import Traced, trace


@pytest.fixture(autouse=True)
def clear_event_registry():
	Event.registry.clear()


def test_tool_execution():
	"""Test basic Tool execution"""

	class TestTool(Tool):
		def execute(self, context: Context) -> ResponseObject:
			return TextResponse(data={'test': 'data'})  # type: ignore

	context = Context(credentials={}, parameters={}, globals={}, contact={}, project={}, constants={})
	result, format, events = TestTool(context)

	# 'events' are returned separately
	assert result == {'test': 'data'}
	assert events == []
	assert format == {'msg': {'text': 'Hello, how can I help you today?'}}


def test_tool_context_access():
	"""Test Tool access to context values"""

	class TestTool(Tool):
		def execute(self, context: Context) -> ResponseObject:
			return QuickReplyResponse(
				data={
					'credential': context.credentials.get('api_key'),
					'param': context.parameters.get('user_id'),
					'global': context.globals.get('env'),
					'contact': context.contact.get('name'),
					'urn': context.contact.get('urn'),
					'project_name': context.project.get('name'),
					'project_uuid': context.project.get('uuid'),
					'constants': dict(context.constants),
				},
				header_type=HeaderType.TEXT,
			)  # type: ignore

	context = Context(
		credentials={'api_key': 'secret123'},
		parameters={'user_id': 'user456'},
		globals={'env': 'production'},
		contact={'name': 'John Doe', 'urn': 'tel:+1234567890'},
		project={'name': 'Project 1', 'uuid': 'project-uuid'},
		constants={'INPUT': {'label': 'Example', 'required': True, 'default': 'Sample'}}
	)

	result, format, events = TestTool(context)
	assert result == {
		'credential': 'secret123',
		'param': 'user456',
		'global': 'production',
		'contact': 'John Doe',
		'urn': 'tel:+1234567890',
		'project_name': 'Project 1',
		'project_uuid': 'project-uuid',
		'constants': {'INPUT': {'label': 'Example', 'required': True, 'default': 'Sample'}},
	}
	assert events == []
	assert format == {
		'msg': {
			'text': 'Hello, how can I help you today?',
			'quick_replies': ['Yes', 'No'],
			'header': {'type': 'text', 'text': 'Important Message'},
		}
	}


def test_tool_without_execute_implementation():
	"""Test Tool without execute implementation"""

	class EmptyTool(Tool):
		pass

	context = Context(credentials={}, parameters={}, globals={}, contact={}, project={}, constants={})
	result, format, events = EmptyTool(context)

	assert result == {}
	assert events == []
	assert format == {'msg': {'text': 'Hello, how can I help you today?'}}


def test_tool_with_invalid_format():
	"""Test Tool where the format value (second return value) is not a dict"""

	class InvalidFormatTool(Tool):
		def execute(self, context: Context) -> ResponseObject:  # type: ignore
			# The first value can be any type (a dictionary here),
			# but the second value (format) must be a dictionary - not a string
			return {}, 'not a dictionary'  # type: ignore

	context = Context(credentials={}, parameters={}, globals={}, contact={}, project={}, constants={})

	with pytest.raises(TypeError) as excinfo:
		InvalidFormatTool(context)

	assert 'Execute method must return a dictionary' in str(excinfo.value)


def test_response_immutability():
	"""Test Response immutability after creation"""
	data = {'key': 'value'}
	result, format = TextResponse(data=data)

	# Modify original data
	data['new_key'] = 'new_value'

	# Response should maintain original values
	assert 'new_key' not in result
	assert format == {'msg': {'text': 'Hello, how can I help you today?'}}


def test_tool_context_immutability():
	"""Test Context immutability in Tool"""

	class MutableTool(Tool):
		def execute(self, context: Context) -> ResponseObject:
			# Try to modify context
			context.credentials['new_key'] = 'value'  # type: ignore
			return TextResponse(data={})  # type: ignore

	context = Context(credentials={'key': 'value'}, parameters={}, globals={}, contact={}, project={}, constants={})
	original_credentials = context.credentials.copy()

	with pytest.raises(TypeError):
		MutableTool(context)

	assert context.credentials == original_credentials


def test_tool_execution_order():
	"""Test Tool execution order and single execution"""
	execution_count = 0

	class CountedTool(Tool):
		def execute(self, context: Context) -> ResponseObject:
			nonlocal execution_count
			execution_count += 1
			return TextResponse(data={'count': execution_count})  # type: ignore

	context = Context(credentials={}, parameters={}, globals={}, contact={}, project={}, constants={})
	result, format, events = CountedTool(context)

	assert execution_count == 1
	assert result == {'count': 1}
	assert events == []
	assert format == {'msg': {'text': 'Hello, how can I help you today?'}}

	result, format, events = CountedTool(context)

	assert execution_count == 2
	assert result == {'count': 2}
	assert events == []
	assert format == {'msg': {'text': 'Hello, how can I help you today?'}}


def test_tool_with_complex_response():
	"""Test Tool with complex response configuration"""

	class ComplexTool(Tool):
		def execute(self, context: Context) -> ResponseObject:
			return QuickReplyResponse(data={'message': 'Choose an option'}, header_type=HeaderType.TEXT, footer=True)  # type: ignore

	context = Context(credentials={}, parameters={}, globals={}, contact={}, project={}, constants={})
	result, format, events = ComplexTool(context)

	assert result == {'message': 'Choose an option'}
	assert events == []
	assert format == {
		'msg': {
			'text': 'Hello, how can I help you today?',
			'quick_replies': ['Yes', 'No'],
			'header': {'type': 'text', 'text': 'Important Message'},
			'footer': 'Powered by Weni',
		}
	}


def test_tool_with_non_dict_response():
	"""Test Tool execution with non-dictionary response data"""

	class ListDataTool(Tool):
		def execute(self, context: Context) -> ResponseObject:
			return TextResponse(data=['item1', 'item2', 'item3'])  # type: ignore

	context = Context(credentials={}, parameters={}, globals={}, contact={}, project={}, constants={})
	result, format, events = ListDataTool(context)

	assert result == ['item1', 'item2', 'item3']
	assert events == []
	assert format == {'msg': {'text': 'Hello, how can I help you today?'}}

	class StringDataTool(Tool):
		def execute(self, context: Context) -> ResponseObject:
			return TextResponse(data='simple string response')  # type: ignore

	result, format, events = StringDataTool(context)

	assert result == 'simple string response'
	assert events == []
	assert format == {'msg': {'text': 'Hello, how can I help you today?'}}

	class NumberDataTool(Tool):
		def execute(self, context: Context) -> ResponseObject:
			return TextResponse(data=42)  # type: ignore

	result, format, events = NumberDataTool(context)

	assert result == 42
	assert events == []
	assert format == {'msg': {'text': 'Hello, how can I help you today?'}}


def test_tool_with_traced_returns_tuple():
	"""Test that Tool with Traced returns tuple (result, format, events, traces)"""
	
	class TracedTool(Traced, Tool):
		def execute(self, context: Context) -> ResponseObject:
			processed = self._process_data(context)
			return TextResponse(data=processed)  # type: ignore
		
		@trace()
		def _process_data(self, context: Context) -> dict:
			return {"processed": True, "value": 42}
	
	context = Context(credentials={}, parameters={}, globals={}, contact={}, project={}, constants={})
	
	# Tool with Traced should return tuple with traces
	result = TracedTool(context)
	
	# Should return tuple (result, format, events, traces)
	assert isinstance(result, tuple)
	assert len(result) == 4
	data, format, events, traces = result
	
	# Verify data
	assert data == {"processed": True, "value": 42}
	assert isinstance(format, dict)
	assert isinstance(events, list)
	
	# Verify traces structure
	assert isinstance(traces, dict)
	assert "name" in traces
	assert traces["name"] == "TracedTool"
	assert "steps" in traces
	assert "started_at" in traces
	assert "status" in traces
	assert len(traces["steps"]) > 0  # Should have at least one step from _process_data


def test_tool_without_traced_returns_three_values():
	"""Test that Tool without Traced returns only (result, format, events)"""
	
	class RegularTool(Tool):
		def execute(self, context: Context) -> ResponseObject:
			return TextResponse(data={"test": "data"})  # type: ignore
	
	context = Context(credentials={}, parameters={}, globals={}, contact={}, project={}, constants={})
	
	# Tool without Traced should return only (result, format, events)
	result = RegularTool(context)
	
	# Should return tuple with 3 values, not 4
	assert isinstance(result, tuple)
	assert len(result) == 3
	data, format, events = result
	
	assert data == {"test": "data"}
	assert isinstance(format, dict)
	assert isinstance(events, list)
