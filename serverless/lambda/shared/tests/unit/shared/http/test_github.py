"""Tests para shared.http.github (httpx con respx)."""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from shared.http.github import (
    GITHUB_API_BASE,
    GithubApiError,
    dispatch_workflow,
    latest_run,
)

pytestmark = pytest.mark.unit

_REPO = 'bypabloc/cv'
_WORKFLOW = 'deploy-apps.yml'
_DISPATCH_URL = (
    f'{GITHUB_API_BASE}/repos/{_REPO}/actions/workflows/'
    f'{_WORKFLOW}/dispatches'
)
_RUNS_URL = f'{GITHUB_API_BASE}/repos/{_REPO}/actions/workflows/{_WORKFLOW}/runs'


class TestDispatchWorkflow:
    """dispatch_workflow — POST /dispatches."""

    @respx.mock
    def test_when_204_then_returns_none(self) -> None:
        """
        Given GitHub responde 204 al workflow_dispatch,
        When dispatch_workflow,
        Then retorna None y el request lleva ref + inputs + Bearer.
        """
        route = respx.post(_DISPATCH_URL).mock(
            return_value=httpx.Response(204)
        )

        result = dispatch_workflow(
            'fake-token', _REPO, _WORKFLOW, 'dev', {'env': 'dev'}
        )

        assert result is None
        assert route.call_count == 1
        request = route.calls[0].request
        assert request.headers['Authorization'] == 'Bearer fake-token'
        assert json.loads(request.content) == {
            'ref': 'dev',
            'inputs': {'env': 'dev'},
        }

    @respx.mock
    def test_when_http_422_then_raises_github_api_error(self) -> None:
        """
        Given GitHub responde 422 (ref/inputs invalidos),
        When dispatch_workflow,
        Then GithubApiError con status en extra y SIN el token.
        """
        respx.post(_DISPATCH_URL).mock(
            return_value=httpx.Response(422, json={'message': 'invalid'})
        )

        with pytest.raises(GithubApiError) as exc:
            dispatch_workflow('fake-token', _REPO, _WORKFLOW, 'dev', {})

        assert exc.value.code == 'GITHUB_API_ERROR'
        assert exc.value.extra['status'] == 422
        assert 'fake-token' not in exc.value.message
        assert 'fake-token' not in str(exc.value.extra)

    @respx.mock
    def test_when_timeout_then_raises_github_api_error(self) -> None:
        """
        Given httpx levanta timeout al POST,
        When dispatch_workflow,
        Then GithubApiError (sin token en el mensaje).
        """
        respx.post(_DISPATCH_URL).mock(
            side_effect=httpx.ConnectTimeout('timeout')
        )

        with pytest.raises(GithubApiError) as exc:
            dispatch_workflow('fake-token', _REPO, _WORKFLOW, 'dev', {})

        assert exc.value.code == 'GITHUB_API_ERROR'
        assert 'fake-token' not in exc.value.message


class TestLatestRun:
    """latest_run — GET /runs?branch=<ref>&per_page=1."""

    @respx.mock
    def test_when_runs_exist_then_returns_first(self) -> None:
        """
        Given el workflow tiene runs para el branch,
        When latest_run,
        Then retorna el primer run del body.
        """
        run = {
            'id': 42,
            'status': 'completed',
            'conclusion': 'success',
            'html_url': 'https://github.com/bypabloc/cv/actions/runs/42',
            'created_at': '2026-06-09T10:00:00Z',
        }
        route = respx.get(_RUNS_URL).mock(
            return_value=httpx.Response(
                200, json={'total_count': 1, 'workflow_runs': [run]}
            )
        )

        result = latest_run('fake-token', _REPO, _WORKFLOW, 'dev')

        assert result == run
        request = route.calls[0].request
        assert request.url.params['branch'] == 'dev'
        assert request.url.params['per_page'] == '1'

    @respx.mock
    def test_when_no_runs_then_returns_none(self) -> None:
        """
        Given el workflow no tiene runs para el branch,
        When latest_run,
        Then retorna None.
        """
        respx.get(_RUNS_URL).mock(
            return_value=httpx.Response(
                200, json={'total_count': 0, 'workflow_runs': []}
            )
        )

        result = latest_run('fake-token', _REPO, _WORKFLOW, 'dev')

        assert result is None

    @respx.mock
    def test_when_http_500_then_raises_github_api_error(self) -> None:
        """
        Given GitHub responde 500,
        When latest_run,
        Then GithubApiError con status=500 en extra.
        """
        respx.get(_RUNS_URL).mock(return_value=httpx.Response(500))

        with pytest.raises(GithubApiError) as exc:
            latest_run('fake-token', _REPO, _WORKFLOW, 'dev')

        assert exc.value.code == 'GITHUB_API_ERROR'
        assert exc.value.extra['status'] == 500
