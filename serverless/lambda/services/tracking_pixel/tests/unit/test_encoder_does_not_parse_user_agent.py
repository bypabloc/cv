"""Controller tracking/track — encoder async NO parsea UA.

Given ASYNC_MODE=true,
When el controller Track procesa un request valido,
Then `parse_user_agent` NUNCA se invoca: la decision de diseno del plan
     es que el worker `tracking_worker` haga el UA parsing (cacheado en
     DynamoDB, namespace='ua'), no el encoder. Asi el encoder responde
     con TTFB minimo y no paga el costo del parsing en el hot path.

AC del plan lambdas-async-sqs: el encoder es minimo; enrichment pesado
es responsabilidad del worker.
"""

import pytest

from tests.unit._helpers import CHROME_UA, valid_body

pytestmark = pytest.mark.unit


def test_encoder_does_not_parse_user_agent(
    async_mode: None,
    captured_queue: list[dict],
    neon_off: dict[str, int],
    monkeypatch: pytest.MonkeyPatch,
    tracking_aws: None,
) -> None:
    from controllers.tracking.track import Track

    # Arrange: instrumentamos parse_user_agent para detectar invocaciones.
    invocations: list[str | None] = []

    def _spy_parse(user_agent: str | None) -> dict[str, str]:
        invocations.append(user_agent)
        return {
            'browser': 'Chrome',
            'browser_version': '118',
            'os': 'Linux',
            'device_type': 'desktop',
        }

    monkeypatch.setattr(
        'services.tracking_service.parse_user_agent', _spy_parse
    )

    event = {
        **valid_body(),
        'meta': {'ip': '1.2.3.4', 'country': 'CL', 'user_agent': CHROME_UA},
    }

    # Act
    result = Track(event=event).run()

    # Assert: el encoder devolvio 202 + 1 mensaje a SQS.
    assert result['is_valid'] is True
    assert result['data']['status'] == 'accepted'
    assert len(captured_queue) == 1
    # CLAVE: parse_user_agent NUNCA se invoco — el worker lo hara.
    assert invocations == []
    # El UA crudo SI viaja en el payload SQS, sin parsear.
    assert captured_queue[0]['payload']['user_agent'] == CHROME_UA
