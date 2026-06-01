# 09 — Commits incrementales

[< 08-descomposicion](08-descomposicion.md) | [Siguiente: 10-paralelizacion-worktrees >](10-paralelizacion-worktrees.md)

## Reglas duras

- Cada commit deja el repo verde (lint + typecheck + tests del scope).
- Conventional Commits en **espanol** (subject + body imperativo).
- Sin atribucion de IA. Sin emojis.
- Primer commit: la carpeta del plan. Ultimo commit: verificacion E2E
  + `git rm -r docs/specs/a-admin/`.
- PR unico `feature/admin-frontend -> dev` con merge commit.

## Secuencia de commits

### 1. Plan committed

```text
docs(specs): agrega plan Admin SPA admin.portfolio

- Plan Large para construir el panel Admin SPA en Next.js 16.2.6 + React 19.2.6 (compiler stable) + shadcn/ui + Tanstack Query v5 + Zustand 5 con persist en localStorage, deployado a Cloudflare Pages en admin.portfolio.{dev|stage|prod}.the-full-stack.com
- Carpeta docs/specs/a-admin/ con README + 11 secciones (contexto, diagramas, estructura, setup-base, ui, auth, settings-features, descomposicion, commits, worktrees, verificacion-e2e)
- Scope: SOLO frontend de gestion (app shell + auth + settings + sessions-mgmt + users-admin + placeholder CV). El API auth YA esta desplegado (serverless/lambda/services/auth/, 26 actions invocables) + el Lambda users (15 actions); la UI de metricas y el Lambda analytics viven en el plan b-analytics-api
- Criterios de aceptacion numerados, todos referenciados por tests
```

**Verify**: `ls docs/specs/a-admin/README.md` + revisar paths internos OK

### 2. Skill + rule + knowledge tree

```text
docs(admin): agrega skill /admin-stack + rule + knowledge tree

- Skill .claude/skills/admin-stack/SKILL.md invocable manualmente, con resumen ejecutivo + comandos canonicos
- Rule .claude/rules/admin.md con reglas SIEMPRE/NUNCA enforced (estructura Hybrid Atomic Design, auth, UI, deploy, env vars, tests)
- Knowledge tree .claude/docs/admin/ con README + 6 capitulos (stack, structure, ui, auth, deploy, testing) totalizando ~3500 lineas
- Validar invocacion con: claude --permission-mode bypassPermissions --disallowedTools WebSearch WebFetch --strict-mcp-config --mcp-config '{"mcpServers":{}}' --output-format json -p "como armo el Admin SPA del portfolio"
```

**Verify**: `claude -p "admin structure"` y `claude -p "next.js 16 spa"` invocan la skill

### 3. Scaffold base (fase 1)

```text
feat(admin): scaffold inicial Next.js 16 SPA en carpeta admin/

- Agrega admin/ a pnpm-workspace.yaml como @portfolio/admin
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
pnpm --filter @portfolio/admin typecheck
pnpm --filter @portfolio/admin lint
```

### 4. Tokens + theme (fase 2)

```text
feat(admin): tokens CSS dark/light + theme provider con next-themes

- src/styles/globals.css con @import tailwind + @fontsource (Space Grotesk + Space Mono) + tokens HSL para :root (dark) y [data-theme="light"] + @theme inline mapping + @layer base + prefers-reduced-motion
- src/providers/theme-provider.tsx con next-themes attribute="data-theme" defaultTheme="system" enableSystem disableTransitionOnChange
- src/components/ui/theme-toggle.tsx con DropdownMenu Sun/Moon/Monitor
- Tokens reflejan los del DS del monorepo (.claude/rules/design-system.md)
- Cumple AC-5, AC-6
```

**Verify**: `pnpm --filter @portfolio/admin build` (CSS compila)

### 5. shadcn init + primitivos (fase 3)

