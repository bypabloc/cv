"""E2E del action `publish.dispatch` del Lambda cv_admin (run REAL).

Dispatch REAL en dev: encola un run de deploy-apps.yml para el ref `dev`
(aceptable — el workflow tiene concurrency queue por env). Marker pytest
`publish` para excluirlo de corridas frecuentes con `-m "not publish"`.

1. `t0` = now UTC (con margen chico de skew de reloj).
2. `publish.dispatch {}` -> 200 con el body exacto
   `{dispatched, ref, actions_url}`.
3. Poll `publish.status` con backoff (max 60s) hasta ver un run del
   workflow con `ref == 'dev'` y `created_at > t0`.
4. Shape exacto del run: status del enum, url del run, created_at > t0.
5. NO espera el deploy completo (eso es la Parte C del plan).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import time
from typing import Any

import pytest

from ._cv_admin_flows import CvAdminSession

_RUN_URL_PREFIX = 'https://github.com/bypabloc/cv/actions/runs/'
_STATUS_ENUM = {'queued', 'in_progress', 'completed'}
_POLL_BUDGET_SECONDS = 60.0


def _parse_created(raw: str) -> datetime:
    """created_at ISO 8601 de GitHub (`...Z`) -> datetime aware UTC."""
    return datetime.fromisoformat(raw.replace('Z', '+00:00'))


@pytest.mark.api
@pytest.mark.publish
def test_cv_admin_publish_dispatch_full_lifecycle(
    cv_admin_session: CvAdminSession,
) -> None:
    """
    Given una sesion admin sintetica contra cv_admin en dev,
    When dispara publish.dispatch y sondea publish.status con backoff
    hasta 60s,
    Then el dispatch responde su contrato exacto y aparece un run NUEVO
    de deploy-apps.yml (ref dev, created_at > t0) con el shape
    {status, url, created_at} esperado — sin esperar el deploy completo.
    [AC-7]
    """
    session = cv_admin_session

    # 1. t0 con margen de 5s por skew entre el reloj local y GitHub.
    t0 = datetime.now(UTC) - timedelta(seconds=5)

    # 2. dispatch REAL (encola un run del workflow en el ref dev).
    rd = session.post('dispatch', {}, operation='publish')
    assert rd.status == 200, f'dispatch HTTP {rd.status}: {rd.body!r}'
    assert rd.body == {
        'dispatched': True,
        'ref': 'dev',
        'actions_url': (
            'https://github.com/bypabloc/cv/actions/workflows/'
            'deploy-apps.yml'
        ),
    }

    # 3. Poll del status con backoff hasta ver el run nuevo.
    deadline = time.monotonic() + _POLL_BUDGET_SECONDS
    delay = 2.0
    run: dict[str, Any] | None = None
    last: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        rs = session.post('status', {}, operation='publish')
        if rs.status == 200 and isinstance(rs.body, dict):
            last = rs.body
            if (
                last.get('ref') == 'dev'
                and isinstance(last.get('created_at'), str)
                and _parse_created(last['created_at']) > t0
            ):
                run = last
                break
        time.sleep(delay)
        delay = min(delay * 1.5, 10.0)

    if run is None:
        pytest.fail(
            'no aparecio un run nuevo de deploy-apps.yml (ref dev, '
            f'created_at > t0) en {_POLL_BUDGET_SECONDS:.0f}s; '
            f'ultimo status: {last!r}'
        )

    # 4. Shape exacto del run nuevo.
    assert run['ref'] == 'dev'
    assert run['status'] in _STATUS_ENUM
    url = run['url']
    assert url[: len(_RUN_URL_PREFIX)] == _RUN_URL_PREFIX
    assert _parse_created(run['created_at']) > t0
