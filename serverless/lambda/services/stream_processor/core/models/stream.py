"""Modelos Pydantic de la operacion `stream`.

Un modelo por action. El modelo valida el campo `data` del evento que el
handler sintetiza a partir del batch de DynamoDB Stream Records.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class StreamModel(BaseModel):
    """Valida el payload de stream/process.

    El `data` del evento sintetico trae los Records del DynamoDB Stream
    bajo la clave `records`. Cada Record de DynamoDB Stream tiene una
    estructura compleja y variable (`eventID`, `eventName`,
    `eventSourceARN`, `dynamodb.NewImage` type-tagged); el modelo es
    permisivo a proposito: solo garantiza que `records` sea una lista de
    objetos. La interpretacion fina de cada Record la hace el service
    (`detect_table`, `parse_*`).
    """

    records: list[dict[str, Any]] = Field(
        default_factory=list,
        description='Batch de Records del DynamoDB Stream.',
    )

    # `extra: allow` — el evento Stream puede traer claves auxiliares; no
    # se rechazan, simplemente se ignoran.
    model_config = {'extra': 'allow'}
