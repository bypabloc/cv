# 08 — Descomposicion para paralelizacion

[< 07-settings-features](07-settings-features.md) | [Siguiente: 09-commits >](09-commits.md)

## Filosofia

Plan **Large** (~20 fases, ~220 archivos). Paralelizable con git
worktrees + subagentes en las fases donde los conjuntos de archivos NO
colisionan. Fases secuenciales: las que modifican el mismo
`package.json`, `globals.css`, o configs centrales.

El plan a-admin es el FRONTEND del admin: scaffold + auth completo + app
shell + gestion total (settings/sessions-mgmt/users-admin) + placeholder
gestion CV + deploy. Consume el Lambda `auth` (26 actions) + el Lambda
`users` (3 operations / 15 actions, ya desplegado). Las pantallas de
METRICAS (analytics, sessions de tracking, events, visits, geo, devices,
funnel, contacts) NO viven aqui: se implementan en el plan
`b-analytics-api`, montadas DENTRO de este mismo app shell.

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
- **Archivos**: `docs/specs/a-admin/*.md` (12 archivos del plan)
- **AC**: — (meta-task)
- **Depende de**: nada
- **Paralelizable con**: ninguna
- **Verify**: `ls docs/specs/a-admin/README.md`
- **Done**: PR feature/admin-frontend creado con la carpeta committed

#### A.2 — Scaffold `admin/` (fase 1)
- **Archivos**:
  - `admin/package.json`
  - `admin/next.config.ts`
  - `admin/tsconfig.json`
  - `admin/biome.json`
  - `admin/postcss.config.mjs`
  - `admin/vitest.config.ts`
  - `admin/.gitignore`
  - `admin/README.md`
  - `pnpm-workspace.yaml` (modify)
- **AC**: AC-1, AC-2, AC-3
- **Depende de**: A.1
- **Paralelizable con**: ninguna (toca workspace root)
- **Verify**: `pnpm install && pnpm --filter @portfolio/admin typecheck && pnpm --filter @portfolio/admin lint`
- **Done**: workspace recoge `@portfolio/admin`, lint y typecheck pasan en archivos vacios

#### A.3 — Tokens + theme provider + ThemeToggle (fase 2)
- **Archivos**:
  - `admin/src/styles/globals.css`
  - `admin/src/providers/theme-provider.tsx`
  - `admin/src/components/ui/theme-toggle.tsx`
- **AC**: AC-5, AC-6
- **Depende de**: A.2
- **Paralelizable con**: ninguna (CSS global)
- **Verify**: `pnpm --filter @portfolio/admin build` (CSS se procesa)
- **Done**: globals.css compila + theme provider OK

#### A.4 — shadcn init + 24 primitivos (fase 3)
- **Archivos**:
  - `admin/components.json`
  - `admin/src/components/ui/{alert,badge,button,calendar,card,chart,checkbox,command,dialog,dropdown-menu,form,input,input-otp,label,popover,select,separator,sheet,skeleton,sonner,switch,table,tabs,tooltip}.tsx`
  - `admin/package.json` (modify, deps de Radix)
- **AC**: AC-2, AC-3
- **Depende de**: A.3
- **Paralelizable con**: ninguna (toca package.json)
- **Verify**: `pnpm --filter @portfolio/admin lint && pnpm --filter @portfolio/admin build`
- **Done**: 24 primitivos en `src/components/ui/`

#### A.5 — Custom UI primitives (fase 4)
- **Archivos**:
  - `admin/src/components/ui/{metric-card,data-table,date-range-picker,empty-state,error-alert,loading-spinner}.tsx`
  - `admin/src/components/ui/index.ts`
  - `admin/src/lib/utils.ts`
  - Tests mirror
- **AC**: AC-21, AC-23
- **Depende de**: A.4
- **Paralelizable con**: ninguna (depende de A.4 + cambia barrel index.ts)
- **Verify**: `pnpm --filter @portfolio/admin test:coverage tests/unit/components/ui`
- **Done**: 6 custom primitives + barrel + tests verdes (>= 80%)

