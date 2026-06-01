# Plan: Admin SPA — admin.portfolio.{env}.the-full-stack.com

> Plan Large. Panel admin **Next.js 16.2.6** SPA estatico
> (`output: 'export'`) + **React 19.2.6** (React Compiler stable,
> `useActionState`, `useOptimistic`, ref-as-prop, Document Metadata
> nativo) + shadcn/ui + Tanstack Query v5 + Zustand 5, deployado a
> Cloudflare Pages en `admin.portfolio.{dev|stage|prod}.the-full-stack.com`.
>
> **El plan `a-admin` se ejecuta PRIMERO** y entrega:
>
> - App shell (feature `admin-shell`): header + sidebar + navegacion +
>   layout protegido `(admin)/layout.tsx` con AuthGuard. El sidebar tiene
>   slots/links a las secciones (metricas, settings, sesiones, admin de
>   usuarios, gestion CV placeholder).
> - Auth completo (feature `auth`): las 26 actions del Lambda `auth`.
>   Pages `(auth)`: login, register, verify, callback, set-password.
> - Gestion total / settings (features separados, consume Lambda `auth` +
>   Lambda `users`): perfil, seguridad (MFA TOTP/email-code + WebAuthn +
>   recovery codes), cambio de password (**gap backend** — ver fases),
>   change-email, eliminar cuenta, sesiones de mi cuenta, admin de
>   usuarios (gestionar otros).
> - Deploy a Cloudflare Pages.
>
> **NO** incluye la UI de metricas: esas pantallas (analytics, sessions de
> tracking, events, visits, geo, devices, funnel, contacts) viven en el
> plan `b-analytics-api`, montadas dentro de este mismo app shell.
>
> Consume el Lambda `auth` (YA desplegado) + Lambda `users` (YA desplegado).
> Mientras el backend no este disponible en el env de trabajo, MSW v2
> provee mocks completos.
>
> Carpeta `admin/` en root del repo (no `apps/admin/`). Entra al pnpm
> workspace como `@portfolio/admin`.

## Cuando leer

| Tema | Archivo |
|------|---------|
| Problema, solucion, AC numerados | [01-contexto-y-decision.md](01-contexto-y-decision.md) |
| Diagramas de flujo (auth, app shell, deploy) | [02-diagramas.md](02-diagramas.md) |
| Estructura completa de archivos (Hybrid Atomic Design) | [03-estructura.md](03-estructura.md) |
| Setup base: pnpm workspace + configs + scaffolding | [04-setup-base.md](04-setup-base.md) |
| UI: shadcn + Tailwind v4 + theming + componentes ui/ | [05-ui-components.md](05-ui-components.md) |
| Auth feature: store + hooks + magic link + MSW handlers | [06-auth-feature.md](06-auth-feature.md) |
| Gestion total / settings (cuenta + sesiones + admin usuarios) | [07-settings-features.md](07-settings-features.md) |
| Descomposicion para paralelizacion + tests (unit + E2E) + cobertura | [08-descomposicion.md](08-descomposicion.md) |
| Deploy: devtools + GH Actions + Cloudflare Pages | [09-commits.md](09-commits.md) (incluye fase de deploy) |
| Paralelizacion con git worktrees | [10-paralelizacion-worktrees.md](10-paralelizacion-worktrees.md) |
| Verificacion E2E iterativa (fase final, gate del PR) | [11-verificacion-e2e.md](11-verificacion-e2e.md) |

## Estado por fase

