"""Controller `email/process` — procesa un mensaje SQS auth-email.

Orquesta el ciclo del mensaje: el `BaseController` valida `self.event`
contra `AuthEmailMessage` (Pydantic) en la fase `validate`, y este
`execute()`:

  1. Resuelve la plantilla por `kind` (template_service.render).
  2. Envia el email via SES (send_service.send).
  3. Inserta `auth_audit_log` event=`email.sent.<kind>` (audit_service).

Politicas de error:

- SES throttle (`ThrottlingException` / `TooManyRequestsException`):
  retorna `is_valid=False` → el handler marca el mensaje como
  batchItemFailure y SQS reintenta (hasta `max_receive_count=3` → DLQ).
- SES bounce permanente (`MessageRejected` de identidad no verificada,
  email invalido, etc.): loggea, registra `email.send.failed` y RETORNA
  `is_valid=True` para que SQS borre el mensaje (NO reintenta — reintentar
  no soluciona un dominio invalido).
- Cualquier otra excepcion: propaga → el handler la captura, marca
  batchItemFailure y SQS reintenta.
"""

from typing import Any

from models.message import AuthEmailMessage
from services.audit_service import log_email_audit
from services.send_service import SesSendError, SesThrottledError, send_auth_email
from services.template_service import TemplateNotFoundError, render_template
from settings.config import logger
from shared.lambda_kit import BaseController


class Process(BaseController):
    """Action `process` de la operation `email`. Procesa 1 mensaje SQS."""

    event_model = AuthEmailMessage

    def execute(self) -> dict[str, Any]:
        """Renderiza la plantilla, envia el email y audita el resultado.

        Returns
        -------
        dict
            `{is_valid: True, data, code: 0}` si el email se envio (o si
            fallo por motivo no-retryable y se audito el fallo). Si SES
            esta throttled, retorna `is_valid=False` para forzar el
            reintento via SQS.
        """
        data: AuthEmailMessage = self.validated_data  # type: ignore[assignment]
        user_id_str = str(data.user_id)

        # 1. Render del template (subject + text + html).
        try:
            subject, text_body, html_body = render_template(
                kind=data.kind,
                data=data.data,
                niche=data.niche,
            )
        except TemplateNotFoundError as exc:
            logger.error(
                'template not found',
                extra={
                    'kind': data.kind,
                    'error': str(exc),
                    'user_id': user_id_str,
                },
            )
            # Configuracion rota: no tiene sentido reintentar.
            log_email_audit(
                event=f'email.send.failed.{data.kind}',
                success=False,
                user_id=user_id_str,
                error_code='TEMPLATE_NOT_FOUND',
                niche=data.niche,
                meta={'subject_id': data.subject_id},
            )
            return {
                'is_valid': True,
                'data': {'sent': False, 'reason': 'template_not_found'},
                'code': 0,
            }

        # 2. Envio via SES.
        try:
            message_id = send_auth_email(
                to=data.to,
                subject=subject,
                text_body=text_body,
                html_body=html_body,
            )
        except SesThrottledError as exc:
            # Retryable: SQS reintenta el mensaje completo.
            logger.warning(
                'SES throttled, reintentando via SQS',
                extra={
                    'kind': data.kind,
                    'user_id': user_id_str,
                    'error': str(exc),
                },
            )
            return {
                'is_valid': False,
                'data': {'sent': False, 'reason': 'ses_throttled'},
                'code': 5002,
            }
        except SesSendError as exc:
            # No-retryable (bounce permanente, MessageRejected, etc.):
            # auditar y RETORNAR ok para que SQS borre el mensaje.
            logger.error(
                'SES send failed permanently',
                extra={
                    'kind': data.kind,
                    'user_id': user_id_str,
                    'error': str(exc),
                },
            )
            log_email_audit(
                event=f'email.send.failed.{data.kind}',
                success=False,
                user_id=user_id_str,
                error_code='SES_SEND_FAILED',
                niche=data.niche,
                meta={'subject_id': data.subject_id, 'reason': str(exc)},
            )
            return {
                'is_valid': True,
                'data': {'sent': False, 'reason': 'ses_send_failed'},
                'code': 0,
            }

        # 3. Audit log de exito. Si el insert falla, propaga -> SQS
        # reintenta. Riesgo asumido: el email puede irse 2 veces, pero
        # NO podemos perder la auditoria silenciosamente.
        log_email_audit(
            event=f'email.sent.{data.kind}',
            success=True,
            user_id=user_id_str,
            niche=data.niche,
            meta={
                'subject_id': data.subject_id,
                'message_id': message_id,
            },
        )

        logger.info(
            'auth email sent',
            extra={
                'kind': data.kind,
                'user_id': user_id_str,
                'message_id': message_id,
            },
        )
        return {
            'is_valid': True,
            'data': {
                'sent': True,
                'kind': data.kind,
                'message_id': message_id,
            },
            'code': 0,
        }
