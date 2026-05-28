# Plan: Dashboard SPA — admin.portfolio.{env}.the-full-stack.com

> Plan Large (~20 fases). Dashboard admin **Next.js 16.2.6** SPA
> estatico (`output: 'export'`) + **React 19.2.6** (React Compiler
> stable, `useActionState`, `useOptimistic`, ref-as-prop, Document
> Metadata nativo) + shadcn/ui + Tanstack Query v5 + Zustand 5,
> deployado a Cloudflare Pages en
> `admin.portfolio.{dev|stage|prod}.the-full-stack.com`. Consume el
> Lambda `auth` (planes 01-02, aun pending) + Lambda `analytics` (plan
> analytics-dashboard-api, aun pending). Mientras no esten deployadas,
> MSW v2 provee mocks completos.
>
> Carpeta `dashboard/` en root del repo (no `apps/dashboard/`). Entra
> al pnpm workspace como `@portfolio/dashboard`.
>
> **Scope**: SOLO frontend. La implementacion del backend es problema
> de los planes 01-auth-infra-basics, 02-auth-mfa y
> analytics-dashboard-api.

## Cuando leer

| Tema | Archivo |
|------|---------|
| Problema, solucion, AC numerados | [01-contexto-y-decision.md](01-contexto-y-decision.md) |
| Diagramas de flujo (auth, dashboard, deploy) | [02-diagramas.md](02-diagramas.md) |
| Estructura completa de archivos (Hybrid Atomic Design) | [03-estructura.md](03-estructura.md) |
| Setup base: pnpm workspace + configs + scaffolding | [04-setup-base.md](04-setup-base.md) |
| UI: shadcn + Tailwind v4 + theming + componentes ui/ | [05-ui-components.md](05-ui-components.md) |
| Auth feature: store + hooks + magic link + MSW handlers | [06-auth-feature.md](06-auth-feature.md) |
| Dashboard features: analytics + sessions + events + ... | [07-dashboard-features.md](07-dashboard-features.md) |
| Descomposicion para paralelizacion + tests (unit + E2E) + cobertura | [08-descomposicion.md](08-descomposicion.md) |
| Deploy: devtools + GH Actions + Cloudflare Pages | [09-commits.md](09-commits.md) (incluye fase de deploy) |
| Paralelizacion con git worktrees | [10-paralelizacion-worktrees.md](10-paralelizacion-worktrees.md) |
| Verificacion E2E iterativa (fase final, gate del PR) | [11-verificacion-e2e.md](11-verificacion-e2e.md) |

## Estado por fase

| Fase | Descripcion | Estado |
|------|-------------|--------|
| 0 | Plan + carpeta `docs/specs/dashboard/` commiteada en `feature/dashboard-frontend` | pending |
| 1 | Scaffold `dashboard/` (package.json, configs, pnpm workspace, biome.json override) | pending |
| 2 | Setup CSS/theming (`globals.css` + tokens compartidos con DS, `next-themes` provider) | pending |
| 3 | shadcn init + agregar componentes base (button, card, form, table, etc.) | pending |
| 4 | Custom UI primitives en `components/ui/` (metric-card, data-table, date-range-picker, empty-state, theme-toggle) | pending |
| 5 | `lib/env.ts` + `lib/api-client.ts` (fetch wrapper + auth interceptor + mutex refresh) | pending |
| 6 | Providers (QueryProvider con persister, RootProviders, layout.tsx) | pending |
| 7 | Feature `auth`: store Zustand + hooks (register/login/verify/logout/refresh) + componentes (LoginForm, RegisterForm, VerifyCodeInput, MagicLinkCallback, AuthGuard, TurnstileWidget) | pending |
| 8 | Pages `(auth)`: login, register, verify, callback, set-password | pending |
| 9 | MSW setup (handlers auth + analytics, server.ts, browser.ts) + tests setup | pending |
| 10 | Feature `dashboard-shell`: sidebar, header, theme toggle, layout `(dashboard)` con AuthGuard | pending |
| 11 | Feature `analytics`: overview, timeseries, top-pages, top-referrers, top-niches, active-now, retention | pending |
| 12 | Feature `sessions`: list + detail | pending |
| 13 | Feature `events`: distribution, list (con Tanstack Virtual), heatmap | pending |
| 14 | Feature `visits` + `geo` + `devices` + `funnel` | pending |
| 15 | Feature `contacts`: list + by-status + update status mutation | pending |
| 16 | Feature `settings`: profile + MFA setup (TOTP + WebAuthn + recovery codes) | pending |
| 17 | Extension `devtools/cloudflare_setup/config.py` para incluir el dashboard (app_type=nextjs) | pending |
| 18 | Extension `devtools/sync_secrets/catalog.py` con nuevas NEXT_PUBLIC_* + actualizar `docker/env/client/.example` | pending |
| 19 | Extension `.github/workflows/deploy-apps.yml` matrix con `dashboard` (dist-dir: dashboard/out) | pending |
| 20 | Tests E2E Playwright en `tests/feature/dashboard/*.spec.ts` | pending |
| 21 | Verificacion E2E iterativa + limpieza `docs/specs/dashboard/` | pending |