#### A.6 — Lib base (fase 5)
- **Archivos**:
  - `admin/src/lib/env.ts`
  - `admin/src/lib/routes.ts`
  - `admin/src/lib/api-client.ts`
  - `admin/src/lib/format/{date,number,duration}.ts`
  - `admin/src/lib/validation/{auth,filters}.ts`
  - `admin/src/types/{api,models,env.d}.ts`
  - Tests mirror (criticos: api-client.test.ts con mutex)
- **AC**: AC-14
- **Depende de**: A.5
- **Paralelizable con**: ninguna (api-client tocado por mucho codigo downstream)
- **Verify**: `pnpm --filter @portfolio/admin test:coverage tests/unit/lib`
- **Done**: api-client + env + format + validation + types + tests >= 90%

#### A.7 — Providers + RootLayout (fase 6)
- **Archivos**:
  - `admin/src/providers/{query-provider,root-providers}.tsx`
  - `admin/src/app/{layout,page,error,global-error,not-found}.tsx`
- **AC**: AC-4
- **Depende de**: A.6
- **Paralelizable con**: ninguna (RootLayout central)
- **Verify**: `pnpm --filter @portfolio/admin build && curl preview /`
- **Done**: build OK + RootLayout renderiza con providers

#### A.8 — MSW setup + Vitest setup (fase 9, pero base de todos los tests)
- **Archivos**:
  - `admin/tests/setup.ts`
  - `admin/tests/utils/render.tsx`
  - `admin/tests/mocks/{server,browser}.ts`
  - `admin/tests/mocks/handlers/{auth,analytics,sessions,events,visits,geo,devices,funnel,contacts}.ts`
  - `admin/tests/fixtures/{users,sessions,events,analytics}.ts`
  - `admin/public/mockServiceWorker.js` (via `npx msw init`)
- **AC**: AC-33 (base infrastructure)
- **Depende de**: A.7
- **Paralelizable con**: ninguna (tests/ y mocks son base de todo testing)
- **Verify**: `pnpm --filter @portfolio/admin test` (no archivos aun, pero setup OK)
- **Done**: setup.ts + mocks + render wrapper + fixtures todos creados

### Bloque B — Auth feature (parcialmente paralelizable con C-shell)

#### B.1 — Auth store + lib + types + api-client (fase 7 parte 1)
- **Archivos**:
  - `admin/src/features/auth/store/use-auth-store.ts`
  - `admin/src/features/auth/lib/{refresh-mutex,broadcast,token-expiry}.ts`
  - `admin/src/features/auth/api/{auth-client,query-keys}.ts`
  - `admin/src/features/auth/types.ts`
  - Tests mirror
- **AC**: AC-14, AC-17, AC-18
- **Depende de**: A.8
- **Paralelizable con**: C.1 (admin-shell — no toca features/auth)
- **Verify**: `pnpm test tests/unit/features/auth/{store,lib,api}`
- **Done**: store + lib + api typed + tests >= 90% (es critico el mutex test)

#### B.2 — Auth hooks (fase 7 parte 2)
- **Archivos**:
  - `admin/src/features/auth/hooks/use-{register-start,register-verify-code,login-start,login-verify-code,login-verify-totp,set-password,resend-code,session-refresh,logout,auth-timer,multi-tab-sync,protected-route}.ts`
  - Tests mirror
- **AC**: AC-15, AC-16, AC-17, AC-18
- **Depende de**: B.1
- **Paralelizable con**: C.1 — NO con tareas del bloque D (D.1 a D.7 dependen transitivamente de B.2 via la cadena B.2 -> B.3 -> C.2; lanzar una tarea D antes de cerrar B.2 invalida el bloqueo de auth components y rompe el merge a feature/admin-frontend)
- **Verify**: `pnpm test tests/unit/features/auth/hooks`
- **Done**: 12 hooks + tests verdes

