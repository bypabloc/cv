# Plan: rediseño del login a "lista de métodos required" + lazy auth + fix email

> Plan **Large**. Toca backend (Lambda `auth`) + frontend (admin Next.js) +
> template de email + la rule de seguridad. **1 PR** a `dev`.
> Carpeta destino: `docs/specs/login-mfa-list-redesign/`.

## 1. Contexto / Problema

El usuario probó el login del admin (`admin.portfolio.dev.the-full-stack.com`)
contra dev y reportó tres cosas:

1. **El flujo de login no es como debe ser.** Hoy es una **máquina lineal
   rígida**: email → (password | passwordless) → `/verify` (code | magic-link).
   El usuario quiere que, tras el primer paso, se muestre **la lista de métodos
   que él marcó como `required`** y se completen **en cualquier orden**, con los
   tokens emitidos SOLO cuando TODOS los required están satisfechos. Además la
   **contraseña debe ser un método más de la lista** (no un gate previo), y
   `login.start` **no debe exigir el email** en el body (se resuelve por el
   `sub` del JWT temporal).

2. **El "Verificando sesión" sobra.** El admin nunca debe verificar
   proactivamente si el JWT es válido: cada petición HTTP descubre su propio
   401 en el **cliente HTTP centralizado** y ahí se maneja (refresh → retry →
   logout). La verificación proactiva al arrancar es innecesaria.

3. **No llegó el email del magic-link.** (Diagnosticado: NO es bug de backend.)

### Hallazgos de exploración (cerrados, no reabrir)

- **El motor multi-factor YA EXISTE** en
  `serverless/lambda/services/auth/core/controllers/login/_mfa_login.py`:
  `decide_mfa_step(satisfied, required)` calcula los pendientes, emite un temp
  `login-mfa` step=2 con `flow=build_mfa_flow(satisfied)` (CSV de satisfechos)
  cuando faltan, y emite access+refresh cuando todos están. `parse_satisfied`
  los recupera del CSV. Hoy arranca tras `verify-password`, no en `check-email`.
- `required` ya está modelado: `auth_mfa_methods.required` (bool) +
  `auth_webauthn_credentials.required` (bool).
  `MfaMethodService.required_methods()` los lista. **NO incluye password ni
  passwordless.**
- `security.overview` ya devuelve el object rico por método
  (`{type,label,configured,enabled,required,preferred,detail}`). El front ya
  sabe renderizar esa forma. `password.required` está **hardcodeado a `False`**
  (`security/overview.py:158`).
- El `temp` JWT (`shared/auth/jwt.py`) tiene `extra='forbid'`; el progreso
  multi-factor se codifica en el claim `flow` (CSV), **NO** en un claim nuevo.
  El email NUNCA viaja en el JWT (solo `sub`=uuid del user, PK de `auth_users`).
- **Frontend**: hay **3 componentes muertos** (`login-totp-input.tsx`,
  `login-password-input.tsx`, `use-login-verify-password.ts`) que existen y
  nunca se montan. `/verify` no renderiza MFA. `admin/src/lib/api-client.ts` ES
  el cliente centralizado (`apiFetch`): inyecta Bearer, detecta 401 reactivo,
  `withRefreshMutex(performRefresh)` → retry, si falla `performLocalLogout`.
  `query-provider` NO reintenta 401/403/422.
- **Lo proactivo a eliminar**: `auth-guard.tsx` ("Verificando sesion..."),
  `use-auth-bootstrap.ts`, el timer proactivo + visibility-refresh de
  `use-auth-timer.ts`, el flag `bootstrapping` del store, el `recoverable` de
  `use-protected-route.ts`. NO hay `GET /auth/verify`: lo proactivo es el
  `doRefresh`-al-reload + el timer.
- **Email (verificado en dev real, NO es bug):** el template `login-unified.html`
  en S3 dev existe, renderiza el botón `{{ verify_url }}` + el link plano + el
  `{{ code }}`. La fila `email-config` apunta bien. Los logs de `send_email`
  muestran los `login-unified` enviados con `message_id` SES OK.
  `MAGIC_LINK_BASE_URL` correcto. Causa de "no llega el link": **client-side**
  (Gmail recorta/colapsa el mensaje; el botón queda bajo el corte). Bug menor
  aparte: el kind `password-changed` no tiene template → `EmailRejected` en
  logs.

