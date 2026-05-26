"""
Given un batch de 5 mensajes validos,
When ProcessBatch.execute corre,
Then `db_session()` se invoca exactamente UNA vez (no 5),
     y los 5 mensajes pasaron por `insert_tracking_idempotent`.

AC-12: una unica conexion Neon compartida entre los mensajes del
batch (cold-start amortizado).
"""

from __future__ import annotations

import pytest

from tests.unit._helpers import valid_body


@pytest.mark.unit
def test_process_batch_controller_shares_db_session(
    db_session_calls: list[int],
    session_visit_calls: list[dict],
    insert_tracking_calls: list[dict],
    patch_parse_user_agent: None,
) -> None:
    # Arrange
    from controllers.worker.process_batch import ProcessBatch

    _ = patch_parse_user_agent
    records = [
        {
            'message_id': f'msg-{i}',
            'body': valid_body(index=i),
        }
        for i in range(5)
    ]

    # Act
    result = ProcessBatch(validated_data=records).execute()

    # Assert: una sola db_session compartida
    assert len(db_session_calls) == 1

    # Cada mensaje persistio (helper + insert idempotente).
    assert len(session_visit_calls) == 5
    assert len(insert_tracking_calls) == 5

    # Resultado: sin fallos.
    assert result == {
        'is_valid': True,
        'data': {'failures': [], 'processed': 5},
        'code': 0,
    }