#### B.3 — Auth components (fase 7 parte 3)
- **Archivos**:
  - `admin/src/features/auth/components/{login-form,register-form,verify-code-input,magic-link-prompt,set-password-form,auth-guard,turnstile-widget,totp-setup,recovery-codes-modal,webauthn-register-button}.tsx`
  - `admin/src/features/auth/index.ts`
  - Tests mirror
- **AC**: AC-8, AC-9, AC-10, AC-11, AC-19, AC-20, AC-26
- **Depende de**: B.2
- **Paralelizable con**: C.1 (admin-shell — no toca features/auth/). Tareas D y B.4 esperan a B.3 porque consumen `AuthGuard` y el barrel `features/auth/index.ts`.
- **Verify**: `pnpm test:coverage tests/unit/features/auth`
- **Done**: 10 componentes + tests >= 80%

#### B.4 — Auth pages (fase 8)
- **Archivos**:
  - `admin/src/app/(auth)/{login,register,verify,callback,set-password}/page.tsx`
- **AC**: AC-12, AC-13
- **Depende de**: B.3
- **Paralelizable con**: C.2 (admin layout — no overlap)
- **Verify**: `pnpm build && curl localhost:3000/login`
- **Done**: 5 pages + build OK

### Bloque C — Admin shell (paralelo con B)

#### C.1 — `admin-shell` feature (fase 10)
- **Archivos**:
  - `admin/src/features/admin-shell/components/{sidebar,header,mobile-sidebar}.tsx`
  - `admin/src/features/admin-shell/lib/nav-items.ts`
  - `admin/src/features/admin-shell/index.ts`
  - Tests mirror
- **AC**: AC-7
- **Depende de**: A.7 (no depende de B!) — puede correr en paralelo con B.1
- **Paralelizable con**: B.* (no toca features/auth)
- **Verify**: `pnpm test tests/unit/features/admin-shell`
- **Done**: sidebar + header + nav-items + tests. El sidebar incluye los
  slots/links a TODAS las secciones del admin (metricas, settings,
  sessions-mgmt, users-admin, gestion CV placeholder). Las pantallas de
  metricas las monta el plan b-analytics-api; aqui solo el link.

#### C.2 — `(admin)/layout.tsx` (fase 10 cierre)
- **Archivos**:
  - `admin/src/app/(admin)/layout.tsx`
- **AC**: AC-7, AC-19
- **Depende de**: B.3 (`AuthGuard`) + C.1 (Sidebar + Header)
- **Paralelizable con**: ninguna (depende de B y C)
- **Verify**: `pnpm build`
- **Done**: layout protegido OK

### Bloque D — Features de gestion (alta paralelizacion)

Cada feature es independiente. Tocan archivos disjuntos
(`src/features/<X>/*`). Despues de A.* + B.1 + B.2 + C.2, todas D.*
pueden correr en paralelo (limite 5-7 worktrees). Estas features son la
GESTION TOTAL del admin: perfil + seguridad de MI cuenta, mis sesiones,
otros usuarios (admin), y el placeholder de gestion CV. Consumen el
Lambda `auth` + el Lambda `users`. Las pantallas de metricas viven en
`b-analytics-api`, NO aqui.

#### D.1 — `settings/` (fase 11) — la mas grande
- **Archivos**:
  - `admin/src/features/settings/**` (componentes, hooks, api, store, types, index)
  - `admin/src/app/(admin)/settings/{page,security/page}.tsx`
  - Tests mirror
- **AC**: AC-26, AC-27, AC-28
- **Depende de**: A.8, B.1 (auth store para Authorization header), B.3
  (`TotpSetup`, `RecoveryCodesModal`, `WebauthnRegisterButton`), C.2 (layout)