## 2. Solución Propuesta

**Modelo unificado de "métodos de la lista".** Todo factor de login es un ítem
de una lista; cada ítem puede ser `required`. El login muestra los `required`,
el user los completa en cualquier orden, y los tokens salen cuando no quedan
pendientes. El motor `decide_mfa_step` ya hace esto — el trabajo es (a)
exponerlo desde `check-email`, (b) sumar **`password`** y **`passwordless`**
como métodos, (c) reescribir el front a un checklist, (d) lazy-auth, (e) el fix
de email.

### Decisiones clave (todas confirmadas con el usuario)

- **Decisión 1 — `check-email` revela `methods_required`.** Para un user
  `active`, `check-email` devuelve `methods_required` (lista de objetos con la
  config mínima de render por método). Acepta el trade-off anti-enumeration; se
  reescribe la regla en `auth-system.md`.
- **Decisión 2 — los métodos son ítems de una lista.** `password`,
  `passwordless` (email: code O magic-link), `totp`, `email_code`, `webauthn`.
  Se completan en cualquier orden; tokens cuando todos los `required` están.
- **Decisión 3 — `passwordless` es el método DEFAULT y siempre hay ≥1
  `required`.** Al registrarse por primera vez el user es passwordless
  (code/magic-link); si vuelve, vuelve a pedir passwordless porque es lo único
  disponible. `passwordless` es un método más, **`required` cuando es el único**.
  En el switch de settings que marca/desmarca `required`, **SIEMPRE** debe
  quedar al menos un `required` (passwordless cuenta como el fallback que no se
  puede quitar si es el único). Guard anti-lockout = "siempre ≥1 required".
- **Decisión 4 — password con flag `required` configurable.** Migration nueva
  en `auth_credentials.required` (default `true`), endpoint
  `security.password.set-required`, sujeto al guard "siempre ≥1 required".
- **Decisión 5 — `login.start` sin email.** El user se resuelve por
  `claims.sub` del precheck. El email solo va en el body en el **único** caso de
  alta (email nuevo, sub placeholder que no resuelve user). El email NUNCA en el
  JWT.
- **Decisión 6 — recovery: cualquier factor habilita recovery.** Sin distinción
  fuerte/débil. Simplifica `recovery-codes-consume` (cualquier step=2
  `login-mfa`).
- **Decisión 7 — lazy auth.** Eliminar la verificación proactiva del access
  (timer, visibility-refresh, "Verificando sesión", `bootstrapping`). Conservar
  UN refresh-en-reload (usa el `refresh_token`, NO valida el access) con un gate
  local efímero `rehydrating` (sin UI de carga). El 401 reactivo en
  `api-client.ts` es el único validador.
- **Decisión 8 — fix email client-side.** Reordenar el template
  `login-unified`/`register-unified` (link ARRIBA del code) + aligerar el HTML
  para que Gmail no lo recorte. Agregar el template faltante `password-changed`.

### Defaults aplicados (gaps menores del diseño, no requieren confirmación)

- Orden fijo de `methods_required`: `password`, `passwordless`, `totp`,
  `email_code`, `webauthn` (solo UX; el backend usa conjuntos).
- `/verify` se mantiene SOLO para alta/passwordless puro; el checklist vive
  inline en `login-form`.
- Detección del sub placeholder: `get_by_id(sub) is None` (el placeholder no
  existe en `auth_users`). El email del body se ignora si el sub resuelve user
  (anti-cross-account ya cubierto).
- `check-email` NO dispara el envío de `email_code` ni el challenge `webauthn`
  (evita email-bombing y quemar el challenge TTL 5min): se piden al expandir el
  método (`login.send-email-code`, `webauthn.login-options`).

## 3. Criterios de Aceptación (AC)

### Backend — `check-email` + métodos

- **AC-1**: Given un user `active` con `password` required + `totp` required,
  When `login.check-email`, Then la respuesta incluye `methods_required` con
  `[{type:'password',input:'password'}, {type:'totp',input:'code6'}]` (orden
  fijo) + `temp_token` + `has_password:true`.
- **AC-2**: Given un user `active` con SOLO `passwordless` required (recién
  registrado, sin más métodos), When `check-email`, Then `methods_required` =
  `[{type:'passwordless',input:'email'}]`.
