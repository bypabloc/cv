# 05. Lambda `auth` — arquitectura

> Aplica el formato lambda-controller: handler delgado, controllers
> orquestan, services tienen la logica de negocio, models Pydantic
> validan estructura. EventModel armado con `build_event_model(OPERATIONS)`
> de shared.lambda_kit. http_handler del repo procesa CORS, request
> extraction, _meta injection, dispatch y serializacion.

## Estructura de carpetas

```text
serverless/lambda/services/auth/
├── manifest.yaml
├── pyproject.toml             # PEP 621; deps: solo lo que NO aporta shared
├── uv.lock
├── .gitignore                 # build/ + build.zip
├── core/
│   ├── handler.py             # lambda_handler -> http_handler(...)
│   ├── settings/
│   │   ├── config.py          # AppConfig (env vars + SSM lazy)
│   │   └── operations.py      # OPERATIONS dict
│   ├── models/
│   │   ├── event.py           # EventModel armado con build_event_model
│   │   ├── register.py        # RegisterStartIn, RegisterVerifyMagicLinkIn, ...
│   │   ├── login.py           # LoginStartIn, LoginVerifyMagicLinkIn, ...
│   │   ├── verify.py          # VerifySetPasswordIn, VerifyResendCodeIn
│   │   └── session.py         # SessionRefreshIn, SessionLogoutIn
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── register/
│   │   │   ├── start.py             # Start(BaseController)
│   │   │   ├── verify_magic_link.py # VerifyMagicLink(BaseController)
│   │   │   └── verify_code.py       # VerifyCode(BaseController)
│   │   ├── login/
│   │   │   ├── start.py
│   │   │   ├── verify_magic_link.py
│   │   │   └── verify_code.py
│   │   ├── verify/
│   │   │   ├── set_password.py
│   │   │   └── resend_code.py
│   │   └── session/
│   │       ├── refresh.py
│   │       └── logout.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user_service.py          # lookup, create, lock, unlock
│   │   ├── code_service.py          # generate + persist (Neon + DDB)
│   │   ├── magic_link_service.py    # generate + persist + verify
│   │   ├── jwt_service.py           # issue temp/access/refresh + rotate + blacklist
│   │   ├── blacklist_service.py     # DDB ops (PutItem, GetItem por jti, Query por family_id)
│   │   ├── email_dispatch_service.py # publica a SQS auth-email-queue
│   │   ├── audit_service.py         # auth_audit_log inserts
│   │   ├── rate_limit_service.py    # wrapper de shared.rate_limit.check_or_raise
│   │   └── flow_service.py          # orquestador de pasos del flujo (verify -> set-password -> ...)
│   └── utils/
│       └── __init__.py              # vacio; el kit ya esta en shared.lambda_kit
├── events/                          # JSONs de prueba para `serverless run`
│   ├── register-start.json
│   ├── register-verify-magic-link.json
│   ├── register-verify-code.json
│   ├── login-start.json
│   ├── login-verify-magic-link.json
│   ├── login-verify-code.json
│   ├── verify-set-password.json
│   ├── verify-resend-code.json
│   ├── session-refresh.json
│   └── session-logout.json
└── tests/
    ├── conftest.py
    ├── unit/
    │   ├── _helpers.py              # builders compartidos
    │   ├── controllers/             # 1 archivo por test
    │   ├── services/
    │   └── models/
    └── integration/
        ├── conftest.py
        ├── _fixtures/
        ├── test_register_start_e2e.py
        ├── test_login_start_e2e.py
        ├── test_full_register_flow_e2e.py
        └── test_logout_blacklists_jwt_e2e.py
```

## `handler.py` (esqueleto)

```python
"""Lambda auth — entrypoint."""

from typing import Any

from shared.lambda_kit import http_handler

from .models.event import EVENT_MODEL


def lambda_handler(event: dict[str, Any], _context: object) -> dict[str, Any]:
    return http_handler(
        event,
        event_model=EVENT_MODEL,
        cors_origin='echo',
        success_status=200,
        metric_names={
            'submitted': 'AuthRequestAccepted',
            'rejected':  'AuthRequestRejected',
            'error':     'AuthRequestError',
        },
    )
```

## `settings/operations.py`

