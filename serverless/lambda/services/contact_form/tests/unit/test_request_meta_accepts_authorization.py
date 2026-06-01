"""Guard de regresion: RequestMeta acepta `_meta.authorization`.

El http_handler generico (shared.lambda_kit.http_dispatch) inyecta SIEMPRE
la clave `authorization` dentro de `data._meta` (la usa el Lambda auth).
RequestMeta tiene `extra='forbid'`; sin declarar el campo, cada POST
/contact reventaba con ValidationError -> 400. Este test fija el contrato.
"""

import pytest

pytestmark = pytest.mark.unit


def test_request_meta_accepts_authorization():
    """
    Given el _meta que http_handler inyecta (con authorization),
    When se construye RequestMeta,
    Then valida sin error y authorization queda accesible.
    """
    from models.contact import RequestMeta

    meta = RequestMeta(
        ip='203.0.113.10',
        country='CL',
        user_agent='Mozilla/5.0',
        bypass_token=None,
        origin='https://hub.portfolio.dev.the-full-stack.com',
        authorization='Bearer abc.def.ghi',
    )

    assert meta.authorization == 'Bearer abc.def.ghi'
    assert meta.ip == '203.0.113.10'