| Fase | Descripcion | Estado |
|------|-------------|--------|
| 0 | Plan + carpeta `docs/specs/a-admin/` commiteada en `feature/admin-frontend` | pending |
| 1 | Scaffold `admin/` (package.json, configs, pnpm workspace, biome.json override) | pending |
| 2 | Setup CSS/theming (`globals.css` + tokens compartidos con DS, `next-themes` provider) | pending |
| 3 | shadcn init + agregar componentes base (button, card, form, table, etc.) | pending |
| 4 | Custom UI primitives en `components/ui/` (metric-card, data-table, date-range-picker, empty-state, theme-toggle) | pending |
| 5 | `lib/env.ts` + `lib/api-client.ts` (fetch wrapper + auth interceptor + mutex refresh) | pending |
| 6 | Providers (QueryProvider con persister, RootProviders, layout.tsx) | pending |
| 7 | Feature `auth`: store Zustand + hooks (register/login/verify/logout/refresh) + componentes (LoginForm, RegisterForm, VerifyCodeInput, MagicLinkCallback, AuthGuard, TurnstileWidget) | pending |
| 8 | Pages `(auth)`: login, register, verify, callback, set-password | pending |
| 9 | MSW setup (handlers auth + users, server.ts, browser.ts) + tests setup | pending |
| 10 | Feature `admin-shell` (app shell): sidebar, header, theme toggle, layout `(admin)` con AuthGuard. Slots/links a metricas, settings, sesiones, admin usuarios, gestion CV (placeholder); las PANTALLAS de metricas NO se implementan aca (plan `b-analytics-api`) | pending |
| 11 | Feature `settings` — perfil: display_name via `users.profile.update`; change-email (`users.profile.change-email` + `confirm-email-change`); eliminar cuenta (`users.profile.delete-account`) | pending |
| 12 | Feature `settings` — seguridad MFA: TOTP (setup/confirm/set-preferred/disable) + email-code (`auth.mfa.*`) + recovery codes | pending |
| 13 | Feature `settings` — seguridad WebAuthn: register/list/delete passkeys (`auth.webauthn.*`) + recovery codes | pending |
| 14 | Feature `settings` — cambio de password: UI en seguridad. **Bloqueado por gap backend** (no existe action para user autenticado; sugerido `users.profile.change-password`). MSW lo mockea; sin E2E real hasta que exista la action | pending |
| 15 | Feature `sessions-mgmt`: ver mis sesiones activas (`users.status.list-sessions` + `get`) + revocar sesion (`users.status.revoke-session`, NUNCA la actual) | pending |
| 16 | Feature `users-admin` (solo admin, whitelist SSM): list-users, get-user, disable-user, enable-user, delete-user, force-logout, list-admin-actions (`users.admin.*`) | pending |
| 17 | Placeholder gestion CV: link en sidebar + page placeholder + nota "plan futuro c-cv-management". SIN backend ni UI de edicion | pending |
| 18 | Extension `devtools/cloudflare_setup/config.py` para incluir el admin (app_type=nextjs) | pending |
| 19 | Extension `devtools/sync_secrets/catalog.py` con nuevas NEXT_PUBLIC_* + actualizar `docker/env/client/.example` | pending |
| 20 | Extension `.github/workflows/deploy-apps.yml` matrix con `admin` (dist-dir: admin/out) | pending |
| 21 | Tests E2E Playwright en `tests/feature/admin/*.spec.ts` | pending |
| 22 | Verificacion E2E iterativa + limpieza `docs/specs/a-admin/` | pending |

### Fases ampliadas (decisiones del usuario durante la ejecucion)

| Fase | Descripcion | Estado |
|------|-------------|--------|
| D-1 | **devtools**: integrar `admin` como modulo del script `docker` existente (`docker lint/build/typecheck/format/test --module=admin` + `docker up` lo incluye). Listas en `devtools/docker/{urls,flags,quality,_helpers}.py` + `devtools/shared/compose.py` | done |
| D-2 | **Docker**: `admin` como 7mo servicio en los 5 compose `{local,dev,test,prod,stage}.yml` + dockerfiles por env (`docker/dockerfiles/<env>/admin/`) + 2 entrypoints + nginx `admin.localhost:9970` (HMR dev server local/dev, build+preview test/prod) + services-page | done |
| D-3 | **Env**: `NEXT_PUBLIC_*` en `docker/env/client/{.example,.local,.dev,.stage,.prod,.test}` derivadas de `PUBLIC_*` + RP_ID por env | done |
| D-4 | **Backend**: action NUEVA `users.profile.change-password` (Lambda `users`): verifica current con argon2, hashea new, REVOCA otras sesiones, audit + deploy dev. La UI de cambio de password conecta contra la action REAL (desbloquea el gap; sin flag, con E2E real) | pending |

> **NODE_ENV fix (bug de build resuelto)**: `next build` fallaba con
> `Cannot read properties of null (useState/useContext)` en `/_not-found`
> y `/_global-error` porque el entorno exporta `NODE_ENV=development`, que
> envenena el build de Next (requiere `production`). Fix: el script `build`
> fuerza `NODE_ENV=production`. NO es Turbopack ni React Compiler.