```python
"""Registro de operations -> {controller_module, action -> Class}."""

from shared.lambda_kit import resolve_operation


OPERATIONS = {
    'register': {
        'actions': ['start', 'verify-magic-link', 'verify-code'],
    },
    'login': {
        'actions': ['start', 'verify-magic-link', 'verify-code'],
    },
    'verify': {
        'actions': ['set-password', 'resend-code'],
    },
    'session': {
        'actions': ['refresh', 'logout'],
    },
}
```

El controller se descubre por convencion:
`core.controllers.<operation>.<action_snake>.<ActionPascal>`. Ej:
`verify-magic-link` -> module `controllers/register/verify_magic_link.py`
+ clase `VerifyMagicLink(BaseController)`.

## `settings/config.py` (AppConfig)

```python
from functools import cached_property
from shared.core import Settings
from shared.aws import get_secret_by_name


class AppConfig(Settings):
    """Env vars + lazy secrets en cold start."""

    log_level: str = 'INFO'
    powertools_service_name: str = 'auth'
    powertools_metrics_namespace: str = 'Portfolio/Auth'

    # Env vars
    jwt_issuer: str = 'portfolio-auth'
    jwt_audience: str = 'portfolio'
    magic_link_base_url: str            # ej. https://api.portfolio.dev.the-full-stack.com/auth
    cors_allowed_origins: str
    stage: str                          # 'dev'|'stage'|'prod'|'local'

    # SSM lazy (paths del manifest)
    @cached_property
    def jwt_secret(self) -> str:
        return get_secret_by_name('jwt-secret', local_env='JWT_SECRET')

    @cached_property
    def turnstile_secret(self) -> str:
        return get_secret_by_name('turnstile-secret', local_env='TURNSTILE_SECRET_KEY')

    @cached_property
    def turnstile_bypass_secret(self) -> str | None:
        return get_secret_by_name(
            'turnstile-bypass-secret', local_env='TURNSTILE_BYPASS_SECRET',
            optional=True,
        )

    @cached_property
    def neon_url(self) -> str:
        return get_secret_by_name('neon-url', local_env='DATABASE_URL')

    @cached_property
    def ses_from_address(self) -> str:
        return get_secret_by_name('ses-from-address', local_env='SES_FROM_ADDRESS')

    # DynamoDB table names (resueltos en cold start desde SSM)
    @cached_property
    def jwt_blacklist_table(self) -> str:
        return _resolve_table_name_from_ssm('SSM_JWT_BLACKLIST_TABLE_PATH')

    @cached_property
    def auth_email_queue_url(self) -> str:
        return _resolve_from_ssm('SSM_AUTH_EMAIL_QUEUE_URL_PATH')


app_config = AppConfig()
```

## `models/event.py`

```python
"""EventModel armado con shared.lambda_kit.build_event_model."""

from shared.lambda_kit import build_event_model

from .login import LoginStartIn, LoginVerifyCodeIn, LoginVerifyMagicLinkIn
from .register import (
    RegisterStartIn,
    RegisterVerifyCodeIn,
    RegisterVerifyMagicLinkIn,
)
from .session import SessionLogoutIn, SessionRefreshIn
from .verify import VerifyResendCodeIn, VerifySetPasswordIn


EVENT_MODEL = build_event_model({
    'register': {
        'start': RegisterStartIn,
        'verify-magic-link': RegisterVerifyMagicLinkIn,
        'verify-code': RegisterVerifyCodeIn,
    },
    'login': {
        'start': LoginStartIn,
        'verify-magic-link': LoginVerifyMagicLinkIn,
        'verify-code': LoginVerifyCodeIn,
    },
    'verify': {
        'set-password': VerifySetPasswordIn,
        'resend-code': VerifyResendCodeIn,
    },
    'session': {
        'refresh': SessionRefreshIn,
        'logout': SessionLogoutIn,
    },
})
```

## Modelos Pydantic (ejemplos)

`models/register.py`:

