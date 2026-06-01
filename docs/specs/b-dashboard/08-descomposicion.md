# 08 — Descomposicion para paralelizacion

[< 07-dashboard-features](07-dashboard-features.md) | [Siguiente: 09-commits >](09-commits.md)

## Filosofia

Plan **Large** (21 fases, ~250 archivos). Paralelizable con git
worktrees + subagentes en las fases donde los conjuntos de archivos NO
colisionan. Fases secuenciales: las que modifican el mismo
`package.json`, `globals.css`, o configs centrales.

Limite: max 5-7 worktrees concurrentes (recurso de la maquina + cognitive
overhead).

## Reglas duras (recordatorio)

Cada tarea pasa 3 checks:

1. **File Exclusivity**: el set de archivos modificados/creados NO
   intersecta con otra tarea concurrente.
2. **Interface Stability**: las dependencias entre tareas (lo que una
   exporta y otra consume) estan definidas y estables ANTES de
   paralelizar.
3. **Bounded Scope**: cada tarea es atomica, completa, y deja el repo
   compilando + tests verdes.

## Inventario de tareas

Cada tarea tiene 6 campos:
- **Archivos**: paths que crea/modifica
- **AC**: criterios de aceptacion cubiertos
- **Depende de**: tareas que deben completar antes
- **Paralelizable con**: tareas que pueden correr al mismo tiempo
- **Verify**: comando de verificacion al cierre
- **Done**: criterio observable de completado

### Bloque A — Base secuencial (NO paralelizable)

Estas tareas tocan archivos centrales (package.json, configs root) y
deben completar ANTES de paralelizar.

#### A.1 — Carpeta del plan
- **Archivos**: `docs/specs/b-dashboard/*.md` (12 archivos del plan)
- **AC**: — (meta-task)
- **Depende de**: nada
- **Paralelizable con**: ninguna
- **Verify**: `ls docs/specs/b-dashboard/README.md`
- **Done**: PR feature/dashboard-frontend creado con la carpeta committed

#### A.2 — Scaffold `dashboard/` (fase 1)
- **Archivos**:
  - `dashboard/package.json`
  - `dashboard/next.config.ts`
  - `dashboard/tsconfig.json`
  - `dashboard/biome.json`
  - `dashboard/postcss.config.mjs`
  - `dashboard/vitest.config.ts`
  - `dashboard/.gitignore`
  - `dashboard/README.md`
  - `pnpm-workspace.yaml` (modify)
- **AC**: AC-1, AC-2, AC-3
- **Depende de**: A.1
- **Paralelizable con**: ninguna (toca workspace root)
- **Verify**: `pnpm install && pnpm --filter @portfolio/dashboard typecheck && pnpm --filter @portfolio/dashboard lint`
- **Done**: workspace recoge `@portfolio/dashboard`, lint y typecheck pasan en archivos vacios

#### A.3 — Tokens + theme provider + ThemeToggle (fase 2)
- **Archivos**:
  - `dashboard/src/styles/globals.css`
  - `dashboard/src/providers/theme-provider.tsx`
  - `dashboard/src/components/ui/theme-toggle.tsx`
- **AC**: AC-5, AC-6
- **Depende de**: A.2
- **Paralelizable con**: ninguna (CSS global)
- **Verify**: `pnpm --filter @portfolio/dashboard build` (CSS se procesa)
- **Done**: globals.css compila + theme provider OK

#### A.4 — shadcn init + 24 primitivos (fase 3)
- **Archivos**:
  - `dashboard/components.json`
  - `dashboard/src/components/ui/{alert,badge,button,calendar,card,chart,checkbox,command,dialog,dropdown-menu,form,input,input-otp,label,popover,select,separator,sheet,skeleton,sonner,switch,table,tabs,tooltip}.tsx`
  - `dashboard/package.json` (modify, deps de Radix)