- **AC-3**: Given un user `pending` o un email inexistente, When `check-email`,
  Then la respuesta NO incluye `methods_required` (alta/onboarding) pero sí
  `temp_token`.
- **AC-4**: Given un user `disabled/locked/deleted`, When `check-email`, Then
  `{exists:true, unavailable:true}` SIN `temp_token` ni `methods_required`.

### Backend — password como método

- **AC-5**: Given la migration `00000006` aplicada, Then `auth_credentials`
  tiene columna `required BOOLEAN NOT NULL DEFAULT true` y todo user con
  credentials queda `password` required.
- **AC-6**: Given `MfaMethodService.required_methods(user_id)`, When el user
  tiene `password` required, Then `'password'` aparece en la lista.
- **AC-7**: Given `security.password.set-required {required:false}` y el user no
  tiene otro método `required`, When ejecuta, Then 409
  `MUST_KEEP_ONE_REQUIRED` (no puede quedar sin ningún required).
- **AC-8**: Given `security.overview`, Then el entry `password` refleja el
  `required` REAL de `auth_credentials` (no hardcoded false).

### Backend — login.start + flujo de lista

- **AC-9**: Given un user `active` (resuelto por `claims.sub` del precheck),
  When `login.start` SIN email ni password en el body, Then devuelve un temp
  `login-mfa` step=2 + `methods` = los `required` pendientes + `step:2`.
- **AC-10**: Given un email nuevo (sub placeholder), When `login.start` con
  `email` en el body, Then crea el user `pending` y envía el email unificado
  (alta passwordless), `created:true`.
- **AC-11**: Given `login.verify-password {temp_token(step=2), password}`
  correcta, When ejecuta, Then suma `'password'` a satisfied y llama
  `decide_mfa_step`: si faltan required → temp nuevo + `methods`; si no →
  access+refresh.
- **AC-12**: Given `login.verify-totp` con un temp step=2, When el code es
  válido, Then suma `'totp'` a satisfied y delega en `decide_mfa_step`.
- **AC-13**: Given `login.send-email-code {temp_token(step=2)}`, When ejecuta,
  Then genera+envía el code y devuelve `{ok:true}`. `login.verify-code` con un
  temp step=2 suma `'email_code'` a satisfied vía `decide_mfa_step`.
- **AC-14**: Given un user `active` con `required` no vacío, When usa
  `verify-code`/`verify-magic-link` de ENTRADA (step=1), Then NO emite tokens
  directo: satisface `'passwordless'` y delega en `decide_mfa_step` (los otros
  required siguen pendientes).
- **AC-15**: Given un user `active` SIN required adicional (solo passwordless),
  When completa el code/magic-link, Then emite access+refresh (comportamiento
  passwordless actual preservado).
- **AC-16**: Given el último factor `required` satisfecho, When el caller
  resuelve `decide_mfa_step`, Then devuelve access+refresh con `family_id`
  nuevo + `mfa_complete:true`.
- **AC-17**: Given `mfa.recovery-codes-consume {temp_token(step=2)}` válido tras
  CUALQUIER método de la lista, When ejecuta, Then emite access+refresh
  (saltea los required restantes — decisión 6).

### Frontend — checklist + lazy auth

- **AC-18**: Given `check-email` con `methods_required` no vacío, When el front
  recibe la respuesta, Then renderiza un checklist con un input por método
  (cualquier orden) y un contador "X de N completados".
- **AC-19**: Given el user completa un método del checklist, When el backend
  responde `mfa_complete:false`, Then el front marca ese método satisfecho,
  reemplaza el `tempToken` (rolling) y actualiza los pendientes.
- **AC-20**: Given el último método completado, When el backend responde
  `mfa_complete:true`, Then `setTokens` + redirect al dashboard.
- **AC-21**: Given un reload (F5) con `access` null + `refresh` vigente, When
  monta `AuthGuard`, Then NO muestra "Verificando sesión", dispara UN refresh
  silencioso, y si OK renderiza el shell; si el refresh falla, redirige a
  `/login`.
- **AC-22**: Given una petición HTTP autenticada que devuelve 401, When la
  procesa `api-client.ts`, Then intenta UN refresh (mutex) y reintenta; si el
  refresh falla, logout local + redirect a `/login`. (El único validador.)
