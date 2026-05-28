# 09 — Commits incrementales

[< 08-descomposicion](08-descomposicion.md) | [Siguiente: 10-paralelizacion-worktrees >](10-paralelizacion-worktrees.md)

## Reglas duras

- Cada commit deja el repo verde (lint + typecheck + tests del scope).
- Conventional Commits en **espanol** (subject + body imperativo).
- Sin atribucion de IA. Sin emojis.
- Primer commit: la carpeta del plan. Ultimo commit: verificacion E2E
  + `git rm -r docs/specs/dashboard/`.
- PR unico `feature/dashboard-frontend -> dev` con merge commit.

## Secuencia de commits

### 1. Plan committed

```text
docs(specs): agrega plan dashboard SPA admin.portfolio

- Plan Large (~21 fases) para construir el dashboard admin SPA en Next.js 16.2.6 + React 19.2.6 (compiler stable) + shadcn/ui + Tanstack Query v5 + Zustand 5 con persist en localStorage, deployado a Cloudflare Pages en admin.portfolio.{dev|stage|prod}.the-full-stack.com
- Carpeta docs/specs/dashboard/ con README + 11 secciones (contexto, diagramas, estructura, setup-base, ui, auth, dashboard-features, descomposicion, commits, worktrees, verificacion-e2e)
- Scope: SOLO frontend. APIs auth (planes 01-02) y analytics (analytics-dashboard-api) se asumen existentes; MSW provee mocks hasta deploy
- 33 criterios de aceptacion numerados, todos referenciados por tests
```

**Verify**: `ls docs/specs/dashboard/README.md` + revisar paths internos OK

### 2. Skill + rule + knowledge tree

```text
docs(dashboard): agrega skill /dashboard-stack + rule + knowledge tree

- Skill .claude/skills/dashboard-stack/SKILL.md invocable manualmente, con resumen ejecutivo + comandos canonicos
- Rule .claude/rules/dashboard.md con reglas SIEMPRE/NUNCA enforced (estructura Hybrid Atomic Design, auth, UI, deploy, env vars, tests)
- Knowledge tree .claude/docs/dashboard/ con README + 6 capitulos (stack, structure, ui, auth, deploy, testing) totalizando ~3500 lineas
- Validar invocacion con: claude --permission-mode bypassPermissions --disallowedTools WebSearch WebFetch --strict-mcp-config --mcp-config '{"mcpServers":{}}' --output-format json -p "como armo el dashboard SPA del portfolio"
```

**Verify**: `claude -p "dashboard structure"` y `claude -p "next.js 16 spa"` invocan la skill

### 3. Scaffold base (fase 1)

```text
feat(dashboard): scaffold inicial Next.js 16 SPA en carpeta dashboard/

- Agrega dashboard/ a pnpm-workspace.yaml como @portfolio/dashboard
- package.json con engines node>=24, scripts dev/build/lint/typecheck/test, deps Next 16.2.6 + React 19.2.6 + react-is@19.2.6 (override Recharts) + Tanstack Query v5.52.3 + Tanstack Table v8.20.5 + shadcn + Zustand 5.0.14 + sonner 1.7.2 + lucide 0.416.0
- next.config.ts con output: 'export', images.unoptimized, trailingSlash, poweredByHeader: false, reactCompiler: true
- tsconfig.json strict + noUncheckedIndexedAccess + paths @/* -> ./src/*
- biome.json extends del root con override en src/components/ui/** (shadcn primitives no respetan reglas strict)
- postcss.config.mjs (@tailwindcss/postcss), vitest.config.ts (happy-dom + coverage)
- Cumple AC-1, AC-2, AC-3
```

**Verify**:
```bash
pnpm install
pnpm --filter @portfolio/dashboard typecheck
pnpm --filter @portfolio/dashboard lint
```

### 4. Tokens + theme (fase 2)

```text
feat(dashboard): tokens CSS dark/light + theme provider con next-themes

- src/styles/globals.css con @import tailwind + @fontsource (Space Grotesk + Space Mono) + tokens HSL para :root (dark) y [data-theme="light"] + @theme inline mapping + @layer base + prefers-reduced-motion
- src/providers/theme-provider.tsx con next-themes attribute="data-theme" defaultTheme="system" enableSystem disableTransitionOnChange
- src/components/ui/theme-toggle.tsx con DropdownMenu Sun/Moon/Monitor
- Tokens reflejan los del DS del monorepo (.claude/rules/design-system.md)
- Cumple AC-5, AC-6
```