- **AC**: AC-2, AC-3
- **Depende de**: A.3
- **Paralelizable con**: ninguna (toca package.json)
- **Verify**: `pnpm --filter @portfolio/dashboard lint && pnpm --filter @portfolio/dashboard build`
- **Done**: 24 primitivos en `src/components/ui/`

#### A.5 — Custom UI primitives (fase 4)
- **Archivos**:
  - `dashboard/src/components/ui/{metric-card,data-table,date-range-picker,empty-state,error-alert,loading-spinner}.tsx`
  - `dashboard/src/components/ui/index.ts`
  - `dashboard/src/lib/utils.ts`
  - Tests mirror
- **AC**: AC-21, AC-23
- **Depende de**: A.4
- **Paralelizable con**: ninguna (depende de A.4 + cambia barrel index.ts)
- **Verify**: `pnpm --filter @portfolio/dashboard test:coverage tests/unit/components/ui`
- **Done**: 6 custom primitives + barrel + tests verdes (>= 80%)

#### A.6 — Lib base (fase 5)
- **Archivos**:
  - `dashboard/src/lib/env.ts`
  - `dashboard/src/lib/routes.ts`
  - `dashboard/src/lib/api-client.ts`
  - `dashboard/src/lib/format/{date,number,duration}.ts`
  - `dashboard/src/lib/validation/{auth,filters}.ts`
  - `dashboard/src/types/{api,models,env.d}.ts`
  - Tests mirror (criticos: api-client.test.ts con mutex)
- **AC**: AC-14
- **Depende de**: A.5
- **Paralelizable con**: ninguna (api-client tocado por mucho codigo downstream)
- **Verify**: `pnpm --filter @portfolio/dashboard test:coverage tests/unit/lib`
- **Done**: api-client + env + format + validation + types + tests >= 90%

#### A.7 — Providers + RootLayout (fase 6)
- **Archivos**:
  - `dashboard/src/providers/{query-provider,root-providers}.tsx`
  - `dashboard/src/app/{layout,page,error,global-error,not-found}.tsx`
- **AC**: AC-4
- **Depende de**: A.6
- **Paralelizable con**: ninguna (RootLayout central)
- **Verify**: `pnpm --filter @portfolio/dashboard build && curl preview /`
- **Done**: build OK + RootLayout renderiza con providers

#### A.8 — MSW setup + Vitest setup (fase 9, pero base de todos los tests)
- **Archivos**:
  - `dashboard/tests/setup.ts`
  - `dashboard/tests/utils/render.tsx`
  - `dashboard/tests/mocks/{server,browser}.ts`
  - `dashboard/tests/mocks/handlers/{auth,analytics,sessions,events,visits,geo,devices,funnel,contacts}.ts`
  - `dashboard/tests/fixtures/{users,sessions,events,analytics}.ts`
  - `dashboard/public/mockServiceWorker.js` (via `npx msw init`)
- **AC**: AC-33 (base infrastructure)
- **Depende de**: A.7
- **Paralelizable con**: ninguna (tests/ y mocks son base de todo testing)
- **Verify**: `pnpm --filter @portfolio/dashboard test` (no archivos aun, pero setup OK)
- **Done**: setup.ts + mocks + render wrapper + fixtures todos creados

### Bloque B — Auth feature (parcialmente paralelizable con C-shell)

#### B.1 — Auth store + lib + types + api-client (fase 7 parte 1)
- **Archivos**:
  - `dashboard/src/features/auth/store/use-auth-store.ts`
  - `dashboard/src/features/auth/lib/{refresh-mutex,broadcast,token-expiry}.ts`
  - `dashboard/src/features/auth/api/{auth-client,query-keys}.ts`
  - `dashboard/src/features/auth/types.ts`
  - Tests mirror
- **AC**: AC-14, AC-17, AC-18
- **Depende de**: A.8
- **Paralelizable con**: C.1 (dashboard-shell — no toca features/auth)
- **Verify**: `pnpm test tests/unit/features/auth/{store,lib,api}`
- **Done**: store + lib + api typed + tests >= 90% (es critico el mutex test)