- **AC-23**: Given el código del front tras el cambio, Then NO existe
  `use-auth-bootstrap.ts`, ni el timer proactivo/visibility-refresh en
  `use-auth-timer.ts`, ni el flag `bootstrapping` en el store, ni el texto
  "Verificando sesión".

### Email

- **AC-24**: Given el template `login-unified` y `register-unified`, Then el
  botón/link del magic-link aparece ARRIBA del code y el HTML es liviano
  (sin riesgo de clipping de Gmail).
- **AC-25**: Given un envío con kind `password-changed`, When `send_email`
  resuelve el template, Then existe la fila `email-config` + el template (ya no
  `EmailRejected`).

## 4. Diagrama de Flujo (Antes y Después)

### Antes (login lineal rígido)
```
email + Turnstile -> check-email -> {exists,has_password}
  has_password -> [input password] -> login.start(email,password) -> /verify
  passwordless -> login.start(email) -> /verify (tabs code | magic-link)
  -> verify-code / callback -> tokens
(MFA nunca se renderiza; password es gate en login.start)
```

### Después (checklist de métodos required)
```
email + Turnstile -> check-email
  -> active: {has_password, temp_token, methods_required:[...]}
       -> login.start (sin email/password, precheck en Authorization)
            -> temp(step=2 login-mfa) + methods=pending
       -> CHECKLIST inline (cualquier orden):
            password    -> login.verify-password(temp,password)  --+
            passwordless-> send-email-code|magic-link -> verify   --+--> decide_mfa_step
            totp        -> login.verify-totp(temp,code)           --+        |
            email_code  -> login.send-email-code -> verify-code   --+        |
            webauthn    -> login-options -> login-verify          --+        v
       cada verify -> {mfa_complete:false, temp_token, methods:pending}  (rolling)
                   -> {access,refresh, mfa_complete:true}  cuando pending=[]
  -> pending/no-existe: alta passwordless -> /verify (sin cambios)
  -> unavailable: alerta
```

## 5. Diagrama ER

```
auth_credentials
  user_id         uuid    (FK auth_users.id, PK)
  password_hash   text
  algo            string
  password_set_at datetime
  last_change_at  datetime
  required (*)    boolean NOT NULL DEFAULT true   <- NUEVO (migration 00000006)

auth_mfa_methods          (sin cambios: ya tiene required boolean)
auth_webauthn_credentials (sin cambios: ya tiene required boolean)
```

`(*)` columna nueva. Sin tablas nuevas. La migration `00000006` es la única con
`op.add_column`; head actual = `00000005_mfa_required_flag.py`.

## 6. Tests Requeridos

### 6.B. Unit Tests — backend (mirror en `services/auth/tests/unit/`)

- `controllers/login/test_check_email_active_methods_required.py` — AC-1/2.
- `repositories/test_password_required.py` o ampliar — `required_methods`
  antepone password (AC-6).
- `controllers/security/test_password_set_required_*.py` — set-required OK + 409
  guard (AC-7), overview refleja real (AC-8).
- `controllers/login/test_login_start_no_email_*.py` — start sin email resuelve
  por sub (AC-9), alta con email (AC-10).
- `controllers/login/test_login_verify_password_step2_*.py` — verify-password
  suma a la lista (AC-11). **Reescribe** los `test_login_verify_password_*`
  actuales (cambian de step=1 a step=2).
- `controllers/login/test_login_verify_code_step2.py` +
  `test_login_send_email_code.py` — AC-13/14/15.
- `controllers/login/test_login_verify_*_with_required.py` — code/magic-link con
  required no emiten tokens directo (AC-14).
- Reescribir los `test_login_start_with_password_*` (password ya no va en start).

### 6.B. Unit Tests — frontend (mirror en `admin/tests/unit/`)

- `features/auth/components/login-form.test.tsx` — reescritura: checklist,
  progreso, completar en cualquier orden, redirect al completar (AC-18/19/20).
- `features/auth/components/login-checklist.test.tsx` (NUEVO si se extrae el
  checklist a su componente).
- `features/auth/components/auth-guard.test.tsx` — sin "Verificando sesión",
  rehydrate silencioso, redirect si refresh falla (AC-21).
- `lib/api-client.test.ts` — 401 → refresh → retry → logout (AC-22).
- Borrar/ajustar `use-auth-bootstrap.test.tsx`, los tests del timer proactivo.

### 6.C. Typecheck / lint