- **Paralelizable con**: D.2 - D.4
- **Verify**: `pnpm test:coverage tests/unit/features/settings && pnpm build`
- **Done**: perfil (display_name via `users.profile.update`) + seguridad
  (MFA TOTP setup/confirm/email-code/set-preferred/disable, WebAuthn
  register/list/delete passkeys, recovery codes via `auth.mfa`/`auth.webauthn`)
  + cambio de password (UI + MSW; BLOQUEADA por el gap de backend, ver nota)
  + change-email (`users.profile.change-email` + `confirm-email-change`) +
  eliminar cuenta (`users.profile.delete-account`) + tests >= 80%

> GAP de backend (cambio de password): NO existe una action para que un
> user autenticado cambie su password (`auth.verify.set-password` usa
> temp_token del flujo register/login, NO access JWT; `users.profile` no
> tiene `change-password`). La UI se implementa y se mockea con MSW, pero
> queda BLOQUEADA por una action NUEVA de backend (sugerida:
> `users.profile.change-password` con `{current_password, new_password}`
> validada con el access JWT). No se puede testear E2E real hasta que
> exista. Ver [07-settings-features.md](07-settings-features.md).

#### D.2 — `sessions-mgmt/` (fase 12)
- **Archivos**:
  - `admin/src/features/sessions-mgmt/**` (lista de sesiones activas de MI
    cuenta + revocacion)
  - `admin/src/app/(admin)/settings/sessions/page.tsx`
  - Tests mirror
- **AC**: AC-29
- **Depende de**: A.8, B.1, C.2
- **Paralelizable con**: D.1, D.3, D.4
- **Verify**: `pnpm test:coverage tests/unit/features/sessions-mgmt`
- **Done**: ver sesiones activas (`users.status.list-sessions` + `get`) +
  revocar sesion (`users.status.revoke-session`, NO la actual -> 400) +
  tests. NO confundir con la feature `sessions` de tracking de visitantes
  (esa es del plan b-analytics-api).

#### D.3 — `users-admin/` (fase 13) — solo admin
- **Archivos**:
  - `admin/src/features/users-admin/**`
  - `admin/src/app/(admin)/users/page.tsx`
  - Tests mirror (incluye test del gate de admin: no-admin -> 404 NOT_FOUND)
- **AC**: AC-30, AC-31
- **Depende de**: A.8, B.1, C.2
- **Paralelizable con**: D.1, D.2, D.4
- **Verify**: `pnpm test:coverage tests/unit/features/users-admin`
- **Done**: gestion de OTROS usuarios (`users.admin`: list-users, get-user,
  disable-user, enable-user, delete-user, force-logout, list-admin-actions)
  + tests. Solo admin (whitelist SSM `/portfolio/admin-emails`; no-admin
  recibe 404 NOT_FOUND, anti-enumeration).

#### D.4 — placeholder gestion CV (fase 14)
- **Archivos**:
  - `admin/src/app/(admin)/cv/page.tsx`
  - Tests mirror
- **AC**: AC-32
- **Depende de**: A.8, C.2
- **Paralelizable con**: D.1 - D.3
- **Verify**: `pnpm test:coverage tests/unit/app/cv`
- **Done**: page placeholder + link en el sidebar (provisto por C.1) + nota
  "plan futuro c-cv-management". SIN backend ni UI de edicion.

### Bloque E — Infraestructura de deploy (paralelizable con D parcialmente)

#### E.1 — devtools/cloudflare_setup extension (fase 15)
- **Archivos**:
  - `devtools/cloudflare_setup/config.py` (modify: agregar `AppConfig` admin)
  - `devtools/cloudflare_setup/README.md` (mencionar admin)
- **AC**: AC-33
- **Depende de**: A.2 (existe el package)
- **Paralelizable con**: D.* (toca archivos Python, no TS)
- **Verify**: `python devtools/run.py cloudflare_setup projects --env=dev --dry-run` (la fase `status` NO existe; las fases validas son projects / domains / triggers / all)
- **Done**: dry-run lista `admin` como 7mo project con app_type='nextjs' + build_output_dir='out' (projects `portfolio-admin` / `-dev` / `-stage`)

