# Plan: Turnstile solo en login.check-email + temp JWT precheck

> Mueve la validacion de Turnstile del flujo de login a UN solo punto
> (`login.check-email`, el primer boton "iniciar sesion"). `check-email`
> emite un temp JWT `flow='login'` step=0 que autoriza `login.start`; este
> ya NO valida Turnstile sino que EXIGE ese temp en `Authorization`.

## Cuando leer

| Tema | Archivo |
|------|---------|
| Contexto + solucion + AC | Este README (secciones 1-7) |
| Commits + paralelizacion + verificacion | Este README (secciones 9-11) |

Plan **Medium** (8-10 archivos): carpeta + README unico (condensado).

## 1. Contexto / Problema

El usuario reporto que el login del admin desplegado contra dev falla con:

```json
{"error": "Turnstile verify failed: ['timeout-or-duplicate']",
 "code": "CAPTCHA_INVALID"}
```

**Causa raiz (doble):**

1. **Backend**: el flujo de login valida Turnstile en DOS controllers
   independientes — `login.check-email` (`check_email.py:54-58`) Y
   `login.start` (`start.py:70-74`). Ambos llaman
   `verify_captcha_or_bypass`.
2. **Frontend**: el `LoginForm` del admin mantiene UN solo
   `turnstileToken` (`admin/src/features/auth/components/login-form.tsx:55`),
   lo adjunta a `check-email` (`:79`) donde Cloudflare lo QUEMA (single-use),
   y luego reusa el MISMO token en `login.start` (`:103` passwordless y
   `:114` con password) -> Cloudflare responde `timeout-or-duplicate`.

### Hallazgos de exploracion (cerrados, no reabrir)

- `cf_turnstile_response` ya es OPCIONAL en `LoginStartIn` y
  `LoginCheckEmailIn` (`models/login.py:28,45`, `Field(default='')`). La
  obligatoriedad la impone solo el `verify_captcha_or_bypass` del controller.
- La AUTO-BLACKLIST anti-solver (`shared/rate_limit/`) cuenta tokens por
  `(ip, endpoint, window)` SEPARADO. `login.check-email` ya alimenta su
  propio counter nativamente — al quitar Turnstile de `login.start`, la
  proteccion anti-solver se mantiene via `check-email`. Threshold real = 10
  tokens/60s, bloqueo 1h.
- Ningun test ASSERTea Turnstile en `login.start`: los 7 solo lo
  monkeypatchean a no-op. Hay que limpiar esos monkeypatch.
- `register.start` sigue vivo como endpoint publico de alta y CONSERVA
  Turnstile. NO se toca.
- El patron temp JWT (`issue_temp(flow, step)` + `verify(expected_flow)` +
  blacklist rolling) ya existe en `jwt_service.py`. `_Meta.authorization`
  (`models/_common.py:44`) ya expone el header `Authorization` (lo consume
  `require_active_user`).

## 2. Solucion Propuesta

Modelo de seguridad basado en **temp JWT** (decision del usuario): el
Turnstile se resuelve UNA vez al inicio; el resto del flujo se autoriza con
un temp JWT de vida corta + rate-limit per-IP.

### Decisiones clave

- **D-1**: `login.check-email` es el UNICO punto con Turnstile en el flujo
  de login. Emite un **temp JWT `flow='login'` step=0** en su respuesta
  (`temp_token`) SOLO en los casos que pueden continuar a `login.start`
  (email `exists+active` o `pending`). Para `exists:false` y `unavailable`
  NO emite temp (no hay flujo que continuar).
- **D-2**: `login.start` QUITA `verify_captcha_or_bypass`. En su lugar EXIGE
  el temp JWT `flow='login'` en el header `Authorization: Bearer <temp>`
  (via `_Meta.authorization`). Lo verifica, valida que el `sub` matchee el
  email del body, y lo blacklistea (rolling). Sin temp valido -> **401
  MISSING_PRECHECK**.
- **D-3**: el paso de password (login.start con password) y el passwordless
  (login.start que crea pending / re-emite email) van SIN Turnstile,
  protegidos por el temp JWT + rate-limit per-IP. El email se envia en
  `login.start` (no en check-email) cuando el user presiona "continuar".
- **D-4**: la auto-blacklist anti-solver pasa a alimentarse SOLO por
  `login.check-email` (que ya lo hace). `register.start` conserva su
  Turnstile + su propia auto-blacklist.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given `login.check-email` de un email active, When ejecuta con
  Turnstile OK, Then la respuesta incluye `temp_token` (temp JWT
  `flow='login'` step=0) ademas de `{exists, has_password}`.
- **AC-2**: Given `login.check-email` de un email pending, When ejecuta,
  Then la respuesta incluye `temp_token` + `{exists, pending, has_password}`.
- **AC-3**: Given `login.check-email` de un email inexistente
  (`exists:false`) o unavailable, When ejecuta, Then la respuesta NO incluye
  `temp_token`.
