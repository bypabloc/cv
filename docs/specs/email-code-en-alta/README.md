# Plan: email_code confirmado automatico en el alta

## Contexto

En `/settings/security` del admin, el metodo **"Codigo por email" (email_code)**
aparece "No configurado" para el usuario, aunque **el email se verifica al
registrarse** (el alta es por code/magic-link al email). La API
`security.overview` lo reporta `configured:false` porque ese metodo MFA solo
se crea con una llamada explicita a `mfa.setup-email-code`; nunca se creo en el
alta.

Decision del dueno del producto (verbatim): *"Cuando se registra el usuario,
deberia de crear este metodo configurado, no falsearlo en overview de la api de
auth"* + *"el email es lo primero que se configura cuando se registra el
usuario, asi que eso ya esta configurado"*.

Resultado buscado: al activar el alta (pending->active) se crea un row REAL
`auth_mfa_methods` kind `email_code` confirmado (`required=false`), de modo que
el panel lo muestre `configured:true, enabled:true` y permita marcarlo
requerido. Los usuarios ya existentes (hay **UN SOLO usuario en todos los
envs**, su data no importa) se arreglan con un backfill perezoso on-read en el
overview.

Modelo: el email tiene DOS roles. `passwordless` (code/magic-link, fallback del
login, NO es un row) y `email_code` (metodo MFA explicito, SI es un row). Este
plan crea el row `email_code` en el alta.

## Solucion propuesta

Crear el `email_code` confirmado de forma **idempotente y SIN revoke de sesion**
en tres puntos (los dos controllers de activacion + backfill on-read en
overview), via un metodo nuevo `MfaMethodService.ensure_email_code`.

### Decisiones clave

- **Decision 1: revoke al primer MFA FUERTE, no al email_code.** Hoy
  `confirm()` y el webauthn confirm revocan sesiones en la transicion 0->1 de
  `count_active_mfa` (re-auth al subir nivel). Si el alta crea email_code, esa
  transicion ocurriria en el alta y romperia el revoke del primer TOTP/passkey
  real. Se separa el conteo: `count_active_mfa` (MUST_KEEP_ONE, INCLUYE
  email_code, sin cambios) vs `count_active_strong_mfa` NUEVO (TOTP confirmado +
  webauthn, EXCLUYE email_code) usado SOLO en la condicion del revoke 0->1.
- **Decision 2: `ensure_email_code` NO revoca.** Crear el email_code del alta
  jamas dispara `SessionService` (no es "primer MFA fuerte"). `setup_email_code`
  pierde su side-effect de revoke y delega en `ensure_email_code`.
- **Decision 3: backfill perezoso on-read en overview**, no migracion Alembic.
  Con un solo usuario, abrir `/settings/security` ya crea su email_code.
- **Decision 4: `email_code` se crea `required=false`** -> NO entra en
  `list_required_methods` -> `required_methods` de un user recien dado de alta
  sigue `['passwordless']`. El login no cambia.

## Criterios de aceptacion (BDD)

- **AC-1**: Given user PENDING que verifica su code via `login.verify-code`,
  When pasa a ACTIVE, Then existe row `auth_mfa_methods` kind=email_code,
  `confirmed_at NOT NULL`, `disabled_at NULL`, `required=false`.
- **AC-2**: Given user PENDING que abre su magic-link via
  `login.verify-magic-link`, When pasa a ACTIVE, Then existe el mismo row.
- **AC-3**: Given el alta, When se crea el email_code, Then NO se invoca
  `SessionService.revoke_all_for_user` y los tokens emitidos siguen validos.
- **AC-4**: Given user active con solo email_code
  (`count_active_strong_mfa=0`), When confirma su primer TOTP o registra su
  primera passkey, Then `count_active_strong_mfa` 0->1 y SI se revocan sesiones.
- **AC-5**: Given user cuyo unico MFA activo es email_code
  (`count_active_mfa=1`), When `mfa.disable email_code`, Then 409
  MUST_KEEP_ONE_MFA_METHOD (email_code cuenta como via de entrada).
