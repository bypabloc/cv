"""Tests de contact_form.service (orquestacion persist + email + metrica)."""

from __future__ import annotations

import pytest

from contact_form import service
from contact_form.service import process_contact_form

pytestmark = pytest.mark.unit


@pytest.fixture
def _no_turnstile(monkeypatch: pytest.MonkeyPatch) -> None:
    """Neutraliza la verificacion de Turnstile (no es lo que se testea aqui)."""
    monkeypatch.setattr(
        service, 'verify_turnstile_token', lambda *a, **kw: None
    )


class TestProcessContactFormEmailMetric:
    """process_contact_form - metrica OwnerEmailFailed (no-bloqueante)."""

    def test_when_email_fails_then_persists_and_emits_metric(
        self,
        monkeypatch: pytest.MonkeyPatch,
        _no_turnstile: None,
    ) -> None:
        """
        Given send_owner_email lanza una excepcion [AC-4],
        When se procesa el contacto,
        Then el contacto queda persistido, se emite OwnerEmailFailed=1
        y no se re-raise (process_contact_form retorna el resultado normal).
        """
        saved = {'contact_id': 'c-123', 'created_at': '2026-05-17T00:00:00Z'}
        monkeypatch.setattr(service, 'save_contact', lambda _payload: saved)

        def _raise(_contact: dict) -> str:
            msg = 'SES boom'
            raise RuntimeError(msg)

        monkeypatch.setattr(service, 'send_owner_email', _raise)
        service.metrics.clear_metrics()

        result = process_contact_form(
            validated_input={
                'name': 'Pablo',
                'email': 'p@example.com',
                'message': 'Hola mundo largo',
            },
            cf_response='token',
            ip='1.2.3.4',
        )

        captured = dict(service.metrics.metric_set)

        assert result == saved
        assert 'OwnerEmailFailed' in captured
        assert captured['OwnerEmailFailed']['Value'] == [1.0]

    def test_when_email_succeeds_then_no_metric(
        self,
        monkeypatch: pytest.MonkeyPatch,
        _no_turnstile: None,
    ) -> None:
        """
        Given send_owner_email tiene exito [AC-5],
        When se procesa el contacto,
        Then NO se emite la metrica OwnerEmailFailed.
        """
        saved = {'contact_id': 'c-456', 'created_at': '2026-05-17T00:00:00Z'}
        monkeypatch.setattr(service, 'save_contact', lambda _payload: saved)
        monkeypatch.setattr(
            service, 'send_owner_email', lambda _contact: 'msg-id'
        )
        service.metrics.clear_metrics()

        result = process_contact_form(
            validated_input={
                'name': 'Pablo',
                'email': 'p@example.com',
                'message': 'Hola mundo largo',
            },
            cf_response='token',
            ip='1.2.3.4',
        )

        captured = dict(service.metrics.metric_set)

        assert result == saved
        assert 'OwnerEmailFailed' not in captured


class TestProcessContactFormPayload:
    """process_contact_form - shape del payload que llega a save_contact."""

    def test_when_processed_then_payload_omits_origin_metadata(
        self,
        monkeypatch: pytest.MonkeyPatch,
        _no_turnstile: None,
    ) -> None:
        """
        Given un contacto con ip/country/user_agent en la request [AC-3],
        When process_contact_form arma el payload,
        Then save_contact NO recibe ip/country/user_agent: contacts deja
        de duplicar datos de origen.
        """
        captured_payload: dict = {}

        def _capture(payload: dict) -> dict:
            captured_payload.update(payload)
            return {'contact_id': 'c-1', 'created_at': '2026-05-17T00:00:00Z'}

        monkeypatch.setattr(service, 'save_contact', _capture)
        monkeypatch.setattr(
            service, 'send_owner_email', lambda _contact: 'msg-id'
        )
        service.metrics.clear_metrics()

        process_contact_form(
            validated_input={
                'name': 'Pablo',
                'email': 'p@example.com',
                'message': 'Hola mundo largo',
            },
            cf_response='token',
            ip='203.0.113.9',
            country='CL',
            user_agent='Mozilla/5.0',
        )

        assert 'ip' not in captured_payload
        assert 'country' not in captured_payload
        assert 'user_agent' not in captured_payload

    def test_when_session_id_present_then_payload_keeps_it(
        self,
        monkeypatch: pytest.MonkeyPatch,
        _no_turnstile: None,
    ) -> None:
        """
        Given validated_input con session_id [AC-3],
        When process_contact_form arma el payload,
        Then save_contact recibe session_id con ese valor (clave de
        correlacion con tracking_events).
        """
        captured_payload: dict = {}

        def _capture(payload: dict) -> dict:
            captured_payload.update(payload)
            return {'contact_id': 'c-2', 'created_at': '2026-05-17T00:00:00Z'}

        monkeypatch.setattr(service, 'save_contact', _capture)
        monkeypatch.setattr(
            service, 'send_owner_email', lambda _contact: 'msg-id'
        )
        service.metrics.clear_metrics()

        session_id = 'a' * 32
        process_contact_form(
            validated_input={
                'name': 'Pablo',
                'email': 'p@example.com',
                'message': 'Hola mundo largo',
                'session_id': session_id,
            },
            cf_response='token',
            ip='203.0.113.9',
        )

        assert captured_payload['session_id'] == session_id
