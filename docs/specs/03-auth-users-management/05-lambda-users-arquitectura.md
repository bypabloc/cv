# 05. Lambda `users` — arquitectura

## Operations + actions

```text
operation 'profile':
- get               POST  -> retorna profile del propio user
- update            POST  -> actualiza display_name/locale/timezone/marketing_consent
- change-email      POST  -> inicia flow magic-link al new_email
- delete-account    POST  -> self-service GDPR soft-delete

operation 'status':
- get               POST  -> status + MFA info
- list-sessions     POST  -> lista sesiones activas
- revoke-session    POST  -> cierra una session (no la actual)

operation 'admin':  (whitelist via SSM)
- list-users        POST  -> paginado
- get-user          POST  -> detalle por user_id
- disable-user      POST  -> marca status=disabled
- enable-user       POST  -> marca status=active
- force-logout      POST  -> revoca todas las sessions del target
- delete-user       POST  -> hard-delete con cascade (sentinel obligatorio)
- list-admin-actions POST -> historico de admin actions
```

Total: 14 actions (4 + 3 + 7).

## Estructura de carpetas

```text
serverless/lambda/services/users/
├── manifest.yaml
├── pyproject.toml             # PEP 621; deps minimas (todo via shared)
├── uv.lock
├── .gitignore                 # build/ + build.zip
├── core/
│   ├── handler.py             # http_handler con EVENT_MODEL
│   ├── settings/
│   │   ├── config.py          # AppConfig
│   │   └── operations.py      # OPERATIONS = {profile, status, admin}
│   ├── models/
│   │   ├── event.py
│   │   ├── profile.py
│   │   ├── status.py
│   │   └── admin.py
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── profile/
│   │   │   ├── get.py
│   │   │   ├── update.py
│   │   │   ├── change_email.py
│   │   │   └── delete_account.py
│   │   ├── status/
│   │   │   ├── get.py
│   │   │   ├── list_sessions.py
│   │   │   └── revoke_session.py
│   │   └── admin/
│   │       ├── list_users.py
│   │       ├── get_user.py
│   │       ├── disable_user.py
│   │       ├── enable_user.py
│   │       ├── force_logout.py
│   │       ├── delete_user.py
│   │       └── list_admin_actions.py
│   ├── services/
│   │   ├── profile_service.py
│   │   ├── session_service.py
│   │   ├── admin_service.py            # require_admin_user helper
│   │   ├── audit_admin_service.py      # writes a auth_user_admin_actions
│   │   ├── consent_service.py          # writes a auth_user_consent_log
│   │   ├── blacklist_service.py        # reusa el shape del de auth lambda
│   │   ├── jwt_service.py              # verify_access (reusa shared.auth)
│   │   ├── email_dispatch_service.py   # publica SQS (change-email magic-link, etc.)
│   │   ├── audit_service.py            # writes a auth_audit_log generico
│   │   └── rate_limit_service.py
│   └── utils/
│       └── (vacio; kit en shared.lambda_kit)
├── events/                    # JSONs de prueba
└── tests/
    ├── unit/
    └── integration/
```

## Patron de controller — ejemplo `profile.update`

```python
"""profile.update — actualiza campos del propio user.

Requiere: access JWT valido.
Acepta parcial: cualquier subset de {display_name, locale,
timezone, marketing_consent, privacy_policy_version}.
Si marketing_consent cambia -> INSERT en auth_user_consent_log.
"""

from shared.lambda_kit import BaseController
from shared.observability import logger, metrics

from ...services.audit_service import AuditService
from ...services.consent_service import ConsentService
from ...services.jwt_service import require_active_user
from ...services.profile_service import ProfileService
from ...services.rate_limit_service import RateLimitService
from ...settings.config import app_config


class Update(BaseController):
    def preload(self):
        return {'is_valid': True, 'data': {}, 'code': 0}

    def validate(self):
        user = require_active_user(
            self.data['_meta'].get('authorization'),
            config=app_config,
        )
        RateLimitService(app_config).check_or_raise(
            ip=self.data['_meta']['ip'],
            endpoint='/users#profile.update',
            key_override=str(user.id),
        )
        self.context = {'user': user}
        return {'is_valid': True, 'data': {}, 'code': 0}

    def execute(self):
        user = self.context['user']
        meta = self.data['_meta']
        profile_svc = ProfileService(app_config)
        consent_svc = ConsentService(app_config)
        audit = AuditService(app_config)

        updates = {
            k: v for k, v in self.data.items()
            if k in {'display_name', 'locale', 'timezone',
                     'marketing_consent', 'privacy_policy_version'}
            and v is not None
        }

        old_marketing = user.marketing_consent
        new_marketing = updates.get('marketing_consent')

        updated_user = profile_svc.update(user_id=user.id, **updates)

        if new_marketing is not None and new_marketing != old_marketing:
            consent_svc.log(
                user_id=user.id, field='marketing_consent',
                old_value=str(old_marketing),
                new_value=str(new_marketing),
                ip=meta['ip'], user_agent=meta['user_agent'],
            )

        audit.log(event='profile.update', success=True, user_id=user.id,
                  ip=meta['ip'], metadata={'fields': list(updates.keys())})
        metrics.add_metric(name='ProfileUpdate', unit='Count', value=1)

        return {
            'is_valid': True, 'code': 0,
            'data': {
                'id': str(updated_user.id),
                'email': updated_user.email,
                'display_name': updated_user.display_name,
                'locale': updated_user.locale,
                'timezone': updated_user.timezone,
                'marketing_consent': updated_user.marketing_consent,
            },
        }
```

