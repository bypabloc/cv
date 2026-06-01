"""contact_service emite metrica OwnerEmailFailed cuando el invoke falla.

Given un contacto que persiste OK pero el invoke a send_email lanza,
When se ejecuta process_contact_form,
Then se persiste igual (no se propaga) y se emite metrica OwnerEmailFailed.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

_TEST_SESSION = 'sess-test-01234567890123456789'


def test_contact_service_emits_metric_when_email_fails(monkeypatch):
    from services import contact_service
    from services.contact_service import process_contact_form
    from shared.aws.lambda_invoke import LambdaInvokeError

    # Arrange: persistencia OK (mock save_contact), pero el invoke async a
    # send_email falla con LambdaInvokeError -> debe loguear + metrica, sin
    # propagar (el contacto ya quedo en Neon).
    contact_service.metrics.clear_metrics()
    saved = {'contact_id': 'c-123', 'created_at': '2026-05-21T00:00:00Z'}
    monkeypatch.setattr(contact_service, 'save_contact', lambda _p: saved)
    monkeypatch.setattr(
        contact_service,
        'get_parameter_by_name',
        lambda *_a, **_kw: 'owner@example.com',
    )

    def _raise(*, function_name: str, payload: dict) -> str:
        msg = f'invoke_async to {function_name} failed'
        raise LambdaInvokeError(msg)

    monkeypatch.setattr(contact_service, 'invoke_async', _raise)

    # Act
    process_contact_form(
        form_fields={
            'name': 'Pablo',
            'email': 'p@example.com',
            'message': 'Hola mundo largo de prueba',
            'session_id': _TEST_SESSION,
        },
        session_id=_TEST_SESSION,
        ip='1.2.3.4',
        country='CL',
        user_agent='Mozilla/5.0',
        origin_niche='fintech',
    )

    # Assert: metrica de fallo emitida (no se propago la excepcion)
    assert 'OwnerEmailFailed' in dict(contact_service.metrics.metric_set)
