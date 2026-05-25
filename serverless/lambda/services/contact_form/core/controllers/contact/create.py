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
from shared.core.niches import niche_from_origin
from shared.core.ulid import new_uuidv7
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


def _resolve_session_id(form_session_id: str | None) -> str:
    """Resuelve el session_id del visitante.

    Spec sessions-normalize, decision 2: si el form envia `session_id`
    (porque el TrackingPixel cargo correctamente), se usa. Sino se
    genera uno on-the-fly: el form se acepta igual y crea una session
    nueva con los datos del request. Caso edge: adblock, JS bloqueado,
    primer click directo al form.

    Formato: UUIDv7 server-side (mismo formato que el cliente genera
    en localStorage, asi sessions con tracking previo no chocan).
    """
    if form_session_id:
        return form_session_id
    return f'cf-{new_uuidv7()}'


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

        # 3. Resolver session_id + niche fallback del Origin (decision 6).
        form_fields = data.form_fields()
        session_id = _resolve_session_id(form_fields.get('session_id'))
        origin_niche = niche_from_origin(meta.origin)

        # Asegurar que form_fields tiene el session_id resuelto (NO el
        # None original — el service espera que session_id este).
        form_fields_with_session = {**form_fields, 'session_id': session_id}

        # 4. Delega al service: UPSERT session + visit + INSERT contact +
        #    envia email.
        result = process_contact_form(
            form_fields=form_fields_with_session,
            session_id=session_id,
            ip=meta.ip,
            country=meta.country,
            user_agent=meta.user_agent,
            origin_niche=origin_niche,
        )

        # 5. Contador de auto-blacklist: marca turnstile_validated=True
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

        # 6. Normaliza la salida de exito a {is_valid, data, code}.
        output = ContactCreatedOutput(**result)
        return {
            'is_valid': True,
            'data': output.model_dump(),
            'code': 0,
        }
