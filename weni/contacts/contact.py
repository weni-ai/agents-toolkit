"""
Contact facade for reading and updating Flows contacts during tool execution.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
	from weni.contacts.sender import ContactSender
	from weni.tool import Tool


class Contact:
	"""
	Tool-bound facade for Flows contact operations.

	Example:
		```python
		from weni.contacts import Contact

		class MyTool(Tool):
		    def execute(self, context: Context):
		        contact = Contact(self).get()
		        Contact(self).update(fields={'email': 'user@example.com'})
		```

	Shorthand via Tool:
		``self.get_contact(urn)`` is equivalent to ``self.contact.get(urn)``.
		``self.update_contact(payload)`` is equivalent to ``self.contact.update(payload)``.
	"""

	# Exposes self.get_contact / self.update_contact on any Tool without adding methods to Tool.
	_tool_methods: dict[str, str] = {
		"get_contact": "get",
		"update_contact": "_update_contact_compat",
	}

	# Contact attributes copied back into the context after a write. Platform
	# metadata returned by Flows (uuid, created_on, modified_on, ...) stays out.
	CONTEXT_REFRESH_KEYS: tuple[str, ...] = ("fields", "name", "language", "groups", "urns")

	def __init__(self, tool: 'Tool'):
		self._tool = tool

	def _get_sender(self) -> 'ContactSender':
		from weni.contacts.sender import ContactSender

		return ContactSender(self._tool.context)

	def get(self, urn: str | None = None) -> dict[str, Any]:
		"""
		Retrieve a single contact by URN.

		Args:
			urn: Optional URN override. When omitted, resolved from tool context.

		Returns:
			The Flows contact object as a dictionary.
		"""

		contact = self._get_sender().get(urn=urn)
		self._tool._register_operation("contacts_get", urn)
		return contact

	def update(
		self,
		payload: dict[str, Any] | None = None,
		urn: str | None = None,
		**kwargs: Any,
	) -> dict[str, Any]:
		"""
		Update an existing contact by URN.

		Args:
			payload: Optional base write body.
			urn: Optional URN override. When omitted, resolved from tool context.
			**kwargs: Write attributes merged into the body; kwargs override conflicting payload keys.

		Returns:
			The updated Flows contact object as a dictionary.
		"""

		from weni.contacts.sender import ContactSender

		merged = ContactSender._merge_update_payload(payload, kwargs)
		result = self._get_sender().update(payload=payload, urn=urn, **kwargs)
		self._tool._register_operation("contacts_updated", merged)
		self._refresh_context(result)
		return result

	def _refresh_context(self, contact: dict[str, Any]) -> None:
		"""
		Merge the contact returned by Flows back into the tool context.

		Reads from the response rather than the sent payload because Flows
		normalizes values. Only whitelisted attributes are merged, so the
		context does not accumulate platform metadata.
		"""

		patch = {key: contact[key] for key in self.CONTEXT_REFRESH_KEYS if key in contact}
		if patch:
			self._tool.context._merge_contact(patch)

	def _update_contact_compat(
		self,
		new_contact: dict[str, Any],
		old_contact: dict[str, Any] | None = None,
	) -> dict[str, Any]:
		"""Backward-compatible shim: mirrors the old Tool.update_contact(new, old) signature."""
		return self.update(payload=new_contact)
