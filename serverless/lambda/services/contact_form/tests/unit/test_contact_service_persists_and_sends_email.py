"""Service contact_service.process_contact_form — persiste y notifica.

Given un payload de form valido + metadata HTTP, y el entorno AWS
mockeado,
When se invoca process_contact_form,
Then el contacto queda persistido en Neon (con contact_id UUIDv7), el
     helper ensure_session_and_visit recibe los kwargs esperados, y se
     invoca send_email async con el payload kind=contact (sin metrica de
     fallo).

Spec sessions-normalize: el service UPSERTea session + visit antes del
INSERT del contact. Los kwargs del helper se capturan via fixture
`session_visit_calls`. El payload del contact YA NO incluye
ip/country/user_agent (movidos a sessions/session_visits). El email al
owner se delega a send_email via invoke async (capturado con `mock_invoke`).
"""

import pytest

pytestmark = pytest.mark.unit

_TEST_SESSION = 'sess-test-01234567890123456789'


def test_contact_service_persists_and_sends_email(
    mock_neon_writes: list[dict],
    session_visit_calls: list[dict],
    mock_invoke: list[dict],
    contact_form_aws: None,
) -> None:
    from services import contact_service
    from services.contact_service import process_contact_form

    # Arrange
    contact_service.metrics.clear_metrics()

    # Act
    result = process_contact_form(
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

    # Assert: respuesta normalizada (UUID v7)
    assert len(result['contact_id']) == 36
    assert result['contact_id'][14] == '7'

    # Assert: el helper recibio los kwargs correctos (ip/country/ua van
    # a sessions, no al contact_payload)
    assert len(session_visit_calls) == 1
    helper_args = session_visit_calls[0]
    assert helper_args['session_id'] == _TEST_SESSION
    assert helper_args['ip'] == '1.2.3.4'
    assert helper_args['country'] == 'CL'
    assert helper_args['user_agent'] == 'Mozilla/5.0'
    # niche del visit (fallback origin si no hay del form).
    # form no envio niche -> origin_niche='fintech' es el fallback.
    assert helper_args['niche'] == 'fintech'
    assert helper_args['bump_event_count'] is True

    # Assert: una sola escritura a contacts con el payload esperado
    assert len(mock_neon_writes) == 1
    payload = mock_neon_writes[0]
    assert payload['id'] == result['contact_id']
    assert payload['name'] == 'Pablo'
    assert payload['email'] == 'p@example.com'
    assert payload['message'] == 'Hola mundo largo de prueba'
    assert payload['session_id'] == _TEST_SESSION
    # Spec sessions-normalize: ip/country/user_agent ya NO van en
    # contacts (movidos a sessions/session_visits).
    assert 'ip' not in payload
    assert 'country' not in payload
    assert 'user_agent' not in payload

    # Assert: se invoco send_email async con el payload kind=contact.
    assert len(mock_invoke) == 1
    invoke = mock_invoke[0]
    assert invoke['function_name'] == 'portfolio-send-email-test'
    sent = invoke['payload']
    assert sent['operation'] == 'email'
    assert sent['action'] == 'send'
    assert sent['data']['kind'] == 'contact'
    assert sent['data']['to'] == ['owner@example.com']
    assert sent['data']['reply_to'] == ['p@example.com']
    assert sent['data']['data']['name'] == 'Pablo'
    assert sent['data']['data']['email'] == 'p@example.com'
    assert sent['data']['data']['message'] == 'Hola mundo largo de prueba'

    # Assert: el email se invoco OK (no hay metrica de fallo)
    assert 'OwnerEmailFailed' not in dict(contact_service.metrics.metric_set)