- `pnpm --filter @portfolio/admin typecheck` + `lint`.
- `python devtools/run.py serverless lint-deps --lambda=auth`.
- `python -m compileall -q serverless/lambda/services/auth/core`.

### 6.D. E2E (Python, contra dev — `tests/api/_flows.py` + `tests/admin/`)

- Reescribir `_run_login_with_password` (password ya no en start; ahora 2-step
  vía checklist).
- `WHEN login de un user con password+totp required THEN completar ambos (orden
  cualquiera) THEN tokens [AC-9..AC-16]`.
- `WHEN reload del admin con sesión vigente THEN no rebota a login (rehydrate)
  [AC-21]`.

## 7. Archivos Afectados

### Crear — backend
- `serverless/lambda/shared/db/alembic/versions/00000006_password_required_flag.py`
  — `add_column auth_credentials.required` (default true).
  - Verificar: `serverless run --lambda=db --event=events/migrate.json` (branch
    Neon de prueba) + `current.json`.
- `serverless/lambda/services/auth/core/controllers/security/password_set_required.py`
  — controller `security.password.set-required` + modelo Pydantic.
- `serverless/lambda/services/auth/core/controllers/login/send_email_code.py`
  — `login.send-email-code` (genera+envía el code dentro del flujo step=2).

### Modificar — backend
- `serverless/lambda/shared/db/models/auth/credentials.py` — columna `required`.
- `serverless/lambda/services/auth/core/services/mfa_method_service.py` —
  `required_methods()` antepone `password`/`passwordless`; nuevo
  `required_methods_config()` (mapa a `{type,input,dispatch_action,sent}`).
  - Verificar: `serverless tests --type=unit --lambda=auth`.
- `serverless/lambda/services/auth/core/controllers/login/check_email.py` — rama
  `active` añade `methods_required` (AC-1/2).
- `serverless/lambda/services/auth/core/controllers/login/start.py` — quita el
  gate de password; `email` opcional; resuelve user por `claims.sub`; emite temp
  `login-mfa` step=2 con `methods=required_methods()` (AC-9/10).
- `serverless/lambda/services/auth/core/controllers/login/verify_password.py` —
  step=2, suma `'password'`, `decide_mfa_step` (AC-11).
- `serverless/lambda/services/auth/core/controllers/login/verify_code.py` +
  `verify_magic_link.py` — ramificar por `claims.step`: step=1 entry
  (passwordless puro si sin required) vs step=2 suma `'email_code'`/
  `'passwordless'` a `decide_mfa_step` (AC-13/14/15).
- `serverless/lambda/services/auth/core/controllers/security/overview.py` —
  `password.required` real (AC-8).
- `serverless/lambda/services/auth/core/models/login.py` — `LoginStartIn.email`
  opcional, quita `password` de start; ajusta `LoginVerifyPasswordIn` a step=2.
- `serverless/lambda/shared/db/repositories/auth_mfa.py` +
  `auth_users.py`/`auth.py` — `set_password_required`, `get_password_required`.
- `serverless/lambda/services/auth/core/settings/operations.py` — registrar las
  actions nuevas (descubrimiento por convención; verificar que el controller
  exista).

### Modificar — email
- `serverless/lambda/services/send_email/seeds/templates/login-unified.html` +
  `.txt` + `register-unified.html` + `.txt` — link ARRIBA del code, HTML liviano
  (AC-24).
- `serverless/lambda/services/send_email/seeds/email_config.py` +
  `templates/password-changed.html`/`.txt` — agregar el kind faltante (AC-25).
  - Verificar (post-deploy): `serverless seed-email-config --stage=dev`.

### Modificar — frontend (admin)
- `admin/src/features/auth/components/login-form.tsx` — reescritura a la máquina
  `LoginMachine` (email | create | passwordless | checklist | unavailable).
- `admin/src/features/auth/components/login-checklist.tsx` (NUEVO) — el checklist
  de métodos (orquesta los inputs por método, trackea el `tempToken` rolling).
- `admin/src/features/auth/components/{login-totp-input,login-password-input}.tsx`
  — parametrizar `tempToken`/`onResult` por props (revivir los muertos).
- `admin/src/features/auth/components/verify-code-input.tsx` — variante step=2
  (prop `mode`).
- `admin/src/features/auth/api/auth-client.ts` — `loginStart` sin email/password
  en el caso checklist; `loginSendEmailCode`; tipos.
