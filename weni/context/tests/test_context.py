from types import MappingProxyType
from weni.context import Context


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