**Verify**: `pnpm --filter @portfolio/dashboard build` (CSS compila)

### 5. shadcn init + primitivos (fase 3)

```text
feat(dashboard): shadcn init + 24 primitivos UI (Radix + Tailwind v4)

- components.json con style new-york, rsc false (export mode), baseColor zinc, aliases @/components/ui y @/lib/utils
- Agrega via pnpm dlx shadcn@latest add: alert, badge, button, calendar, card, chart, checkbox, command, dialog, dropdown-menu, form, input, input-otp, label, popover, select, separator, sheet, skeleton, sonner, switch, table, tabs, tooltip
- Deps Radix instaladas automaticamente por shadcn CLI
```

**Verify**: `pnpm --filter @portfolio/dashboard lint && pnpm --filter @portfolio/dashboard build`

### 6. Custom UI primitives (fase 4)

```text
feat(dashboard,ui): primitivos custom genericos (MetricCard, DataTable, DateRangePicker, EmptyState)

- src/components/ui/metric-card.tsx con title/value/delta/trend/icon
- src/components/ui/data-table.tsx wrapper generico de Tanstack Table v8 con sort + paginator
- src/components/ui/date-range-picker.tsx con Popover + Calendar (range, default last 30d)
- src/components/ui/empty-state.tsx con icon + title + description + action
- src/components/ui/error-alert.tsx con shadcn Alert variant=destructive + retry button
- src/components/ui/loading-spinner.tsx accesible (role=status, aria-label)
- src/components/ui/index.ts barrel
- src/lib/utils.ts con cn() de shadcn (clsx + tailwind-merge)
- Tests unit con coverage >= 80% en cada primitivo
- Cumple AC-21, AC-23
```

**Verify**: `pnpm --filter @portfolio/dashboard test:coverage tests/unit/components/ui`

### 7. Lib base (fase 5)

```text
feat(dashboard,lib): env validation + api-client con mutex refresh + types

- src/lib/env.ts con Zod schema valida NEXT_PUBLIC_API_ENDPOINT, NEXT_PUBLIC_TURNSTILE_SITEKEY, NEXT_PUBLIC_DASHBOARD_URL, NEXT_PUBLIC_AUTH_REFRESH_LEAD_MS (fail-fast en build)
- src/lib/api-client.ts con apiFetch wrapper + ApiError class + auth interceptor + mutex refresh + flags skipAuth/skipRefresh
- src/lib/routes.ts con constantes ROUTES.dashboard.*, ROUTES.auth.*
- src/lib/format/{date,number,duration}.ts (formatDate, formatNumber, formatPercent, formatDurationMs)
- src/lib/validation/{auth,filters}.ts (Zod schemas reusables)
- src/types/{api,models}.ts (responses tipadas y domain models)
- Tests unit con coverage >= 90% (critico: test mutex con 5 requests concurrent que solo dispara 1 refresh)
- Cumple AC-14
```

**Verify**: `pnpm --filter @portfolio/dashboard test:coverage tests/unit/lib`

### 8. Providers + RootLayout (fase 6)

```text
feat(dashboard,providers): RootLayout con Theme + Query (persister con lz-string)

- src/providers/query-provider.tsx con QueryClient (refetchOnWindowFocus false, retry sin 401/403/422) + PersistQueryClientProvider con lz-string compression + dehydrate filter (no persistir contacts list ni events list)
- src/providers/root-providers.tsx compone ThemeProvider > QueryProvider
- src/app/layout.tsx con RootLayout (html lang es, suppressHydrationWarning) + RootProviders + Toaster (sonner top-right richColors) + import @/lib/env (fail-fast) + metadata robots noindex nofollow
- src/app/{page,error,global-error,not-found}.tsx (home redirect, boundaries, 404)
- Cumple AC-4
```

**Verify**: `pnpm --filter @portfolio/dashboard build` + preview en localhost:3000

### 9. MSW setup + Vitest setup (fase 9, antes de features para usar en tests)

