# Plan: eliminar la operation `register` por completo (backend + E2E + docs)

> Plan **Medium-Large**. Elimina la operation `register` del Lambda `auth`
> (controllers + models + tests + email kinds + enums DB) y convierte todas
> sus referencias en el harness/E2E al flujo `login` unificado. **1 PR** a `dev`.
> Carpeta: `docs/specs/remove-register/`.

## 1. Contexto / Problema

El alta de usuarios se fusiono en el flujo `login` unico (plan
admin-security-overview + login-mfa-list-redesign): `login.start` crea el user
`pending` si el email no existe, y `login.verify-code`/`login.verify-magic-link`
lo activan. La operation `register` (3 actions: `start`, `verify-code`,
`verify-magic-link`) quedo como **deuda legacy**: sigue desplegada pero ningun
flujo de producto la usa. El usuario pide eliminarla de TODO: backend, E2E,
docs/rules/skills, y tambien del schema (los enums `register` de la DB).

### Hallazgos de exploracion (cerrados, no reabrir)

- **Backend**: `controllers/register/` (4 archivos) + `models/register.py` +
  entrada `'register'` en `operations.py` + 19 tests unit. El descubrimiento de
  operations es por convencion (`OPERATIONS` dict + carpeta del controller); no
  hay rutas hardcodeadas en `manifest.yaml`.
- **Email kinds**: `register-unified` / `register-code` / `register-magic-link`
  (3 filas en `send_email/seeds/email_config.py` + 6 templates). El login usa
  `login-*`, NO los `register-*` -> seguros de borrar.
- **Enums DB (RIESGO)**: `AuthCodeKind.REGISTER` / `AuthLinkKind.REGISTER`
  (`shared/db/models/auth/enums.py`) estan en los tipos Postgres
  `auth_code_kind` / `auth_link_kind` (creados en la migration `00000002` como
  `ENUM('register','login','password_reset')`). Columnas que los usan:
  `auth_email_codes.kind` + `auth_magic_links.kind`. **Verificado en la DB**:
  dev tiene **143 filas `kind='register'` (TODAS inactivas**: consumidas o
  expiradas, basura de tests E2E); **prod tiene 0 filas** (tablas vacias).
- **`verify/resend_code.py`** soporta flows `register` y `login` dinamicamente
  (dict `{'register': (REGISTER kinds), 'login': (LOGIN kinds)}`): hay que quitar
  la rama `register` y cambiar el default `claims.flow or 'register'` a `'login'`.
- **Harness E2E**: `tests/shared/auth_support.register_active_with_password`
  usa `register.start` + `register.verify-code` para crear un user active. Hay
  que reescribirlo al flujo login. Lo usan ~12 sitios en `tests/api/_flows.py`.
- **`tests/admin/conftest.create_active_user`** + `test_register_verify.py`
  usan register. `tests/api/_flows.py` tiene casos `register.start (success)`,
  `register.verify-code (success)`, `register.verify-magic-link (GET 302 + POST)`
  + errores -> convertir a `login`.
- **Frontend admin**: ya NO hay page `/register` ni `RegisterForm` (eliminados
  en admin-security-overview). Solo quedan `webauthn.register-*` (passkeys, MFA)
  que NO se tocan. La rule `admin.md` aun lista la page `/register` + `register`
  (3) en las actions -> limpiar.
- **Docs/rules/skills** con menciones a register: `auth-system.md`, `admin.md`,
  `e2e-testing.md`, skills `auth-system`/`admin-stack`, docs `auth-system/*.md`.

## 2. Solucion Propuesta

Eliminar el codigo `register` y convertir sus consumidores al flujo `login`.
Decisiones del usuario (confirmadas):

### Decisiones clave

- **Decision 1 — convertir los casos E2E register -> login** (no eliminarlos):
  `register.start` -> `login.check-email` + `login.start`; `register.verify-code`
  -> `login.verify-code` (kind `login`); `register.verify-magic-link` ->
  `login.verify-magic-link`. Mantiene la cobertura del alta + verify por
  code/magic-link.