```text
feat(admin): shadcn init + 24 primitivos UI (Radix + Tailwind v4)

- components.json con style new-york, rsc false (export mode), baseColor zinc, aliases @/components/ui y @/lib/utils
- Agrega via pnpm dlx shadcn@latest add: alert, badge, button, calendar, card, chart, checkbox, command, dialog, dropdown-menu, form, input, input-otp, label, popover, select, separator, sheet, skeleton, sonner, switch, table, tabs, tooltip
- Deps Radix instaladas automaticamente por shadcn CLI
```

**Verify**: `pnpm --filter @portfolio/admin lint && pnpm --filter @portfolio/admin build`

### 6. Custom UI primitives (fase 4)

```text
feat(admin,ui): primitivos custom genericos (DataTable, DateRangePicker, EmptyState)

- src/components/ui/data-table.tsx wrapper generico de Tanstack Table v8 con sort + paginator
- src/components/ui/date-range-picker.tsx con Popover + Calendar (range, default last 30d)
- src/components/ui/empty-state.tsx con icon + title + description + action
- src/components/ui/error-alert.tsx con shadcn Alert variant=destructive + retry button
- src/components/ui/loading-spinner.tsx accesible (role=status, aria-label)
- src/components/ui/index.ts barrel
- src/lib/utils.ts con cn() de shadcn (clsx + tailwind-merge)
- NOTA: MetricCard (especifico de metricas) NO va aqui — vive en b-analytics-api
- Tests unit con coverage >= 80% en cada primitivo
- Cumple AC-23
```

**Verify**: `pnpm --filter @portfolio/admin test:coverage tests/unit/components/ui`

### 7. Lib base (fase 5)

```text
feat(admin,lib): env validation + api-client con mutex refresh + types

- src/lib/env.ts con Zod schema valida NEXT_PUBLIC_API_ENDPOINT, NEXT_PUBLIC_TURNSTILE_SITEKEY, NEXT_PUBLIC_ADMIN_URL, NEXT_PUBLIC_AUTH_REFRESH_LEAD_MS (fail-fast en build)
- src/lib/api-client.ts con apiFetch wrapper + ApiError class + auth interceptor + mutex refresh + flags skipAuth/skipRefresh
- src/lib/routes.ts con constantes ROUTES.admin.*, ROUTES.auth.*
- src/lib/format/{date,number,duration}.ts (formatDate, formatNumber, formatPercent, formatDurationMs)
- src/lib/validation/{auth,filters}.ts (Zod schemas reusables)
- src/types/{api,models}.ts (responses tipadas y domain models)
- Tests unit con coverage >= 90% (critico: test mutex con 5 requests concurrent que solo dispara 1 refresh)
- Cumple AC-14
```

**Verify**: `pnpm --filter @portfolio/admin test:coverage tests/unit/lib`

### 8. Providers + RootLayout (fase 6)

```text
feat(admin,providers): RootLayout con Theme + Query (persister con lz-string)

- src/providers/query-provider.tsx con QueryClient (refetchOnWindowFocus false, retry sin 401/403/422) + PersistQueryClientProvider con lz-string compression + dehydrate filter (no persistir datos sensibles)
- src/providers/root-providers.tsx compone ThemeProvider > QueryProvider
- src/app/layout.tsx con RootLayout (html lang es, suppressHydrationWarning) + RootProviders + Toaster (sonner top-right richColors) + import @/lib/env (fail-fast) + metadata robots noindex nofollow
- src/app/{page,error,global-error,not-found}.tsx (home redirect, boundaries, 404)
- Cumple AC-4
```

**Verify**: `pnpm --filter @portfolio/admin build` + preview en localhost:3000

### 9. MSW setup + Vitest setup (fase 9, antes de features para usar en tests)

