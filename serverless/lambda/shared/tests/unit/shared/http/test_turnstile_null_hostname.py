"""verify_turnstile_token NO crashea si siteverify devuelve hostname null.

Given Cloudflare retorna success=true con `"hostname": null` (key presente
     pero null),
When verify_turnstile_token,
Then retorna el dict sin lanzar AttributeError (None.lower()).

Guard de regresion: `result.get('hostname', '').lower()` devolvia None
(el default '' solo aplica si la key esta AUSENTE, no si es null) y
None.lower() reventaba toda la validacion.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from shared.http.turnstile import (
    TURNSTILE_SITEVERIFY_URL,
    verify_turnstile_token,
)

pytestmark = pytest.mark.unit


@respx.mock
def test_verify_turnstile_token_tolerates_null_hostname(
    turnstile_env: None,
) -> None:
    respx.post(TURNSTILE_SITEVERIFY_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                'success': True,
                'hostname': None,
                'challenge_ts': '2026-05-29T10:00:00Z',
            },
        ),
    )

    result = verify_turnstile_token('valid-cf-response', remote_ip='1.2.3.4')

    assert result['success'] is True
