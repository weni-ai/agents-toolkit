from types import MappingProxyType
from weni.context import Context, PreProcessorContext


def test_context_initialization():
    """Test basic context initialization with all parameters"""
    credentials = {"api_key": "secret123"}
    parameters = {"user_id": "123"}
    globals_ = {"env": "production"}

    context = Context(credentials=credentials, parameters=parameters, globals=globals_)

    assert isinstance(context.credentials, MappingProxyType)
    assert isinstance(context.parameters, MappingProxyType)
    assert isinstance(context.globals, MappingProxyType)
    assert context.credentials == credentials
    assert context.parameters == parameters
    assert context.globals == globals_

def test_preprocessor_context_initialization():
    """Test basic preprocessor context initialization with all parameters"""
    params = {"api_key": "secret123"}
    payload = {"user_id": "123"}
    credentials = {"env": "production"}

    context = PreProcessorContext(params=params, payload=payload, credentials=credentials)

    assert isinstance(context.params, MappingProxyType)
    assert isinstance(context.payload, MappingProxyType)
    assert isinstance(context.credentials, MappingProxyType)
    assert context.params == params
    assert context.payload == payload
    assert context.credentials == credentials
