"""Controller `login.check-email` — existencia + has_password + metodos.

Paso 0 del login (unico endpoint con Turnstile). Dado un email (con
Turnstile + rate-limit), reporta si existe, si tiene password, y para un user
`active` la LISTA de factores `required` con su config de render
(`methods_required`), para que el front monte el checklist de metodos a
completar en cualquier orden (plan login-mfa-list-redesign).

Trade-off anti-enumeration ACEPTADO por el dueno del producto: la lista de
factores se revela ANTES de autenticar (reconnaissance de "que exige cada
cuenta"). La existencia del email + has_password ya eran enumerables; la
lista de required agrega ese dato deliberadamente. Los estados disabled/
locked/deleted se reportan como `unavailable` (existe, sin metodos ni temp)
sin revelar el estado real.

AC cubiertos: AC-1..AC-4.
"""

from __future__ import annotations

from typing import Any

from models.login import LoginCheckEmailIn
from services.audit_service import AuditService
from services.jwt_service import JwtService
from services.mfa_method_service import MfaMethodService
from services.password_service import PasswordService
from services.rate_limit_service import RateLimitService
from services.user_service import UserService
from settings.config import app_config
from shared.core.ulid import new_uuidv7
from shared.crypto.captcha import verify_captcha_or_bypass
from shared.db.models.auth.enums import AuthUserStatus
from shared.lambda_kit.base_controller import BaseController

_ENDPOINT = '/auth#login.check-email'
# El temp JWT precheck (paso 0 del login) autoriza `login.start`: este
# es el UNICO punto del flujo de login con Turnstile (decision D-1/D-2).
_PRECHECK_FLOW = 'login'
_PRECHECK_STEP = 0


class CheckEmail(BaseController):
    """Reporta existencia + has_password de un email (action `check-email`)."""

    event_model = LoginCheckEmailIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit per-IP estricto + Turnstile (AC-C5/C7)."""
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: LoginCheckEmailIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta
        RateLimitService(app_config).check_or_raise(
            ip=meta.ip or '',
            endpoint=_ENDPOINT,
            country=meta.country,
            turnstile_validated=False,
            brought_turnstile_token=bool(data.cf_turnstile_response),
        )
        verify_captcha_or_bypass(
            data.cf_turnstile_response,
            remote_ip=meta.ip,
            bypass_token=meta.bypass_token,
        )
        return base

    def execute(self) -> dict[str, Any]:
        """Reporta existencia + has_password + methods_required (si active).

        Tras validar Turnstile (en `validate`), emite un temp JWT precheck
        (`flow='login'` step=0) en los casos que pueden continuar a
        `login.start` (active, pending, o email nuevo para el alta). Para un
        email unavailable NO se emite temp (no hay flujo que continuar).

        Returns:
            200 `{exists:false, temp_token}` si el email no existe (alta;
            AC-3).
            200 `{exists:true, pending:true, has_password:false, temp_token}`
            si pending (sin methods_required: aun no hay MFA; AC-3).
            200 `{exists:true, unavailable:true}` si disabled/locked/deleted
            (AC-4, sin temp_token ni methods_required).
            200 `{exists:true, has_password, temp_token, methods_required}`
            si active (AC-1/AC-2).
        """
        data: LoginCheckEmailIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta
        email = data.email.lower()

        user_svc = UserService(app_config)
        audit_svc = AuditService(app_config)

        audit_svc.log(
            event='login.check-email',
            success=True,
            ip=meta.ip,
            user_agent=meta.user_agent,
        )

        user = user_svc.get_by_email(email)
        if user is None:
            # Email nuevo: emite el precheck igual (la fusion register->login
            # permite que login.start CREE el pending). El temp lleva un sub
            # placeholder (aun no hay user); login.start no compara el sub
            # cuando el email no existe (solo cuando ya existe, anti-cross-
            # account). El abuso queda acotado: crear un pending ya costo un
            # Turnstile, igual que register.start (decision usuario).
            return {
                'is_valid': True,
                'code': 0,
                'data': {
                    'exists': False,
                    'temp_token': self._issue_precheck(user_id=new_uuidv7()),
                },
            }

        if user.status == AuthUserStatus.PENDING:
            return {
                'is_valid': True,
                'code': 0,
                'data': {
                    'exists': True,
                    'pending': True,
                    'has_password': False,
                    'temp_token': self._issue_precheck(user_id=user.id),
                },
            }

        if user.status in (
            AuthUserStatus.DISABLED,
            AuthUserStatus.LOCKED,
            AuthUserStatus.DELETED,
        ):
            return {
                'is_valid': True,
                'code': 0,
                'data': {'exists': True, 'unavailable': True},
            }

        # active: expone has_password + la lista de metodos REQUIRED (con su
        # config de render) + el temp precheck que autoriza login.start.
        #
        # Trade-off anti-enumeration ACEPTADO por el dueno del producto (plan
        # login-mfa-list-redesign): revelar que factores exige cada cuenta
        # ANTES de autenticar. El front necesita la lista para montar el
        # checklist de metodos a completar en cualquier orden. La existencia
        # del email + has_password ya eran enumerables; la lista de required
        # agrega ese dato deliberadamente.
        status = PasswordService(app_config).status(user_id=user.id)
        methods_required = MfaMethodService(app_config).required_methods_config(
            user_id=user.id,
        )
        return {
            'is_valid': True,
            'code': 0,
            'data': {
                'exists': True,
                'has_password': bool(status['has_password']),
                'temp_token': self._issue_precheck(user_id=user.id),
                'methods_required': methods_required,
            },
        }

    def _issue_precheck(self, *, user_id: Any) -> str:
        """Emite el temp JWT precheck (`flow='login'` step=0) para el user.

        Solo se llama tras pasar Turnstile (en `validate`). `login.start`
        lo verifica (flow + sub) y lo blacklistea rolling.
        """
        token, _ = JwtService(app_config).issue_temp(
            user_id=user_id,
            flow=_PRECHECK_FLOW,
            step=_PRECHECK_STEP,
        )
        return token
