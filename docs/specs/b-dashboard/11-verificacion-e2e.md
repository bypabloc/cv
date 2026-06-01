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
rg --files dashboard/tests/ -g '*.test.*'
```

### A.2 — Verifica que TODOS los tests nuevos estan en la ruta correcta

```bash
# Mirror: cada src/<X>/<Y>.ts(x) debe tener tests/unit/<X>/<Y>.test.ts(x).
# Usamos `rg --files` con globs (-g) en vez de `find` (aliasado a `fd` en WSL2).
mkdir -p tmp
rg --files dashboard/src/ \
  -g '*.ts' -g '*.tsx' \
  -g '!**/components/ui/**' \
  -g '!**/app/**' \
  -g '!**/index.ts' \
  -g '!**/*.d.ts' \
  | sort > tmp/dashboard-sources.txt

rg --files dashboard/tests/unit/ -g '*.test.*' | sort > tmp/dashboard-tests.txt

# Comparar: cada source deberia tener test correspondiente (revision manual
# con `diff` o script python en tmp/).
```

### A.3 — Barrido global de referencias eliminadas

```bash
# Verifica que no quedan imports a paths que no existen
# (en este plan no aplica fuerte porque todo es nuevo)
cd dashboard
pnpm typecheck  # cualquier import roto sale aqui
```

### A.4 — Verifica que las routes del dashboard estan en `routes.ts`

```bash
# Las pages no deberian hardcodear paths — todo via ROUTES.dashboard.*
# Esto es review humano, pero un grep ayuda
rg -l "href=\"/dashboard" dashboard/src/  # debe estar SOLO en src/lib/routes.ts o tests
```

### A.5 — Verifica que `process.env.NEXT_PUBLIC_*` solo se usa en `env.ts`

```bash
# Todos los componentes deben importar `env` de @/lib/env (validacion Zod).
# NUNCA process.env.* directo. `tsx` NO es un type built-in de rg —
# `rg --type ts` ya cubre .ts y .tsx via la definicion built-in `typescript`.
# Confirmar con: rg --type-list | rg ^typescript
rg "process\.env\." dashboard/src/ --type ts
# Resultado esperado: SOLO src/lib/env.ts. vitest.config.ts vive fuera de dashboard/src/.
```

## Parte B — Bateria completa de comandos

Ejecutar EN ORDEN. Si alguno falla, **DETENER**, diagnosticar,
corregir, RE-EJECUTAR LA SUITE COMPLETA. NO continuar hasta que todo
pase.

### B.1 — Sintaxis + linting

```bash
pnpm --filter @portfolio/dashboard lint
# Esperado: 0 errors, 0 warnings
```

### B.2 — Typecheck

```bash
pnpm --filter @portfolio/dashboard typecheck
# Esperado: sin errores
```

### B.3 — Unit tests

```bash
pnpm --filter @portfolio/dashboard test
# Esperado: TODOS verdes
```

### B.4 — Coverage >= 80% per-file

```bash
pnpm --filter @portfolio/dashboard test:coverage
# Esperado: report imprime per-file coverage
# Si alguno < 80% (excluyendo components/ui/, app/, types/, env.d.ts, index.ts): FAIL
```

### B.5 — Build estatico

```bash
pnpm --filter @portfolio/dashboard build
# Esperado:
# - Sin errores
# - dashboard/out/index.html existe
# - dashboard/out/404.html existe
# - dashboard/out/_next/static/chunks/ existe
# - dashboard/out/_redirects existe
# - dashboard/out/_headers existe
ls -lah dashboard/out/index.html dashboard/out/_redirects dashboard/out/_headers
```

### B.6 — Preview manual (smoke test golden path)

```bash
# Servir el build estatico
pnpm --filter @portfolio/dashboard preview &
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
NEXT_PUBLIC_USE_MSW=true pnpm --filter @portfolio/dashboard dev &
DEV_PID=$!
sleep 5

