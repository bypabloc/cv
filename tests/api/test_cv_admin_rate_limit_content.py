"""E2E del rate-limit per-IP del endpoint `/cv-admin#content` (30/60s).

Marker `slow`: el test alinea la rafaga al INICIO de una ventana de 60s
alineada a epoch (mejor caso: cae entera en una ventana). IP FIJA dedicada
FUERA del pool del IpRotator (`203.0.113.0` — el pool usa hosts .1-.254)
para no contaminar (ni ser contaminado por) el resto de la suite; los
buckets de esa IP se limpian antes de la rafaga.

La rafaga dispara `catalogs` consecutivos con la MISMA IP hasta el primer
429 (cap 2x limite + 2). El sliding window weighted del backend bucketiza
por SU reloj: aun alineando, el drift test<->Lambda puede partir la rafaga
en 2 ventanas y correr el 429 unos requests mas alla del 31 (medido: la
ventana previa con count 1 deja effective = 29 + peso < 30 en el request
31). Por eso el numero de 200s NO es exacto — los invariantes si:
NUNCA un 429 antes de 30 doscientos (buckets limpios) y el body/headers
del 429 EXACTOS (RATE_LIMIT_EXCEEDED + extra + Retry-After). [doc 11]
"""

from __future__ import annotations

import re
import time

import pytest

from shared.environment import Environment

from ._cv_admin_flows import CvAdminSession


# IP dedicada FUERA del pool TEST-NET del IpRotator (hosts .1-.254).
_FIXED_IP = '203.0.113.0'
_ENDPOINT = '/cv-admin#content'
_LIMIT = 30
_WINDOW_SECONDS = 60


def _align_to_window_start(min_remaining: float = 50.0) -> None:
    """Espera al proximo inicio de ventana si queda poco margen.

    Las ventanas del rate-limit estan alineadas a epoch
    (`now // 60 * 60`). Si quedan menos de `min_remaining` segundos en la
    ventana actual, duerme hasta el proximo inicio (+0.5s de margen) para
    que la rafaga completa caiga DENTRO de una sola ventana.
    """
    remaining = _WINDOW_SECONDS - (time.time() % _WINDOW_SECONDS)
    if remaining < min_remaining:
        time.sleep(remaining + 0.5)


@pytest.mark.api
@pytest.mark.slow
def test_cv_admin_rate_limit_content(
    cv_admin_session: CvAdminSession,
    environment: Environment,
) -> None:
    """
    Given la regla 30/60s del endpoint /cv-admin#content y una IP fija
    dedicada con sus buckets limpios,
    When dispara catalogs consecutivos con la misma IP hasta el primer 429,
    Then nunca recibe un 429 antes de 30 doscientos y el 429 llega con el
    body del rate-limit EXACTO (RATE_LIMIT_EXCEEDED +
    limit/window/endpoint/ip) y el header Retry-After. [doc 11]
    """
    session = cv_admin_session

    # Arrange: warm del Lambda (IP rotada, no cuenta para la IP fija) +
    # buckets de la IP fija limpios + rafaga alineada a la ventana.
    warm = session.post('catalogs', {})
    assert warm.status == 200, f'warm fallo: {warm.status}: {warm.body!r}'
    environment.cleanup_rate_limit_buckets(ip=_FIXED_IP, endpoint=_ENDPOINT)
    _align_to_window_start()

    # Act: misma IP, sin retries (cada status cuenta), hasta el primer 429.
    # Cap 2x limite + 2: si la rafaga cruza el borde de ventana, el peso de
    # la ventana previa corre el 429 unos requests; 2 ventanas lo cubren.
    responses = []
    for _ in range(2 * _LIMIT + 2):
        response = session.post_raw(
            'catalogs',
            {},
            bearer=session.token(),
            ip=_FIXED_IP,
        )
        responses.append(response)
        if response.status == 429:
            break
    statuses = [r.status for r in responses]

    # Assert: el ultimo es el 429; todos los previos 200; y el throttle
    # NUNCA llego antes del limite (los buckets partian limpios).
    assert statuses[-1] == 429, f'sin 429 tras {len(statuses)}: {statuses}'
    successes = statuses[:-1]
    assert successes == [200] * len(successes), f'statuses: {statuses}'

    # WEAK-ASSERT exento: el sliding window weighted hace inalcanzable un
    # conteo exacto de 200s (el drift de reloj test<->Lambda parte la
    # rafaga en 2 ventanas); el invariante duro es ">= limite".
    assert len(successes) >= _LIMIT, f'429 temprano: {statuses}'  # noqa: WEAK-ASSERT

    throttled = responses[-1]
    assert throttled.body['code'] == 'RATE_LIMIT_EXCEEDED'
    assert re.fullmatch(
        rf'Rate limit exceeded: \d+\.\d >= {_LIMIT} '
        rf'in {_WINDOW_SECONDS}s window',
        throttled.body['error'],
    ), f'error message: {throttled.body["error"]!r}'
    extra = throttled.body['extra']
    assert extra['limit'] == _LIMIT
    assert extra['window_seconds'] == _WINDOW_SECONDS
    assert extra['endpoint'] == _ENDPOINT
    assert extra['ip'] == _FIXED_IP

    # WEAK-ASSERT exento: effective_count = count actual + count previo
    # ponderado; con la rafaga partida en 2 ventanas el valor exacto
    # depende del instante del corte. Sin ">= limite" no habria 429.
    assert extra['effective_count'] >= float(_LIMIT)  # noqa: WEAK-ASSERT
    assert extra['retry_after_seconds'] == 30
    assert throttled.header('Retry-After') == '30'
