from types import MappingProxyType
from typing import Mapping


class Context:
    """
    An immutable context container for skill execution.

    The Context class provides a thread-safe, immutable container for passing data
    to skills during execution. It contains three separate namespaces:

    Attributes:
        credentials (Mapping): Immutable mapping for configured secrets data
        parameters (Mapping): Immutable mapping for skill-specific parameters
        globals (Mapping): Immutable mapping for global configuration values
    """

    credentials: Mapping
    parameters: Mapping
    globals: Mapping

    def __init__(self, credentials: dict, parameters: dict, globals: dict):
        # Convert mutable dicts to immutable mappings
        self.credentials = MappingProxyType(credentials)
        self.parameters = MappingProxyType(parameters)
        self.globals = MappingProxyType(globals)
