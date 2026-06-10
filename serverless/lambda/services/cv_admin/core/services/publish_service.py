"""Publish service del Lambda `cv_admin` — workflow_dispatch via GitHub.

`dispatch` dispara el workflow `deploy-apps.yml` del repo `bypabloc/cv`
para el ref del stage actual (dev -> `dev`, prod -> `main`; el input
`env` del workflow acepta exactamente esos dos valores — ver el bloque
`on.workflow_dispatch.inputs` del yaml). `status` consulta el run mas
reciente del workflow para ese ref.

El PAT fine-grained (Actions RW en bypabloc/cv) se lee de SSM en cada
invocacion via `get_secret_by_name` (cachea el cliente SSM, no el valor
en logs). NUNCA se loguea el token; los errores HTTP de GitHub se
traducen a `ServiceError` 5200 GITHUB_API_ERROR sin incluirlo.
"""

from __future__ import annotations

from typing import Any

from settings.config import app_config
from shared.aws.ssm import get_secret_by_name
from shared.http.github import GithubApiError, dispatch_workflow, latest_run

from ._errors import ServiceError

_REPO = 'bypabloc/cv'
_WORKFLOW = 'deploy-apps.yml'
_ACTIONS_URL = (
    f'https://github.com/{_REPO}/actions/workflows/{_WORKFLOW}'
)


def _resolve_ref() -> str:
    """Branch objetivo del workflow segun el stage del Lambda.

    prod deploya `main`; cualquier otro stage (dev, local) deploya `dev`.
    Coincide con las options del input `env` de deploy-apps.yml.
    """
    return 'main' if app_config.environment == 'prod' else 'dev'


def _github_token() -> str:
    """PAT fine-grained leido de SSM (local: GITHUB_DEPLOY_TOKEN)."""
    return get_secret_by_name(
        'github-deploy-token', local_env='GITHUB_DEPLOY_TOKEN',
    )


def dispatch() -> dict[str, Any]:
    """Dispara el workflow_dispatch de deploy-apps.yml para el ref del stage.

    Returns:
        `{'dispatched': True, 'ref': <ref>, 'actions_url': <url>}`.

    Raises:
        ServiceError: 5200 GITHUB_API_ERROR si GitHub rechaza el dispatch
            (HTTP != 204, red o timeout). El mensaje NUNCA incluye el PAT.
    """
    ref = _resolve_ref()
    try:
        dispatch_workflow(
            _github_token(), _REPO, _WORKFLOW, ref, {'env': ref},
        )
    except GithubApiError as exc:
        raise ServiceError(
            f'GitHub rechazo el dispatch del workflow para ref {ref!r}',
            code=5200,
            error_code='GITHUB_API_ERROR',
            detail={'ref': ref},
        ) from exc
    return {'dispatched': True, 'ref': ref, 'actions_url': _ACTIONS_URL}


def status() -> dict[str, Any]:
    """Consulta el run mas reciente de deploy-apps.yml para el ref del stage.

    Returns:
        `{'status', 'conclusion', 'url', 'created_at', 'ref'}` del run mas
        reciente, o `{'status': 'none', 'ref': <ref>}` si no hay runs.

    Raises:
        ServiceError: 5200 GITHUB_API_ERROR si GitHub falla.
    """
    ref = _resolve_ref()
    try:
        run = latest_run(_github_token(), _REPO, _WORKFLOW, ref)
    except GithubApiError as exc:
        raise ServiceError(
            f'GitHub fallo al consultar los runs para ref {ref!r}',
            code=5200,
            error_code='GITHUB_API_ERROR',
            detail={'ref': ref},
        ) from exc
    if run is None:
        return {'status': 'none', 'ref': ref}
    return {
        'status': run.get('status'),
        'conclusion': run.get('conclusion'),
        'url': run.get('html_url'),
        'created_at': run.get('created_at'),
        'ref': ref,
    }