- **AC-6**: Given user active (nuevo o existente sin row), When consulta
  `security.overview`, Then email_code es `configured:true, enabled:true,
  required:false` (backfill on-read idempotente).
- **AC-7**: Given email_code del alta, When `mfa.set-required kind=email_code
  required=true`, Then 204 y el login lo exige.
- **AC-8**: Given email_code ya confirmado del alta, When `mfa.setup-email-code`,
  Then 204 no-op (idempotente, no duplica, no revoca).
- **AC-9**: Given user recien dado de alta (email_code required=false), When se
  calcula `required_methods`, Then sigue `['passwordless']`.

## Diagrama de flujo

### Antes
```
login.verify-code (pending) --> mark_active --> [emite tokens]
  overview: email_code configured:false  (no hay row)
```
### Despues
```
login.verify-code (pending) --> mark_active --> ensure_email_code (sin revoke)
  --> jwt blacklist --> decide_mfa_step (emite tokens)
  overview: ensure_email_code (backfill) --> email_code configured:true
  primer TOTP/passkey: count_active_strong_mfa 0->1 --> revoke sesiones
```

## Diagrama ER

N/A — no hay cambios de schema. `auth_mfa_methods` ya soporta kind=email_code
(no se crea tabla ni columna; sin migracion Alembic).

## Archivos afectados

### Crear
- `serverless/lambda/shared/tests/unit/shared/db/repositories/test_auth_mfa_count_active_strong_excludes_email_code.py`
  - Verificar: `serverless tests --type=unit --shared`
- `serverless/lambda/services/auth/tests/unit/services/test_mfa_method_service_ensure_email_code.py`
  (3 casos: crea / no-op / reconfirma; los 3 sin `SessionService`)
- `serverless/lambda/services/auth/tests/unit/controllers/login/test_login_verify_code_pending_creates_email_code.py`
- `serverless/lambda/services/auth/tests/unit/controllers/login/test_login_verify_magic_link_pending_creates_email_code.py`
- `serverless/lambda/services/auth/tests/unit/controllers/security/test_overview_backfills_email_code.py`
- `tests/api/test_auth_register_creates_email_code.py` (E2E: alta -> overview
  email_code configured:true, sin pasar por setup-email-code)
  - Verificar: `e2e --module=api --lambda=auth --env=dev --aws-profile=tfs-dev`

### Modificar
- `serverless/lambda/shared/db/repositories/auth_mfa.py` — nueva
  `count_active_strong_mfa` (= count_active_mfa + filtro
  `AuthMfaMethod.kind != EMAIL_CODE`) + `__all__`.
  - Verificar: `serverless tests --type=unit --shared`
- `serverless/lambda/services/auth/core/services/mfa_method_service.py` —
  importar `count_active_strong_mfa`; nuevo `ensure_email_code` idempotente sin
  revoke; `confirm()` usa `count_active_strong_mfa` en la condicion del revoke;
  `setup_email_code` pierde su revoke y delega en `ensure_email_code`.
  - Verificar: `serverless tests --type=unit --lambda=auth`
- `serverless/lambda/services/auth/core/services/webauthn_service.py` —
  `persist_credential` usa `count_active_strong_mfa` en la condicion del revoke.
  - Verificar: `serverless tests --type=unit --lambda=auth`
- `serverless/lambda/services/auth/core/controllers/login/verify_code.py` —
  tras `mark_active` (branch pending), antes de `jwt blacklist`/`decide_mfa_step`:
  `mfa_svc.ensure_email_code(user_id=user.id)`.
- `serverless/lambda/services/auth/core/controllers/login/verify_magic_link.py`
  — mismo patron tras `mark_active`.
- `serverless/lambda/services/auth/core/controllers/security/overview.py` —
  backfill: tras `require_active_user`, antes de `list_all`,
  `mfa_svc.ensure_email_code(user_id=user.id)`.
