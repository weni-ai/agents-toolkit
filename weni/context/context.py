from types import MappingProxyType
from typing import Mapping


class Context:
    credentials: Mapping
    parameters: Mapping
    globals: Mapping

    def __init__(self, credentials: dict, parameters: dict, globals: dict):
        # Convert mutable dicts to immutable mappings
        self.credentials = MappingProxyType(credentials)
        self.parameters = MappingProxyType(parameters)
        self.globals = MappingProxyType(globals)