- `admin/src/types/api.ts` — `CheckEmailResponse.methods_required`,
  `TempTokenResponse`.
- `admin/src/features/auth/store/use-auth-store.ts` — quitar `bootstrapping`,
  `setBootstrapping`.
- `admin/src/features/auth/components/auth-guard.tsx` — sin "Verificando
  sesión", `useSessionRehydrate` + gate local `rehydrating`.
- `admin/src/features/auth/hooks/use-protected-route.ts` — quitar `recoverable`
  + `bootstrapping`.
- `admin/src/features/auth/hooks/use-session-rehydrate.ts` (NUEVO) — UN refresh
  en reload (reusa `performRefresh` de `api-client.ts`).

### Eliminar — frontend
- `admin/src/features/auth/hooks/use-auth-bootstrap.ts`.
- `admin/src/features/auth/hooks/use-auth-timer.ts` (o reducir al rehydrate).

### Modificar — docs/rule
- `.claude/rules/auth-system.md` — reescribir la sección anti-enumeration de
  `check-email` (ahora revela `methods_required`); documentar el modelo de lista
  de métodos, `passwordless`/`password` como métodos required, el guard "≥1
  required", el flag `auth_credentials.required`, recovery sin fuerte/débil.

### NO se tocan
- `_mfa_login.py` (`decide_mfa_step` ya hace lo necesario; solo se le pasan las
  listas nuevas).
- `admin/src/lib/api-client.ts` (el 401 reactivo ya está; solo se reusa
  `performRefresh` desde el rehydrate).
- `webauthn/login_options.py` + `login_verify.py` (ya entran a `decide_mfa_step`
  con `satisfied=['webauthn']`).

## 8. Descomposición para Paralelización

El plan tiene 3 zonas con archivos **disjuntos** → worktree-safe tras la base
secuencial:

- **Base secuencial (NO paralelizable)**: migration `00000006` +
  `mfa_method_service.required_methods()` + `credentials.py` (todo lo demás
  depende de que `required_methods` incluya password/passwordless).
- **Zona A (backend login)**: `check_email`, `start`, `verify_*`,
  `send_email_code`, `security/password_set_required`, `overview`, `models`,
  `operations` + sus tests. Disjunta de la zona C.
- **Zona B (email)**: templates + `email_config`. Totalmente aislada.
- **Zona C (frontend)**: `login-form`, `login-checklist`, inputs, `auth-client`,
  `types`, store, `auth-guard`, hooks. Disjunta de A salvo el contrato (los
  shapes que A define).

Por el acoplamiento de contrato (C consume el shape de A), el orden es: base → A
→ (B ∥ C). NO fan-out de tests (Bash/devtools). Ver `orchestration.md` (cap ≤4
agentes, 1 workflow).

## 9. Commits (rama `feature/login-mfa-list-redesign` desde `dev`)

1. `docs(specs): plan rediseño login lista de métodos + lazy auth`.
2. `feat(auth): columna auth_credentials.required + migration 00000006` (base).
3. `feat(auth): required_methods incluye password y passwordless` (base).
4. `feat(auth): check-email devuelve methods_required` (AC-1..4).
5. `feat(auth): login.start sin email + password como método de la lista`
   (AC-9..12, reescribe verify-password a step=2).
6. `feat(auth): email_code/passwordless entran a la lista de required`
   (AC-13..16, send-email-code, verify-code/magic-link ramificados).
7. `feat(auth): security.password.set-required + guard ≥1 required` (AC-5..8).
8. `fix(email): link arriba del code + template password-changed` (AC-24/25).
9. `feat(admin): login checklist de métodos required` (AC-18..20).
10. `refactor(admin): lazy auth — elimina verificación proactiva del JWT`
    (AC-21..23).
11. `docs(rules): auth-system refleja el modelo de lista de métodos`.
12. `test(specs): verificación E2E + limpieza del plan` (sección 11 +
    `git rm -r docs/specs/login-mfa-list-redesign/`).

Cada commit deja el repo verde. 1 PR `feature/login-mfa-list-redesign -> dev`.

## 10. Paralelización con git worktrees

