"""Controller contact/create — escritura inline a Neon + invoke send_email.

Orquestador del flujo del form de contacto. Ejecuta SIEMPRE las
verificaciones de gating ANTES de persistir:

  1. rate-limit per-IP (puede levantar 429 / 403).
  2. validacion Turnstile  (puede levantar 403).

Luego persiste el contacto INLINE a Neon (sessions + visit + contact en
una tx) y notifica al owner invocando `send_email` async (best-effort).
Responde HTTP 201. Sin SQS, sin ASYNC_MODE (refactor cold-start).

Despues del exito incrementa el contador de auto-blacklist (bot
detection): 3+ tokens Turnstile validos en 60s desde la misma IP ->
blacklist 24h.

NO contiene logica de negocio: delega en
`services.contact_service.process_contact_form`.

Sobre errores: rate-limit + Turnstile levantan `ApplicationError` que el
handler traduce al HTTP correcto (429 / 403).
"""

from __future__ import annotations

from typing import Any

from models.contact import ContactCreatedOutput, ContactCreateModel
from services.contact_service import process_contact_form
from settings.config import logger
from shared.core.niches import niche_from_origin
from shared.core.ulid import new_uuidv7
from shared.crypto.captcha import verify_captcha_or_bypass
from shared.lambda_kit.base_controller import BaseController
from shared.rate_limit.auto_blacklist import (
    create_blacklist_rule,
    should_auto_blacklist,
)
from shared.rate_limit.buckets import increment_bucket
from shared.rate_limit.check import check_or_raise

_ENDPOINT = '/contact'
_WINDOW_SECONDS = 60


def _resolve_session_id(form_session_id: str | None) -> str:
    """Resuelve el session_id del visitante.

    Si el form envia `session_id` (TrackingPixel cargo bien), se usa. Sino
    se genera uno on-the-fly: el form se acepta igual y crea una session
    nueva con los datos del request (caso edge: adblock, JS bloqueado,
    primer click directo al form). Formato UUIDv7 server-side.
    """
    if form_session_id:
        return form_session_id
    return f'cf-{new_uuidv7()}'


def _auto_blacklist_step(ip: str) -> None:
    """Incrementa el contador de tokens validos + auto-blacklist si excede.

    Corre DESPUES del exito: marca `turnstile_validated=True` para detectar
    bots con solver (3+ tokens validos en 60s desde la misma IP -> blacklist
    24h).
    """
    bucket = increment_bucket(
        ip=ip,
        endpoint=_ENDPOINT,
        window_seconds=_WINDOW_SECONDS,
        turnstile_validated=True,
    )
    if should_auto_blacklist(bucket['turnstile_tokens']):
        create_blacklist_rule(ip)
        logger.warning(
            'auto-blacklisted IP',
            extra={
                'ip': ip,
                'turnstile_tokens': bucket['turnstile_tokens'],
            },
        )


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
            `{is_valid: True, data, code: 0}` en exito (HTTP 201). Los
            fallos de rate-limit / Turnstile NO se normalizan aqui:
            propagan como `ApplicationError` para que el handler los
            traduzca al HTTP exacto (429 / 403).
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

        # 2. Verificacion Turnstile (o bypass firmado en dev/stage). Puede
        #    levantar 403 (CAPTCHA_*).
        verify_captcha_or_bypass(
            data.cf_token,
            remote_ip=meta.ip,
            bypass_token=meta.bypass_token,
        )

        # 3. Resolver session_id + niche fallback del Origin.
        form_fields = data.form_fields()
        session_id = _resolve_session_id(form_fields.get('session_id'))
        origin_niche = niche_from_origin(meta.origin)
        form_fields_with_session = {**form_fields, 'session_id': session_id}

        # 4. Persistir INLINE a Neon + notificar owner (invoke send_email).
        result = self._persist(
            form_fields=form_fields_with_session,
            session_id=session_id,
            meta=meta,
            origin_niche=origin_niche,
        )

        # 5. Contador de auto-blacklist (despues del exito). check_or_raise
        #    ya hizo un ADD con turnstile_validated=False; este INCREMENT
        #    marca el token como valido para la deteccion de bots.
        _auto_blacklist_step(meta.ip)

        return result

    def _persist(
        self,
        *,
        form_fields: dict[str, Any],
        session_id: str,
        meta: Any,
        origin_niche: str | None,
    ) -> dict:
        """Persiste el contacto a Neon (inline) + invoke send_email async."""
        result = process_contact_form(
            form_fields=form_fields,
            session_id=session_id,
            ip=meta.ip,
            country=meta.country,
            user_agent=meta.user_agent,
            origin_niche=origin_niche,
        )
        output = ContactCreatedOutput(**result)
        return {
            'is_valid': True,
            'data': output.model_dump(),
            'code': 0,
        }