```text
feat(admin,tests): MSW handlers (auth + users) + Vitest setup + render wrapper

- tests/setup.ts: import @testing-library/jest-dom + polyfill BroadcastChannel + vi.stubEnv NEXT_PUBLIC_* + server.listen/resetHandlers/close + reset Zustand entre tests
- tests/mocks/server.ts (setupServer Node) + tests/mocks/browser.ts (setupWorker browser dev)
- tests/mocks/handlers/auth.ts: registerStart, verify-code, loginStart, sessionRefresh, logout, mfa.*, webauthn.* (con makeJwt helper)
- tests/mocks/handlers/users.ts: profile.{get,update,change-email,confirm-email-change,delete-account}, status.{get,list-sessions,revoke-session}, admin.{list-users,get-user,disable-user,enable-user,delete-user,force-logout,list-admin-actions}
- tests/utils/render.tsx wrapper con ThemeProvider + QueryClient de test + Toaster
- tests/fixtures/{users,sessions,admin-actions}.ts data sintetica
- public/mockServiceWorker.js generado con npx msw init public/
- NOTA: los mocks de metricas (analytics/events/visits/geo/...) viven en b-analytics-api
- Cumple AC base de infraestructura de tests
```

**Verify**: `pnpm --filter @portfolio/admin test` (setup OK aunque no haya tests aun)

### 10. Auth store + lib + api (fase 7 parte 1)

```text
feat(admin,auth): Zustand store + refresh mutex + broadcast + auth-client typed

- src/features/auth/store/use-auth-store.ts con persist partialize (solo refreshToken + refreshExpiry + user; NUNCA accessToken ni tempToken — rotan/expiran y dejarian estado stale tras reload). Bootstrap: `useAuthTimer` hidrata accessToken en memoria via /session/refresh al detectar refreshToken + refreshExpiry > now
- src/features/auth/lib/refresh-mutex.ts singleton in-flight Promise
- src/features/auth/lib/broadcast.ts BroadcastChannel helpers (LOGOUT, TOKEN_REFRESH) con guard SSR
- src/features/auth/lib/token-expiry.ts (getJwtExpiry, isJwtExpired)
- src/features/auth/api/auth-client.ts: las 26 actions del Lambda auth desplegado typed (register 3 + login 5 + verify 2 + session 2 + mfa 8 + webauthn 6). Shapes exactos de serverless/lambda/services/auth/core/{models,controllers}/ (ver .claude/docs/auth-system/)
- src/features/auth/api/query-keys.ts
- src/features/auth/types.ts (User, AuthResponse, Method, MfaMethod)
- Tests unit con coverage >= 90% (critico mutex test, store test, broadcast guard test)
- Cumple AC-14, AC-17, AC-18
```

**Verify**: `pnpm --filter @portfolio/admin test:coverage tests/unit/features/auth/{store,lib,api}`

### 11. Auth hooks (fase 7 parte 2)

```text
feat(admin,auth): 12 hooks Tanstack (login/register/verify/logout/refresh/auth-timer/multi-tab-sync)

- src/features/auth/hooks/use-{register-start,register-verify-code,login-start,login-verify-code,login-verify-totp,set-password,resend-code,session-refresh,logout}.ts (useMutation con onSuccess/onError + toast + redirect)
- src/features/auth/hooks/use-auth-timer.ts auto-refresh proactivo (setTimeout basado en jwt exp + lead ms) + Page Visibility API re-check
- src/features/auth/hooks/use-multi-tab-sync.ts BroadcastChannel listener (LOGOUT, TOKEN_REFRESH)
- src/features/auth/hooks/use-protected-route.ts hook alternativo al AuthGuard component
- Tests unit con fake timers y mock BroadcastChannel
- Cumple AC-15, AC-16, AC-17, AC-18
```

**Verify**: `pnpm --filter @portfolio/admin test tests/unit/features/auth/hooks`

### 12. Auth components (fase 7 parte 3)

