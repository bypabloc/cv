"""Controller `login.start` — inicia el flujo de login (modelo de lista).

El visitante existente pide login: el controller EXIGE el temp JWT precheck
(`flow='login'` step=0, emitido por `login.check-email` tras validar
Turnstile), resuelve el user por el `sub` del precheck (NO por el email del
body), lo blacklistea (rolling), y abre el checklist de factores.

Plan login-mfa-list-redesign:
- `login.start` ya NO recibe ni valida la password (es un metodo mas de la
  lista, se verifica con `login.verify-password`).
- `login.start` ya NO recibe el email para un user existente (se resuelve por
  el `sub`). El email solo va en el body en el UNICO caso de ALTA (email
  nuevo, sub placeholder que no resuelve user).
- Para un user `active`: emite un temp `login-mfa` step=2 con
  `methods = required_methods()` (los factores a completar) y `satisfied=[]`.
  El front los completa en cualquier orden; cada `verify-*` delega en
  `decide_mfa_step`, que emite access+refresh cuando no quedan pendientes.
- Para alta (email nuevo) / pending: flujo passwordless de entrada (envia el
  email unificado con code + magic-link), temp `flow='login'` step=1.

`login.start` NO valida Turnstile: el captcha se resuelve UNA sola vez en
`login.check-email`. Sin un temp precheck valido -> 401 MISSING_PRECHECK.

AC cubiertos: AC-9, AC-10, AC-16.
"""

from __future__ import annotations

from typing import Any

from models.login import LoginStartIn
from services.audit_service import AuditService
from services.code_service import CodeService
from services.email_dispatch_service import EmailDispatchService
from services.jwt_service import JwtService
from services.magic_link_service import LINK_TTL_MINUTES, MagicLinkService
from services.mfa_method_service import MfaMethodService
from services.rate_limit_service import RateLimitService
from services.user_service import UserService
from settings.config import app_config
from shared.auth.jwt import JwtError
from shared.db.models.auth.enums import (
    AuthCodeKind,
    AuthLinkKind,
    AuthUserStatus,
)
from shared.lambda_kit.base_controller import BaseController

from ._mfa_login import build_mfa_flow

_ENDPOINT = '/auth#login.start'
_TEMP_TTL_SECONDS = 300
# El temp JWT step=2 del checklist lleva este flow (CSV de satisfechos).
_MFA_FLOW = 'login-mfa'
# El precheck (flow='login' step=0) lo emite login.check-email tras Turnstile.
_PRECHECK_FLOW = 'login'