#### E.2 — devtools/sync_secrets + docker/env extension (fase 16)
- **Archivos**:
  - `devtools/sync_secrets/catalog.py` (modify)
  - `docker/env/client/.example` (modify: agregar NEXT_PUBLIC_*)
- **AC**: AC-33
- **Depende de**: A.2
- **Paralelizable con**: D.*, E.1
- **Verify**: `python devtools/run.py sync_secrets --env=dev --category=client --dry-run`
- **Done**: dry-run muestra las 4 keys nuevas

#### E.3 — GH Actions workflows extension (fase 17)
- **Archivos**:
  - `.github/workflows/deploy-apps.yml` (modify: matrix include admin + env vars NEXT_PUBLIC_*)
  - `.github/workflows/ci.yml` (modify: filter incluye admin)
  - `.claude/docs/subdomain-standard/02-naming-rules.md` (modify: agregar `admin` a reserved)
- **AC**: AC-33, AC-34
- **Depende de**: E.1, E.2
- **Paralelizable con**: D.* (yaml + md, no codigo)
- **Verify**: `act -W .github/workflows/ci.yml` (con skill github-actions)
- **Done**: workflows YAML validos + ci local pasa

### Bloque F — E2E + cierre (secuencial al final)

#### F.1 — Playwright E2E specs (fase 18)
- **Archivos**:
  - `tests/feature/admin/01-login-magic-link.spec.ts`
  - `tests/feature/admin/02-register-verify-code.spec.ts`
  - `tests/feature/admin/03-callback-fragment-hash.spec.ts`
  - `tests/feature/admin/04-auth-guard-redirect.spec.ts`
  - `tests/feature/admin/05-logout-multi-tab.spec.ts`
  - `tests/feature/admin/06-settings-profile-update.spec.ts`
  - `tests/feature/admin/07-sessions-mgmt-revoke.spec.ts`
- **AC**: AC-35
- **Depende de**: TODAS las B, C, D
- **Paralelizable con**: ninguna (necesita el stack completo)
- **Verify**: `python devtools/run.py docker up --env=local && python devtools/run.py test_runner --module=feature --type=feature --env=local`
- **Done**: 7 specs E2E verdes. NO hay spec de metricas (la UI de metricas es
  del plan b-analytics-api). El cambio de password NO tiene spec E2E real
  (bloqueado por el gap de backend; cubierto solo por MSW en unit).

#### F.2 — Verificacion E2E iterativa (fase 19) — la ultima
- **Archivos**: ninguno nuevo. Es la fase de verify-before-done + limpieza de `docs/specs/a-admin/`.
- **AC**: AC-35, AC-36 + TODOS los AC del plan
- **Depende de**: F.1 + TODAS
- **Paralelizable con**: ninguna
- **Verify**: bateria completa de la seccion 11
- **Done**: bateria verde + `git rm -r docs/specs/a-admin/` committed

## Diagrama de paralelizacion

```text
A.1 -> A.2 -> A.3 -> A.4 -> A.5 -> A.6 -> A.7 -> A.8
                                            |
                +---------------------------+----+
                |                                |
              B.1 (auth store/lib/api)        C.1 (admin-shell)
                |                                |
              B.2 (auth hooks)                   |
                |                                |
              B.3 (auth components) -----+      |
                                          v      |
                                    C.2 (layout)<+
                                          |
              B.4 (auth pages) <----------+
                                          |
                +-------------------------+----------+-------------+
                |               |              |               |
              D.1 settings  D.2 sessions   D.3 users      D.4 cv
                |             -mgmt         -admin         placeholder
                +-------------+--------------+---------------+----+
                |                                                 |
                +-------------------------------------------------+
                                          |
              (mientras tanto en otra worktree: E.1, E.2, E.3 paralelo a D)
                                          |
                                       F.1 (E2E Playwright) — necesita TODAS
                                          |
                                       F.2 (verificacion + limpieza) — gate del PR
```

## Granularidad

Total tareas: **23** (A.1-A.8 = 8, B.1-B.4 = 4, C.1-C.2 = 2, D.1-D.4 = 4, E.1-E.3 = 3, F.1-F.2 = 2).