```text
feat(admin,auth): 10 componentes (LoginForm, RegisterForm, VerifyCodeInput, AuthGuard, TurnstileWidget, ...)

- src/features/auth/components/{login-form,register-form}.tsx con react-hook-form + Zod + shadcn Form + TurnstileWidget
- src/features/auth/components/verify-code-input.tsx con shadcn InputOTP 8 chars alfabeto Crockford
- src/features/auth/components/magic-link-prompt.tsx con button Reenviar (useResendCode)
- src/features/auth/components/set-password-form.tsx con Zod refine confirmPassword
- src/features/auth/components/auth-guard.tsx con AuthGuard HOC (redirect /login?next=... si !isAuthenticated)
- src/features/auth/components/turnstile-widget.tsx wrapper @marsidev/react-turnstile
- src/features/auth/components/{totp-setup,confirm-totp-input,recovery-codes-modal}.tsx (setup-totp + confirm-totp + recovery-codes-generate)
- src/features/auth/components/{webauthn-register-button,webauthn-credentials-list}.tsx (register-options/verify + list-credentials/delete-credential)
- src/features/auth/components/{verify-totp-input,recovery-codes-consume-form}.tsx (login.verify-totp + mfa.recovery-codes-consume del flujo de login con MFA)
- src/features/auth/index.ts barrel
- Tests unit con BDD-style + coverage >= 80%
- Cumple AC-8, AC-9, AC-10, AC-11, AC-19, AC-20, AC-26
```

**Verify**: `pnpm --filter @portfolio/admin test:coverage tests/unit/features/auth`

### 13. Auth pages (fase 8)

```text
feat(admin,auth): pages (auth)/ login/register/verify/callback/set-password

- src/app/(auth)/login/page.tsx con LoginForm + link a /register
- src/app/(auth)/register/page.tsx con RegisterForm + link a /login
- src/app/(auth)/verify/page.tsx con Suspense + Tabs (code | magic-link) basado en ?flow= param
- src/app/(auth)/callback/page.tsx CRITICO: decodea window.location.hash (fragment), valida JWT shape, guarda en Zustand, history.replaceState para limpiar URL, redirect a la raiz del area protegida (admin). useRef guard para StrictMode
- src/app/(auth)/set-password/page.tsx con SetPasswordForm
- Cumple AC-12, AC-13
```

**Verify**:

```bash
pnpm --filter @portfolio/admin build
pnpm --filter @portfolio/admin preview &
PREVIEW_PID=$!
sleep 3
curl -sI http://localhost:3000/login/ | head -1 | grep -q "200" || echo "FAIL /login"
curl -sI http://localhost:3000/register/ | head -1 | grep -q "200" || echo "FAIL /register"
curl -sI http://localhost:3000/verify/ | head -1 | grep -q "200" || echo "FAIL /verify"
curl -sI http://localhost:3000/callback/ | head -1 | grep -q "200" || echo "FAIL /callback"
curl -sI http://localhost:3000/set-password/ | head -1 | grep -q "200" || echo "FAIL /set-password"
kill $PREVIEW_PID
```

### 14. App shell + layout protegido (fase 10)

```text
feat(admin,admin-shell): Sidebar + Header + MobileSidebar + (admin)/layout con AuthGuard

- src/features/admin-shell/components/sidebar.tsx con lucide icons + nav items + active state segun pathname. Los links a las secciones de metricas (/metrics, /analytics, ...) son slots: el shell los declara, pero las pantallas de metricas se implementan en b-analytics-api
- src/features/admin-shell/components/header.tsx con breadcrumb dinamico + ThemeToggle + UserMenu (dropdown logout)
- src/features/admin-shell/components/mobile-sidebar.tsx con shadcn Sheet
- src/features/admin-shell/lib/nav-items.ts array con {href, label, icon} (settings, sessions-mgmt, users-admin, gestion CV placeholder + slots de metricas)
- src/app/(admin)/layout.tsx con AuthGuard wrappeando Sidebar + Header + main
- Cumple AC-7, AC-19, AC-20
```

**Verify**:

```bash
pnpm --filter @portfolio/admin test tests/unit/features/admin-shell
pnpm --filter @portfolio/admin build
pnpm --filter @portfolio/admin preview &
PREVIEW_PID=$!
sleep 3
# El (admin)/layout esta protegido por AuthGuard. Sin token, redirige a /login.
# Verificar que la layout renderiza (sirve HTML del SPA, JS aplica el guard en el cliente):
curl -sI http://localhost:3000/settings/ | head -1 | grep -q "200" || echo "FAIL /settings"
curl -sI http://localhost:3000/sessions/ | head -1 | grep -q "200" || echo "FAIL /sessions"
# Manual: con MSW activado (NEXT_PUBLIC_USE_MSW=true) y user logueado, navegar entre
# /settings, /sessions, /users y confirmar que Sidebar no remontea
# (verificar en React DevTools que el componente Sidebar mantiene su instancia, o que el
# scroll del sidebar persiste entre navegaciones — comportamiento esperado del layout group).
kill $PREVIEW_PID
```

