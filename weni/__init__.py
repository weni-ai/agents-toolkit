"""
Weni Agents Toolkit

A Python library for creating and managing tools for the Weni platform.
"""

from weni.tool import Tool
from weni.context import Context
import weni.components as Components
import weni.responses as Responses
import weni.broadcasts as Broadcasts
import weni.tracing as Tracing

# Register Flows integration facades so that tool developers can access them
# as self.broadcasts, self.contact, etc. without any imports inside Tool itself.
from weni.broadcasts.broadcast import Broadcast
from weni.contacts.contact import Contact

Tool.register_integration("broadcasts", Broadcast)
Tool.register_integration("contact", Contact)

__all__ = [
    "Tool",
    "Context",
    "Components",
    "Responses",
    "Broadcasts",
    "Tracing",
]