```python
from typing import Literal

from shared.core import BaseModel, EmailStr, Field, model_validator


# Lista cerrada: los 6 niches del portfolio. Cualquier otro valor en
# el payload del cliente -> ValidationError 400. Esto evita que un
# atacante meta strings arbitrarios (incluyendo HTML/script) en el
# audit log o templates de email.
Niche = Literal['generic', 'hub', 'fintech', 'architect', 'leader', 'vibe']


class _Meta(BaseModel):
    ip: str | None = None
    country: str | None = None
    user_agent: str | None = None
    bypass_secret: str | None = None
    origin: str | None = None


class RegisterStartIn(BaseModel):
    """POST /auth operation=register action=start."""
    email: EmailStr
    cf_turnstile_response: str = Field(min_length=1)
    niche: Niche | None = None
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = {'populate_by_name': True}


class RegisterVerifyMagicLinkIn(BaseModel):
    """GET callback of the magic-link OR POST."""
    token: str = Field(min_length=32, max_length=128)
    temp_token: str | None = None        # opcional (si el user lo trae al GET)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = {'populate_by_name': True}


class RegisterVerifyCodeIn(BaseModel):
    code: str = Field(min_length=8, max_length=8, pattern=r'^[A-HJ-NP-Z2-9]{8}$')
    temp_token: str = Field(min_length=20)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')

    model_config = {'populate_by_name': True}
```

`models/session.py`:

```python
class SessionRefreshIn(BaseModel):
    refresh_token: str = Field(min_length=20)
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = {'populate_by_name': True}


class SessionLogoutIn(BaseModel):
    access_token: str = Field(min_length=20)
    refresh_token: str | None = None   # logout invalida ambos si llega
    meta: _Meta = Field(default_factory=_Meta, alias='_meta')
    model_config = {'populate_by_name': True}
```

## Patron de controller (ejemplo: `register.start`)

`controllers/register/start.py`:

```python
"""Register.Start — inicia el flujo de registro.

Flujo:
  1. preload: nada (config ya en cold start)
  2. validate: Pydantic + Turnstile + rate-limit
  3. execute:
     a. lookup user por email -> si existe + active -> 409
     b. crear/upsert user pendiente
     c. generar code + magic-link
     d. persistir (Neon + DDB en paralelo via TaskGroup)
     e. publicar 2 mensajes SQS
     f. emitir temp JWT (flow='register', step=1)
     g. audit log success
     h. devolver {temp_token, user_id, expires_in: 300}
"""

from shared.lambda_kit import BaseController, ErrorCode
from shared.observability import logger, metrics

from ...services.audit_service import AuditService
from ...services.code_service import CodeService
from ...services.email_dispatch_service import EmailDispatchService
from ...services.jwt_service import JwtService
from ...services.magic_link_service import MagicLinkService
from ...services.rate_limit_service import RateLimitService
from ...services.user_service import UserService
from ...settings.config import app_config


class Start(BaseController):
    def preload(self):
        return {'is_valid': True, 'data': {}, 'code': 0}

    def validate(self):
        # http_handler ya valido Pydantic. Aqui aplicamos validaciones de negocio:
        meta = self.data['_meta']
        RateLimitService(app_config).check_or_raise(
            ip=meta['ip'], endpoint='/auth#register.start',
            country=meta['country'],
        )
        # Turnstile
        from shared.http import verify_turnstile_token
        verify_turnstile_token(
            self.data['cf_turnstile_response'],
            remote_ip=meta['ip'],
            bypass_secret=meta['bypass_secret'],
        )
        return {'is_valid': True, 'data': {}, 'code': 0}

    def execute(self):
        user_svc = UserService(app_config)
        code_svc = CodeService(app_config)
        link_svc = MagicLinkService(app_config)
        jwt_svc  = JwtService(app_config)
        email_svc = EmailDispatchService(app_config)
        audit = AuditService(app_config)
        meta = self.data['_meta']

        # 1. Idempotency
        existing = user_svc.get_by_email(self.data['email'])
        if existing and existing.status == 'active':
            audit.log(event='register.start', success=False,
                      error_code='EMAIL_ALREADY_REGISTERED',
                      user_id=existing.id, ip=meta['ip'])
            return {
                'is_valid': False, 'code': 4001,
                'data': {'error': 'EMAIL_ALREADY_REGISTERED'},
            }

        # 2. Crear/upsert pending
        user = existing or user_svc.create_pending(email=self.data['email'])

        # 3. Generar + persistir
        code, code_hash = code_svc.generate_and_persist(
            user_id=user.id, kind='register',
        )
        token, token_hash = link_svc.generate_and_persist(
            user_id=user.id, kind='register',
            ip=meta['ip'], user_agent=meta['user_agent'],
        )

        # 4. Publicar emails a SQS
        verify_url = (
            f"{app_config.magic_link_base_url}"
            f"?operation=register&action=verify-magic-link&token={token}"
        )
        email_svc.publish_magic_link(
            to=user.email, user_id=user.id, niche=self.data.get('niche'),
            kind='register-magic-link', token=token, verify_url=verify_url,
        )
        email_svc.publish_code(
            to=user.email, user_id=user.id, niche=self.data.get('niche'),
            kind='register-code', code=code,
        )

        # 5. Temp JWT (rolling)
        temp_token, claims = jwt_svc.issue_temp(
            user_id=user.id, flow='register', step=1,
        )

        # 6. Audit
        audit.log(event='register.start', success=True, user_id=user.id,
                  ip=meta['ip'], user_agent=meta['user_agent'])

        return {
            'is_valid': True, 'code': 0,
            'data': {
                'temp_token': temp_token,
                'user_id': str(user.id),
                'expires_in': 300,
            },
        }
```