### 15. Settings: perfil + seguridad (fase 11)

```text
feat(admin,settings): perfil + seguridad (MFA + WebAuthn + recovery + cambio password + cambio email + eliminar cuenta)

- src/features/settings/api/settings-client.ts typed: users.profile.{get,update,change-email,confirm-email-change,delete-account} + auth.mfa.{setup-totp,confirm-totp,setup-email-code,set-preferred,disable} + auth.webauthn.{register-options,register-verify,list-credentials,delete-credential} + auth.mfa.recovery-codes-generate
- src/features/settings/hooks/ useQuery/useMutation por accion con invalidacion de queryKeys
- src/features/settings/components/: profile-form.tsx (display_name), totp-setup.tsx, confirm-totp-input.tsx, email-code-setup.tsx, mfa-method-list.tsx (set-preferred/disable), webauthn-register-button.tsx, webauthn-credentials-list.tsx, recovery-codes-modal.tsx, change-email-form.tsx, delete-account-dialog.tsx
- src/features/settings/components/change-password-form.tsx: UI presente pero MARCADA como bloqueada por dependencia de backend (GAP: no existe users.profile.change-password; auth.verify.set-password usa temp_token, no access JWT). MSW mockea el endpoint sugerido (users.profile.change-password {current_password,new_password}) mientras la action no existe. Documentar la dependencia en el AC/nota
- src/app/(admin)/settings/page.tsx (perfil) + src/app/(admin)/settings/security/page.tsx (MFA + WebAuthn + recovery + password + email + eliminar cuenta)
- Tests unit con coverage >= 80% per-file (mock MSW)
- Cumple AC de settings/seguridad
```

**Verify**: `pnpm --filter @portfolio/admin test:coverage tests/unit/features/settings`

### 16. Sessions-mgmt: sesiones de mi cuenta (fase 12)

```text
feat(admin,sessions-mgmt): listar + revocar sesiones de la cuenta auth

- src/features/sessions-mgmt/api/sessions-mgmt-client.ts typed: users.status.{get,list-sessions,revoke-session}
- src/features/sessions-mgmt/hooks/ useSessionsList (useQuery) + useRevokeSession (useMutation, error 400 CANNOT_REVOKE_CURRENT_SESSION para la sesion actual)
- src/features/sessions-mgmt/components/sessions-list.tsx (DataTable con device/ip/last-seen + boton revocar) + revoke-session-dialog.tsx
- src/app/(admin)/sessions/page.tsx
- NOTA: esto es la gestion de MIS sesiones de login (auth), NO el tracking de visitantes (esa feature "sessions" de metricas vive en b-analytics-api)
- Tests unit con coverage >= 80% per-file (mock MSW)
- Cumple AC de sessions-mgmt
```

**Verify**: `pnpm --filter @portfolio/admin test:coverage tests/unit/features/sessions-mgmt`

### 17. Users-admin: gestion de otros usuarios (fase 13)

```text
feat(admin,users-admin): gestion de usuarios (solo admin via whitelist SSM)

- src/features/users-admin/api/users-admin-client.ts typed: users.admin.{list-users,get-user,disable-user,enable-user,delete-user,force-logout,list-admin-actions}
- src/features/users-admin/hooks/ useUsersList (useQuery con paginacion) + useUserDetail + mutaciones disable/enable/delete/force-logout + useAdminActions (audit log)
- src/features/users-admin/components/: users-table.tsx (DataTable + paginator), user-detail.tsx, user-actions-menu.tsx (disable/enable/delete/force-logout con confirm dialogs), admin-actions-log.tsx
- Acceso solo admin (no-admin -> 404 NOT_FOUND del backend). El sidebar oculta la seccion si el user no es admin
- src/app/(admin)/users/page.tsx + src/app/(admin)/users/[id]/page.tsx
- Tests unit con coverage >= 80% per-file (mock MSW)
- Cumple AC de users-admin
```