# Manual: abrir http://localhost:3000 en browser, probar:
# 1. /login → email user@test.com + Turnstile success → submit
# 2. /verify → input code "12345678" → submit
# 3. Redirect a /dashboard → ver MetricCards
# 4. Navegar a /dashboard/analytics → ver TimeseriesChart
# 5. Cambiar DateRangePicker → ver refetch
# 6. Click logout → redirect a /login
# 7. Abrir 2da tab logueada, logout en 1 → 2da tab tambien logout (BroadcastChannel)

kill $DEV_PID
```

### B.8 — Verify devtools cloudflare_setup config

```bash
# El subcomando `status` NO existe en cloudflare_setup. Las fases validas
# son: projects, domains, triggers, all. Para verificar que el
# project del dashboard esta declarado correctamente en config.py,
# re-aplicar la fase projects con --dry-run (idempotente, sin side
# effects si el config matchea el remoto):
export CLOUDFLARE_API_TOKEN=$(grep -m1 '^CLOUDFLARE_API_TOKEN=' docker/env/dev-cli/.dev | cut -d= -f2-)
export ACCOUNT_ID=$(grep -m1 '^CLOUDFLARE_ACCOUNT_ID=' docker/env/dev-cli/.dev | cut -d= -f2-)
python devtools/run.py cloudflare_setup projects --env=dev --dry-run
# Esperado: lista los 7 projects (6 Astro + dashboard) con build_config + env_vars
# diff. Sin --dry-run aplicaria los cambios al remoto.

# Alternativa: leer la config declarada
python -c "from devtools.cloudflare_setup.config import APPS, app_for; print(app_for('dashboard'))"
# Esperado: AppConfig(name='dashboard', root_dir='dashboard', app_type='nextjs', build_output_dir='out', ...)
```

### B.9 — Verify devtools sync_secrets dry-run

```bash
python devtools/run.py sync_secrets --env=dev --category=client --dry-run
# Esperado: las 6 keys NEXT_PUBLIC_* del dashboard muestran su status (CREATE/PUSH/SKIP):
#   - NEXT_PUBLIC_API_ENDPOINT
#   - NEXT_PUBLIC_TURNSTILE_SITEKEY
#   - NEXT_PUBLIC_DASHBOARD_URL
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

# Correr E2E del dashboard
python devtools/run.py test_runner --module=feature --type=feature --env=local

# Esperado: 7 specs en tests/feature/dashboard/ verdes:
# - 01-login-magic-link.spec.ts
# - 02-register-verify-code.spec.ts
# - 03-callback-fragment-hash.spec.ts
# - 04-auth-guard-redirect.spec.ts
# - 05-logout-multi-tab.spec.ts
# - 06-analytics-navigation.spec.ts
# - 07-sessions-table-pagination.spec.ts

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
# El Lambda `auth` ya esta desplegado: el login real (magic-link, code,
# password, MFA, WebAuthn) funciona contra el backend. La data analitica
# se sirve via MSW hasta que se mergee el Lambda `analytics`.
```

### B.13 — Limpieza del plan (ULTIMO PASO)

```bash
# Solo si TODO lo anterior (B.1-B.12) paso en verde:
git rm -r docs/specs/b-dashboard/
git commit -m "chore(dashboard): elimina docs/specs/b-dashboard/ tras mergear el plan

- Plan dashboard SPA completado y mergeado a dev
- El conocimiento permanente queda en:
  - .claude/rules/dashboard.md
  - .claude/skills/dashboard-stack/SKILL.md
  - .claude/docs/dashboard/ (7 archivos)
- Trazabilidad del plan en git log + PR

Cumple TODOS los AC (1-33). Verificacion completa en seccion 11 del plan."

# Push final
git push origin feature/dashboard-frontend
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

El PR `feature/dashboard-frontend -> dev` se crea con:

```bash
gh pr create --base dev --head feature/dashboard-frontend \
  --title "feat(dashboard): admin SPA Next.js 16.2.6 + React 19.2.6 + shadcn + Tanstack" \
  --body "$(cat <<'EOF'
## Problema

El portfolio no tiene panel admin para ver la data analitica generada
por los visitantes (sessions, visits, tracking events, contacts). Hoy
solo se accede con psql o consola Neon.

## Solucion

Dashboard SPA estatico Next.js 16.2.6 + React 19.2.6 (compiler stable) +
shadcn/ui + Tanstack Query v5 + Zustand 5 (persist en localStorage),
deployado a Cloudflare Pages en
admin.portfolio.{dev|stage|prod}.the-full-stack.com.

Estructura Hybrid Atomic Design:
- src/components/ui/ — primitivos genericos (shadcn + custom)
- src/features/<X>/ — 11 features por dominio (auth, analytics,
  sessions, events, visits, geo, devices, funnel, contacts, settings,
  dashboard-shell)
- src/app/ — Next App Router con groups (auth) y (dashboard)

Auth contra el Lambda `auth` (desplegado en dev/stage/prod, 26 actions:
register / login / verify / session / mfa / webauthn — ver
serverless/lambda/services/auth/, .claude/rules/auth-system.md y
.claude/docs/auth-system/): tokens en localStorage
(accessToken en memoria Zustand, refreshToken + refreshExpiry + user
persistidos). NO HttpOnly cookies cross-origin — el dashboard vive en
admin.portfolio.{env}.the-full-stack.com y el API en api.portfolio.{env},
una cookie HttpOnly tendria que ser SameSite=None + Domain=.the-full-stack.com
y abrir CSRF en los 6 niches publicos. Defensa primaria contra XSS: CSP
estricta sin unsafe-inline/unsafe-eval + SRI en third-party + access JWT
corto (15 min) + family_id refresh rotation backend (RFC 9700). Mutex
client-side garantiza 1 sola /session/refresh in-flight. Magic link
callback con fragment hash + BroadcastChannel multi-tab sync.

Data fetching contra Lambda `analytics` (plan a-analytics-dashboard-api):
Tanstack Query v5 con persister + 19 endpoints typed.

El Lambda `auth` ya esta desplegado, asi que el flujo de auth (login,
register, MFA, WebAuthn, refresh) corre contra el backend real. Mientras
el Lambda `analytics` no este mergeado, MSW provee mocks de la data
analitica (NEXT_PUBLIC_USE_MSW=true).

## Como probar

Local con MSW (sin backend live):
```
NEXT_PUBLIC_USE_MSW=true pnpm --filter @portfolio/dashboard dev
# http://localhost:3000
# - Login: user@test.com + Turnstile success + code 12345678
# - Navegar /dashboard /dashboard/analytics /dashboard/sessions
# - Logout (verificar multi-tab sync)
```

Tests:
```
pnpm --filter @portfolio/dashboard test:coverage  # >= 80% per-file
pnpm --filter @portfolio/dashboard build           # genera dashboard/out
```

E2E:
```
python devtools/run.py docker up --env=local
python devtools/run.py test_runner --module=feature --type=feature --env=local
```

Deploy preview en dev (tras merge):
- admin.portfolio.dev.the-full-stack.com
- (Auth real ya funcional contra el Lambda `auth` desplegado; data
  analytics real cuando se mergee a-analytics-dashboard-api)

## TODO (out of scope)

- Plan a-analytics-dashboard-api no mergeado aun (bloqueante para data
  real; MSW provee mocks de la data analitica)
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
| Eliminar `docs/specs/b-dashboard/` antes del cierre real | Pierde el plan | Solo al final (B.13) |
| Atribuir a IA en commit del cleanup | Politica empresa | Mensaje limpio |

[< 10-paralelizacion-worktrees](10-paralelizacion-worktrees.md) | [Volver al README](README.md)
