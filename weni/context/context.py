from types import MappingProxyType
from typing import Any, Mapping


class Context:
    """
    A read-only context container for tool execution.

    The Context class provides a container for passing data to tools during
    execution. Every namespace is exposed as an immutable mapping, so tool code
    cannot assign to it. It contains the following namespaces:

    Attributes:
        credentials (Mapping): Immutable mapping for configured secrets data
        parameters (Mapping): Immutable mapping for tool-specific parameters
        globals (Mapping): Immutable mapping for global configuration values
        contact (Mapping): Immutable mapping for contact data
        constants (Mapping): Immutable mapping for constant values

    The `contact` namespace is the one exception: Flows integrations refresh it
    in place via `_merge_contact` after a write, so that the rest of the
    execution reads the current contact state. See that method for details.
    """

    credentials: Mapping
    parameters: Mapping
    globals: Mapping
    contact: Mapping
    project: Mapping
    constants: Mapping

    def __init__(self, credentials: dict, parameters: dict, globals: dict, contact: dict, project: dict, constants: dict):
        # Convert mutable dicts to immutable mappings
        self.credentials = MappingProxyType(credentials)
        self.parameters = MappingProxyType(parameters)
        self.globals = MappingProxyType(globals)
        self.contact = MappingProxyType(contact)
        self.project = MappingProxyType(project)
        self.constants = MappingProxyType(constants)

        # Kept so integrations can refresh the contact namespace; the proxy above
        # is a view over this dict, so merges are visible through self.contact.
        self._contact_data: dict[str, Any] = contact

    def _merge_contact(self, patch: Mapping[str, Any]) -> None:
        """
        Refresh the contact namespace in place with new contact data.

        Called by Flows integrations after a successful contact write - not by
        tool developers. Mutating in place (instead of rebuilding the Context)
        keeps the object identity, so the `context` argument received by
        `Tool.execute` reflects the update as well as `self.context`.

        Dict values are merged into the existing dict (so a partial `fields`
        payload keeps untouched keys); every other value replaces the current
        one. The mutation applies to the dict originally passed to `__init__`.

        Args:
            patch: Contact attributes to merge into the namespace.
        """
        for key, value in patch.items():
            current = self._contact_data.get(key)
            if isinstance(value, dict) and isinstance(current, dict):
                current.update(value)
            else:
                self._contact_data[key] = value