## Rolling temp JWT — patron implementado en cada controller del flujo

`verify.set-password`, `register.verify-code`, `register.verify-magic-link`,
`verify.resend-code` siguen este patron:

```python
# 1. Recibe temp_token en data
temp_token = self.data['temp_token']

# 2. Verifica signature + exp + typ='temp' + NOT in blacklist
claims = jwt_svc.verify_temp(temp_token, expected_flow='register')

# 3. Blacklistea el jti viejo
jwt_svc.blacklist(jti=claims.jti, exp=claims.exp,
                  user_id=claims.sub, reason='rotation')

# 4. Ejecuta la accion (verify code, set password, ...)

# 5. Si el flujo terminal -> emite access + refresh (NO temp).
#    Si el flujo continua -> emite un NUEVO temp con step+1
if is_terminal_step:
    access, _  = jwt_svc.issue_access(user_id=claims.sub, email=user.email)
    refresh, _ = jwt_svc.issue_refresh(user_id=claims.sub,
                                        family_id=uuidv7())
    return {'access_token': access, 'refresh_token': refresh,
            'expires_in': 900, 'token_type': 'Bearer',
            'user': {'id': str(user.id), 'email': user.email,
                     'status': user.status}}
else:
    new_temp, _ = jwt_svc.issue_temp(user_id=claims.sub,
                                      flow=claims.flow, step=claims.step + 1)
    return {'temp_token': new_temp, 'expires_in': 300, ...}
```

## Flujo de magic-link (GET → 302 redirect al dashboard)

El magic-link es una URL que el user clickea desde su email. API
Gateway recibe `GET /auth?operation=register&action=verify-magic-link&token=<X>`.
La Lambda **responde con HTTP 302** y un header `Location:` que apunta
al dashboard con los tokens en el **fragment hash**.

```text
HTTP/1.1 302 Found
Location: https://admin.portfolio.{env}.the-full-stack.com/callback#access=<JWT>&refresh=<JWT>&user_id=<X>&email=<Y>
Cache-Control: no-store, no-cache, must-revalidate
Pragma: no-cache
```

Por que **fragment hash** y NO query string:

+ El fragment (`#...`) NUNCA se envia al servidor en el siguiente
  request — vive solo en el browser.
+ NO aparece en logs de CloudFront / CloudWatch / nginx / proxies
  intermedios.
+ NO se incluye en `Referer` headers de subsequent navigations.
+ El dashboard lee `window.location.hash` desde JS, decodifica los
  tokens, los guarda en `localStorage` via Zustand, limpia el hash con
  `history.replaceState`, y redirige a `/dashboard`.

Ventajas vs servir HTML inline desde la Lambda:

+ **El handler `http_handler` NO se extiende**. Sigue devolviendo
  JSON-only para el resto de actions. El 302 lo expresa el controller
  retornando un `DispatchResult` con el header `Location` populated
  (patron que `http_handler` ya soporta — solo agrega el header al
  response final, sin tocar `content_type`).
+ Cero HTML servido por API Gateway: si el dashboard tiene XSS, el
  blast radius esta acotado al dashboard (no a la API).