Tras la base secuencial (commits 2-3), las zonas A (commits 4-7), B (commit 8) y
C (commits 9-10) tocan archivos disjuntos → worktree-safe. En la práctica, por
el contrato A↔C, se ejecuta: base → A → (B ∥ C) → docs → verificación. La
sección 11 NO se paraleliza. `isolation:'worktree'` solo si se lanzan agentes
que mutan en paralelo (cap ≤4).

## 11. Verificación E2E iterativa (fase final)

**Parte A — refactor de tests**: ningún test asume password en `login.start`;
ningún test asume el flujo lineal del front; barrido `rg` de
`bootstrapping`/"Verificando sesion"/`use-auth-timer` → 0 resultados;
`_run_login_with_password` reescrito.

**Parte B — batería local (repo verde)**:
```
pnpm --filter @portfolio/admin lint && typecheck && test && build
python -m compileall -q serverless/lambda/services/auth/core
python devtools/run.py serverless lint-deps --lambda=auth
python devtools/run.py serverless tests --type=unit --lambda=auth
python devtools/run.py serverless tests --type=coverage --lambda=auth   # >=80%
python devtools/run.py serverless tests --type=unit --shared
```
Bucle: corregir → re-ejecutar hasta verde. Gate de push/PR: solo con A+B verde.

**Parte C — despliegue REAL (post-merge, OBLIGATORIA — toca DB + Lambda +
apps)**:
1. Merge a `dev` dispara `deploy-backend.yml` (migrate-db → deploy auth) +
   `deploy-apps.yml` (admin). Esperar y MIRAR ambos runs (cada job).
2. `serverless seed-email-config --stage=dev` (sube templates nuevos).
3. E2E api contra dev:
   `python devtools/run.py e2e --module=api --lambda=auth --env=dev --aws-profile=tfs-dev`.
4. `curl` real: `login.check-email` de un user con required → confirma
   `methods_required`. Login completo de un user con password+totp.
5. Admin: abrir `admin.portfolio.dev.the-full-stack.com`, login con checklist,
   **recargar** → no rebota a login, sin "Verificando sesión".
6. Enviar un `login.start` real → confirmar el email con el link ARRIBA del code.

Bucle de corrección idéntico a la Parte B. El plan NO está "listo" sin la Parte
C verde (E2E api + admin real + email real).

## 12. Validación y Definition of Done

**Pre-implementación**:
- [ ] AC-1..25 referenciados por tests.
- [ ] Rama `feature/login-mfa-list-redesign` creada desde `dev`.
- [ ] Branch Neon de prueba para la migration `00000006`.

**Definition of Done**:
- [ ] Todos los AC con test que pasa (unit) + Parte C (E2E real).
- [ ] Coverage per-file ≥80% en backend `auth` + admin modificados.
- [ ] Typecheck + lint + lint-deps limpios.
- [ ] Build estático del admin OK.
- [ ] CI verde; PR mergeado a `dev` con `--merge`.
- [ ] Parte C: `methods_required` real en dev; login con checklist completo;
      reload sin "Verificando sesión"; email con link arriba del code.
- [ ] `auth-system.md` reescrita; carpeta `docs/specs/login-mfa-list-redesign/`
      eliminada en el último commit.

## Riesgos / Edge-cases

- **Migration en prod (`00000006`)**: `default true` preserva el comportamiento
  (todo user con password sigue exigiéndola). Reversible (downgrade dropea
  columna). Probar upgrade+downgrade en branch Neon antes de dev.
- **Guard "≥1 required"**: el front (`security.overview`) debe mostrar el 409 con
  copy claro. El passwordless es el fallback que nunca se quita si es el único.
- **`tempToken` rolling en el checklist**: cada verify emite un temp nuevo y
  blacklistea el anterior; el front DEBE reemplazarlo o el siguiente verify da
  `TOKEN_BLACKLISTED`. Punto crítico de implementación.
- **code/magic-link de entrada vs lista**: un user `active` con required NO debe
  saltarse los required vía magic-link. La ramificación por `claims.step` +
  `required_methods()` lo cubre (AC-14).
- **F5 sin gate**: sin `bootstrapping`, `useProtectedRoute` redirige antes de que
  el rehydrate async complete. El gate local efímero `rehydrating` (1 boolean,
  sin UI) lo cubre sin reintroducir la maquinaria proactiva.
- **Email Gmail clipping**: reordenar + aligerar reduce el riesgo; no se puede
  garantizar 100% en todos los clientes (es comportamiento del cliente).