## Decisiones no-reabribles

Las 25 decisiones cerradas en el Q&A inicial (ver
[.claude/docs/admin/README.md](../../../.claude/docs/admin/README.md)
seccion "Decisiones no-reabribles"). Resumen:

1. **Next.js 16.2.6 SPA** (`output: 'export'`) — NO Vite, NO Astro.
2. **React 19.2.6** — obligatorio en Next 16.x. Compiler stable
   habilitado. `useActionState`, `useFormStatus`, `useOptimistic`,
   `useDeferredValue(value, initialValue)`, `useEffectEvent`, Activity
   Component, View Transitions disponibles. `ref` como prop normal
   (NUNCA `forwardRef`). Document Metadata nativo (`<title>`/`<meta>`
   en componentes auto-hoisteado al `<head>`).
3. **App Router** — NO Pages Router. Client Components todo.
4. **TypeScript 6.0.6** strict + `noUncheckedIndexedAccess`.
5. **Biome v2** sin ESLint. Override para `components/ui/*`.
6. **Tailwind v4.1.4** con `@theme` inline + `@tailwindcss/postcss`.
7. **shadcn/ui** (Radix primitives, copy-paste; codegen sin `forwardRef`).
8. **Tanstack Query v5.52.3** + `useSuspenseQuery` para data required +
   persister `localStorage` + lz-string compression.
9. **Zustand 5.0.14** (Jan 2026 state consistency fix) para auth + theme.
   Tanstack Query para data.
10. **Forms**: react-hook-form 7 + Zod + shadcn `<Form>` para complejos
    (auth, multi-step). `useActionState` + `useFormStatus` para simples.
11. **next-themes 0.4.8** con `attribute="data-theme"`.
12. **lucide-react 0.416.0** para iconos.
13. **Recharts 2.14.2** via shadcn add chart + override `react-is@19.2.6`.
14. **Tanstack Table v8.20.5 + Tanstack Virtual 3.5.1** para listas grandes.
15. **sonner 1.7.2** para toasts.
16. **Vitest 2.2.5 + Testing Library v16.1.0 + happy-dom 16.5.1 + MSW
    v2.3.2 + Playwright 1.48.2**.
17. **Hybrid Atomic Design** — `components/ui/` + `features/<X>/`.
18. **Carpeta `admin/`** en root (user choice).
19. **Subdominio `admin.portfolio.{env}.the-full-stack.com`**.
20. **Cloudflare Pages** via devtools/cloudflare_setup.
21. **Prefijo `NEXT_PUBLIC_*`** para env vars del cliente.
22. **Auth — storage**: tokens (access, refresh, temp) en `localStorage`
    via Zustand `persist`. **NO HttpOnly cookies** — el admin es
    SPA cross-origin (subdomain admin vs api), una cookie HttpOnly
    requeriria `SameSite=None` cross-site + `Domain=.the-full-stack.com`,
    abriendo CSRF en los 6 niches publicos y rompiendo portabilidad.
    Defensa: CSP estricta sin `unsafe-inline`/`unsafe-eval` + SRI en
    third-party + access JWT corto (15 min) + family_id refresh rotation.
23. **Magic link callback** con fragment hash (NO query params). Backend
    redirect 302 a `/auth/callback#access=X&refresh=Y&user=...`.
    Frontend decodea + guarda en `localStorage` via Zustand + limpia
    con `history.replaceState`.
24. **BroadcastChannel API** para multi-tab logout sync + fallback
    `storage` event de `localStorage`.
25. **React Compiler** habilitado via `reactCompiler: true` en
    `next.config.ts`. Opt-out per file con `'use no memo'` solo si
    rompe algo medido.
26. **Plan scope** SOLO frontend; consume los Lambdas `auth` y `users`
    (ambos YA desplegados). La UI de metricas NO entra aca (plan
    `b-analytics-api`). MSW v2 mockea el backend mientras no este
    disponible en el env de trabajo (toggle via `NEXT_PUBLIC_USE_MSW=true`).

## Reglas criticas (siempre activas)