- **AC-4**: Given `login.start` SIN header `Authorization` (o con un JWT no
  `flow='login'`/expirado/revocado), When ejecuta, Then responde **401
  MISSING_PRECHECK** y NO toca Neon ni envia email.
- **AC-5**: Given `login.start` con un temp JWT `flow='login'` valido cuyo
  `sub` NO matchea el email del body, When ejecuta, Then responde **401
  MISSING_PRECHECK** (anti-cross-account).
- **AC-6**: Given `login.start` con el temp JWT valido del email correcto,
  When ejecuta, Then NO valida Turnstile, blacklistea el temp (rolling) y
  procede (passwordless: envia email; con password: valida argon2).
- **AC-7**: Given `login.start`, Then el controller ya NO llama
  `verify_captcha_or_bypass` (ni en validate ni en execute).
- **AC-8**: Given el frontend del admin, When `check-email` devuelve OK,
  Then guarda el `temp_token` y lo manda en `Authorization: Bearer` en
  `login.start`, SIN `cf_turnstile_response`.
- **AC-9** (E2E post-deploy): el login real en dev (curl) funciona:
  `check-email` con Turnstile -> `temp_token`; `login.start` con ese temp en
  `Authorization` -> 200, sin `timeout-or-duplicate`.

## 4. Diagrama de Flujo (Antes y Despues)

### Antes
```
[boton iniciar sesion] -> login.check-email {email, cf_turnstile_response}
                            verify_captcha (QUEMA el token single-use)
                            -> {exists, has_password}
[boton continuar / password] -> login.start {email, [password], cf_turnstile_response=<MISMO token>}
                            verify_captcha -> timeout-or-duplicate -> 403  ❌
```

### Despues
```
[boton iniciar sesion] -> login.check-email {email, cf_turnstile_response}
                            verify_captcha (OK)
                            -> {exists, has_password, temp_token}  (si continua)
[boton continuar / password] -> login.start {email, [password]}
                            Authorization: Bearer <temp_token>
                            verify_jwt(flow='login') + sub==email -> blacklist rolling
                            sin temp valido -> 401 MISSING_PRECHECK
                            -> procede (email / password)  ✅
```

## 5. Diagrama ER

N/A — no hay cambios en base de datos. El temp JWT es stateless (HS256); su
blacklist usa la tabla DDB `jwt-blacklist` existente (sin cambio de schema).

## 6. Tests Requeridos

### 6.B. Unit (Lambda auth, mirror en `tests/unit/controllers/login/`)

- `test_check_email_active_with_password.py` (MODIF): assertea
  `temp_token` en la respuesta [AC-1].
- `test_check_email_pending.py` (NUEVO): pending -> `temp_token` +
  `{exists, pending, has_password:false}` [AC-2].
- `test_check_email_not_found.py` (MODIF): `exists:false` -> SIN
  `temp_token` [AC-3].
- `test_check_email_unavailable.py` (NUEVO): disabled/locked -> SIN
  `temp_token` [AC-3].
- `test_login_start_missing_precheck_401.py` (NUEVO): sin Authorization ->
  401 MISSING_PRECHECK; no toca services [AC-4].
- `test_login_start_precheck_sub_mismatch_401.py` (NUEVO): temp valido,
  sub != email -> 401 [AC-5].
- Los 7 `test_login_start_*` existentes (MODIF): inyectar el temp JWT valido
  en `_meta.authorization` (via `_make_authed_event`) + mockear
  `jwt_svc.verify` para devolver claims con `sub` matcheando; quitar el
  monkeypatch de `verify_captcha_or_bypass` [AC-6/7].

### 6.C. Typecheck / lint
- `serverless lint-deps --lambda=auth` + `tests --type=coverage --lambda=auth`
  (>=80%).
- `pnpm --filter @portfolio/admin lint` + `typecheck` + `test` + `build`.

### 6.D. E2E (manual post-deploy)
- `WHEN check-email en dev con Turnstile THEN devuelve temp_token; WHEN
  login.start con ese temp en Authorization THEN 200 (sin timeout-or-
  duplicate) [AC-9]`.

## 7. Archivos Afectados

### Modificar — Backend (Lambda auth)
- `serverless/lambda/services/auth/core/controllers/login/check_email.py`
  — emite temp JWT `flow='login'` step=0 en los casos active/pending;
  agrega `temp_token` a la respuesta.
  - Verificar: `serverless tests --type=unit --lambda=auth`
- `serverless/lambda/services/auth/core/controllers/login/start.py`
  — quita `verify_captcha_or_bypass` (import + validate); agrega
  `_require_precheck()` que lee `meta.authorization`, verifica el temp
  `flow='login'`, valida `sub==email`, blacklistea rolling; 401
  MISSING_PRECHECK si falla.
  - Verificar: idem
- `serverless/lambda/services/auth/tests/unit/controllers/login/*` — ver 6.B.

### Crear — Backend (tests)
- `test_check_email_pending.py`, `test_check_email_unavailable.py`,
  `test_login_start_missing_precheck_401.py`,
  `test_login_start_precheck_sub_mismatch_401.py`.