**Verify**: `pnpm --filter @portfolio/admin test:coverage tests/unit/features/users-admin`

### 18. Placeholder gestion CV (fase 14)

```text
feat(admin,cv-management): placeholder de gestion del CV (sin backend)

- src/app/(admin)/cv/page.tsx: page placeholder con EmptyState + nota "plan futuro c-cv-management"
- Link en el sidebar (nav-items) hacia /cv
- SIN backend ni UI de edicion. Solo el slot + page
- Tests unit del placeholder (render del EmptyState)
- Cumple AC del placeholder CV
```

**Verify**: `pnpm --filter @portfolio/admin test tests/unit/app/cv`

> Las features de METRICAS (analytics, sessions de tracking, events, visits,
> geo, devices, funnel, contacts) NO van en este plan: se montan dentro del
> app shell del admin en el plan **b-analytics-api** (full-stack, segundo).

### 19. Devtools cloudflare_setup extension (fase 17)

```text
feat(devtools,admin): extiende cloudflare_setup para soportar app_type='nextjs'

- devtools/cloudflare_setup/config.py: agrega APP_ADMIN (AppConfig con root_dir='admin', app_type='nextjs', build_output_dir='out')
- Funciones output_dir_for() y env_vars_for() respetan app_type
- custom_domain_for(): admin.portfolio.{env}.the-full-stack.com (prod sin sufijo)
- env_vars del project Pages incluye NEXT_PUBLIC_* para admin
- project Cloudflare Pages: portfolio-admin / portfolio-admin-dev / portfolio-admin-stage
- devtools/cloudflare_setup/README.md menciona admin como 7mo app
- Cumple AC-30
```

**Verify**: `python devtools/run.py cloudflare_setup projects --env=dev --dry-run` (la fase `status` NO existe; las fases validas son projects / domains / triggers / all). Aplica el config con `--dry-run` para validar sin tocar el remoto.

### 20. Devtools sync_secrets + docker/env (fase 18)

```text
feat(devtools,admin): extiende sync_secrets catalog con NEXT_PUBLIC_*

- devtools/sync_secrets/catalog.py: agrega 6 SecretDefinition (NEXT_PUBLIC_API_ENDPOINT, NEXT_PUBLIC_TURNSTILE_SITEKEY, NEXT_PUBLIC_ADMIN_URL, NEXT_PUBLIC_AUTH_REFRESH_LEAD_MS, NEXT_PUBLIC_FEATURE_MFA, NEXT_PUBLIC_WEBAUTHN_RP_ID)
- docker/env/client/.example: agrega placeholders para los 6 nuevos
- Valores por env:
  - NEXT_PUBLIC_FEATURE_MFA: el backend MFA ya esta desplegado (serverless/lambda/services/auth/, operations mfa + webauthn). Si se conserva el flag, es solo un toggle opcional de UI (default true en dev/stage/prod), NUNCA un gate de "backend pending". Eliminarlo es valido si la UI de MFA no necesita ocultarse.
  - NEXT_PUBLIC_WEBAUTHN_RP_ID: config base (no detras de flag). admin.portfolio.dev.the-full-stack.com (dev), admin.portfolio.stage.the-full-stack.com (stage), admin.portfolio.the-full-stack.com (prod). Requerido por `navigator.credentials.create({publicKey: {rp: {id}}})` en la Fase 16. Sin este valor el flujo de passkeys falla.
```

**Verify**: `python devtools/run.py sync_secrets --env=dev --category=client --dry-run`

### 21. GH Actions workflows extension (fase 19)