- **SIEMPRE** Client Components (`'use client'`). NO Server Components.
- **SIEMPRE** API calls via `lib/api-client.ts` (fetch wrapper con
  auth interceptor + mutex refresh).
- **SIEMPRE** Hybrid Atomic: `components/ui/` (genericos, 2+ features
  uses) vs `features/<X>/components/` (especificos).
- **SIEMPRE** rama de trabajo `feature/admin-frontend` (NUNCA
  trabajar en `dev`/`stage`/`main` directo). Bootstrap explicito (ANTES
  del primer commit del plan):

  ```bash
  git checkout dev && git pull origin dev
  git checkout -b feature/admin-frontend
  ```

  Si la rama actual al iniciar el plan no es `feature/admin-frontend`,
  ese par de comandos es la primera accion del implementador. NUNCA
  asumir que la rama actual coincide.
- **SIEMPRE** verificar incrementalmente por commit (lint + typecheck +
  unit del scope).
- **SIEMPRE** push + PR SOLO con la bateria de la seccion 11 completa
  en verde.
- **NUNCA** API routes, middleware, Server Components async.
- **NUNCA** tokens JWT en URL query, persistir accessToken, logear JWT.
- **NUNCA** atribucion IA en commits/PRs.

## Matriz de verificacion (rapida)

| Capa | Comando |
|------|---------|
| Lint + format | `pnpm --filter @portfolio/admin lint` |
| Typecheck | `pnpm --filter @portfolio/admin typecheck` |
| Unit tests | `pnpm --filter @portfolio/admin test` |
| Coverage (>= 80% per-file) | `pnpm --filter @portfolio/admin test:coverage` |
| Build estatico | `pnpm --filter @portfolio/admin build` |
| Preview local | `pnpm --filter @portfolio/admin preview` |
| Dev con MSW | `NEXT_PUBLIC_USE_MSW=true pnpm --filter @portfolio/admin dev` |
| Devtools cloudflare config | `python devtools/run.py cloudflare_setup projects --env=dev --dry-run` |
| Devtools sync_secrets | `python devtools/run.py sync_secrets --env=dev --category=client --dry-run` |
| E2E Playwright (cuando stack arriba) | `python devtools/run.py test_runner --module=feature --type=feature --env=local` |
| CI local | `act -W .github/workflows/ci.yml` (skill github-actions) |

## Tamano del plan

Large (~20 fases, ~80-100 archivos nuevos). Duracion estimada
2-3 semanas de trabajo continuo con paralelizacion via git worktrees
en fases independientes (ver seccion 10).

## Ciclo de vida de la carpeta

Esta carpeta `docs/specs/a-admin/` es **efimera**. Se elimina con
`git rm -r docs/specs/a-admin/` en el ultimo commit del PR (fase 22,
seccion 11). La trazabilidad queda en `git log` y en el PR mergeado.

El conocimiento permanente vive en:
- `.claude/rules/admin.md` (enforcement)
- `.claude/skills/admin-stack/SKILL.md` (referencia invocable)
- `.claude/docs/admin/` (knowledge tree, 7 capitulos)

## Bibliografia interna

- Skill: [`/admin-stack`](../../../.claude/skills/admin-stack/SKILL.md)
- Rule: [`.claude/rules/admin.md`](../../../.claude/rules/admin.md)
- Knowledge tree: [`.claude/docs/admin/`](../../../.claude/docs/admin/)
- Backend auth: [`serverless/lambda/services/auth/`](../../../serverless/lambda/services/auth/) (YA desplegado: 6 operations / 26 actions — register 3, login 5, verify 2, session 2, mfa 8, webauthn 6) — reglas `.claude/rules/auth-system.md`, docs `.claude/docs/auth-system/`
- Backend users: [`serverless/lambda/services/users/`](../../../serverless/lambda/services/users/) (YA desplegado: 3 operations / 15 actions — profile 5, status 3, admin 7) — reglas `.claude/rules/auth-system.md`, docs `.claude/docs/auth-system/06-users.md`
- Plan b-analytics-api: [`docs/specs/b-analytics-api/`](../b-analytics-api/) (pending, se ejecuta DESPUES de este plan; la UI de metricas vive ahi, montada en este app shell)
- Research raw (efimero): `tmp/research/dashboard/` (7783 lineas)
