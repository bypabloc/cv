# 11 — Verificacion E2E iterativa (gate del PR)

[< 10-paralelizacion-worktrees](10-paralelizacion-worktrees.md) | [Volver al README](README.md)

## Aclaracion

Fase 21 — la **ultima** del plan. SIEMPRE es el ultimo commit del PR.
Dos partes:

- **Parte A — refactor de tests**: confirmar que ningun test viejo
  referencia codigo eliminado; tests nuevos en ruta correcta; barrido
  global con `rg -l` para verificar.
- **Parte B — bateria de comandos reales**: ejecutar la verificacion
  completa de punta a punta con el codigo final. Bucle "no parar hasta
  que funcione": ejecutar → si falla → diagnosticar → corregir →
  re-ejecutar la suite → repetir.

NO se marca completa con un comando fallando, un test rojo o coverage
< 80%.

## Parte A — Refactor de tests + barrido

### A.1 — Verifica que NO hay tests viejos huerfanos

```bash
# Listar tests que referencien archivos eliminados o renombrados.
# (En este plan no hay archivos eliminados — todo es nuevo.)
# OJO WSL2: `find` esta aliasado a `fd` y la sintaxis GNU falla silenciosamente.
# Usar `rg --files` (mejor disponibilidad cross-platform) o `fd` directo.
rg --files admin/tests/ -g '*.test.*'
```

### A.2 — Verifica que TODOS los tests nuevos estan en la ruta correcta

```bash
# Mirror: cada src/<X>/<Y>.ts(x) debe tener tests/unit/<X>/<Y>.test.ts(x).
# Usamos `rg --files` con globs (-g) en vez de `find` (aliasado a `fd` en WSL2).
mkdir -p tmp
rg --files admin/src/ \
  -g '*.ts' -g '*.tsx' \
  -g '!**/components/ui/**' \
  -g '!**/app/**' \
  -g '!**/index.ts' \
  -g '!**/*.d.ts' \
  | sort > tmp/admin-sources.txt

rg --files admin/tests/unit/ -g '*.test.*' | sort > tmp/admin-tests.txt

# Comparar: cada source deberia tener test correspondiente (revision manual
# con `diff` o script python en tmp/).
```

### A.3 — Barrido global de referencias eliminadas

```bash
# Verifica que no quedan imports a paths que no existen
# (en este plan no aplica fuerte porque todo es nuevo)
pnpm --filter @portfolio/admin typecheck  # cualquier import roto sale aqui
```

### A.4 — Verifica que las routes del admin estan en `routes.ts`

```bash
# Las pages no deberian hardcodear paths — todo via ROUTES.admin.*
# Esto es review humano, pero un grep ayuda
rg -l "href=\"/(settings|sessions|users|cv)" admin/src/  # debe estar SOLO en src/lib/routes.ts o tests
```

### A.5 — Verifica que `process.env.NEXT_PUBLIC_*` solo se usa en `env.ts`

```bash
# Todos los componentes deben importar `env` de @/lib/env (validacion Zod).
# NUNCA process.env.* directo. `tsx` NO es un type built-in de rg —
# `rg --type ts` ya cubre .ts y .tsx via la definicion built-in `typescript`.
# Confirmar con: rg --type-list | rg ^typescript
rg "process\.env\." admin/src/ --type ts
# Resultado esperado: SOLO src/lib/env.ts. vitest.config.ts vive fuera de admin/src/.
```

## Parte B — Bateria completa de comandos

Ejecutar EN ORDEN. Si alguno falla, **DETENER**, diagnosticar,
corregir, RE-EJECUTAR LA SUITE COMPLETA. NO continuar hasta que todo
pase.

### B.1 — Sintaxis + linting

```bash
pnpm --filter @portfolio/admin lint
# Esperado: 0 errors, 0 warnings
```

### B.2 — Typecheck

```bash
pnpm --filter @portfolio/admin typecheck
# Esperado: sin errores
```

### B.3 — Unit tests

```bash
pnpm --filter @portfolio/admin test
# Esperado: TODOS verdes
```

### B.4 — Coverage >= 80% per-file

```bash
pnpm --filter @portfolio/admin test:coverage
# Esperado: report imprime per-file coverage
# Si alguno < 80% (excluyendo components/ui/, app/, types/, env.d.ts, index.ts): FAIL
```

### B.5 — Build estatico