### Modificar — Frontend (admin)
- `admin/src/features/auth/components/login-form.tsx` — guarda el
  `temp_token` de `check-email`; lo manda en `Authorization` a `login.start`;
  NO manda `cf_turnstile_response` en `login.start`.
- `admin/src/features/auth/api/auth-client.ts` (o donde viva el cliente) —
  el shape de `loginStart` acepta `temp_token` (Authorization) en vez de
  `cf_turnstile_response`.
  - Verificar: `pnpm --filter @portfolio/admin test` + `build`
- tests admin del LoginForm/auth-client (MODIF): el segundo paso manda el
  temp en Authorization, no el captcha.

### Modificar — Docs
- `.claude/rules/auth-system.md` — AC-12: "login.start" -> "login.check-email";
  la seccion de check-email documenta el temp JWT step=0.

### NO se tocan
- `register.start` (conserva Turnstile).
- El schema DDB / Neon.
- El resto del flujo (`verify-*`, `session.*`).

## 8. Descomposicion para Paralelizacion

N/A — secuencial inline. Backend (commits 2-3) y frontend (commit 4) tocan
arboles disjuntos pero el plan es Medium y se ejecuta en orden. Los tests
corren en Bash/devtools (NO fan-out de 1 agente por suite).

## 9. Commits (rama `fix/login-turnstile-precheck` desde `dev`)

1. `docs(specs): plan turnstile solo en login.check-email`
2. `feat(auth): check-email emite temp JWT precheck del login` — check_email.py
   + tests check-email. [AC-1/2/3]
3. `fix(auth): login.start exige el temp precheck en vez de turnstile` —
   start.py + tests login.start (limpia monkeypatch turnstile). [AC-4/5/6/7]
4. `fix(admin): login.start usa el temp de check-email, no el captcha` —
   login-form + auth-client + tests admin. [AC-8]
5. `docs(rules): turnstile del login pasa a check-email (AC-12)` —
   auth-system.md.
6. `test(specs): verificacion E2E + limpieza del plan` — seccion 11 +
   `git rm -r docs/specs/login-turnstile-precheck/`.

Un solo PR `fix/login-turnstile-precheck -> dev`.

## 10. Paralelizacion con git worktrees

N/A — secuencial.

## 11. Verificacion E2E iterativa (fase final)

**Parte A — refactor de tests**: `rg -n verify_captcha_or_bypass
serverless/lambda/services/auth/core/controllers/login/start.py` -> 0
resultados; ningun test de login.start monkeypatchea turnstile;
`rg -n cf_turnstile_response admin/src/features/auth` -> solo el paso
check-email.

**Parte B — bateria local (repo verde)**:
```
python devtools/run.py serverless lint-deps --lambda=auth
python devtools/run.py serverless tests --type=unit --lambda=auth
python devtools/run.py serverless tests --type=coverage --lambda=auth  # >=80%
pnpm --filter @portfolio/admin lint
pnpm --filter @portfolio/admin typecheck
pnpm --filter @portfolio/admin test
pnpm --filter @portfolio/admin build
```
Bucle: si algo falla -> corregir -> re-ejecutar. No declarar listo con rojo o
coverage <80%.

**Gate de cierre**: solo con Parte A+B verde. push + PR -> dev, 3 checks CI
verdes, merge `--merge`.

**Parte C — despliegue REAL (post-merge, OBLIGATORIA — toca el Lambda auth)**:
El merge dispara `deploy-backend.yml` (redeploya `auth`) + `deploy-apps.yml`
(admin). Tras esperar ambos runs:
1. **Backend**: curl real contra dev:
   - `login.check-email` con un Turnstile real (o el flujo del admin) ->
     confirmar `temp_token` en la respuesta.
   - `login.start` con ese temp en `Authorization: Bearer` -> 200 (NO
     `timeout-or-duplicate`) [AC-9].
   - `login.start` SIN Authorization -> 401 MISSING_PRECHECK.
   - E2E api module (`e2e --module=api --env=dev`) verde (el bypass token
     E2E sigue funcionando: si el E2E pega directo a login.start, ajustar el
     flow para que pase por check-email primero o mande un temp).
2. **Frontend**: abrir `admin.portfolio.dev.the-full-stack.com`, login con
   password real -> NO debe dar `timeout-or-duplicate`; el captcha se
   resuelve una sola vez.

Bucle de correccion identico a Parte B. No declarar listo sin Parte C verde.

## 12. Definition of Done

- [ ] AC-1..AC-9 cubiertos por test (unit) + Parte C (E2E).
- [ ] Coverage per-file >= 80% (auth + admin modificados).
- [ ] lint + typecheck + lint-deps limpios.
- [ ] Build admin OK.
- [ ] CI verde; PR mergeado con `--merge`.
- [ ] Parte C: check-email -> temp_token; login.start con temp -> 200;
      sin temp -> 401; login real del admin sin `timeout-or-duplicate`.
- [ ] Carpeta `docs/specs/login-turnstile-precheck/` eliminada en el ultimo
      commit.
