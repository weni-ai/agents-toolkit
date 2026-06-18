"""
Tests for FlowsClient configuration resolution (User Story 2).

Covers precedence (project > credentials > globals > environment),
default fallback, normalization, and fail-fast configuration errors.
"""

import pytest

from weni.flows import FlowsClient, FlowsClientConfigError


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
	"""Ensure ambient environment variables don't leak into resolution tests."""
	monkeypatch.delenv('FLOWS_BASE_URL', raising=False)
	monkeypatch.delenv('PROJECT_UUID', raising=False)


class TestBaseURLResolution:
	def test_project_takes_precedence_over_credentials(self, make_context):
		context = make_context(
			project={'flows_url': 'https://flows.project', 'auth_token': 'tk'},
			credentials={'flows_url': 'https://flows.creds'},
		)

		assert FlowsClient(context).base_url == 'https://flows.project'

	def test_credentials_take_precedence_over_globals(self, make_context):
		context = make_context(
			project={'auth_token': 'tk'},
			credentials={'flows_url': 'https://flows.creds'},
			globals={'flows_url': 'https://flows.globals'},
		)

		assert FlowsClient(context).base_url == 'https://flows.creds'

	def test_globals_take_precedence_over_environment(self, make_context, monkeypatch):
		monkeypatch.setenv('FLOWS_BASE_URL', 'https://flows.env')
		context = make_context(project={'auth_token': 'tk'}, globals={'flows_url': 'https://flows.globals'})

		assert FlowsClient(context).base_url == 'https://flows.globals'

	def test_environment_fallback(self, make_context, monkeypatch):
		monkeypatch.setenv('FLOWS_BASE_URL', 'https://flows.env')
		context = make_context(project={'auth_token': 'tk'})

		assert FlowsClient(context).base_url == 'https://flows.env'

	def test_default_when_absent_everywhere(self, make_context):
		context = make_context(project={'auth_token': 'tk'})

		assert FlowsClient(context).base_url == 'https://flows.stg.cloud.weni.ai'

	def test_trailing_slash_stripped(self, make_context):
		context = make_context(project={'flows_url': 'https://flows.example.com/', 'auth_token': 'tk'})

		assert FlowsClient(context).base_url == 'https://flows.example.com'


class TestProjectUUIDResolution:
	def test_resolved_from_project(self, make_context):
		context = make_context(project={'auth_token': 'tk', 'uuid': 'proj-123'})

		assert FlowsClient(context).project_uuid == 'proj-123'

	def test_resolved_from_credentials(self, make_context):
		context = make_context(project={'auth_token': 'tk'}, credentials={'uuid': 'proj-creds'})

		assert FlowsClient(context).project_uuid == 'proj-creds'

	def test_resolved_from_globals(self, make_context):
		context = make_context(project={'auth_token': 'tk'}, globals={'uuid': 'proj-globals'})

		assert FlowsClient(context).project_uuid == 'proj-globals'

	def test_resolved_from_environment(self, make_context, monkeypatch):
		monkeypatch.setenv('PROJECT_UUID', 'proj-env')
		context = make_context(project={'auth_token': 'tk'})

		assert FlowsClient(context).project_uuid == 'proj-env'

	def test_none_when_absent(self, make_context):
		context = make_context(project={'auth_token': 'tk'})

		assert FlowsClient(context).project_uuid is None


class TestAuthTokenValidation:
	def test_missing_token_raises_config_error(self, make_context):
		with pytest.raises(FlowsClientConfigError) as exc_info:
			FlowsClient(make_context(project={'flows_url': 'https://flows.example.com'}))

		assert 'auth_token' in str(exc_info.value)
		assert 'context.project' in str(exc_info.value)

	def test_missing_token_never_sends_request(self, make_context, mocker):
		mock_request = mocker.patch('weni.flows.client.requests.request')

		with pytest.raises(FlowsClientConfigError):
			FlowsClient(make_context())

		mock_request.assert_not_called()