## Patron admin — ejemplo `admin.disable-user`

```python
class DisableUser(BaseController):
    def validate(self):
        actor = require_active_user(
            self.data['_meta'].get('authorization'),
            config=app_config,
        )
        # require_admin_user levanta 404 (no 403) si no es admin
        from ...services.admin_service import require_admin_user
        require_admin_user(actor, ip=self.data['_meta']['ip'],
                            audit_action='admin.disable-user.attempt')
        self.context = {'actor': actor}
        return {'is_valid': True, 'data': {}, 'code': 0}

    def execute(self):
        actor = self.context['actor']
        meta = self.data['_meta']
        target_id = UUID(self.data['user_id'])
        reason = self.data.get('reason', 'admin discretion')

        profile_svc = ProfileService(app_config)
        admin_audit = AuditAdminService(app_config)

        target = profile_svc.get_by_id(user_id=target_id)
        if target is None or target.deleted_at is not None:
            return {'is_valid': False, 'code': 4040,
                    'data': {'error': 'NOT_FOUND'}}

        if target.id == actor.id:
            return {'is_valid': False, 'code': 4000,
                    'data': {'error': 'CANNOT_DISABLE_SELF'}}

        profile_svc.disable_user(user_id=target.id)

        # Audit PRE-hoc — ya se intento, el DB cambio
        admin_audit.log(
            admin_user_id=actor.id, target_user_id=target.id,
            action='disable', metadata={'reason': reason},
            ip=meta['ip'], user_agent=meta['user_agent'],
        )

        return {
            'is_valid': True, 'code': 0,
            'data': {'message': 'OK', 'status': 204},
        }
```

## Modelos Pydantic — ejemplos

`models/profile.py`:

```python
class ProfileGetIn(BaseModel):
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = {'populate_by_name': True}


class ProfileUpdateIn(BaseModel):
    display_name: str | None = Field(default=None, max_length=64)
    locale: Literal['es', 'en'] | None = None
    timezone: str | None = Field(default=None, max_length=64)
    marketing_consent: bool | None = None
    privacy_policy_version: str | None = Field(default=None, max_length=16)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = {'populate_by_name': True}


class ProfileChangeEmailIn(BaseModel):
    new_email: EmailStr
    password: str | None = Field(default=None, min_length=12, max_length=256)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = {'populate_by_name': True}


class ProfileDeleteAccountIn(BaseModel):
    confirm: Literal['DELETE-MY-ACCOUNT']
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = {'populate_by_name': True}
```

`models/admin.py`:

```python
class AdminListUsersIn(BaseModel):
    cursor: UUID | None = None
    page_size: int = Field(default=50, ge=1, le=200)
    status_filter: Literal['pending', 'active', 'disabled', 'locked'] | None = None
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = {'populate_by_name': True}


class AdminDisableUserIn(BaseModel):
    user_id: UUID
    reason: str | None = Field(default=None, max_length=256)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = {'populate_by_name': True}


class AdminDeleteUserIn(BaseModel):
    user_id: UUID
    confirm: str = Field(min_length=20)  # debe matchear `HARD-DELETE-USER-<uuid>`
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = {'populate_by_name': True}

    @field_validator('confirm')
    @classmethod
    def confirm_matches_user_id(cls, v, info):
        user_id = info.data.get('user_id')
        if user_id and v != f'HARD-DELETE-USER-{user_id}':
            raise ValueError('Confirm sentinel must match user_id')
        return v
```

