from types import MappingProxyType
from weni.context import Context


def test_context_initialization():
    """Test basic context initialization with all parameters"""
    credentials = {"api_key": "secret123"}
    parameters = {"user_id": "123"}
    globals_ = {"env": "production"}
    contact = {"name": "John Doe", "urn": "tel:+1234567890"}

    context = Context(credentials=credentials, parameters=parameters, globals=globals_, contact=contact)

    assert isinstance(context.credentials, MappingProxyType)
    assert isinstance(context.parameters, MappingProxyType)
    assert isinstance(context.globals, MappingProxyType)
    assert isinstance(context.contact, MappingProxyType)
    assert context.credentials == credentials
    assert context.parameters == parameters
    assert context.globals == globals_
    assert context.contact == contact