```text
feat(dashboard,tests): MSW handlers (auth + analytics) + Vitest setup + render wrapper

- tests/setup.ts: import @testing-library/jest-dom + polyfill BroadcastChannel + vi.stubEnv NEXT_PUBLIC_* + server.listen/resetHandlers/close + reset Zustand entre tests
- tests/mocks/server.ts (setupServer Node) + tests/mocks/browser.ts (setupWorker browser dev)
- tests/mocks/handlers/auth.ts: registerStart, verify-code, loginStart, sessionRefresh, logout (con makeJwt helper)
- tests/mocks/handlers/analytics.ts: overview, timeseries, sessions list, etc.
- tests/utils/render.tsx wrapper con ThemeProvider + QueryClient de test + Toaster
- tests/fixtures/{users,sessions,events,analytics}.ts data sintetica
- public/mockServiceWorker.js generado con npx msw init public/
- Cumple AC-33 (base infrastructure)
```

**Verify**: `pnpm --filter @portfolio/dashboard test` (setup OK aunque no haya tests aun)

### 10. Auth store + lib + api (fase 7 parte 1)

```text
feat(dashboard,auth): Zustand store + refresh mutex + broadcast + auth-client typed

- src/features/auth/store/use-auth-store.ts con persist partialize (solo user + refreshExpiry, NUNCA accessToken)
- src/features/auth/lib/refresh-mutex.ts singleton in-flight Promise
- src/features/auth/lib/broadcast.ts BroadcastChannel helpers (LOGOUT, TOKEN_REFRESH) con guard SSR
- src/features/auth/lib/token-expiry.ts (getJwtExpiry, isJwtExpired)
- src/features/auth/api/auth-client.ts: 10 endpoints typed (register/login/verify/session)
- src/features/auth/api/query-keys.ts
- src/features/auth/types.ts (User, AuthResponse, Method, MfaMethod)
- Tests unit con coverage >= 90% (critico mutex test, store test, broadcast guard test)
- Cumple AC-14, AC-17, AC-18
```

**Verify**: `pnpm --filter @portfolio/dashboard test:coverage tests/unit/features/auth/{store,lib,api}`

### 11. Auth hooks (fase 7 parte 2)

```text
feat(dashboard,auth): 12 hooks Tanstack (login/register/verify/logout/refresh/auth-timer/multi-tab-sync)

- src/features/auth/hooks/use-{register-start,register-verify-code,login-start,login-verify-code,login-verify-totp,set-password,resend-code,session-refresh,logout}.ts (useMutation con onSuccess/onError + toast + redirect)
- src/features/auth/hooks/use-auth-timer.ts auto-refresh proactivo (setTimeout basado en jwt exp + lead ms) + Page Visibility API re-check
- src/features/auth/hooks/use-multi-tab-sync.ts BroadcastChannel listener (LOGOUT, TOKEN_REFRESH)
- src/features/auth/hooks/use-protected-route.ts hook alternativo al AuthGuard component
- Tests unit con fake timers y mock BroadcastChannel
- Cumple AC-15, AC-16, AC-17, AC-18
```

**Verify**: `pnpm --filter @portfolio/dashboard test tests/unit/features/auth/hooks`

### 12. Auth components (fase 7 parte 3)

```text
feat(dashboard,auth): 10 componentes (LoginForm, RegisterForm, VerifyCodeInput, AuthGuard, TurnstileWidget, ...)

- src/features/auth/components/{login-form,register-form}.tsx con react-hook-form + Zod + shadcn Form + TurnstileWidget
- src/features/auth/components/verify-code-input.tsx con shadcn InputOTP 8 chars alfabeto Crockford
- src/features/auth/components/magic-link-prompt.tsx con button Reenviar (useResendCode)
- src/features/auth/components/set-password-form.tsx con Zod refine confirmPassword
- src/features/auth/components/auth-guard.tsx con AuthGuard HOC (redirect /login?next=... si !isAuthenticated)
- src/features/auth/components/turnstile-widget.tsx wrapper @marsidev/react-turnstile
- src/features/auth/components/{totp-setup,recovery-codes-modal,webauthn-register-button}.tsx (plan 02, opcional)
- src/features/auth/index.ts barrel
- Tests unit con BDD-style + coverage >= 80%
- Cumple AC-8, AC-9, AC-10, AC-11, AC-19, AC-20, AC-26
```