## EventModel

```python
EVENT_MODEL = build_event_model({
    'profile': {
        'get': ProfileGetIn,
        'update': ProfileUpdateIn,
        'change-email': ProfileChangeEmailIn,
        'delete-account': ProfileDeleteAccountIn,
    },
    'status': {
        'get': StatusGetIn,
        'list-sessions': StatusListSessionsIn,
        'revoke-session': StatusRevokeSessionIn,
    },
    'admin': {
        'list-users': AdminListUsersIn,
        'get-user': AdminGetUserIn,
        'disable-user': AdminDisableUserIn,
        'enable-user': AdminEnableUserIn,
        'force-logout': AdminForceLogoutIn,
        'delete-user': AdminDeleteUserIn,
        'list-admin-actions': AdminListAdminActionsIn,
    },
})
```

## Que toca cada service

| Service | Responsabilidad |
|---------|-----------------|
| `ProfileService` | CRUD `auth_users`: get_by_id, update, change_email, soft_delete, hard_delete, disable, enable |
| `SessionService` | CRUD `auth_user_sessions`: list_for_user, revoke, revoke_all_for_user |
| `AdminService` | `require_admin_user` helper |
| `AuditAdminService` | INSERT `auth_user_admin_actions` |
| `ConsentService` | INSERT `auth_user_consent_log` |
| `BlacklistService` | reusa del lambda auth (DDB ops) |
| `JwtService` | verify_access (lectura), `require_active_user` |
| `EmailDispatchService` | publica a `auth-email-queue` (kind: `email-changed`, `account-disabled`, `account-deleted`) |
| `AuditService` | INSERT `auth_audit_log` generico |
| `RateLimitService` | wrapper de `shared.rate_limit.check_or_raise` |

## Errores

| Codigo | Significado |
|--------|-------------|
| `NOT_FOUND` | user_id no existe O caller no es admin (deliberado) |
| `CANNOT_DISABLE_SELF` | admin intentando deshabilitarse a si mismo |
| `CANNOT_DELETE_SELF` | admin intentando hard-deletarse a si mismo |
| `EMAIL_ALREADY_IN_USE` | el `change-email` apunta a un email ya activo |
| `INVALID_PASSWORD` | el `change-email` exige password (si user tiene) — no matchea |
| `CANNOT_REVOKE_CURRENT_SESSION` | (AC-10) usar `auth.session.logout` en su lugar |
| `USER_NOT_DISABLED` | `enable-user` aplicado a alguien no disabled |
| `INVALID_CONFIRM_SENTINEL` | `delete-account` con sentinel no exacto |

## Que toca cada controller — matriz resumen

| Controller | Neon R/W | DDB R/W | SQS publish | JWT/Auth |
|------------|----------|---------|-------------|----------|
| profile.get | R auth_users + auth_mfa_methods + auth_webauthn_credentials | — | 0 | require_active_user |
| profile.update | RW auth_users + W consent_log | — | 0 | require_active_user |
| profile.change-email | R auth_users + W auth_magic_links | — | 1 (magic-link) | require_active_user |
| profile.delete-account | RW auth_users (soft) + cascade DELETE | RW blacklist (todas las sessions) | 1 (notify) | require_active_user |
| status.get | R auth_users + mfa + webauthn | — | 0 | require_active_user |
| status.list-sessions | R auth_user_sessions | — | 0 | require_active_user |
| status.revoke-session | RW auth_user_sessions | RW blacklist (family_id) | 0 | require_active_user |
| admin.list-users | R auth_users paginado | — | 0 | require_admin_user |
| admin.get-user | R auth_users + relations + audit_log | — | 0 | require_admin_user |
| admin.disable-user | RW auth_users + W admin_actions | — | 1 (notify target) | require_admin_user |
| admin.enable-user | RW auth_users + W admin_actions | — | 0 | require_admin_user |
| admin.force-logout | DELETE auth_user_sessions + W admin_actions | RW blacklist | 0 | require_admin_user |
| admin.delete-user | cascade DELETE + W admin_actions | RW blacklist | 1 (notify) | require_admin_user |
| admin.list-admin-actions | R admin_actions paginado | — | 0 | require_admin_user |
