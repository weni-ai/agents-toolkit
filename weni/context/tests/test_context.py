from types import MappingProxyType
from weni.context import Context, PreProcessorContext


def test_context_initialization():
    """Test basic context initialization with all parameters"""
    credentials = {"api_key": "secret123"}
    parameters = {"user_id": "123"}
    globals_ = {"env": "production"}
    contact = {"name": "John Doe", "urn": "tel:+1234567890"}
    project = {"name": "Project 1", "uuid": "project-uuid"}
    constants = {"INPUT": {"label": "Example", "required": True, "default": "Sample"}}

    context = Context(credentials=credentials, parameters=parameters, globals=globals_, contact=contact, project=project, constants=constants)

    assert isinstance(context.credentials, MappingProxyType)
    assert isinstance(context.parameters, MappingProxyType)
    assert isinstance(context.globals, MappingProxyType)
    assert isinstance(context.contact, MappingProxyType)
    assert isinstance(context.project, MappingProxyType)
    assert isinstance(context.constants, MappingProxyType)
    assert context.credentials == credentials
    assert context.parameters == parameters
    assert context.globals == globals_
    assert context.contact == contact
    assert context.project == project
    assert context.constants == constants

def test_preprocessor_context_initialization():
    """Test basic preprocessor context initialization with all parameters"""
    params = {"api_key": "secret123"}
    payload = {"user_id": "123"}
    credentials = {"env": "production"}
    project = {"name": "Project 1", "uuid": "project-uuid"}

    context = PreProcessorContext(params=params, payload=payload, credentials=credentials, project=project)

    assert isinstance(context.params, MappingProxyType)
    assert isinstance(context.payload, MappingProxyType)
    assert isinstance(context.credentials, MappingProxyType)
    assert isinstance(context.project, MappingProxyType)
    assert context.params == params
    assert context.payload == payload
    assert context.credentials == credentials
    assert context.project == project