#### B.2 — Auth hooks (fase 7 parte 2)
- **Archivos**:
  - `dashboard/src/features/auth/hooks/use-{register-start,register-verify-code,login-start,login-verify-code,login-verify-totp,set-password,resend-code,session-refresh,logout,auth-timer,multi-tab-sync,protected-route}.ts`
  - Tests mirror
- **AC**: AC-15, AC-16, AC-17, AC-18
- **Depende de**: B.1
- **Paralelizable con**: C.1 — NO con tareas del bloque D (D.1 a D.7 dependen transitivamente de B.2 via la cadena B.2 -> B.3 -> C.2; lanzar una tarea D antes de cerrar B.2 invalida el bloqueo de auth components y rompe el merge a feature/dashboard-frontend)
- **Verify**: `pnpm test tests/unit/features/auth/hooks`
- **Done**: 12 hooks + tests verdes

#### B.3 — Auth components (fase 7 parte 3)
- **Archivos**:
  - `dashboard/src/features/auth/components/{login-form,register-form,verify-code-input,magic-link-prompt,set-password-form,auth-guard,turnstile-widget,totp-setup,recovery-codes-modal,webauthn-register-button}.tsx`
  - `dashboard/src/features/auth/index.ts`
  - Tests mirror
- **AC**: AC-8, AC-9, AC-10, AC-11, AC-19, AC-20, AC-26
- **Depende de**: B.2
- **Paralelizable con**: C.1 (dashboard-shell — no toca features/auth/). Tareas D y B.4 esperan a B.3 porque consumen `AuthGuard` y el barrel `features/auth/index.ts`.
- **Verify**: `pnpm test:coverage tests/unit/features/auth`
- **Done**: 10 componentes + tests >= 80%

#### B.4 — Auth pages (fase 8)
- **Archivos**:
  - `dashboard/src/app/(auth)/{login,register,verify,callback,set-password}/page.tsx`
- **AC**: AC-12, AC-13
- **Depende de**: B.3
- **Paralelizable con**: C.2 (dashboard pages — no overlap)
- **Verify**: `pnpm build && curl localhost:3000/login`
- **Done**: 5 pages + build OK

### Bloque C — Dashboard shell (paralelo con B)

#### C.1 — `dashboard-shell` feature (fase 10)
- **Archivos**:
  - `dashboard/src/features/dashboard-shell/components/{sidebar,header,mobile-sidebar}.tsx`
  - `dashboard/src/features/dashboard-shell/lib/nav-items.ts`
  - `dashboard/src/features/dashboard-shell/index.ts`
  - Tests mirror
- **AC**: AC-7
- **Depende de**: A.7 (no depende de B!) — puede correr en paralelo con B.1
- **Paralelizable con**: B.* (no toca features/auth)
- **Verify**: `pnpm test tests/unit/features/dashboard-shell`
- **Done**: sidebar + header + nav-items + tests

#### C.2 — `(dashboard)/layout.tsx` (fase 10 cierre)
- **Archivos**:
  - `dashboard/src/app/(dashboard)/layout.tsx`
- **AC**: AC-7, AC-19
- **Depende de**: B.3 (`AuthGuard`) + C.1 (Sidebar + Header)
- **Paralelizable con**: ninguna (depende de B y C)
- **Verify**: `pnpm build`
- **Done**: layout protegido OK

### Bloque D — Features de data (alta paralelizacion)

Cada feature es independiente. Tocan archivos disjuntos
(`src/features/<X>/*`). Despues de A.* + B.1 + B.2, todas D.* pueden
correr en paralelo (limite 5-7 worktrees).

#### D.1 — `analytics/` (fase 11) — la mas grande
- **Archivos**:
  - `dashboard/src/features/analytics/**` (componentes, hooks, api, store, types, index)
  - `dashboard/src/app/(dashboard)/{page,analytics/page}.tsx`
  - Tests mirror
