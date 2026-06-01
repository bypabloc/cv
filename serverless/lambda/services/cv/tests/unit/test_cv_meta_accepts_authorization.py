"""Guard de regresion: CvRequestMeta acepta `_meta.authorization`.

El http_handler generico inyecta SIEMPRE `authorization` en `data._meta`.
CvRequestMeta tiene `extra='forbid'`; sin declarar el campo, cada GET /cv
reventaba con ValidationError -> 400. Este test fija el contrato.
"""

import pytest

pytestmark = pytest.mark.unit


def test_cv_request_meta_accepts_authorization():
    """
    Given el _meta que http_handler inyecta (con authorization),
    When se construye CvRequestMeta,
    Then valida sin error y authorization queda accesible.
    """
    from models.cv import CvRequestMeta

    meta = CvRequestMeta(
        ip='203.0.113.10',
        country='CL',
        user_agent='Mozilla/5.0',
        bypass_token=None,
        origin='https://the-full-stack.com',
        authorization='Bearer abc.def.ghi',
    )

    assert meta.authorization == 'Bearer abc.def.ghi'
    assert meta.ip == '203.0.113.10'