```bash
pnpm --filter @portfolio/admin build
# Esperado:
# - Sin errores
# - admin/out/index.html existe
# - admin/out/404.html existe
# - admin/out/_next/static/chunks/ existe
# - admin/out/_redirects existe
# - admin/out/_headers existe
ls -lah admin/out/index.html admin/out/_redirects admin/out/_headers
```

### B.6 — Preview manual (smoke test golden path)

```bash
# Servir el build estatico
pnpm --filter @portfolio/admin preview &
PREVIEW_PID=$!
sleep 3

# Status codes esperados
curl -sI http://localhost:3000/ | head -1 | grep -q "200" || echo "FAIL /"
curl -sI http://localhost:3000/login/ | head -1 | grep -q "200" || echo "FAIL /login"
curl -sI http://localhost:3000/register/ | head -1 | grep -q "200" || echo "FAIL /register"

# Smoke: HTML contiene el bundle Next.js
curl -s http://localhost:3000/ | grep -q "_next/static" || echo "FAIL bundle"

kill $PREVIEW_PID
```

### B.7 — Preview con MSW (golden path manual)

```bash
NEXT_PUBLIC_USE_MSW=true pnpm --filter @portfolio/admin dev &
DEV_PID=$!
sleep 5

# Manual: abrir http://localhost:3000 en browser, probar el admin (gestion):
# 1. /login → email user@test.com + Turnstile success → submit
# 2. /verify → input code "12345678" → submit
# 3. Redirect a la raiz del area protegida → ver el app shell (sidebar + header)
# 4. Navegar a /settings → ver profile-form + seguridad (MFA setup, WebAuthn, recovery)
# 5. Navegar a /sessions → ver lista de sesiones de la cuenta + boton revocar
# 6. Navegar a /users (si user admin) → ver users-table + acciones
# 7. Click logout → redirect a /login
# 8. Abrir 2da tab logueada, logout en 1 → 2da tab tambien logout (BroadcastChannel)
# NOTA: las pantallas de metricas (TimeseriesChart, MetricCards, ...) se verifican
# en b-analytics-api, no aqui.

kill $DEV_PID
```

### B.8 — Verify devtools cloudflare_setup config

```bash
# El subcomando `status` NO existe en cloudflare_setup. Las fases validas
# son: projects, domains, triggers, all. Para verificar que el
# project del admin esta declarado correctamente en config.py,
# re-aplicar la fase projects con --dry-run (idempotente, sin side
# effects si el config matchea el remoto):
export CLOUDFLARE_API_TOKEN=$(grep -m1 '^CLOUDFLARE_API_TOKEN=' docker/env/dev-cli/.dev | cut -d= -f2-)
export ACCOUNT_ID=$(grep -m1 '^CLOUDFLARE_ACCOUNT_ID=' docker/env/dev-cli/.dev | cut -d= -f2-)
python devtools/run.py cloudflare_setup projects --env=dev --dry-run
# Esperado: lista los 7 projects (6 Astro + admin) con build_config + env_vars
# diff. Sin --dry-run aplicaria los cambios al remoto.

# Alternativa: leer la config declarada
python -c "from devtools.cloudflare_setup.config import APPS, app_for; print(app_for('admin'))"
# Esperado: AppConfig(name='admin', root_dir='admin', app_type='nextjs', build_output_dir='out', ...)
```

### B.9 — Verify devtools sync_secrets dry-run

```bash
python devtools/run.py sync_secrets --env=dev --category=client --dry-run
# Esperado: las 6 keys NEXT_PUBLIC_* del admin muestran su status (CREATE/PUSH/SKIP):
#   - NEXT_PUBLIC_API_ENDPOINT
#   - NEXT_PUBLIC_TURNSTILE_SITEKEY
#   - NEXT_PUBLIC_ADMIN_URL
#   - NEXT_PUBLIC_AUTH_REFRESH_LEAD_MS
#   - NEXT_PUBLIC_FEATURE_MFA               (toggle de UI opcional; el backend MFA ya esta desplegado, NO es un gate de "pending")
#   - NEXT_PUBLIC_WEBAUTHN_RP_ID            (config base, hostname admin.portfolio.{env}.the-full-stack.com, requerido por la API WebAuthn)
```

### B.10 — GH Actions local (act + skill github-actions)

```bash
# Validar yaml + dry-run con act
act -W .github/workflows/ci.yml --container-architecture linux/amd64 --dry-run
act -W .github/workflows/deploy-apps.yml --container-architecture linux/amd64 --dry-run
# Esperado: sin syntax errors
```

### B.11 — E2E Playwright (con stack local arriba)