- **AC**: AC-21, AC-22
- **Depende de**: A.8, B.1 (auth store para Authorization header), C.2 (layout)
- **Paralelizable con**: D.2 - D.7
- **Verify**: `pnpm test:coverage tests/unit/features/analytics && pnpm build`
- **Done**: 7 hooks + 8 componentes + 2 pages + tests >= 80%

#### D.2 — `sessions/` (fase 12)
- **Archivos**:
  - `dashboard/src/features/sessions/**` (incluye `SessionDetailDrawer` con deep-link via `?session=<id>`)
  - `dashboard/src/app/(dashboard)/sessions/page.tsx` (SOLO la list; el detalle vive en drawer lateral. NO se crea ruta dinamica `[id]` — Next 16 con `output: 'export'` la rechaza sin `generateStaticParams()`)
  - Tests mirror
- **AC**: AC-23
- **Depende de**: A.8, B.1, C.2
- **Paralelizable con**: D.1, D.3 - D.7
- **Verify**: `pnpm test:coverage tests/unit/features/sessions`
- **Done**: list + detail dialog + tests

#### D.3 — `events/` (fase 13)
- **Archivos**:
  - `dashboard/src/features/events/**`
  - `dashboard/src/app/(dashboard)/events/page.tsx`
  - Tests mirror (incluye test de virtualization)
- **AC**: AC-24
- **Depende de**: A.8, B.1, C.2
- **Paralelizable con**: D.1, D.2, D.4 - D.7
- **Verify**: `pnpm test:coverage tests/unit/features/events`
- **Done**: distribution + list virtual + heatmap + tests

#### D.4 — `visits/` + `geo/` (fase 14a)
- **Archivos**:
  - `dashboard/src/features/{visits,geo}/**`
  - `dashboard/src/app/(dashboard)/{visits,geo}/page.tsx`
  - Tests mirror
- **AC**: — (variantes de listado)
- **Depende de**: A.8, B.1, C.2
- **Paralelizable con**: D.1, D.2, D.3, D.5 - D.7
- **Verify**: `pnpm test:coverage tests/unit/features/{visits,geo}`
- **Done**: 2 features + 2 pages

#### D.5 — `devices/` + `funnel/` (fase 14b)
- **Archivos**:
  - `dashboard/src/features/{devices,funnel}/**`
  - `dashboard/src/app/(dashboard)/{devices,funnel}/page.tsx`
  - Tests mirror
- **AC**: —
- **Depende de**: A.8, B.1, C.2
- **Paralelizable con**: D.1 - D.4, D.6, D.7
- **Verify**: `pnpm test:coverage tests/unit/features/{devices,funnel}`
- **Done**: 2 features + 2 pages

#### D.6 — `contacts/` (fase 15) — incluye mutation
- **Archivos**:
  - `dashboard/src/features/contacts/**`
  - `dashboard/src/app/(dashboard)/contacts/page.tsx`
  - Tests mirror (critico: test de mutation + invalidation)
- **AC**: AC-25
- **Depende de**: A.8, B.1, C.2
- **Paralelizable con**: D.1 - D.5, D.7
- **Verify**: `pnpm test:coverage tests/unit/features/contacts`
- **Done**: list + by-status + detail + mutation + tests

#### D.7 — `settings/` (fase 16)
- **Archivos**:
  - `dashboard/src/features/settings/**`
  - `dashboard/src/app/(dashboard)/settings/{page,security/page}.tsx`
  - Tests mirror
- **AC**: AC-26
- **Depende de**: A.8, B.1, C.2
- **Paralelizable con**: D.1 - D.6
- **Verify**: `pnpm test:coverage tests/unit/features/settings`
- **Done**: profile + MFA management + recovery codes

### Bloque E — Infraestructura de deploy (paralelizable con D parcialmente)

