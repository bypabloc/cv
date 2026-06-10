"""E2E del action `publish.status` del Lambda cv_admin (sin dispatch).

`publish.status {}` consulta el run mas reciente del workflow
`deploy-apps.yml` para el ref del stage (dev -> branch `dev`) via la
GitHub API y devuelve el shape
`{status, conclusion, url, created_at, ref}`. Este test NO dispara
ningun run: valida el shape exacto contra el ultimo run real.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from ._cv_admin_flows import CvAdminSession


_RUN_URL_PREFIX = 'https://github.com/bypabloc/cv/actions/runs/'
_STATUS_ENUM = {'queued', 'in_progress', 'completed'}
_CONCLUSION_ENUM = {
    None,
    'success',
    'failure',
    'cancelled',
    'skipped',
    'startup_failure',
    'timed_out',
    'action_required',
    'neutral',
    'stale',
}


@pytest.mark.api
def test_cv_admin_publish_status(
    cv_admin_session: CvAdminSession,
) -> None:
    """
    Given el workflow deploy-apps.yml con runs previos en el ref dev,
    When se invoca publish.status sin dispatch previo,
    Then devuelve el ultimo run real con el shape exacto: ref 'dev',
    status del enum, url del run en GitHub y created_at ISO 8601. [AC-7]
    """
    r = cv_admin_session.post('status', {}, operation='publish')

    assert r.status == 200, f'publish.status HTTP {r.status}: {r.body!r}'
    assert sorted(r.body.keys()) == [
        'conclusion',
        'created_at',
        'ref',
        'status',
        'url',
    ]
    assert r.body['ref'] == 'dev'
    assert r.body['status'] in _STATUS_ENUM
    assert r.body['conclusion'] in _CONCLUSION_ENUM
    url = r.body['url']
    assert url[: len(_RUN_URL_PREFIX)] == _RUN_URL_PREFIX
    created = datetime.fromisoformat(r.body['created_at'])
    assert created.utcoffset().total_seconds() == 0
