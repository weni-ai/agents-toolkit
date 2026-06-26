from __future__ import annotations

from typing import Any, ClassVar

from weni.context import Context
from weni.events.event import Event
from weni.responses import ResponseObject, TextResponse


class Tool:
    """
    Base class for implementing tools.

    Tools receive a Context object and must return a Response (tuple of data and format).

    Flows integrations (broadcasts, contacts, etc.) are available as namespaced facades via
    ``self.<name>``. Each facade is lazy-initialised on first access and cached for the
    duration of the execution. Any integration can register itself without touching this class:

        Tool.register_integration("broadcasts", Broadcast)
        Tool.register_integration("contact", Contact)

    Then inside a tool's ``execute`` method:

        self.broadcasts.send(Text("Processing..."))
        contact = self.contact.get()
        self.contact.update(fields={"email": "a@b.com"})

    The tool execution flow is:
    1. ``Tool.__new__`` prepares the instance state.
    2. ``execute()`` is called with the Context.
    3. Operations registered via ``_register_operation`` accumulate in ``_pending_operations``.
    4. ``__new__`` returns ``(result, format, events, traces)`` to the caller.
    """

    # Maps integration name → facade class.  Populated by register_integration().
    _FACADE_REGISTRY: ClassVar[dict[str, type]] = {}

    _pending_events: list[Event]
    # Generic operation log: {"messages_sent": [...], "contacts_updated": [...], ...}
    # Pre-seeded with "messages_sent" so that key is always present in the result dict.
    _pending_operations: dict[str, list[Any]]
    context: Context

    @classmethod
    def register_integration(cls, name: str, facade_cls: type) -> None:
        """Register a Flows integration facade under *name*.

        After registration, every tool instance exposes ``self.<name>`` as a
        pre-bound facade instance without any per-integration code in this class.
        """
        cls._FACADE_REGISTRY[name] = facade_cls

    def __getattr__(self, name: str) -> Any:
        registry = type(self)._FACADE_REGISTRY

        # Direct facade access: self.broadcasts, self.contact, …
        facade_cls = registry.get(name)
        if facade_cls is not None:
            facade = facade_cls(self)
            object.__setattr__(self, name, facade)
            return facade

        # Shorthand method access: self.send_broadcast, self.get_contact, …
        # Each facade class may declare _tool_methods = {"shorthand": "method_on_facade"}.
        for facade_name, facade_cls in registry.items():
            shorthands: dict[str, str] = getattr(facade_cls, "_tool_methods", {})
            if name in shorthands:
                facade = getattr(self, facade_name)   # reuses facade lookup + caching above
                method = getattr(facade, shorthands[name])
                object.__setattr__(self, name, method)
                return method

        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __new__(cls, context: Context):
        instance = super().__new__(cls)
        instance._pending_events = []
        instance._pending_operations = {"messages_sent": []}  # always present for compat
        instance.context = context

        Event.registry = []

        execute_result = instance.execute(context)

        legacy_events = [event.to_dict() for event in Event.registry]
        new_events = [event.to_dict() for event in instance._pending_events]
        events = legacy_events + new_events

        result, format = execute_result
        if not isinstance(format, dict):
            raise TypeError(f"Execute method must return a dictionary, got {type(format)}")

        result = {"result": result, **instance._pending_operations}

        traces = {}
        if hasattr(instance, '_get_trace_summary') and hasattr(instance, '_tracer_initialized'):
            if instance._tracer_initialized:
                traces = instance._get_trace_summary()

        return result, format, events, traces

    def execute(self, context: Context) -> ResponseObject:
        """Override this method to implement the tool's behaviour."""
        return TextResponse(data={})  # type: ignore

    def register_event(self, event: Event) -> None:
        self._pending_events.append(event)

    def _register_operation(self, key: str, value: Any) -> None:
        """Append *value* to the named operation list in ``_pending_operations``.

        Called by integration facades (Broadcast, Contact, …) — not by tool developers.
        """
        self._pending_operations.setdefault(key, []).append(value)
