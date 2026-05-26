"""
Given un mensaje cuyo INSERT en tracking_events ya existe en Neon
     (ON CONFLICT DO NOTHING -> rowcount == 0),
When ProcessBatch.execute lo procesa,
Then el resultado es exitoso (is_valid=True, sin failures) y el
     mensaje NO aparece en `batchItemFailures` — la idempotencia es
     correcta, no un error.

AC-14: idempotencia bajo retries SQS.
"""

from __future__ import annotations

import pytest

from tests.unit._helpers import valid_body


@pytest.mark.unit
def test_process_batch_controller_idempotent_on_conflict(
    db_session_calls: list[int],
    session_visit_calls: list[dict],
    monkeypatch: pytest.MonkeyPatch,
    patch_parse_user_agent: None,
) -> None:
    # Arrange
    from controllers.worker.process_batch import ProcessBatch

    _ = db_session_calls, session_visit_calls, patch_parse_user_agent

    # Stub: insert_tracking_idempotent retorna False (no-op por
    # ON CONFLICT). El controller debe tratarlo como exito.
    insert_calls: list[dict] = []

    def _fake_insert_conflict(_session: object, payload: dict) -> bool:
        insert_calls.append(payload)
        return False

    monkeypatch.setattr(
        'services.persistence.insert_tracking_idempotent',
        _fake_insert_conflict,
    )

    records = [
        {
            'message_id': 'duplicate-msg-id',
            'body': valid_body(index=0),
        },
    ]

    # Act
    result = ProcessBatch(validated_data=records).execute()

    # Assert: el conflict NO es un fallo del mensaje.
    assert result == {
        'is_valid': True,
        'data': {'failures': [], 'processed': 1},
        'code': 0,
    }
    assert len(insert_calls) == 1