Plan Large = 10-20 tareas. Con 23 tareas el plan esta por encima del
limite alto, justificado por el scope: scaffold + auth completo (26
actions) + app shell + 4 features de gestion (settings/sessions-mgmt/
users-admin/cv placeholder) + infra de deploy + E2E. Bajo respecto del
plan original (26) porque las 7 features de METRICAS se movieron a
`b-analytics-api`; subio por las features de gestion de usuarios
(settings + sessions-mgmt + users-admin) que el scope nuevo agrega. La
paralelizacion via worktrees (ver seccion 10) consolida D.* en 2-4
worktrees concurrentes (limite recomendado por
`.claude/rules/plan-format.md` capitulo 1).

## Lanzar worktrees (ejemplo)

```bash
# Desde la rama feature/admin-frontend, despues de A.8 + B.3 + C.2.
# CADA worktree usa SU PROPIA branch (-b) — no se puede reutilizar
# feature/admin-frontend porque esa branch ya esta checked out en el
# worktree principal y git lo rechaza (`fatal: ... is already checked out`).

git worktree add -b feature/admin-wt-settings      ../portfolio-wt-settings      feature/admin-frontend
git worktree add -b feature/admin-wt-sessions-mgmt ../portfolio-wt-sessions-mgmt feature/admin-frontend
git worktree add -b feature/admin-wt-users-admin   ../portfolio-wt-users-admin   feature/admin-frontend
git worktree add -b feature/admin-wt-devtools      ../portfolio-wt-devtools      feature/admin-frontend

# Cada worktree commitea a SU branch. Despues del verify del scope, el
# worktree principal mergea cada branch a feature/admin-frontend
# con merge commit (sin rebase, ver .claude/rules/git-workflow.md):
#   cd ../portfolio
#   git checkout feature/admin-frontend
#   git merge --no-ff feature/admin-wt-settings
#   git push origin feature/admin-frontend
# Despues del merge, eliminar la branch del worktree (local + remoto).

# Al terminar todas las worktrees:
git worktree remove ../portfolio-wt-settings
git worktree remove ../portfolio-wt-sessions-mgmt
git worktree remove ../portfolio-wt-users-admin
git worktree remove ../portfolio-wt-devtools

# Limpiar branches mergeadas
git branch -d feature/admin-wt-settings feature/admin-wt-sessions-mgmt feature/admin-wt-users-admin feature/admin-wt-devtools
git push origin --delete feature/admin-wt-settings feature/admin-wt-sessions-mgmt feature/admin-wt-users-admin feature/admin-wt-devtools
```

Ver detalle en [10-paralelizacion-worktrees.md](10-paralelizacion-worktrees.md).

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Paralelizar A.* | Tocan archivos centrales (package.json, configs) | Secuencial |
| Paralelizar D.1 con D.2 sin completar B.1 + B.3 antes | Auth store y `TotpSetup`/`RecoveryCodesModal` no existen, falla import | Esperar B.1 + B.3 |
| Implementar pantallas de metricas en a-admin | El scope de metricas es del plan b-analytics-api | Aqui solo el link en el sidebar (C.1) |
| Confundir `sessions-mgmt` (mis sesiones auth) con `sessions` (tracking de visitantes) | Son features de planes distintos | `sessions-mgmt` en a-admin, `sessions` en b-analytics-api |
| Implementar cambio de password contra un endpoint inexistente | No hay action de backend para user autenticado | UI + MSW; documentar la dependencia de backend |
| Paralelizar mas de 7 worktrees | Cognitive overhead + memoria de la maquina | Max 5-7 |
| Crear commit en una worktree sin re-run de tests | Romper otra worktree | Verify antes de commit |
| F.1 antes de TODAS las D.* | Specs E2E necesitan stack completo | Esperar |

[< 07-settings-features](07-settings-features.md) | [Siguiente: 09-commits >](09-commits.md)
