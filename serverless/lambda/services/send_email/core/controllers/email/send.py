"""Controller email/send — renderiza y envia un email.

Orquesta: valida el payload (EmailSendRequest) -> llama email_service.send
-> normaliza a {is_valid, data, code}.
"""

from __future__ import annotations

from models.email import EmailSendRequest
from services import email_service
from services.email_service import EmailServiceError
from shared.lambda_kit.base_controller import BaseController


class Send(BaseController):
    """Renderiza el template del `kind` y lo envia por SES."""

    event_model = EmailSendRequest

    def execute(self) -> dict:
        """Envia el email y devuelve el MessageId."""
        data: EmailSendRequest = self.validated_data  # type: ignore[assignment]
        try:
            message_id = email_service.send(
                kind=data.kind,
                to=data.to,
                data=data.data,
                reply_to=data.reply_to,
            )
        except EmailServiceError as exc:
            return {
                'is_valid': False,
                'data': {
                    'error_code': exc.error_code,
                    'message': exc.message,
                },
                'code': exc.code,
            }

        return {
            'is_valid': True,
            'data': {'message_id': message_id, 'kind': data.kind},
            'code': 0,
        }