+ El callback del dashboard se reusa para el flujo de login y
  password-reset (mismo handler `/callback` del dashboard).

Implementacion del controller (`register.verify_magic_link.VerifyMagicLink`):

```python
def execute(self):
    # ... verificar token, marcar consumido, emitir JWT ...
    callback_url = (
        f"https://admin.portfolio.{stage_to_env_label(app_config.stage)}"
        f".the-full-stack.com/callback"
        f"#access={access_token}&refresh={refresh_token}"
        f"&user_id={user.id}&email={user.email}"
    )
    return {
        'is_valid': True,
        'code': 0,
        'data': {},
        'redirect': {
            'status': 302,
            'location': callback_url,
            'cache_control': 'no-store, no-cache, must-revalidate',
        },
    }
```

`http_handler` interpreta el campo opcional `redirect` del
DispatchResult y, en lugar de devolver el JSON estandar, construye:

```python
{
    'statusCode': dispatch.redirect['status'],
    'headers': {
        'Location': dispatch.redirect['location'],
        'Cache-Control': dispatch.redirect['cache_control'],
        # CORS sigue aplicando segun cors_origin del handler
    },
    'body': '',
}
```

Este cambio es **aditivo** (campo opcional `redirect`) y NO rompe el
contrato JSON existente del resto de actions. Se documenta en
`shared.lambda_kit.http_handler` y se cubre con un test unit nuevo
(`test_http_handler_redirect.py` en `shared/tests/unit/shared/lambda_kit/`).

### Por que el redirect apunta a admin (no a un niche)

Antes de plan auth no habia "dashboard" — los usuarios del portfolio
son visitantes anonimos de las 6 apps publicas. El **dashboard
(`admin.portfolio.{env}.the-full-stack.com`)** es el unico contexto
autenticado del proyecto (admin de Pablo, futuras areas privadas).
Los magic-links siempre llevan ahi.

Si un futuro plan agrega areas autenticadas en algun niche (ej.
`fintech.portfolio.../app/dashboard`), se parametrizara via `niche`
en el payload del controller — pero ese cambio NO entra en plan 01.

## Que toca cada controller (matriz resumen)

| Controller | Neon (lectura/escritura) | DDB (lectura/escritura) | SQS publish | JWT issue/verify/blacklist |
|------------|--------------------------|-------------------------|-------------|----------------------------|
| register.start | R/W auth_users, W auth_email_codes/links, W audit | (ninguna) | 2 (magic-link + code) | issue temp |
| register.verify-magic-link | R/W links, R/W user, W audit | R/W blacklist (temp) | 0 | verify temp, issue access+refresh, blacklist temp |
| register.verify-code | R/W codes, R/W user, W audit | R/W blacklist (temp) | 0 | idem |
| login.start | R user, W audit, W codes/links | (ninguna) | 0..2 | issue temp (si user existe) |
| login.verify-magic-link | mismo que register | mismo | 0 | idem |
| login.verify-code | mismo | mismo | 0 | idem |
| verify.set-password | R user, W auth_credentials, W audit | R/W blacklist (temp) | 0 | verify temp, issue temp nuevo |
| verify.resend-code | R/W codes/links, W audit | (ninguna) | 1-2 | verify temp, issue temp nuevo |
| session.refresh | R user, W audit | R/W blacklist | 0 | verify refresh, issue access+refresh rotado |
| session.logout | W audit | W blacklist (jti + family_id) | 0 | verify access, blacklist access+refresh |

## Donde NO va la logica

- `handler.py`: solo router via `http_handler`. Cero negocio.
- `controllers/`: orquestan. Cero queries SQL ni boto3 directo. Solo
  llamadas a `services/`.
- `models/`: solo Pydantic schemas. Sin negocio.
- `services/`: TODA la logica. Acceso a `shared.db.repositories.auth.*`,
  `shared.aws.get_resource`, `shared.aws.get_table`, `shared.auth.*`.

## Cierre de la arquitectura

La forma del Lambda `auth` clona `contact_form` (HTTP write + SQS
publisher + Turnstile + rate-limit + Neon + DDB) pero con mas operations
y un dominio nuevo. No introduce patrones nuevos al backend. SnapStart
habilitado para reducir cold start (~10x mejora segun la skill
`aws-lambda-python`).
