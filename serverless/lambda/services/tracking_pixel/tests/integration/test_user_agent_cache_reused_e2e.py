"""E2E — dos requests con el mismo User-Agent reusan el cache de parseo.

Given dos eventos API Gateway con identico User-Agent,
When lambda_handler procesa ambos end-to-end,
Then parse_user_agent escribe UNA sola entrada de cache (namespace `ua`)
  en la tabla cache: la primera request la computa y la segunda la lee,
  sin generar una entrada nueva. Ambos items quedan enriquecidos igual.
"""

import pytest

from tests.integration._fixtures._builders import (
    CHROME_UA,
    api_gw_event,
    cache_table,
    lambda_context,
    scan_tracking,
    valid_body,
)

pytestmark = pytest.mark.integration


def _ua_cache_keys() -> list[str]:
    """Devuelve los cache_key de las entradas del namespace `ua`.

    El decorador @cached escribe la key `ua:parse_user_agent:<hash>`. Se
    excluyen los items de lock distribuido (prefijo `lock:`).
    """
    items = cache_table().scan().get('Items', [])
    return sorted(
        item['cache_key']
        for item in items
        if str(item['cache_key']).startswith('ua:parse_user_agent:')
    )


def test_user_agent_cache_reused_e2e():
    import handler

    ctx = lambda_context()

    # Act: primera request con el User-Agent -> computa y cachea el parseo.
    first = handler.lambda_handler(
        api_gw_event(body=valid_body(), user_agent=CHROME_UA), ctx
    )
    keys_after_first = _ua_cache_keys()

    # Act: segunda request con el MISMO User-Agent -> reusa el cache.
    second = handler.lambda_handler(
        api_gw_event(body=valid_body(), user_agent=CHROME_UA), ctx
    )
    keys_after_second = _ua_cache_keys()

    # Assert: ambas requests pasaron.
    assert first['statusCode'] == 204
    assert second['statusCode'] == 204

    # Assert: la primera request creo exactamente una entrada de cache.
    assert len(keys_after_first) == 1

    # Assert: la segunda request NO creo una entrada nueva (reuso la
    # misma key): el set de keys es identico tras ambas requests.
    assert keys_after_second == keys_after_first

    # Assert: el enrichment fue identico en los dos items persistidos.
    items = scan_tracking()
    assert len(items) == 2
    assert {item['browser'] for item in items} == {'Chrome'}
    assert {item['device_type'] for item in items} == {'desktop'}