```bash
# Levantar stack local (nginx + apps)
python devtools/run.py docker up --env=local

# Esperar ~30s a que los servicios respondan
sleep 30

# Correr E2E del admin
python devtools/run.py test_runner --module=feature --type=feature --env=local

# Esperado: 7 specs en tests/feature/admin/ verdes:
# - 01-login-magic-link.spec.ts
# - 02-register-verify-code.spec.ts
# - 03-callback-fragment-hash.spec.ts
# - 04-auth-guard-redirect.spec.ts
# - 05-logout-multi-tab.spec.ts
# - 06-settings-security.spec.ts
# - 07-sessions-mgmt-revoke.spec.ts
# NOTA: los specs de navegacion y tablas de METRICAS viven en b-analytics-api

# Bajar stack
python devtools/run.py docker down --env=local
```

### B.12 — Smoke deploy real a dev

Solo hacer **post-merge a `dev`** (CI deploya automaticamente):

```bash
# Tras merge, esperar ~3 min a que deploy-apps.yml termine
gh run watch  # con la flag de seleccionar el run

# Verificar URL responde
curl -sI https://admin.portfolio.dev.the-full-stack.com/ | head -3
# Esperado: HTTP/2 200

# Verificar bundle Next.js sirve
curl -s https://admin.portfolio.dev.the-full-stack.com/ | grep -q "_next/static"

# Verificar CSP header se sirve
curl -sI https://admin.portfolio.dev.the-full-stack.com/ | grep -i "content-security-policy"
# Esperado: header con script-src 'self' 'wasm-unsafe-eval'; etc.

# Verificar SSL OK
openssl s_client -connect admin.portfolio.dev.the-full-stack.com:443 -showcerts < /dev/null 2>&1 \
  | grep -E "subject|issuer" | head -4

# Verificar el flow manual real: abrir admin.portfolio.dev en browser
# Los Lambdas `auth` y `users` ya estan desplegados: el login real (magic-link,
# code, password, MFA, WebAuthn) + la gestion (perfil, settings de seguridad,
# sesiones de la cuenta, users-admin) funcionan contra el backend. La UI de
# metricas (y su data analitica) NO es parte de este plan: vive en b-analytics-api.
```

### B.13 — Limpieza del plan (ULTIMO PASO)

```bash
# Solo si TODO lo anterior (B.1-B.12) paso en verde:
git rm -r docs/specs/a-admin/
git commit -m "chore(admin): elimina docs/specs/a-admin/ tras mergear el plan

- Plan Admin SPA (gestion: auth + app shell + settings + sessions-mgmt + users-admin + placeholder CV) completado y mergeado a dev
- El conocimiento permanente queda en:
  - .claude/rules/admin.md
  - .claude/skills/admin-stack/SKILL.md
  - .claude/docs/admin/ (7 archivos)
- Trazabilidad del plan en git log + PR

Cumple TODOS los AC del plan a-admin. Verificacion completa en seccion 11 del plan."

# Push final
git push origin feature/admin-frontend
```

## Bucle de correccion

Si algun paso (B.1 - B.12) falla:

1. **Diagnosticar**: leer el output completo del fail. Identificar root
   cause.
2. **Corregir**: editar el codigo (sin atajos, sin --no-verify).
3. **Verify incremental**: ejecutar SOLO el paso que fallo + re-correr
   tests del scope corregido.
4. **Re-ejecutar suite**: empezar de nuevo desde B.1. NO confiar en
   verde parcial.
5. **Repetir** hasta que B.1 - B.12 pasen todos.

## Regla de cierre

**SIEMPRE** el `git push` final + creacion del PR pasa SOLO cuando
B.1 - B.12 estan en verde. NUNCA con un test rojo, coverage < 80%, o
build roto.

El PR `feature/admin-frontend -> dev` se crea con:

```bash
gh pr create --base dev --head feature/admin-frontend \
  --title "feat(admin): admin SPA Next.js 16.2.6 + React 19.2.6 + shadcn + Tanstack" \
  --body "$(cat <<'EOF'
## Problema

El portfolio no tiene un panel de administracion: gestionar la cuenta
(perfil, seguridad MFA/WebAuthn, sesiones activas) y a otros usuarios
(admin) solo se hace por psql, consola Neon o invocando los Lambdas a
mano. Falta tambien el app shell que albergara la UI de metricas (plan
b-analytics-api).

## Solucion

Admin SPA estatico Next.js 16.2.6 + React 19.2.6 (compiler stable) +
shadcn/ui + Tanstack Query v5 + Zustand 5 (persist en localStorage),
deployado a Cloudflare Pages en
admin.portfolio.{dev|stage|prod}.the-full-stack.com.

Scope de este plan (a-admin): SOLO el frontend de gestion. La UI de
metricas y el Lambda `analytics` viven en el plan b-analytics-api.

Estructura Hybrid Atomic Design:
- src/components/ui/ — primitivos genericos (shadcn + custom)
- src/features/<X>/ — features de gestion: auth, admin-shell (app shell),
  settings (perfil + seguridad), sessions-mgmt (sesiones de la cuenta),
  users-admin (gestion de otros usuarios), cv (placeholder). Las features
  de metricas se agregan en b-analytics-api
- src/app/ — Next App Router con groups (auth) y (admin)

Auth contra el Lambda `auth` (desplegado en dev/stage/prod, 26 actions:
register / login / verify / session / mfa / webauthn — ver
serverless/lambda/services/auth/, .claude/rules/auth-system.md y
.claude/docs/auth-system/) + gestion contra el Lambda `users`
(desplegado, 15 actions: profile / status / admin). Tokens en localStorage
(accessToken en memoria Zustand, refreshToken + refreshExpiry + user
persistidos). NO HttpOnly cookies cross-origin — el admin vive en
admin.portfolio.{env}.the-full-stack.com y el API en api.portfolio.{env},
una cookie HttpOnly tendria que ser SameSite=None + Domain=.the-full-stack.com
y abrir CSRF en los 6 niches publicos. Defensa primaria contra XSS: CSP
estricta sin unsafe-inline/unsafe-eval + SRI en third-party + access JWT
corto (15 min) + family_id refresh rotation backend (RFC 9700). Mutex
client-side garantiza 1 sola /session/refresh in-flight. Magic link
callback con fragment hash + BroadcastChannel multi-tab sync.

Los Lambdas `auth` y `users` ya estan desplegados, asi que auth (login,
register, MFA, WebAuthn, refresh) y gestion (perfil, settings de
seguridad, sesiones, users-admin) corren contra el backend real. Unico
gap conocido: NO existe una action para que un user autenticado cambie su
password (auth.verify.set-password usa temp_token, no access JWT; users
no tiene change-password). La UI de cambio de password queda marcada como
bloqueada por esa dependencia de backend y se mockea con MSW
(users.profile.change-password sugerido) hasta que exista.

## Como probar

Local con MSW (sin backend live):
```
NEXT_PUBLIC_USE_MSW=true pnpm --filter @portfolio/admin dev
# http://localhost:3000
# - Login: user@test.com + Turnstile success + code 12345678
# - Navegar /settings /sessions /users
# - Settings: ver perfil + seguridad (MFA setup, WebAuthn, recovery)
# - Logout (verificar multi-tab sync)
```

Tests:
```
pnpm --filter @portfolio/admin test:coverage  # >= 80% per-file
pnpm --filter @portfolio/admin build           # genera admin/out
```

E2E:
```
python devtools/run.py docker up --env=local
python devtools/run.py test_runner --module=feature --type=feature --env=local
```

Deploy preview en dev (tras merge):
- admin.portfolio.dev.the-full-stack.com
- (Auth + gestion reales funcionales contra los Lambdas `auth` y `users`
  desplegados; la UI de metricas llega con b-analytics-api)

## TODO (out of scope)

- Plan b-analytics-api: Lambda `analytics` + UI de metricas (montadas
  dentro de este app shell)
- Backend action users.profile.change-password (cambio de password con
  access JWT) — la UI ya esta, bloqueada por esa dependencia
- Plan futuro c-cv-management: gestion del CV (hoy solo placeholder)
EOF
)"
```

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| `git push --force` con tests rojos | Romper la branch para otros + reviewers | Esperar tests verdes |
| Skip pasos de la bateria "porque ya los hice" | Verificacion stale | Re-ejecutar la suite completa |
| `--no-verify` para saltar pre-push hook | Saltea quality gates | Diagnosticar el error real |
| Crear PR sin coverage 80% | Plan-format lo prohibe | Agregar tests faltantes |
| Mergear sin que CI termine en verde | Romper main | Esperar |
| Eliminar `docs/specs/a-admin/` antes del cierre real | Pierde el plan | Solo al final (B.13) |
| Atribuir a IA en commit del cleanup | Politica empresa | Mensaje limpio |

[< 10-paralelizacion-worktrees](10-paralelizacion-worktrees.md) | [Volver al README](README.md)