#### E.1 — devtools/cloudflare_setup extension (fase 17)
- **Archivos**:
  - `devtools/cloudflare_setup/config.py` (modify: agregar `AppConfig` dashboard)
  - `devtools/cloudflare_setup/README.md` (mencionar dashboard)
- **AC**: AC-30
- **Depende de**: A.2 (existe el package)
- **Paralelizable con**: D.* (toca archivos Python, no TS)
- **Verify**: `python devtools/run.py cloudflare_setup projects --env=dev --dry-run` (la fase `status` NO existe; las fases validas son projects / domains / triggers / all)
- **Done**: dry-run lista el dashboard como 7mo project con app_type='nextjs' + build_output_dir='out'

#### E.2 — devtools/sync_secrets + docker/env extension (fase 18)
- **Archivos**:
  - `devtools/sync_secrets/catalog.py` (modify)
  - `docker/env/client/.example` (modify: agregar NEXT_PUBLIC_*)
- **AC**: AC-30
- **Depende de**: A.2
- **Paralelizable con**: D.*, E.1
- **Verify**: `python devtools/run.py sync_secrets --env=dev --category=client --dry-run`
- **Done**: dry-run muestra las 4 keys nuevas

#### E.3 — GH Actions workflows extension (fase 19)
- **Archivos**:
  - `.github/workflows/deploy-apps.yml` (modify: matrix include dashboard + env vars NEXT_PUBLIC_*)
  - `.github/workflows/ci.yml` (modify: filter incluye dashboard)
  - `.claude/docs/subdomain-standard/02-naming-rules.md` (modify: agregar `admin` a reserved)
- **AC**: AC-30, AC-31
- **Depende de**: E.1, E.2
- **Paralelizable con**: D.* (yaml + md, no codigo)
- **Verify**: `act -W .github/workflows/ci.yml` (con skill github-actions)
- **Done**: workflows YAML validos + ci local pasa

### Bloque F — E2E + cierre (secuencial al final)

#### F.1 — Playwright E2E specs (fase 20)
- **Archivos**:
  - `tests/feature/dashboard/01-login-magic-link.spec.ts`
  - `tests/feature/dashboard/02-register-verify-code.spec.ts`
  - `tests/feature/dashboard/03-callback-fragment-hash.spec.ts`
  - `tests/feature/dashboard/04-auth-guard-redirect.spec.ts`
  - `tests/feature/dashboard/05-logout-multi-tab.spec.ts`
  - `tests/feature/dashboard/06-analytics-navigation.spec.ts`
  - `tests/feature/dashboard/07-sessions-table-pagination.spec.ts`
- **AC**: AC-32
- **Depende de**: TODAS las B, C, D
- **Paralelizable con**: ninguna (necesita el stack completo)
- **Verify**: `python devtools/run.py docker up --env=local && python devtools/run.py test_runner --module=feature --type=feature --env=local`
- **Done**: 7 specs E2E verdes

#### F.2 — Verificacion E2E iterativa (fase 21) — la ultima
- **Archivos**: ninguno nuevo. Es la fase de verify-before-done + limpieza de `docs/specs/b-dashboard/`.
- **AC**: AC-32, AC-33 + TODOS los AC del plan
- **Depende de**: F.1 + TODAS
- **Paralelizable con**: ninguna
- **Verify**: bateria completa de la seccion 11
- **Done**: bateria verde + `git rm -r docs/specs/b-dashboard/` committed

## Diagrama de paralelizacion