```text
feat(ci,admin): extiende deploy-apps.yml matrix con admin + confirma admin en subdomain reserved

- .github/workflows/deploy-apps.yml: matrix include {name: admin, dist-dir: admin/out, project: portfolio-admin} en deploy-pages + verify-deploy. Job build-apps lee NEXT_PUBLIC_* desde vars + ejecuta workspace-concurrency=7 (6 Astro + 1 Next)
- .github/workflows/ci.yml: filter incluye @portfolio/admin en lint + build
- .claude/docs/subdomain-standard/02-naming-rules.md: 'admin' ya es reserved component (confirmar)
- Cumple AC-30, AC-31
```

**Verify**: `act -W .github/workflows/ci.yml` (con skill github-actions)

### 22. E2E Playwright (fase 20)

```text
test(admin,e2e): 7 specs Playwright para flujos golden path del admin

- tests/feature/admin/01-login-magic-link.spec.ts
- tests/feature/admin/02-register-verify-code.spec.ts
- tests/feature/admin/03-callback-fragment-hash.spec.ts (critico: verifica hash limpio del URL post-decoder)
- tests/feature/admin/04-auth-guard-redirect.spec.ts (verifica next param)
- tests/feature/admin/05-logout-multi-tab.spec.ts (BroadcastChannel)
- tests/feature/admin/06-settings-security.spec.ts (perfil + MFA setup; change-password mockeado por MSW por el gap de backend)
- tests/feature/admin/07-sessions-mgmt-revoke.spec.ts (listar sesiones de la cuenta + revocar; users-admin si el user es admin)
- Corren contra stack local con MSW habilitado (NEXT_PUBLIC_USE_MSW=true)
- NOTA: la navegacion y tablas de METRICAS se verifican en b-analytics-api
- Cumple AC-32
```

**Verify**: `python devtools/run.py docker up --env=local && python devtools/run.py test_runner --module=feature --type=feature --env=local`

### 23. Verificacion E2E iterativa + cleanup (fase 21) — ultimo commit

```text
chore(admin): verificacion E2E completa + elimina docs/specs/a-admin/

- Bateria completa pasa: lint + typecheck + unit + coverage (>= 80%) + build + E2E + smoke deploy a dev
- Verifica el admin: auth + app shell + settings + sessions-mgmt + users-admin (las metricas se verifican en b-analytics-api)
- Elimina docs/specs/a-admin/ (plan efimero). El conocimiento permanente vive en:
  - .claude/rules/admin.md
  - .claude/skills/admin-stack/SKILL.md
  - .claude/docs/admin/ (7 archivos)
- Cumple TODOS los AC del plan a-admin
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
09. MSW setup (auth + users)       <- secuencial (A.8)
10-13. auth (store/lib/api -> hooks -> components -> pages)    <- secuencial (B.*)
14. app shell + layout             <- secuencial (C.*)
15. settings (perfil + seguridad)  <- PARALELO (D.1)
16. sessions-mgmt                  <- PARALELO (D.2)
17. users-admin                    <- PARALELO (D.3)
18. placeholder CV                 <- PARALELO (D.4)
19. devtools cloudflare_setup      <- paralelo a D.*
20. devtools sync_secrets          <- paralelo a D.*
21. GH Actions workflows           <- depende de 19 + 20
22. E2E Playwright (admin)         <- secuencial (F.1, depende de TODAS)
23. verificacion + cleanup         <- secuencial (F.2, el ultimo)
```

23 commits totales. La UI de metricas (analytics/sessions de
tracking/events/visits/geo/devices/funnel/contacts) NO esta aqui: vive
en b-analytics-api. Con paralelizacion via worktrees el wall-clock se
reduce en las fases D.* (gestion).

## PR

Un solo PR `feature/admin-frontend -> dev`. Merge commit
(`gh pr merge --merge --delete-branch`). Sin atribucion IA en el body.

Despues, promocion `dev -> stage` y `stage -> main` via PRs separados
con merge commit (sin `--delete-branch` — `dev`/`stage` son
permanentes).

[< 08-descomposicion](08-descomposicion.md) | [Siguiente: 10-paralelizacion-worktrees >](10-paralelizacion-worktrees.md)
