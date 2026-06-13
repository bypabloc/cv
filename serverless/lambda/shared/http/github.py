"""@module shared.http.github — cliente minimo de la GitHub REST API.

Portador unico de las llamadas salientes a `api.github.com` del backend
(hoy: la operation `publish` del Lambda `cv`). Mismo criterio que
`shared.http.turnstile`: httpx sincrono con timeout corto, y un error
tipado (`GithubApiError`) que el caller traduce a su contrato.

Operaciones soportadas:
- `dispatch_workflow` — `POST /repos/{repo}/actions/workflows/{workflow}/
  dispatches` (workflow_dispatch). GitHub responde 204 sin body.
- `latest_run` — `GET /repos/{repo}/actions/workflows/{workflow}/runs?
  branch={ref}&per_page=1` y devuelve el run mas reciente (o None).

Seguridad: el `token` (PAT fine-grained) viaja SOLO en el header
`Authorization` del request saliente. NUNCA se loguea ni se incluye en
`message`/`extra` de una excepcion.
"""

from __future__ import annotations

from typing import Any

import httpx

from shared.core.exceptions import ApplicationError
from shared.observability.logger import logger

GITHUB_API_BASE = 'https://api.github.com'

# Timeout corto: el dispatch es fire-and-forget y el status es un GET
# liviano; un GitHub degradado no debe colgar el Lambda.
_TIMEOUT_SECONDS = 10.0
_API_VERSION = '2022-11-28'


class GithubApiError(ApplicationError):
    """Fallo al llamar la GitHub REST API (HTTP inesperado, red o timeout)."""

    default_code = 'GITHUB_API_ERROR'
    status_code = 502


def _headers(token: str) -> dict[str, str]:
    """Headers estandar de la GitHub REST API (Bearer + version pinneada)."""
    return {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': _API_VERSION,
    }


def dispatch_workflow(
    token: str,
    repo: str,
    workflow: str,
    ref: str,
    inputs: dict[str, str] | None = None,
) -> None:
    """Dispara un `workflow_dispatch` del workflow dado sobre `ref`.

    Args:
        token: PAT fine-grained con permiso Actions RW sobre `repo`.
            NUNCA se loguea.
        repo: repositorio `owner/name` (ej. 'bypabloc/cv').
        workflow: filename del workflow (ej. 'deploy-apps.yml').
        ref: branch o tag sobre el que corre el workflow.
        inputs: inputs del `workflow_dispatch` (segun el `on:` del yaml).

    Raises:
        GithubApiError: red/timeout o HTTP distinto de 204.
    """
    url = (
        f'{GITHUB_API_BASE}/repos/{repo}/actions/workflows/'
        f'{workflow}/dispatches'
    )
    payload: dict[str, Any] = {'ref': ref, 'inputs': inputs or {}}
    try:
        with httpx.Client(timeout=_TIMEOUT_SECONDS) as client:
            response = client.post(url, json=payload, headers=_headers(token))
    except httpx.HTTPError as exc:
        msg = 'GitHub workflow dispatch fallo (red o timeout)'
        raise GithubApiError(
            msg,
            extra={'repo': repo, 'workflow': workflow, 'ref': ref},
        ) from exc

    if response.status_code != 204:
        logger.warning(
            'github workflow dispatch rechazado',
            extra={
                'status': response.status_code,
                'repo': repo,
                'workflow': workflow,
                'ref': ref,
            },
        )
        msg = f'GitHub dispatch HTTP {response.status_code}'
        raise GithubApiError(
            msg,
            extra={
                'status': response.status_code,
                'repo': repo,
                'workflow': workflow,
                'ref': ref,
            },
        )


def latest_run(
    token: str,
    repo: str,
    workflow: str,
    ref: str,
) -> dict[str, Any] | None:
    """Devuelve el run mas reciente del workflow para `ref` (o None).

    Args:
        token: PAT fine-grained con permiso Actions sobre `repo`.
            NUNCA se loguea.
        repo: repositorio `owner/name` (ej. 'bypabloc/cv').
        workflow: filename del workflow (ej. 'deploy-apps.yml').
        ref: branch cuyos runs se consultan.

    Returns:
        El dict crudo del run mas reciente (`workflow_runs[0]` de la API)
        o `None` si el workflow no tiene runs para ese ref.

    Raises:
        GithubApiError: red/timeout, HTTP distinto de 200 o body no-JSON.
    """
    url = f'{GITHUB_API_BASE}/repos/{repo}/actions/workflows/{workflow}/runs'
    params = {'branch': ref, 'per_page': 1}
    try:
        with httpx.Client(timeout=_TIMEOUT_SECONDS) as client:
            response = client.get(url, params=params, headers=_headers(token))
    except httpx.HTTPError as exc:
        msg = 'GitHub workflow runs fallo (red o timeout)'
        raise GithubApiError(
            msg,
            extra={'repo': repo, 'workflow': workflow, 'ref': ref},
        ) from exc

    if response.status_code != 200:
        msg = f'GitHub runs HTTP {response.status_code}'
        raise GithubApiError(
            msg,
            extra={
                'status': response.status_code,
                'repo': repo,
                'workflow': workflow,
                'ref': ref,
            },
        )

    try:
        body: dict[str, Any] = response.json()
    except ValueError as exc:
        msg = 'GitHub runs devolvio un body no-JSON'
        raise GithubApiError(
            msg,
            extra={'repo': repo, 'workflow': workflow, 'ref': ref},
        ) from exc

    runs = body.get('workflow_runs') or []
    if not runs:
        return None
    run: dict[str, Any] = runs[0]
    return run
