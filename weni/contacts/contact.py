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
	"""

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
		return self._get_sender().get(urn=urn)

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
		return self._get_sender().update(payload=payload, urn=urn, **kwargs)
