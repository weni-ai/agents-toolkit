
from types import MappingProxyType
from typing import Mapping

class PreProcessorContext:
    """
    An immutable context container for preprocessor execution.
    
    The PreProcessorContext class provides a thread-safe, immutable container for passing data
    to preprocessor during execution. It contains three separate namespaces:

    Attributes:
        params (Mapping): Immutable mapping for preprocessor-specific parameters
        payload (Mapping): Immutable mapping for payload data
        credentials (Mapping): Immutable mapping for credentials data
    """

    params: Mapping
    payload: Mapping
    credentials: Mapping
    project: Mapping
    
    def __init__(self, params: dict, payload: dict, credentials: dict, project: dict):
        self.params = MappingProxyType(params)
        self.payload = MappingProxyType(payload)
        self.credentials = MappingProxyType(credentials)
        self.project = MappingProxyType(project)
