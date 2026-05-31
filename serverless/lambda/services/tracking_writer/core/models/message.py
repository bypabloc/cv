"""@module message — schema del `data` del invoke async del tracking_writer.

`TrackingWriteModel` valida el `data` que el encoder `tracking_pixel`
arma en `invoke_tracking_writer` y envia por `InvocationType='Event'`
(sin SQS) en el contrato estandar `{operation:'tracking', action:'write',
data:{...}}`. El encoder pre-genera los IDs fisicos (`page_id` UUIDv7,
`created_at`) ANTES de invocar, de modo que el writer sea estrictamente
idempotente: si AWS reintenta el invoke async, el INSERT con
`ON CONFLICT DO NOTHING` sobre la PK compuesta `(created_at, visit_id,
page_id)` es no-op.

`extra='forbid'` rechaza payloads con campos no declarados: si el
encoder agrega un campo nuevo sin coordinar version, el writer falla
ruidoso (preferible a silenciar el cambio).

`schema_version` permite evolucion: cuando el contrato cambie de
manera incompatible, el encoder invoca con `schema_version=2`, este
modulo agrega otra clase y el handler enruta segun el valor.
"""

from datetime import datetime
from typing import Any, Literal

from shared.core.pydantic_types import BaseModel, ConfigDict


class TrackingWriteModel(BaseModel):
    """`data` del invoke async que arma el encoder `tracking_pixel`.

    Una instancia = un evento de tracking a persistir en Neon. El writer
    procesa UN evento por invocacion (a diferencia del worker SQS que
    reemplaza, que procesaba hasta 10 por batch).
    """

    model_config = ConfigDict(extra='forbid')

    # Contrato del mensaje. Literal[1] => Pydantic rechaza otros valores.
    schema_version: Literal[1] = 1

    # IDs pre-generados por el encoder (idempotencia).
    page_id: str
    created_at: datetime

    # Campos validados del evento.
    session_id: str
    event_id: str
    event_type_id: str
    page_url: str | None = None
    page_title: str | None = None
    page_path: str
    niche: str | None = None
    viewport_width: int
    viewport_height: int
    device_pixel_ratio: float | None = None
    event_props: dict[str, Any] | None = None

    # UTM + referrer (alimentan ensure_session_and_visit).
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    utm_content: str | None = None
    utm_term: str | None = None
    referrer: str | None = None

    # Metadata del request HTTP que el encoder extrajo de los headers.
    ip: str
    country: str | None = None
    user_agent: str | None = None
