"""Controller `worker/process` — procesa un mensaje SQS del contact_worker.

Orquesta el ciclo del mensaje: el `BaseController` valida `self.event`
contra `ContactQueueMessage` (Pydantic) en la fase `validate`, y este
`execute()` llama a la persistencia idempotente y al envio del email.

Es idempotente por diseño: si SQS re-entrega el mismo mensaje (mismo
`contact_id`), el INSERT a Neon es no-op (`ON CONFLICT (id) DO NOTHING`)
y el email NO se envia 2 veces (lo controla el helper de persistence
que retorna `persisted=False` cuando la fila ya existia).
"""

from typing import Any

from models.message import ContactQueueMessage
from services.persistence import (
    save_contact_idempotent,
    send_owner_email_safe,
)
from settings.config import logger
from shared.lambda_kit import BaseController


class Process(BaseController):
    """Action `process` de la operation `worker`. Procesa 1 mensaje SQS."""

    event_model = ContactQueueMessage

    def execute(self) -> dict[str, Any]:
        """Persiste el contact (idempotente) y, si fue nuevo, manda email.

        Returns
        -------
        dict
            `{is_valid: True, data, code: 0}` siempre que la persistencia
            no levante. Si SES falla, la excepcion PROPAGA al handler
            (que marca `batchItemFailures` con el messageId para que SQS
            reintente). NO se atrapa aqui.
        """
        data: ContactQueueMessage = self.validated_data  # type: ignore[assignment]

        # 1. Persistir contact (idempotente). Errores propagan -> handler
        # marca batchItemFailure -> SQS reintenta.
        result = save_contact_idempotent(data)

        if not result['persisted']:
            logger.info(
                'contact already persisted, skipping email',
                extra={
                    'contact_id': data.contact_id,
                    'session_id': data.session_id,
                },
            )
            return {
                'is_valid': True,
                'data': {
                    'contact_id': data.contact_id,
                    'skipped': True,
                },
                'code': 0,
            }

        # 2. Enviar email. Si SES falla, propaga -> batchItemFailure ->
        # reintento SQS. La persistencia es no-op en el reintento, por
        # eso es seguro re-encolar el mensaje entero.
        send_owner_email_safe(data, result)

        logger.info(
            'contact processed and email sent',
            extra={
                'contact_id': data.contact_id,
                'session_id': data.session_id,
            },
        )
        return {
            'is_valid': True,
            'data': {
                'contact_id': data.contact_id,
                'persisted': True,
            },
            'code': 0,
        }