## Decisiones no-reabribles

Las 25 decisiones cerradas en el Q&A inicial (ver
[.claude/docs/dashboard/README.md](../../../.claude/docs/dashboard/README.md)
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
18. **Carpeta `dashboard/`** en root (user choice).
19. **Subdominio `admin.portfolio.{env}.the-full-stack.com`**.
20. **Cloudflare Pages** via devtools/cloudflare_setup.
21. **Prefijo `NEXT_PUBLIC_*`** para env vars del cliente.
22. **Auth — storage**: tokens (access, refresh, temp) en `localStorage`
    via Zustand `persist`. **NO HttpOnly cookies** — el dashboard es
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
26. **Plan scope** SOLO frontend; MSW v2 mocks hasta que el backend
    exista (toggle via `NEXT_PUBLIC_USE_MSW=true`).

## Reglas criticas (siempre activas)

- **SIEMPRE** Client Components (`'use client'`). NO Server Components.
- **SIEMPRE** API calls via `lib/api-client.ts` (fetch wrapper con
  auth interceptor + mutex refresh).
- **SIEMPRE** Hybrid Atomic: `components/ui/` (genericos, 2+ features
  uses) vs `features/<X>/components/` (especificos).
- **SIEMPRE** rama de trabajo `feature/dashboard-frontend` (NUNCA
  trabajar en `dev`/`stage`/`main` directo). Bootstrap explicito (ANTES
  del primer commit del plan):

  ```bash
  git checkout dev && git pull origin dev
  git checkout -b feature/dashboard-frontend
  ```

  Si la rama actual al iniciar el plan no es `feature/dashboard-frontend`,
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
| Lint + format | `pnpm --filter @portfolio/dashboard lint` |
| Typecheck | `pnpm --filter @portfolio/dashboard typecheck` |
| Unit tests | `pnpm --filter @portfolio/dashboard test` |
| Coverage (>= 80% per-file) | `pnpm --filter @portfolio/dashboard test:coverage` |
| Build estatico | `pnpm --filter @portfolio/dashboard build` |
| Preview local | `pnpm --filter @portfolio/dashboard preview` |
| Dev con MSW | `NEXT_PUBLIC_USE_MSW=true pnpm --filter @portfolio/dashboard dev` |
| Devtools cloudflare config | `python devtools/run.py cloudflare_setup projects --env=dev --dry-run` |
| Devtools sync_secrets | `python devtools/run.py sync_secrets --env=dev --category=client --dry-run` |
| E2E Playwright (cuando stack arriba) | `python devtools/run.py test_runner --module=feature --type=feature --env=local` |
| CI local | `act -W .github/workflows/ci.yml` (skill github-actions) |

## Tamano del plan

Large (~20 fases, ~80-100 archivos nuevos). Duracion estimada
2-3 semanas de trabajo continuo con paralelizacion via git worktrees
en fases independientes (ver seccion 10).

## Ciclo de vida de la carpeta

Esta carpeta `docs/specs/dashboard/` es **efimera**. Se elimina con
`git rm -r docs/specs/dashboard/` en el ultimo commit del PR (fase 21,
seccion 11). La trazabilidad queda en `git log` y en el PR mergeado.

El conocimiento permanente vive en:
- `.claude/rules/dashboard.md` (enforcement)
- `.claude/skills/dashboard-stack/SKILL.md` (referencia invocable)
- `.claude/docs/dashboard/` (knowledge tree, 7 capitulos)

## Bibliografia interna

- Skill: [`/dashboard-stack`](../../../.claude/skills/dashboard-stack/SKILL.md)
- Rule: [`.claude/rules/dashboard.md`](../../../.claude/rules/dashboard.md)
- Knowledge tree: [`.claude/docs/dashboard/`](../../../.claude/docs/dashboard/)
- Plan auth: [`docs/specs/01-auth-infra-basics/`](../01-auth-infra-basics/) (pending)
- Plan MFA: [`docs/specs/02-auth-mfa/`](../02-auth-mfa/) (pending)
- Plan analytics: [`docs/specs/analytics-dashboard-api/`](../analytics-dashboard-api/) (pending)
- Research raw (efimero): `tmp/research/dashboard/` (7783 lineas)
