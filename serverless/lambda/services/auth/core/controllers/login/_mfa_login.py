"""Helper privado del login con MFA (plan 02 + plan 03 + multi-factor).

`issue_terminal_tokens` emite el par access+refresh terminal del login
(con un `family_id` NUEVO uuidv7, segun el lifecycle de JWT: cada login =
nueva familia). Lo comparten `login.start` (con password directo),
`login.verify-password` y `login.verify-totp`.

Plan 03: el access lleva el `family_id` de la sesion (para que el Lambda
`users` identifique la sesion en curso) y, si se pasa `app_config`, se
registra la sesion en `auth_user_sessions` via SessionTrackingService
(best-effort).

Multi-factor (plan admin-security-overview, bloque B): el login EXIGE
todos los metodos marcados `required`. Como `JwtClaims` tiene
`extra='forbid'` (solo `flow:str` + `step:int`), el progreso de factores
satisfechos se codifica en el `flow` del temp step=2:
`'login-mfa'` (sin satisfechos) o `'login-mfa:totp'` /
`'login-mfa:totp,webauthn'` (CSV de satisfechos). `decide_mfa_step`
compara los satisfechos contra `required_methods(user_id)` de la DB y
decide: emitir tokens (todos los requeridos cubiertos, o sin requeridos
y al menos un factor MFA hecho) o rotar el temp con el flow actualizado.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from services.mfa_method_service import MfaMethodService
from services.session_tracking_service import SessionTrackingService
from shared.core.ulid import new_uuidv7

_MFA_FLOW = 'login-mfa'


def parse_satisfied(flow: str | None) -> list[str]:
    """Extrae los metodos ya satisfechos del `flow` del temp step=2.

    `'login-mfa'` -> []; `'login-mfa:totp'` -> ['totp'];
    `'login-mfa:totp,webauthn'` -> ['totp','webauthn'].
    """
    if not flow or ':' not in flow:
        return []
    _, _, csv = flow.partition(':')
    return [m for m in csv.split(',') if m]


def build_mfa_flow(satisfied: list[str]) -> str:
    """Construye el `flow` del temp step=2 con los satisfechos (CSV ordenado)."""
    uniq = sorted(set(satisfied))
    return _MFA_FLOW if not uniq else f'{_MFA_FLOW}:{",".join(uniq)}'


def issue_terminal_tokens(
    *,
    jwt_svc: Any,
    user_id: UUID | str,
    app_config: Any = None,
    ip: str | None = None,
    country: str | None = None,
    user_agent: str | None = None,
) -> dict[str, Any]:
    """Emite access+refresh con family nuevo. Devuelve el dict de la response.

    Si `app_config` se pasa, ademas registra la sesion en
    `auth_user_sessions` (best-effort). El `family_id` se genera ANTES de
    emitir el access para embeberlo en sus claims (plan 03).
    """
    family_id = UUID(new_uuidv7())
    access_token, _ = jwt_svc.issue_access(
        user_id=user_id, family_id=family_id,
    )
    refresh_token, _ = jwt_svc.issue_refresh(
        user_id=user_id,
        family_id=family_id,
    )
    if app_config is not None:
        SessionTrackingService(app_config).on_session_created(
            user_id=user_id,
            family_id=family_id,
            ip=ip,
            country=country,
            user_agent=user_agent,
        )
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': 900,
    }


def decide_mfa_step(
    *,
    jwt_svc: Any,
    app_config: Any,
    user_id: UUID | str,
    satisfied: list[str],
    required: list[str] | None = None,
    ip: str | None = None,
    country: str | None = None,
    user_agent: str | None = None,
) -> dict[str, Any]:
    """Decide si emitir tokens o pedir mas factores (multi-factor required).

    Tras verificar UN factor MFA, el caller llama esto con la lista de
    metodos `satisfied` (incluido el recien verificado). Logica:

    - `required` = los metodos marcados `required` y activos. Si el caller
      no lo pasa, se resuelve con `MfaMethodService.required_methods` (los
      controllers que ya tienen un `mfa_svc` mockeable DEBEN pasarlo para
      no acoplar el test a la DB).
    - Si hay requeridos y `satisfied` NO los cubre todos: rota un temp
      step=2 nuevo con el `flow` actualizado y devuelve
      `{temp_token, methods: <faltantes>, step: 2}` (HTTP 200, sin tokens).
    - En cualquier otro caso (todos los requeridos cubiertos, o sin
      requeridos y ya hay >=1 factor satisfecho): emite access+refresh
      terminal.

    Devuelve un dict de response (`data`). El caller lo envuelve en
    `{is_valid, code, data}`.
    """
    if required is None:
        required = MfaMethodService(app_config).required_methods(
            user_id=user_id,
        )
    pending = [m for m in required if m not in satisfied]
    if pending:
        temp_token, _ = jwt_svc.issue_temp(
            user_id=user_id,
            flow=build_mfa_flow(satisfied),
            step=2,
        )
        return {
            'temp_token': temp_token,
            'methods': pending,
            'step': 2,
            'mfa_complete': False,
        }
    tokens = issue_terminal_tokens(
        jwt_svc=jwt_svc,
        user_id=user_id,
        app_config=app_config,
        ip=ip,
        country=country,
        user_agent=user_agent,
    )
    tokens['mfa_complete'] = True
    return tokens
