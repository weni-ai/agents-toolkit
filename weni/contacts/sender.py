"""
HTTP-based contacts sender.

Reads and updates Flows contacts via the shared FlowsClient during tool execution.
"""

from typing import Any

from weni.context import Context
from weni.flows.client import FlowsClient
from weni.flows.exceptions import FlowsClientConfigError, FlowsClientError


class ContactSenderError(Exception):
	"""Raised when there is an error performing a contacts operation."""


class ContactSenderConfigError(ContactSenderError):
	"""Raised when the sender is not properly configured."""


class ContactNotFoundError(ContactSenderError):
	"""Raised when no contact matches the requested URN."""


class ContactAmbiguousError(ContactSenderError):
	"""Raised when more than one contact matches the requested URN."""


class ContactValidationError(ContactSenderError):
	"""Raised when an update payload violates contacts integration rules."""


class ContactSender:
	"""
	Sends contact read/update requests to the Flows contacts API via FlowsClient.

	Configuration is resolved by FlowsClient from the execution context.
	Contact URN resolution follows the same precedence as broadcasts integrations.
	"""

	CONTACTS_PATH = '/api/v2/contacts.json'

	def __init__(self, context: Context):
		self.context = context
		try:
			self._client = FlowsClient(context)
		except FlowsClientConfigError as exc:
			raise ContactSenderConfigError(str(exc)) from exc

	def _get_contact_urn(self) -> str | None:
		"""
		Get the contact URN from context.

		Priority: contact.urns[0] > contact.urn > parameters.contact_urn
		"""
		urns = self.context.contact.get('urns')
		if urns and isinstance(urns, (list, tuple)) and len(urns) > 0:
			return urns[0]
		return self.context.contact.get('urn') or self.context.parameters.get('contact_urn')

	def _resolve_urn(self, urn: str | None) -> str:
		"""Resolve the effective URN from an override or the execution context."""
		resolved = urn or self._get_contact_urn()
		if not resolved:
			raise ContactSenderConfigError(
				"Missing required configuration: contact URN not found in context "
				"(expected contact.urns, contact.urn, or parameters.contact_urn)."
			)
		return resolved

	@staticmethod
	def _alternate_whatsapp_brazil_urn(urn: str) -> str | None:
		"""
		Compute the alternate 9th-digit variant for WhatsApp Brazil URNs.

		Mirrors Flows ContactsEndpoint lookup behavior for whatsapp:55... numbers.
		"""
		if not urn.startswith('whatsapp:55'):
			return None

		_, _, path = urn.partition(':')

		if len(path) == 13 and path[4] == '9':
			alternate_path = path[:4] + path[5:]
		else:
			alternate_path = path[:4] + '9' + path[4:]

		return f'whatsapp:{alternate_path}'

	def _fetch_list(self, urn: str) -> list[dict[str, Any]]:
		"""Fetch the contacts list envelope for a URN filter."""
		try:
			response = self._client.get(self.CONTACTS_PATH, params={'urn': urn})
		except FlowsClientError as exc:
			raise ContactSenderError(str(exc)) from exc

		if not isinstance(response, dict):
			raise ContactSenderError('Unexpected Flows contacts list response.')

		results = response.get('results')
		if not isinstance(results, list):
			raise ContactSenderError('Unexpected Flows contacts list response.')

		return results

	def _get_by_urn(self, urn: str) -> tuple[dict[str, Any], str]:
		"""
		Resolve a single contact by URN, applying WhatsApp Brazil retry when needed.

		Returns:
			A tuple of (contact_dict, effective_urn).
		"""
		results = self._fetch_list(urn)
		if len(results) == 1:
			return results[0], urn
		if len(results) > 1:
			raise ContactAmbiguousError(f'Multiple contacts matched URN {urn!r}.')

		alternate_urn = self._alternate_whatsapp_brazil_urn(urn)
		if alternate_urn and alternate_urn != urn:
			alternate_results = self._fetch_list(alternate_urn)
			if len(alternate_results) == 1:
				return alternate_results[0], alternate_urn
			if len(alternate_results) > 1:
				raise ContactAmbiguousError(f'Multiple contacts matched URN {alternate_urn!r}.')

		raise ContactNotFoundError(f'No contact found for URN {urn!r}.')

	def get(self, urn: str | None = None) -> dict[str, Any]:
		"""
		Retrieve a single contact by URN.

		Args:
			urn: Optional URN override. When omitted, resolved from context.

		Returns:
			The Flows contact object as a dictionary.
		"""
		resolved_urn = self._resolve_urn(urn)
		contact, _effective_urn = self._get_by_urn(resolved_urn)
		return contact

	@staticmethod
	def _merge_update_payload(payload: dict[str, Any] | None, kwargs: dict[str, Any]) -> dict[str, Any]:
		"""Merge payload dict and kwargs, with kwargs taking precedence on conflict."""
		body = dict(payload or {})
		body.update(kwargs)
		return body

	@staticmethod
	def _validate_update_body(body: dict[str, Any]) -> None:
		"""Validate an update body before sending it to Flows."""
		if not body:
			raise ContactValidationError('Update payload must include at least one attribute.')
		if 'urns' in body:
			raise ContactValidationError(
				'Cannot include urns in the body when identifying the contact by URN in the query string.'
			)

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
			urn: Optional URN override. When omitted, resolved from context.
			**kwargs: Write attributes merged into the body; kwargs override conflicting payload keys.

		Returns:
			The updated Flows contact object as a dictionary.
		"""
		resolved_urn = self._resolve_urn(urn)
		body = self._merge_update_payload(payload, kwargs)
		self._validate_update_body(body)
		_contact, effective_urn = self._get_by_urn(resolved_urn)

		try:
			response = self._client.post(self.CONTACTS_PATH, params={'urn': effective_urn}, json=body)
		except FlowsClientError as exc:
			raise ContactSenderError(str(exc)) from exc

		if not isinstance(response, dict):
			raise ContactSenderError('Unexpected Flows contact update response.')

		return response