- **Decision 2 — quitar tambien los enums `register` + migration** `00000007`:
  borrar las filas `kind='register'` (inactivas en dev, 0 en prod) y recrear los
  tipos `auth_code_kind`/`auth_link_kind` SIN `'register'` (Postgres no soporta
  `DROP VALUE`; se hace rename-old + create-new + alter-columns + drop-old).
- **Decision 3 — reescribir `register_active_with_password` ->
  `create_active_user_with_password`** usando solo `login` (check-email ->
  start -> seed code `kind='login'` -> verify-code -> set-password).
- **Decision 4 — NO tocar `webauthn.register-*`** (passkeys/MFA, no es la
  operation `register` de auth).
- **Decision 5 — la seccion "Flujo de entrada unico: register fusionado en
  login" de `auth-system.md` se MANTIENE** (documenta la historia), pero se
  ajusta para decir que la operation register YA NO EXISTE (antes decia "puede
  seguir presente como deuda legacy").

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given el Lambda `auth` tras el cambio, Then NO existe
  `controllers/register/`, `models/register.py`, ni la entrada `'register'` en
  `OPERATIONS`; un request `{operation:'register', action:'start'}` devuelve el
  error de operation desconocida (4xx).
- **AC-2**: Given `verify.resend-code` con un temp `flow='login'`, Then re-emite
  el code/link de kind `login`; el dict de flows ya no tiene la rama `register`
  y el default es `login`.
- **AC-3**: Given la migration `00000007` aplicada, Then los tipos
  `auth_code_kind` y `auth_link_kind` son `ENUM('login','password_reset')` (sin
  `register`), las columnas `auth_email_codes.kind`/`auth_magic_links.kind` usan
  el tipo nuevo, y NO quedan filas `kind='register'`. El `downgrade` re-agrega
  `register`.
- **AC-4**: Given `AuthCodeKind`/`AuthLinkKind` en Python, Then NO tienen el
  miembro `REGISTER`; importar el enum y referenciar `.REGISTER` falla.
- **AC-5**: Given `send_email/seeds/email_config.py`, Then NO existen las filas
  ni los templates `register-unified`/`register-code`/`register-magic-link`; los
  `login-*` se mantienen.
- **AC-6**: Given el harness E2E, Then `create_active_user_with_password` crea un
  user active con password usando SOLO `login` (sin tocar `register`); `_flows.py`
  prueba el alta + verify por `login.check-email`/`login.start`/
  `login.verify-code`/`login.verify-magic-link` (casos convertidos).
- **AC-7**: Given la suite unit del Lambda `auth`, Then pasa sin los tests de
  register (borrados) y con coverage >=80% per-file en los archivos tocados.
- **AC-8**: Given las rules/skills/docs de `.claude`, Then NO listan `register`
  como operation/action ni la page `/register`; las referencias historicas (la
  fusion) quedan como contexto, no como flujo vigente.
- **AC-9** (E2E post-deploy): el alta + login por code y por magic-link funciona
  en dev (E2E api + admin TODOS PASS); un `{operation:'register'}` da error.

## 4. Diagrama de Flujo (Antes y Despues)

### Antes
```
ALTA: register.start (Turnstile) -> register.verify-code|verify-magic-link -> active
LOGIN: login.check-email -> login.start -> login.verify-* -> tokens
(dos operations distintas para el alta vs el login)
```

### Despues
```
ALTA + LOGIN: login.check-email -> login.start (crea pending si no existe) ->
  login.verify-code|verify-magic-link (activa el pending) -> tokens
(operation `register` ELIMINADA; el login cubre alta + entrada)
```

## 5. Diagrama ER

```
Tipo Postgres auth_code_kind:  ENUM('register','login','password_reset')
                            -> ENUM('login','password_reset')          (00000007)
Tipo Postgres auth_link_kind:  ENUM('register','login','password_reset')
                            -> ENUM('login','password_reset')          (00000007)

Columnas afectadas (se re-apuntan al tipo nuevo):
  auth_email_codes.kind   (auth_code_kind)
  auth_magic_links.kind   (auth_link_kind)
Filas borradas: WHERE kind='register' (143 inactivas en dev, 0 en prod)
```

## 6. Tests Requeridos

### 6.B. Unit Tests — backend

- **Borrar** los 19 tests de register (`tests/unit/controllers/register/` +
  `tests/unit/models/test_register_*.py`).
- `tests/unit/controllers/verify/` — ajustar/crear el test de `resend-code` para
  el flow `login` (sin la rama register) [AC-2].
- `shared/tests/unit/.../test_*enums*` o similar — si hay un test que asserta los
  valores de `AuthCodeKind`/`AuthLinkKind`, actualizarlo a sin `register` [AC-4].
- Guard de la migration: el test de FK/registry del shared debe seguir verde tras
  recrear los tipos enum.

### 6.D. E2E (Python, contra dev)

- `tests/shared/auth_support.py`: `create_active_user_with_password` (flujo
  login) [AC-6].
- `tests/api/_flows.py`: casos register convertidos a login [AC-6]; el import +
  los ~12 call-sites usan el nombre nuevo.
- `tests/admin/conftest.py`: `create_active_user` al flujo login; renombrar
  `test_register_verify.py` -> `test_login_create_and_verify.py` (o ajustar sus
  3 tests al `login`).

### 6.C. Typecheck / lint

- `python devtools/run.py serverless lint-deps --lambda=auth`.
- `python -m compileall -q serverless/lambda/services/auth/core`.
- `ruff` sobre los tests Python tocados.

## 7. Archivos Afectados

### Eliminar — backend
- `serverless/lambda/services/auth/core/controllers/register/` (carpeta, 4
  archivos).
- `serverless/lambda/services/auth/core/models/register.py`.
- `serverless/lambda/services/auth/tests/unit/controllers/register/` (carpeta) +
  `serverless/lambda/services/auth/tests/unit/models/test_register_*.py` (5).
- `serverless/lambda/services/auth/events/register-*.json` (3).
- `serverless/lambda/services/send_email/seeds/templates/register-{unified,code,
  magic-link}.{html,txt}` (6).

### Modificar — backend
- `serverless/lambda/services/auth/core/settings/operations.py` — quita la
  entrada `'register'`.
- `serverless/lambda/services/auth/core/controllers/verify/resend_code.py` —
  quita la rama `register` del dict + default `login` [AC-2].
- `serverless/lambda/services/auth/core/handler.py` +
  `core/controllers/__init__.py` — docstrings sin `register`.
- `serverless/lambda/shared/db/models/auth/enums.py` — quita `REGISTER` de
  `AuthCodeKind` y `AuthLinkKind` [AC-4].
- `serverless/lambda/shared/db/models/auth/email_code.py` +
  `magic_link.py` — el `postgresql.ENUM(...)` de la columna ya no lista
  `register` (debe matchear el tipo nuevo).
- `serverless/lambda/services/auth/core/services/user_service.py` — el default
  `AuthCodeKind.REGISTER` de `invalidate_active_codes_and_links` pasa a `LOGIN`.
- `serverless/lambda/services/send_email/seeds/email_config.py` — quita las 3
  filas `register-*` + ajusta el comentario.

### Crear — backend
- `serverless/lambda/shared/db/alembic/versions/00000007_drop_register_kind.py`
  — borra filas `kind='register'` + recrea `auth_code_kind`/`auth_link_kind` sin
  `register` (rename-old/create-new/alter-columns/drop-old) [AC-3].
  - Verificar: probar upgrade+downgrade en un branch Neon ANTES de dev.

### Modificar — E2E / harness
- `tests/shared/auth_support.py` — `register_active_with_password` ->
  `create_active_user_with_password` (flujo login).
- `tests/api/_flows.py` — import + ~12 call-sites al nombre nuevo; casos register
  convertidos a login; `seed_code(kind='login')`.
- `tests/admin/conftest.py` — `create_active_user` al flujo login + docstrings.
- `tests/admin/test_register_verify.py` — renombrar/ajustar a `login`.
- `tests/admin/test_mfa.py`, `tests/shared/environment.py` — docstrings.

### Modificar — docs/rules/skills
- `.claude/rules/auth-system.md` — quita `register` de la tabla de operations +
  rate-limit; ajusta la seccion de la fusion (register YA NO EXISTE).
- `.claude/rules/admin.md` — quita la page `/register` + `register` (3) de las
  actions.
- `.claude/rules/e2e-testing.md` — quita `register` de la descripcion del modulo
  admin.
- `.claude/skills/auth-system/SKILL.md` + `admin-stack/SKILL.md` — quita
  `register` de las listas (mantiene `webauthn.register-*`).
- `.claude/docs/auth-system/*.md` — ajusta menciones (README, 02-flows,
  03-rate-limit-rules, 04-mfa, etc.).

### NO se tocan
- `admin/src/` — el frontend ya no tiene register (solo `webauthn.register-*`,
  que es MFA).
- `login-unified` / `login-code` / `login-magic-link` email kinds + templates.
- La operation `verify` (`set-password`, `resend-code`): `resend-code` se ajusta,
  `set-password` no cambia.

## 8. Descomposicion para Paralelizacion

Tres zonas con archivos disjuntos tras la base:
- **Base secuencial**: migration `00000007` + `enums.py` + `email_code.py`/
  `magic_link.py` (todo lo demas depende del enum sin register).
- **Zona A (backend)**: borrar controllers/models/tests register + operations +
  resend_code + email_config + templates.
- **Zona B (E2E)**: harness + `_flows.py` + admin conftest/tests.
- **Zona C (docs)**: rules + skills + docs.

A/B/C son worktree-safe pero el plan es secuencial inline (base -> A -> B -> C).
NO fan-out de tests (Bash/devtools). Ver `orchestration.md`.

## 9. Commits (rama `chore/remove-register` desde `dev`)

1. `docs(specs): plan eliminar la operation register`.
2. `feat(auth): migration 00000007 dropea el kind register de los enums` (base:
   migration + enums.py + email_code/magic_link).
3. `refactor(auth): elimina la operation register` (controllers + models +
   operations + resend_code + tests borrados + user_service default).
4. `chore(email): elimina los kinds register-* (filas + templates)`.
5. `test(e2e): el harness crea users active por el flujo login` (auth_support +
   _flows + admin conftest/tests).
6. `docs(rules): register eliminado de rules/skills/docs`.
7. `test(specs): verificacion E2E + limpieza del plan` (seccion 11 + `git rm -r
   docs/specs/remove-register/`).

1 PR `chore/remove-register -> dev`.

## 10. Paralelizacion con git worktrees

N/A — secuencial inline. La base (migration + enums) bloquea todo; el resto es
mecanico. La seccion 11 no se paraleliza.

## 11. Verificacion E2E iterativa (fase final)

**Parte A — refactor de tests**: barrido `rg -n "make_body\('register'|register\.start|kind='register'|AuthCodeKind.REGISTER|AuthLinkKind.REGISTER|controllers/register|models/register"` -> solo en la migration (downgrade) + comentarios historicos; `rg "register_active_with_password"` -> 0 (renombrado); ningun test importa el modulo register borrado.

**Parte B — bateria local (repo verde)**:
```
python -m compileall -q serverless/lambda/services/auth/core
python devtools/run.py serverless lint-deps --lambda=auth
python devtools/run.py serverless tests --type=coverage --lambda=auth   # >=80%
python devtools/run.py serverless tests --type=unit --shared            # enums
python devtools/run.py serverless tests --type=unit --lambda=send_email
# migration: upgrade+downgrade+upgrade en un branch Neon de prueba
```
Bucle: corregir -> re-ejecutar. Gate de push/PR: A+B verde.

**Parte C — despliegue REAL (post-merge, OBLIGATORIA — toca DB + Lambda)**:
1. Merge a `dev` dispara `deploy-backend.yml`: **migrate-db (00000007, dropea el
   kind register) ANTES de deploy auth**. Esperar y MIRAR cada job.
2. `serverless seed-email-config --stage=dev` (re-sincroniza email-config sin los
   register-*).
3. Verificar el enum en dev:
   `SELECT enum_range(NULL::auth_code_kind);` -> `{login,password_reset}`.
4. E2E api + admin contra dev:
   `e2e --module=api --lambda=auth --env=dev` + `e2e --module=admin --env=dev`
   -> TODOS PASS (el alta + login por code/magic-link via login).
5. Confirmar que `{operation:'register'}` da error de operation desconocida.

Bucle de correccion identico a la Parte B. El plan NO esta listo sin la Parte C
verde (migration aplicada + enum sin register + E2E verde en dev).

## 12. Validacion y Definition of Done

**Pre-implementacion**:
- [ ] AC-1..9 referenciados por tests.
- [ ] Rama `chore/remove-register` desde `dev`.
- [ ] Branch Neon de prueba para la migration `00000007`.

**Definition of Done**:
- [ ] Todos los AC con test/verificacion + Parte C (E2E real).
- [ ] Coverage per-file >=80% en los archivos backend tocados.
- [ ] lint-deps + compile + ruff limpios.
- [ ] CI verde; PR mergeado a `dev` con `--merge`.
- [ ] Parte C: migration 00000007 aplicada en dev (`enum_range` sin register);
      E2E api + admin verde; `{operation:'register'}` -> error.
- [ ] rules/skills/docs sin `register`; carpeta `docs/specs/remove-register/`
      eliminada en el ultimo commit.

## Riesgos / Edge-cases

- **Migration del enum (el mayor riesgo)**: Postgres NO tiene `DROP VALUE`. El
  patron es: `ALTER TYPE auth_code_kind RENAME TO auth_code_kind_old` ->
  `CREATE TYPE auth_code_kind AS ENUM('login','password_reset')` ->
  `ALTER TABLE auth_email_codes ALTER COLUMN kind TYPE auth_code_kind USING
  kind::text::auth_code_kind` -> `DROP TYPE auth_code_kind_old`. El `USING` falla
  si queda alguna fila `kind='register'` -> por eso el `DELETE` va PRIMERO. Idem
  para `auth_link_kind`/`auth_magic_links`. Probar upgrade+downgrade en branch
  Neon antes de dev. En prod (0 filas) es trivial; en dev borra 143 filas
  inactivas (basura de tests).
- **Default `--cov-fail-under=80` global**: borrar los tests de register baja el
  numerador y el denominador; verificar que el global sigue >=80 y los archivos
  tocados >=80 per-file.
- **`resend_code.py`**: el unico consumidor del dict de flows; tras quitar
  `register` el default debe ser `login` (un temp viejo `flow='register'` ya no
  existe porque register se elimino).
- **Datos historicos**: los 143 codes/links `kind='register'` en dev estan
  inactivos (consumidos/expirados) -> borrarlos no afecta ninguna sesion. El
  audit log (`auth_audit_log`) NO usa estos enums (es texto libre), no se toca.
- **Orden deploy**: la migration corre ANTES del deploy de auth en
  `deploy-backend.yml` (migrate-db -> deploy-lambdas), asi el Lambda nuevo (sin
  el enum register) nunca convive con el tipo viejo.