**Verify**: `pnpm --filter @portfolio/dashboard test:coverage tests/unit/features/auth`

### 13. Auth pages (fase 8)

```text
feat(dashboard,auth): pages (auth)/ login/register/verify/callback/set-password

- src/app/(auth)/login/page.tsx con LoginForm + link a /register
- src/app/(auth)/register/page.tsx con RegisterForm + link a /login
- src/app/(auth)/verify/page.tsx con Suspense + Tabs (code | magic-link) basado en ?flow= param
- src/app/(auth)/callback/page.tsx CRITICO: decodea window.location.hash (fragment), valida JWT shape, guarda en Zustand, history.replaceState para limpiar URL, redirect /dashboard. useRef guard para StrictMode
- src/app/(auth)/set-password/page.tsx con SetPasswordForm
- Cumple AC-12, AC-13
```

**Verify**: `pnpm --filter @portfolio/dashboard build && curl preview /login` (200)

### 14. Dashboard shell + layout protegido (fase 10)

```text
feat(dashboard,shell): Sidebar + Header + MobileSidebar + (dashboard)/layout con AuthGuard

- src/features/dashboard-shell/components/sidebar.tsx con lucide icons + nav items (10 destinos) + active state segun pathname
- src/features/dashboard-shell/components/header.tsx con breadcrumb dinamico + ThemeToggle + UserMenu (dropdown logout)
- src/features/dashboard-shell/components/mobile-sidebar.tsx con shadcn Sheet
- src/features/dashboard-shell/lib/nav-items.ts array con {href, label, icon}
- src/app/(dashboard)/layout.tsx con AuthGuard wrappeando Sidebar + Header + main
- Cumple AC-7, AC-19, AC-20
```

**Verify**: navegar entre pages mantiene sidebar (no remontaje)

### 15-21. Features data (fases 11-16) — paralelizables

Commits paralelos en worktrees distintas (D.1 - D.7). Cada uno
similar:

```text
feat(dashboard,analytics): 7 hooks + 8 componentes (Overview, Timeseries, TopPages, ...) + filters store + 2 pages

- 7 hooks useQuery con queryKeys estructurados + staleTime adaptado al cache backend (60s agregadas, 10s active-now)
- 7+ componentes (OverviewCards, TimeseriesChart, TopPagesChart, TopReferrersTable, TopNichesChart, ActiveNowCard, RetentionChart, AnalyticsFilters)
- Zustand local store useAnalyticsFiltersStore (date_range, niche, eventType) con persist sessionStorage
- Pages src/app/(dashboard)/page.tsx (overview) + src/app/(dashboard)/analytics/page.tsx (full)
- Tests unit con coverage >= 80% per-file
- Cumple AC-21, AC-22
```

Idem para `sessions`, `events`, `visits/geo`, `devices/funnel`,
`contacts`, `settings`. **7 commits paralelos en worktrees**.

### 22. Devtools cloudflare_setup extension (fase 17)

```text
feat(devtools,dashboard): extiende cloudflare_setup para soportar app_type='nextjs'

- devtools/cloudflare_setup/config.py: agrega APP_DASHBOARD (AppConfig con root_dir='dashboard', app_type='nextjs', build_output_dir='out')
- Funciones output_dir_for() y env_vars_for() respetan app_type
- custom_domain_for(): admin.portfolio.{env}.the-full-stack.com (prod sin sufijo)
- env_vars del project Pages incluye NEXT_PUBLIC_* para dashboard
- devtools/cloudflare_setup/README.md menciona el dashboard como 7mo app
- Cumple AC-30
```

**Verify**: `python devtools/run.py cloudflare_setup status --env=dev --dry-run`

### 23. Devtools sync_secrets + docker/env (fase 18)

```text
feat(devtools,dashboard): extiende sync_secrets catalog con NEXT_PUBLIC_*

- devtools/sync_secrets/catalog.py: agrega 4 SecretDefinition (NEXT_PUBLIC_API_ENDPOINT, NEXT_PUBLIC_TURNSTILE_SITEKEY, NEXT_PUBLIC_DASHBOARD_URL, NEXT_PUBLIC_AUTH_REFRESH_LEAD_MS)
- docker/env/client/.example: agrega placeholders para los 4 nuevos
```

