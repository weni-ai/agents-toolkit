import inspect
from typing import Type, Any
from copy import deepcopy
from weni.components import Component


# Store original component values when module is loaded
_original_components: dict[str, dict[str, Any]] = {}


def _store_original_values() -> None:
    """
    Store deep copies of original component values when module is loaded.

    Creates immutable snapshots of all official component attributes to use
    for validation. This prevents component modification after module load.
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
    Validates the integrity of component classes.

    Ensures that component attributes haven't been modified from their original
    values and that only official components are being used.

    Args:
        components: List of Component classes to validate

    Returns:
        bool: True if all components are valid

    Raises:
        ValueError: If components have been modified or aren't official

    Example:
        ```python
        try:
            validate_components([Text, Header, Footer])
        except ValueError as e:
            print(f"Validation failed: {e}")
        ```
    """
    component_attrs = _get_component_attributes()
    official_components = _get_official_components()

    for component in components:
        _validate_component_is_official(component, official_components)
        _validate_component_attributes(component, component_attrs)

    return True


def _get_component_attributes() -> set[str]:
    """
    Get all non-private, non-callable attributes from the Component class.

    Returns:
        set[str]: Set of attribute names that should be validated
    """
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
    """
    Verify that a component is officially defined in the components module.

    Args:
        component: Component class to validate
        official_components: Dictionary of official component classes

    Raises:
        ValueError: If component is not in the official components list
    """
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
