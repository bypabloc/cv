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
# Listar tests que referencien archivos eliminados o renombrados
# (en este plan no hay archivos eliminados — todo es nuevo)
find dashboard/tests -type f -name '*.test.*'
```

### A.2 — Verifica que TODOS los tests nuevos estan en la ruta correcta

```bash
# Mirror: cada src/<X>/<Y>.ts(x) debe tener tests/unit/<X>/<Y>.test.ts(x)
# Listar fuentes
find dashboard/src -type f \( -name '*.ts' -o -name '*.tsx' \) \
  -not -path '*/components/ui/*' \
  -not -name 'index.ts' \
  -not -name '*.d.ts' \
  -not -path '*/app/*' \
  | sort > /tmp/dashboard-sources.txt

# Listar tests
find dashboard/tests/unit -type f -name '*.test.*' | sort > /tmp/dashboard-tests.txt

# Compare: cada source deberia tener test correspondiente
# (revision manual o con script)
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
# Todos los componentes deben importar `env` de @/lib/env (validacion Zod)
# NUNCA process.env.* directo
rg "process\.env\." dashboard/src/ --type ts --type tsx
# Resultado esperado: SOLO src/lib/env.ts y vitest.config.ts (excluido)
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

### B.8 — Verify devtools cloudflare_setup dry-run

```bash
python devtools/run.py cloudflare_setup status --env=dev --dry-run
# Esperado: lista el project portfolio-dashboard-dev con config correcta
```

### B.9 — Verify devtools sync_secrets dry-run

```bash
python devtools/run.py sync_secrets --env=dev --category=client --dry-run
# Esperado: 4 keys NEXT_PUBLIC_* (DASHBOARD_URL, API_ENDPOINT, TURNSTILE_SITEKEY, AUTH_REFRESH_LEAD_MS) muestran su status (CREATE/PUSH/SKIP)
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
# Sin auth backend desplegado: las APIs fallaran (esto es esperado;
# cuando se deploye el plan auth se podra hacer login real).
```

### B.13 — Limpieza del plan (ULTIMO PASO)

```bash
# Solo si TODO lo anterior (B.1-B.12) paso en verde:
git rm -r docs/specs/dashboard/
git commit -m "chore(dashboard): elimina docs/specs/dashboard/ tras mergear el plan

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
  --title "feat(dashboard): admin SPA Next.js 16 + React 18 + shadcn + Tanstack" \
  --body "$(cat <<'EOF'
## Problema

El portfolio no tiene panel admin para ver la data analitica generada
por los visitantes (sessions, visits, tracking events, contacts). Hoy
solo se accede con psql o consola Neon.

## Solucion

Dashboard SPA estatico Next.js 16 + React 18 + shadcn/ui + Tanstack
Query + Zustand, deployado a Cloudflare Pages en
admin.portfolio.{dev|stage|prod}.the-full-stack.com.

Estructura Hybrid Atomic Design:
- src/components/ui/ — primitivos genericos (shadcn + custom)
- src/features/<X>/ — 11 features por dominio (auth, analytics,
  sessions, events, visits, geo, devices, funnel, contacts, settings,
  dashboard-shell)
- src/app/ — Next App Router con groups (auth) y (dashboard)

Auth contra Lambda `auth` (planes 01-02): JWT in-memory + refresh
HttpOnly cookie + mutex client-side + magic link callback con fragment
hash + BroadcastChannel multi-tab sync.

Data fetching contra Lambda `analytics` (plan analytics-dashboard-api):
Tanstack Query v5 con persister + 19 endpoints typed.

Mientras los planes backend no esten mergeados, MSW provee mocks
completos (NEXT_PUBLIC_USE_MSW=true).

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
- (Auth real funcional cuando se mergeen los planes 01-02 + analytics)

## TODO (out of scope)

- Plan 01-auth-infra-basics no mergeado aun (bloqueante para
  funcionalidad real de auth)
- Plan analytics-dashboard-api no mergeado aun (bloqueante para data
  real)
- Plan 02-auth-mfa no mergeado aun (afecta features de MFA en settings;
  componentes ya existen, mocks via MSW hasta entonces)
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
| Eliminar `docs/specs/dashboard/` antes del cierre real | Pierde el plan | Solo al final (B.13) |
| Atribuir a IA en commit del cleanup | Politica empresa | Mensaje limpio |

[< 10-paralelizacion-worktrees](10-paralelizacion-worktrees.md) | [Volver al README](README.md)