**Verify**: `python devtools/run.py sync_secrets --env=dev --category=client --dry-run`

### 24. GH Actions workflows extension (fase 19)

```text
feat(ci,dashboard): extiende deploy-apps.yml matrix con dashboard + agrega admin a subdomain reserved

- .github/workflows/deploy-apps.yml: matrix include {name: dashboard, dist-dir: dashboard/out, project: dashboard} en deploy-pages + verify-deploy. Job build-apps lee NEXT_PUBLIC_* desde vars + ejecuta workspace-concurrency=7 (6 Astro + 1 Next)
- .github/workflows/ci.yml: filter incluye @portfolio/dashboard en lint + build
- .claude/docs/subdomain-standard/02-naming-rules.md: agrega 'admin' a reserved components
- Cumple AC-30, AC-31
```

**Verify**: `act -W .github/workflows/ci.yml` (con skill github-actions)

### 25. E2E Playwright (fase 20)

```text
test(dashboard,e2e): 7 specs Playwright para flujos golden path

- tests/feature/dashboard/01-login-magic-link.spec.ts
- tests/feature/dashboard/02-register-verify-code.spec.ts
- tests/feature/dashboard/03-callback-fragment-hash.spec.ts (critico: verifica hash limpio del URL post-decoder)
- tests/feature/dashboard/04-auth-guard-redirect.spec.ts (verifica next param)
- tests/feature/dashboard/05-logout-multi-tab.spec.ts (BroadcastChannel)
- tests/feature/dashboard/06-analytics-navigation.spec.ts
- tests/feature/dashboard/07-sessions-table-pagination.spec.ts
- Corren contra stack local con MSW habilitado (NEXT_PUBLIC_USE_MSW=true)
- Cumple AC-32
```

**Verify**: `python devtools/run.py docker up --env=local && python devtools/run.py test_runner --module=feature --type=feature --env=local`

### 26. Verificacion E2E iterativa + cleanup (fase 21) — ultimo commit

```text
chore(dashboard): verificacion E2E completa + elimina docs/specs/dashboard/

- Bateria completa pasa: lint + typecheck + unit + coverage (>= 80%) + build + E2E + smoke deploy a dev
- Elimina docs/specs/dashboard/ (plan efimero). El conocimiento permanente vive en:
  - .claude/rules/dashboard.md
  - .claude/skills/dashboard-stack/SKILL.md
  - .claude/docs/dashboard/ (7 archivos)
- Cumple TODOS los AC (1-33)
```

**Verify**: ver seccion 11.

## Resumen secuencia (sin paralelizacion)

```text
01. plan committed
02. skill + rule + KT
03. scaffold base                  <- secuencial (A.2)
04. tokens + theme                 <- secuencial (A.3)
05. shadcn primitivos              <- secuencial (A.4)
06. custom UI primitives           <- secuencial (A.5)
07. lib base                       <- secuencial (A.6)
08. providers + RootLayout         <- secuencial (A.7)
09. MSW setup                      <- secuencial (A.8)
10-13. auth (store/lib/api -> hooks -> components -> pages)    <- secuencial (B.*)
14. dashboard-shell + layout       <- secuencial (C.*)
15-21. features data (D.1 - D.7)   <- PARALELO (max 5-7 worktrees)
22. devtools cloudflare_setup      <- paralelo a D.*
23. devtools sync_secrets          <- paralelo a D.*
24. GH Actions workflows           <- depende de 22 + 23
25. E2E Playwright                 <- secuencial (F.1, depende de TODAS)
26. verificacion + cleanup         <- secuencial (F.2, el ultimo)
```

26 commits totales. Con paralelizacion via worktrees el wall-clock se
reduce significativamente en las fases D.*.

## PR

Un solo PR `feature/dashboard-frontend -> dev`. Merge commit
(`gh pr merge --merge --delete-branch`). Sin atribucion IA en el body.

Despues, promocion `dev -> stage` y `stage -> main` via PRs separados
con merge commit (sin `--delete-branch` — `dev`/`stage` son
permanentes).

[< 08-descomposicion](08-descomposicion.md) | [Siguiente: 10-paralelizacion-worktrees >](10-paralelizacion-worktrees.md)