```text
A.1 -> A.2 -> A.3 -> A.4 -> A.5 -> A.6 -> A.7 -> A.8
                                            |
                +---------------------------+----+
                |                                |
              B.1 (auth store/lib/api)        C.1 (dashboard-shell)
                |                                |
              B.2 (auth hooks)                   |
                |                                |
              B.3 (auth components) -----+      |
                                          v      |
                                    C.2 (layout)<+
                                          |
              B.4 (auth pages) <----------+
                                          |
                +-------------------------+--------------+----------------+
                |                |                 |                |
              D.1 anal.   D.2 sess.+events    D.4 visits+geo    D.5 dev+fun
                |                |                 |                |        D.6 cont +
                |                |                 |                |        D.7 sett (consolidados, max 5-7 worktrees)
                +----------------+-----------------+----------------+----+
                |                                                        |
                +--------------------------------------------------------+
                                          |
              (mientras tanto en otra worktree: E.1, E.2, E.3 paralelo a D)
                                          |
                                       F.1 (E2E Playwright) — necesita TODAS
                                          |
                                       F.2 (verificacion + limpieza) — gate del PR
```

## Granularidad

Total tareas: **26** (A.1-A.8 = 8, B.1-B.4 = 4, C.1-C.2 = 2, D.1-D.7 = 7, E.1-E.3 = 3, F.1-F.2 = 2).

Plan Large = 10-20 tareas. Con 26 tareas el plan esta por encima del
limite alto, justificado por el scope: scaffold + auth + 7 features
de data + infra de deploy + E2E. La paralelizacion via worktrees (ver
seccion 10) consolida D.* en 5-6 worktrees concurrentes (limite
recomendado por `.claude/rules/plan-format.md` capitulo 1).

## Lanzar worktrees (ejemplo)

```bash
# Desde la rama feature/dashboard-frontend, despues de A.8 + B.3 + C.2.
# CADA worktree usa SU PROPIA branch (-b) — no se puede reutilizar
# feature/dashboard-frontend porque esa branch ya esta checked out en el
# worktree principal y git lo rechaza (`fatal: ... is already checked out`).

git worktree add -b feature/dashboard-wt-analytics       ../portfolio-wt-analytics       feature/dashboard-frontend
git worktree add -b feature/dashboard-wt-sessions-events ../portfolio-wt-sessions-events feature/dashboard-frontend
git worktree add -b feature/dashboard-wt-contacts-settings ../portfolio-wt-contacts-settings feature/dashboard-frontend
git worktree add -b feature/dashboard-wt-devtools        ../portfolio-wt-devtools        feature/dashboard-frontend

# Cada worktree commitea a SU branch. Despues del verify del scope, el
# worktree principal mergea cada branch a feature/dashboard-frontend
# con merge commit (sin rebase, ver .claude/rules/git-workflow.md):
#   cd ../portfolio
#   git checkout feature/dashboard-frontend
#   git merge --no-ff feature/dashboard-wt-analytics
#   git push origin feature/dashboard-frontend
# Despues del merge, eliminar la branch del worktree (local + remoto).

# Al terminar todas las worktrees:
git worktree remove ../portfolio-wt-analytics
git worktree remove ../portfolio-wt-sessions-events
git worktree remove ../portfolio-wt-contacts-settings
git worktree remove ../portfolio-wt-devtools

# Limpiar branches mergeadas
git branch -d feature/dashboard-wt-analytics feature/dashboard-wt-sessions-events feature/dashboard-wt-contacts-settings feature/dashboard-wt-devtools
git push origin --delete feature/dashboard-wt-analytics feature/dashboard-wt-sessions-events feature/dashboard-wt-contacts-settings feature/dashboard-wt-devtools
```

Ver detalle en [10-paralelizacion-worktrees.md](10-paralelizacion-worktrees.md).

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Paralelizar A.* | Tocan archivos centrales (package.json, configs) | Secuencial |
| Paralelizar D.1 con D.2 sin completar B.1 antes | Auth store no existe, falla import | Esperar B.1 |
| Paralelizar mas de 7 worktrees | Cognitive overhead + memoria de la maquina | Max 5-7 |
| Crear commit en una worktree sin re-run de tests | Romper otra worktree | Verify antes de commit |
| F.1 antes de TODAS las D.* | Specs E2E necesitan stack completo | Esperar |

[< 07-dashboard-features](07-dashboard-features.md) | [Siguiente: 09-commits >](09-commits.md)
