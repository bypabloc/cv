"""Un payload invalido corta en validate() (el service nunca corre).

Given un evento de upsert-experience SIN company (campo requerido),
When se ejecuta UpsertExperience.run(),
Then {is_valid: False, code: 1000 VALIDATION_ERROR} y el service NO se
llama (la fase validate corta antes de execute).
"""

from unittest.mock import MagicMock

from ._helpers import _make_authed_event


def test_controller_invalid_payload_validation_error(monkeypatch):
    from services import content_service

    service_mock = MagicMock()
    monkeypatch.setattr(content_service, 'upsert_entity', service_mock)

    from controllers.content import upsert_experience as ctl

    event = _make_authed_event(
        data={'slug': 'x', 'role': {'es': 'r'}},  # faltan company/etc.
    )
    result = ctl.UpsertExperience(event=event).run()

    assert result['is_valid'] is False
    assert result['code'] == 1000
    service_mock.assert_not_called()
