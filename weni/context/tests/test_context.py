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

def make_context(contact: dict) -> Context:
    """Build a Context with the given contact namespace and placeholder values elsewhere."""
    return Context(
        credentials={"api_key": "secret123"},
        parameters={"user_id": "123"},
        globals={"env": "production"},
        contact=contact,
        project={"name": "Project 1", "uuid": "project-uuid"},
        constants={"INPUT": {"label": "Example"}},
    )


def test_merge_contact_deep_merges_fields():
    """Merging fields keeps the sibling keys already present"""
    context = make_context({"name": "John", "fields": {"email": "old@example.com", "cpf": "123"}})

    context._merge_contact({"fields": {"email": "new@example.com"}})

    assert context.contact["fields"] == {"email": "new@example.com", "cpf": "123"}


def test_merge_contact_creates_missing_fields():
    """Merging fields into a contact without them creates the key"""
    context = make_context({"name": "John"})

    context._merge_contact({"fields": {"email": "new@example.com"}})

    assert context.contact["fields"] == {"email": "new@example.com"}


def test_merge_contact_overwrites_scalar_and_list_values():
    """Non-dict values replace the current value instead of being merged"""
    context = make_context({"name": "John", "urns": ["tel:+551199999999"], "groups": [{"name": "Leads"}]})

    context._merge_contact({"name": "Jane", "urns": ["tel:+5511888888888"], "groups": []})

    assert context.contact["name"] == "Jane"
    assert context.contact["urns"] == ["tel:+5511888888888"]
    assert context.contact["groups"] == []


def test_merge_contact_with_empty_patch_is_a_no_op():
    """An empty patch leaves the contact namespace untouched"""
    context = make_context({"name": "John", "fields": {"email": "old@example.com"}})

    context._merge_contact({})

    assert context.contact == {"name": "John", "fields": {"email": "old@example.com"}}


def test_merge_contact_does_not_touch_other_namespaces():
    """Only the contact namespace changes"""
    context = make_context({"name": "John"})

    context._merge_contact({"name": "Jane"})

    assert context.credentials == {"api_key": "secret123"}
    assert context.parameters == {"user_id": "123"}
    assert context.globals == {"env": "production"}
    assert context.project == {"name": "Project 1", "uuid": "project-uuid"}
    assert context.constants == {"INPUT": {"label": "Example"}}


def test_merge_contact_preserves_object_identity():
    """Another reference to the same Context sees the update, as Tool.execute's argument does"""
    context = make_context({"fields": {"email": "old@example.com"}})
    same_context = context
    contact_proxy = context.contact

    context._merge_contact({"fields": {"email": "new@example.com"}})

    assert same_context.contact["fields"]["email"] == "new@example.com"
    assert contact_proxy["fields"]["email"] == "new@example.com"


def test_merge_contact_mutates_the_original_dict():
    """The dict handed to the constructor is the one being mutated"""
    contact = {"fields": {"email": "old@example.com"}}
    context = make_context(contact)

    context._merge_contact({"fields": {"email": "new@example.com"}, "name": "Jane"})

    assert contact == {"fields": {"email": "new@example.com"}, "name": "Jane"}


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
