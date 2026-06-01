"""Guard de regresion: TrackEventMeta acepta `_meta.authorization`.

El http_handler generico inyecta SIEMPRE `authorization` en `data._meta`.
TrackEventMeta tiene `extra='forbid'`; sin declarar el campo, cada POST
/track reventaba con ValidationError -> 400. Este test fija el contrato.
"""

import pytest

pytestmark = pytest.mark.unit


def test_track_event_meta_accepts_authorization():
    """
    Given el _meta que http_handler inyecta (con authorization),
    When se construye TrackEventMeta,
    Then valida sin error y authorization queda accesible.
    """
    from models.tracking import TrackEventMeta

    meta = TrackEventMeta(
        ip='203.0.113.10',
        country='CL',
        user_agent='Mozilla/5.0',
        bypass_token=None,
        origin='https://hub.portfolio.dev.the-full-stack.com',
        authorization='Bearer abc.def.ghi',
    )

    assert meta.authorization == 'Bearer abc.def.ghi'
    assert meta.ip == '203.0.113.10'