- Tests unit a ACTUALIZAR (asserts/mocks):
  - `test_mfa_method_service_confirm_first_revokes.py` (mock
    `count_active_strong_mfa` en vez de `count_active_mfa`)
  - `test_mfa_method_service_setup_email_code.py` (setup ya no revoca)
  - `test_webauthn_service_more.py` (revoke usa `count_active_strong_mfa`)
  - `test_overview_empty_user.py` + `test_overview_returns_five_methods.py`
    (email_code ahora `configured:true`; ajustar `list_all.return_value`)
  - `test_login_verify_code_ok_updates_last_login.py` +
    `test_login_verify_magic_link_ok_updates_last_login.py` (caso active:
    `ensure_email_code` no se llama)
- E2E a AUDITAR/ajustar baseline (el helper `create_active_user_with_password`
  ahora crea email_code en todos los users de prueba):
  `tests/api/test_auth_email_code_full_lifecycle.py` (setup-email-code ahora
  idempotente sobre el row del alta) + auditar
  `test_auth_{disable_unconfirmed_mfa,delete_pending_mfa,set_required_requires_confirmed,totp_full_lifecycle,mfa,multifactor_checklist,webauthn_full_lifecycle}.py`
  por asserts que asuman email_code no configurado o count MFA=0 pre-setup.

## Descomposicion / commits (atomicos, en orden, TDD)

1. `test(auth): cuenta fuerte de MFA que excluye email_code` — repo
   `count_active_strong_mfa` + su test shared.
2. `feat(auth): ensure_email_code idempotente sin revoke` — metodo nuevo +
   `setup_email_code` delega y pierde el revoke + tests.
3. `fix(auth): el revoke 0->1 usa la cuenta fuerte` — `confirm()` +
   `persist_credential` migran al conteo fuerte + tests actualizados.
4. `feat(auth): crea email_code al activar el alta (verify-code + magic-link)` —
   las 2 lineas en los controllers + tests pending.
5. `feat(auth): backfill perezoso de email_code en security.overview` — linea
   en overview + tests overview actualizados.
6. `test(auth): E2E del alta crea email_code + lifecycle idempotente` — E2E
   nuevo + ajuste del lifecycle + lint-deps + deploy a dev + E2E contra dev.

Worktrees: N/A — secuencial (los commits comparten mfa_method_service.py y
auth_mfa.py; no son worktree-safe). Un solo PR `feature/... -> dev`.

## Verificacion E2E iterativa (fase final)

Parte A (tests): ningun test referencia el comportamiento viejo (email_code
configured:false tras alta); `rg` de baseline en los E2E auditados.

Parte B (bateria, bucle hasta verde):
```
python devtools/run.py serverless tests --type=unit --shared
python devtools/run.py serverless tests --type=unit --lambda=auth
python devtools/run.py serverless tests --type=coverage --lambda=auth   # >=80%
python devtools/run.py serverless lint-deps --lambda=auth
python devtools/run.py serverless lint-deps --shared
```
Gate de push/PR: todo verde. Merge -> deploy auth a dev.

Parte C (deploy real, post-merge):
```
python devtools/run.py serverless deploy --lambda=auth --stage=dev --aws-profile=tfs-dev
python devtools/run.py e2e --module=api --lambda=auth --env=dev --aws-profile=tfs-dev
```
+ verificar manual en `/settings/security` de dev: "Codigo por email" aparece
Activo (no "No configurado") tras refrescar (el backfill on-read lo crea para
el unico usuario existente).

## Definition of Done

- [ ] AC-1..AC-9 cubiertos por tests que pasan.
- [ ] `count_active_mfa` (MUST_KEEP_ONE) intacto; revoke usa
  `count_active_strong_mfa`.
- [ ] email_code del alta NO revoca sesiones; primer TOTP/passkey SI.
- [ ] coverage auth >=80% per-file; lint-deps OK (sin imports externos nuevos).
- [ ] deploy auth a dev + E2E api verde.
- [ ] `/settings/security` de dev muestra email_code Activo.
