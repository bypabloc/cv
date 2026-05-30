"""Controller contact/create — encoder + sync legacy detras de ASYNC_MODE.

Orquestador del flujo del form de contacto. Ejecuta SIEMPRE las
verificaciones de gating ANTES de branchear:

  1. rate-limit per-IP (puede levantar 429 / 403).
  2. validacion Turnstile  (puede levantar 403).

Despues, decide segun `AppConfig.async_mode`:

  - `True`  (encoder, default): pre-genera contact_id + created_at,
    publica el mensaje a SQS via `enqueue_contact_message` y devuelve
    HTTP 202.
  - `False` (sync legacy, rollback): delega al service viejo que
    persiste en Neon + envia el email via SES, devuelve HTTP 201.

En AMBOS modos, despues del branch, se incrementa el contador de
auto-blacklist (bot detection). Asi el comportamiento de defensa
contra bots es identico independientemente del modo.

NO contiene logica de negocio: el encoder delega a
`services.contact_service.enqueue_contact_message`; el sync legacy
delega a `services.contact_service.process_contact_form`.

Sobre el manejo de errores: rate-limit + Turnstile levantan
`ApplicationError` que el handler traduce al HTTP correcto (429 / 403).
Si `enqueue_contact_message` falla, propaga `QueuePublishError`: NO se
hace fallback automatico a sync (decision explicita, ver spec) — el
handler la traduce a 5xx.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from models.contact import (
    ContactAcceptedOutput,
    ContactCreatedOutput,
    ContactCreateModel,
)
from services.contact_service import (
    enqueue_contact_message,
    process_contact_form,
)
from settings.config import AppConfig, logger
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


def _auto_blacklist_step(ip: str) -> None:
    """Incrementa el contador de tokens validos + auto-blacklist si excede.

    Corre en AMBOS modos (async + sync) DESPUES del exito del branch:
    marca `turnstile_validated=True` para detectar bots con solver
    (3+ tokens validos en 60s desde la misma IP -> blacklist 24h).
    Spec: auto-blacklist runs independientemente del modo.
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
            `{is_valid: True, data, code: 0}` en exito. Los fallos de
            rate-limit, Turnstile o publicacion SQS NO se normalizan
            aqui: propagan como `ApplicationError`/`QueuePublishError`
            para que el handler los traduzca al HTTP exacto (429 / 403
            / 5xx).
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

        # 3. Resolver session_id + niche fallback del Origin (decision 6).
        form_fields = data.form_fields()
        session_id = _resolve_session_id(form_fields.get('session_id'))
        origin_niche = niche_from_origin(meta.origin)

        # Asegurar que form_fields tiene el session_id resuelto (NO el
        # None original — el service espera que session_id este).
        form_fields_with_session = {**form_fields, 'session_id': session_id}

        # 4. Branch por feature flag ASYNC_MODE.
        if AppConfig.async_mode:
            result = self._execute_async(
                form_fields=form_fields_with_session,
                session_id=session_id,
                meta=meta,
                origin_niche=origin_niche,
            )
        else:
            result = self._execute_sync(
                form_fields=form_fields_with_session,
                session_id=session_id,
                meta=meta,
                origin_niche=origin_niche,
            )

        # 5. Contador de auto-blacklist (en AMBOS modos, despues del exito).
        #    check_or_raise ya hizo un ADD con turnstile_validated=False;
        #    este segundo INCREMENT marca el token como valido para la
        #    deteccion de bots con solver.
        _auto_blacklist_step(meta.ip)

        return result

    def _execute_async(
        self,
        *,
        form_fields: dict[str, Any],
        session_id: str,
        meta: Any,
        origin_niche: str | None,
    ) -> dict:
        """Modo encoder (ASYNC_MODE=true): publica a SQS y devuelve 202.

        Pre-genera contact_id (UUIDv7) y created_at antes de encolar.
        El worker los usa tal cual: si SQS re-entrega el mensaje, el
        worker hace ON CONFLICT DO NOTHING — idempotencia garantizada.

        Nunca toca Neon ni SES en este modo.
        """
        contact_id = new_uuidv7()
        created_at = datetime.now(UTC)

        enqueue_contact_message(
            contact_id=contact_id,
            created_at=created_at,
            form_fields=form_fields,
            session_id=session_id,
            ip=meta.ip,
            country=meta.country,
            user_agent=meta.user_agent,
            origin_niche=origin_niche,
        )

        output = ContactAcceptedOutput(
            contact_id=contact_id,
            created_at=created_at,
            accepted=True,
        )
        return {
            'is_valid': True,
            'data': output.model_dump(mode='json'),
            'code': 0,
        }

    def _execute_sync(
        self,
        *,
        form_fields: dict[str, Any],
        session_id: str,
        meta: Any,
        origin_niche: str | None,
    ) -> dict:
        """Modo legacy (ASYNC_MODE=false): persiste + email sincronamente.

        Path de rollback: mantiene el comportamiento del Lambda viejo
        para que un flipeo del flag a 'false' restaure el flujo
        original sin redeploy del worker.
        """
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
