"""Controller contact/create — procesa una submission del form de contacto.

Orquestador delgado: toma el payload validado (`ContactCreateModel`) y
ejecuta el flujo del form en el orden requerido:

  1. rate-limit per-IP (sliding window) — puede levantar 429 / 403.
  2. validacion Turnstile — puede levantar 403.
  3. delega al service (persistencia DynamoDB + email SES).
  4. contador de auto-blacklist (bot detection).

NO contiene logica de negocio del dominio (persistir / enviar email):
eso vive en `services/contact_service.py`. El controller orquesta.

Sobre el manejo de errores: el rate-limit y Turnstile levantan las
`ApplicationError` del backend (`RateLimitExceededError`,
`TurnstileError`, etc.). El controller las deja propagar — el handler
las captura y las traduce al `error_response` HTTP, conservando el
comportamiento observable IDENTICO al Lambda plano (mismos HTTP status
y `code`). Las fases del estandar (`preload`/`validate`) siguen
devolviendo `{is_valid, data, code}`; `execute()` solo devuelve el caso
de exito normalizado.
"""

from __future__ import annotations

from models.contact import ContactCreatedOutput, ContactCreateModel
from services.contact_service import process_contact_form
from settings.config import logger
from shared.http.turnstile import verify_turnstile_token
from shared.lambda_kit import BaseController
from shared.rate_limit import check_or_raise
from shared.rate_limit.auto_blacklist import (
    create_blacklist_rule,
    should_auto_blacklist,
)
from shared.rate_limit.buckets import increment_bucket

_ENDPOINT = '/contact'
_WINDOW_SECONDS = 60


class Create(BaseController):
    """Controller para la accion 'create' de la operacion 'contact'.

    El nombre de la clase es action.capitalize() ('create' -> 'Create').
    """

    event_model = ContactCreateModel

    def execute(self) -> dict:
        """Orquesta contact/create.

        Returns
        -------
        dict
            `{is_valid: True, data, code: 0}` en exito. Los fallos de
            rate-limit y Turnstile NO se normalizan aqui: propagan como
            `ApplicationError` para que el handler los traduzca al HTTP
            status exacto (429 / 403), igual que el Lambda plano.
        """
        data: ContactCreateModel = self.validated_data  # type: ignore[assignment]
        meta = data.meta

        # 1. Rate-limit per-IP (sliding window). Puede levantar 429/403.
        check_or_raise(
            ip=meta.ip,
            endpoint=_ENDPOINT,
            country=meta.country,
            turnstile_validated=False,
        )

        # 2. Verificacion Turnstile. Puede levantar 403 (CAPTCHA_*).
        verify_turnstile_token(
            data.cf_token,
            remote_ip=meta.ip,
            bypass_secret=meta.bypass_secret,
        )

        # 3. Delega al service: persiste en DynamoDB + envia email.
        result = process_contact_form(form_fields=data.form_fields())

        # 4. Contador de auto-blacklist: marca turnstile_validated=True
        #    DESPUES del exito. check_or_raise ya hizo un ADD con
        #    turnstile_validated=False; este segundo INCREMENT marca el
        #    token como valido para la deteccion de bots con solver.
        bucket = increment_bucket(
            ip=meta.ip,
            endpoint=_ENDPOINT,
            window_seconds=_WINDOW_SECONDS,
            turnstile_validated=True,
        )
        if should_auto_blacklist(bucket['turnstile_tokens']):
            create_blacklist_rule(meta.ip)
            logger.warning(
                'auto-blacklisted IP',
                extra={
                    'ip': meta.ip,
                    'turnstile_tokens': bucket['turnstile_tokens'],
                },
            )

        # 5. Normaliza la salida de exito a {is_valid, data, code}.
        output = ContactCreatedOutput(**result)
        return {
            'is_valid': True,
            'data': output.model_dump(),
            'code': 0,
        }
