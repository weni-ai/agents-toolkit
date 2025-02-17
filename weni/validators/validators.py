import inspect
from typing import Type, Dict, Any
from copy import deepcopy
from weni.components import Component


# Store original component values when module is loaded
_original_components: Dict[str, Dict[str, Any]] = {}


def _store_original_values() -> None:
    """Store original values of all official components.

    This function:
    1. Gets all non-callable, non-private attributes from the Component class
    2. Finds all Component subclasses in the component module
    3. Creates deep copies of their attributes to prevent shared references
    """
    # Get non-private, non-callable attributes from Component class
    component_attrs = {
        name for name, value in vars(Component).items() if not name.startswith("__") and not callable(value)
    }

    # Get all Component subclasses from the component module
    component_module = inspect.getmodule(Component)
    component_classes = inspect.getmembers(component_module, inspect.isclass)

    # Store deep copies of attributes for each valid component
    for name, cls in component_classes:
        if issubclass(cls, Component) and cls is not Component:
            _original_components[name] = {attr: deepcopy(getattr(cls, attr)) for attr in component_attrs}


def validate_components(components: list[Type[Component]]) -> bool:
    """
    Validates that component attributes haven't been modified from their original values.

    Args:
        components: List of Component classes to validate

    Returns:
        bool: True if all components are valid

    Raises:
        ValueError: If a component's attributes have been modified or if using third-party components
    """
    component_attrs = _get_component_attributes()
    official_components = _get_official_components()

    for component in components:
        _validate_component_is_official(component, official_components)
        _validate_component_attributes(component, component_attrs)

    return True


def _get_component_attributes() -> set[str]:
    """Get non-private, non-callable attributes from Component class"""
    return {name for name, value in vars(Component).items() if not name.startswith("__") and not callable(value)}


def _get_official_components() -> dict[str, Type[Component]]:
    """Get all official components defined in the component module"""
    return {
        name: cls
        for name, cls in inspect.getmembers(inspect.getmodule(Component), inspect.isclass)
        if issubclass(cls, Component) and cls is not Component
    }


def _validate_component_is_official(
    component: Type[Component], official_components: dict[str, Type[Component]]
) -> None:
    """Validate that component is an official one"""
    if component not in official_components.values():
        raise ValueError(
            f"Component {component.__name__} is not an official component. "
            f"Only components defined in {Component.__module__} are allowed."
        )


def _validate_component_attributes(component: Type[Component], component_attrs: set[str]) -> None:
    """Validate that component attributes haven't been modified"""
    original_values = _original_components[component.__name__]

    for attr_name in component_attrs:
        current_value = getattr(component, attr_name)
        original_value = original_values[attr_name]

        if str(original_value) != str(current_value):
            raise ValueError(
                f"{component.__name__}.{attr_name} has been modified. "
                f"Original value: {original_value!r}, Current value: {current_value!r}"
            )


# Store original values when module is loaded
_store_original_values()