class Start(BaseController):
    """Inicia el flujo de login (action `start`)."""

    event_model = LoginStartIn

    def validate(self) -> dict[str, Any]:
        """Pydantic + rate-limit per-IP. SIN Turnstile.

        El captcha se resuelve en `login.check-email`; aqui la autorizacion
        es el temp JWT precheck (verificado en `execute`).
        """
        base = super().validate()
        if not base.get('is_valid'):
            return base

        data: LoginStartIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta

        RateLimitService(app_config).check_or_raise(
            ip=meta.ip or '',
            endpoint=_ENDPOINT,
            country=meta.country,
            turnstile_validated=True,
        )
        return base

    @staticmethod
    def _extract_bearer(authorization: str | None) -> str | None:
        """Extrae el JWT de un header `Authorization: Bearer <token>`."""
        if not authorization:
            return None
        parts = authorization.split(' ', 1)
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None
        token = parts[1].strip()
        return token or None

    def _verify_precheck(
        self, *, jwt_svc: Any, meta: Any,
    ) -> Any | None:
        """Verifica el temp precheck del header `Authorization`.

        Returns:
            Los claims del temp (`flow='login'`) si es valido, o None si
            falta / no verifica / no es del flow correcto.
        """
        token = self._extract_bearer(meta.authorization)
        if token is None:
            return None
        try:
            return jwt_svc.verify(
                token,
                expected_typ='temp',
                expected_flow=_PRECHECK_FLOW,
            )
        except JwtError:
            return None

    @staticmethod
    def _missing_precheck(*, audit_svc: Any, meta: Any) -> dict[str, Any]:
        """Respuesta 401 MISSING_PRECHECK (sin precheck valido)."""
        audit_svc.log(
            event='login.start',
            success=False,
            error_code='MISSING_PRECHECK',
            ip=meta.ip,
        )
        return {
            'is_valid': False,
            'code': 4003,
            'status': 401,
            'data': {'error': 'MISSING_PRECHECK'},
        }

    def execute(self) -> dict[str, Any]:
        """Resuelve el user por el `sub` del precheck y abre el checklist.

        Returns:
            Exito (user active): 200 `{temp_token(step=2), methods, step:2}`
            (AC-9).
            Alta (email nuevo): 200 `{temp_token(step=1), methods:[...],
            created:true}` (AC-10).
            Email disabled/locked: 404 EMAIL_NOT_FOUND, suggest_register
            =False (anti-enumeration).
        """
        data: LoginStartIn = self.validated_data  # type: ignore[assignment]
        meta = data.meta
        niche = data.niche

        user_svc = UserService(app_config)
        jwt_svc = JwtService(app_config)
        audit_svc = AuditService(app_config)

        # Precheck obligatorio: el temp JWT flow='login' step=0 emitido por
        # login.check-email (tras Turnstile). Sin el -> 401 MISSING_PRECHECK.
        claims = self._verify_precheck(jwt_svc=jwt_svc, meta=meta)
        if claims is None:
            return self._missing_precheck(audit_svc=audit_svc, meta=meta)

        # Resuelve el user por el sub del precheck (NO por el email del body).
        existing = user_svc.get_by_id(str(claims.sub))

        # El precheck es single-use: lo blacklistea (rolling).
        jwt_svc.blacklist(
            jti=claims.jti,
            exp=claims.exp,
            user_id=existing.id if existing is not None else claims.sub,
            reason='rotation',
        )

        # Alta (fusion register -> login): el sub del precheck es un
        # placeholder que no resuelve user. Se exige el email en el body para
        # crear el pending (el unico caso donde el email viaja en el body).
        if existing is None:
            if data.email is None:
                return self._missing_precheck(audit_svc=audit_svc, meta=meta)
            return self._issue_entry_email(
                user=user_svc.create_pending(email=data.email.lower()),
                niche=niche,
                meta=meta,
                created=True,
                jwt_svc=jwt_svc,
                audit_svc=audit_svc,
                user_svc=user_svc,
            )

        if existing.status == AuthUserStatus.PENDING:
            # Pending: re-emite los artefactos passwordless (alta en curso).
            return self._issue_entry_email(
                user=existing,
                niche=niche,
                meta=meta,
                created=False,
                jwt_svc=jwt_svc,
                audit_svc=audit_svc,
                user_svc=user_svc,
            )

        if existing.status in (
            AuthUserStatus.DISABLED,
            AuthUserStatus.LOCKED,
        ):
            audit_svc.log(
                event='login.start',
                success=False,
                user_id=existing.id,
                error_code='EMAIL_NOT_FOUND',
                ip=meta.ip,
                niche=niche,
            )
            return {
                'is_valid': False,
                'code': 4001,
                'status': 404,
                'data': {
                    'error': 'EMAIL_NOT_FOUND',
                    'suggest_register': False,
                    'methods': [],
                },
            }

        # status active: abre el checklist de factores required (step=2).
        return self._open_checklist(
            user=existing,
            meta=meta,
            niche=niche,
            jwt_svc=jwt_svc,
            audit_svc=audit_svc,
        )

    def _open_checklist(
        self,
        *,
        user: Any,
        meta: Any,
        niche: str | None,
        jwt_svc: Any,
        audit_svc: Any,
    ) -> dict[str, Any]:
        """Emite el temp step=2 con los factores required a completar (AC-9).

        El front recibe `methods` (los pendientes, aun sin nada satisfecho) y
        completa cada uno con su `verify-*`, que delega en `decide_mfa_step`.
        """
        methods = MfaMethodService(app_config).required_methods(
            user_id=user.id,
        )
        temp_token, _ = jwt_svc.issue_temp(
            user_id=user.id,
            flow=build_mfa_flow([]),
            step=2,
        )
        audit_svc.log(
            event='login.start',
            success=True,
            user_id=user.id,
            ip=meta.ip,
            user_agent=meta.user_agent,
            niche=niche,
        )
        return {
            'is_valid': True,
            'code': 0,
            'data': {
                'temp_token': temp_token,
                'methods': methods,
                'step': 2,
                'mfa_complete': False,
            },
        }

    def _issue_entry_email(
        self,
        *,
        user: Any,
        niche: str | None,
        meta: Any,
        created: bool,
        jwt_svc: Any,
        audit_svc: Any,
        user_svc: Any,
    ) -> dict[str, Any]:
        """Genera code + magic-link, envia el email unificado, emite el temp.

        Es el flujo passwordless de entrada UNIFICADO (alta + pending): un
        user nuevo (created=True) o pending recibe el magic-link + code para
        verificar. El `verify-*` cierra el flujo (pending -> active).
        """
        code_svc = CodeService(app_config)
        link_svc = MagicLinkService(app_config)
        email_svc = EmailDispatchService(app_config)

        if not created:
            user_svc.invalidate_active_codes_and_links(
                user_id=str(user.id),
                kind_code=AuthCodeKind.LOGIN,
                kind_link=AuthLinkKind.LOGIN,
            )

        code, _ = code_svc.generate_and_persist(
            user_id=user.id,
            kind=AuthCodeKind.LOGIN,
        )
        token, _ = link_svc.generate_and_persist(
            user_id=user.id,
            kind=AuthLinkKind.LOGIN,
            ip=meta.ip,
            user_agent=meta.user_agent,
        )

        verify_url = (
            f'{app_config.magic_link_base_url}'
            f'?operation=login&action=verify-magic-link&token={token}'
        )
        email_svc.publish_unified(
            to=user.email,
            user_id=user.id,
            niche=niche,
            kind='login-unified',
            verify_url=verify_url,
            code=code,
            expires_in_min=LINK_TTL_MINUTES,
        )

        temp_token, _ = jwt_svc.issue_temp(
            user_id=user.id,
            flow='login',
            step=1,
        )

        audit_svc.log(
            event='login.start',
            success=True,
            user_id=user.id,
            ip=meta.ip,
            user_agent=meta.user_agent,
            niche=niche,
        )

        return {
            'is_valid': True,
            'code': 0,
            'data': {
                'temp_token': temp_token,
                'methods': ['passwordless'],
                'expires_in': _TEMP_TTL_SECONDS,
                'created': created,
            },
        }
