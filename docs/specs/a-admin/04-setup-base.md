# 04 — Setup base + configs + scaffolding

[< 03-estructura](03-estructura.md) | [Siguiente: 05-ui-components >](05-ui-components.md)

## Aclaracion

Esta seccion describe **que** se crea en las fases 1-6 (setup base).
El **codigo concreto** de cada archivo vive en
`.claude/docs/admin/01-stack.md` y `04-auth.md` (knowledge tree
permanente). Aqui solo el plan ejecutable: que archivo, que verifica.

## Fase 1 — Scaffold `admin/`

| Archivo | Descripcion | Verificar |
|---------|-------------|-----------|
| `admin/package.json` | name `@portfolio/admin`, engines node>=24, scripts dev/build/lint/typecheck/test, deps de la seccion 01-stack del KT | `pnpm install` sin errores |
| `admin/.gitignore` | `.next`, `out`, `node_modules`, `*.tsbuildinfo`, `.env*.local`, `coverage` | `git status` no muestra basura |
| `admin/next.config.ts` | `output: 'export'`, `images.unoptimized: true`, `trailingSlash: true`, `poweredByHeader: false` | `pnpm exec next build` arranca |
| `admin/tsconfig.json` | strict + `noUncheckedIndexedAccess` + paths `@/*` apuntando a `./src/*` + paths `@tests/*` apuntando a `./tests/*` (necesario para que `await import('@tests/mocks/browser')` resuelva en build/tests; `tests/` esta fuera de `src/`) | `pnpm typecheck` sin errores |
| `admin/biome.json` | `extends: ["../biome.json"]` + override `src/components/ui/**` | `pnpm lint` sin errores |
| `admin/postcss.config.mjs` | `@tailwindcss/postcss` plugin | (validado en build) |
| `admin/vitest.config.ts` | happy-dom + coverage + alias `@` (= `./src`) y `@tests` (= `./tests`) en `resolve.alias`, espejando los paths del `tsconfig.json` | `pnpm test` corre sin archivos |
| `admin/README.md` | corto, link a knowledge tree + plan | (revision visual) |
| `pnpm-workspace.yaml` | agregar `'admin'` al array `packages` | `pnpm install` recoge el package |

**Commit**: `feat(admin): scaffold inicial Next.js 16 SPA`

## Fase 2 — CSS / theming base

| Archivo | Descripcion | Verificar |
|---------|-------------|-----------|
| `admin/src/styles/globals.css` | `@import tailwind` + import fonts `@fontsource/space-grotesk` y `@fontsource/space-mono` + tokens HSL `:root` y `[data-theme="light"]` + `@theme inline` mapping a HSL + `@layer base` + `prefers-reduced-motion` (ver `01-stack.md` del KT) | `pnpm build` genera CSS |
| `admin/src/providers/theme-provider.tsx` | `next-themes` con `attribute="data-theme"`, `defaultTheme="system"`, `enableSystem`, `disableTransitionOnChange` | preview muestra theme aplicado |
| `admin/src/components/ui/theme-toggle.tsx` | DropdownMenu con Sun/Moon/Monitor icons, ciclo dark/light/system, persist en localStorage | toggle funciona en preview |

**Commit**: `feat(admin): tema dark/light con next-themes + tokens compartidos del DS`

## Fase 3 — shadcn init + componentes base

| Comando / Archivo | Descripcion | Verificar |
|-------------------|-------------|-----------|
| `cd admin && pnpm dlx shadcn@latest init` | Genera `components.json`, no `tailwind.config.ts` (v4 inline), aliases `@/components`, `@/lib/utils`, baseColor zinc | `components.json` existe |
| `pnpm dlx shadcn@latest add alert badge button card chart checkbox dialog dropdown-menu form input input-otp label popover select separator sheet skeleton sonner switch table tabs tooltip` | Crea ~24 primitivos en `src/components/ui/*.tsx` | Lint pasa en cada archivo |
| `pnpm dlx shadcn@latest add calendar command` | Para DateRangePicker (Calendar + Command para search) | Idem |
| `pnpm install` | Instala deps de Radix que shadcn pidio | OK |

**Commit**: `feat(admin): shadcn init + agregar 24 primitivos UI (Radix + Tailwind v4)`

## Fase 4 — Custom UI primitives genericos

| Archivo | Descripcion | Tests | AC |
|---------|-------------|-------|-----|
| `src/components/ui/metric-card.tsx` | `MetricCard({title, value, delta?, trend?, icon?})` | unit | AC-21 |
| `src/components/ui/data-table.tsx` | Tanstack Table wrapper generico (`columns, data, isLoading, emptyMessage`) | unit | AC-23 |
| `src/components/ui/date-range-picker.tsx` | Popover + Calendar (single range), default last 30d | unit | AC-22 |
| `src/components/ui/empty-state.tsx` | `EmptyState({icon, title, description?, action?})` | unit | — |
| `src/components/ui/error-alert.tsx` | shadcn Alert variant=destructive con retry button | unit | — |
| `src/components/ui/loading-spinner.tsx` | spinner accesible (role=status, aria-label) | unit | — |
| `src/components/ui/index.ts` | barrel exports | (typecheck) | — |

**Commit**: `feat(admin): custom UI primitives (MetricCard, DataTable, DateRangePicker, EmptyState)`

## Fase 5 — Lib base (env + api-client)

| Archivo | Descripcion | Tests | AC |
|---------|-------------|-------|-----|
| `src/lib/env.ts` | Zod schema valida `NEXT_PUBLIC_*` en cold start | unit | — |
| `src/lib/utils.ts` | `cn(...classes)` con `clsx` + `tailwind-merge` | unit | — |
| `src/lib/routes.ts` | `ROUTES.auth.callback`, `ROUTES.settings.security`, `ROUTES.metrics` (raiz del area de metricas, pantallas en plan b-analytics-api), etc. constants | (typecheck) | — |
| `src/lib/api-client.ts` | `apiFetch` wrapper con `ApiError` class, auth interceptor, mutex refresh, `skipAuth/skipRefresh` flags | unit (critico: test concurrent 401s) | AC-14 |
| `src/lib/format/date.ts` | `formatDate`, `relativeTime` (date-fns o Temporal API) | unit | — |
| `src/lib/format/number.ts` | `formatNumber`, `formatPercent` (Intl.NumberFormat) | unit | — |
| `src/lib/format/duration.ts` | `formatDurationMs` (00:01:23) | unit | — |
| `src/lib/validation/auth.ts` | Zod schemas: loginSchema, registerSchema, verifyCodeSchema | unit (cubre via component test) | AC-8 |
| `src/lib/validation/filters.ts` | dateRangeSchema, paginationSchema | unit | — |
| `src/types/api.ts` | typed responses /auth y /analytics (mirrors backend) | (typecheck) | — |
| `src/types/models.ts` | User, Session, Visit, Event, Contact domain types | (typecheck) | — |

**Commit**: `feat(admin): lib base (env validation con Zod, api-client con mutex refresh, types)`

## Fase 6 — Providers + RootLayout

| Archivo | Descripcion | Tests | AC |
|---------|-------------|-------|-----|
| `src/providers/query-provider.tsx` | QueryClient con defaults (refetchOnWindowFocus: false, retry: 1 menos 401/403/422), PersistQueryClientProvider con lz-string compression, dehydrate filter (NO persistir contacts list ni events list) | unit (smoke) | — |
| `src/providers/root-providers.tsx` | Composicion `ThemeProvider > QueryProvider` | (typecheck) | — |
| `src/app/layout.tsx` | RootLayout: import `globals.css`, RootProviders, Toaster (sonner position top-right richColors), `<html suppressHydrationWarning>` lang="es", `import '@/lib/env'` (fail-fast en build), metadata con `robots: noindex,nofollow` | preview funciona | AC-4 |
| `src/app/page.tsx` | Redirect a `/login` o `/metrics` (raiz autenticada del area de metricas; pantallas en plan b-analytics-api) segun `isAuthenticated()` | (smoke) | — |
| `src/app/error.tsx` | Error boundary global con button retry | (smoke) | — |
| `src/app/global-error.tsx` | Fallback ultimo (Error en RootLayout) | (smoke) | — |
| `src/app/not-found.tsx` | 404 page con link a `/` | (smoke) | — |

**Commit**: `feat(admin): providers (Query con persister, Theme) + RootLayout + 404 + error boundaries`

## Verificacion al final de fase 6 (gate intermedio)

```bash
# Desde root
pnpm install
pnpm --filter @portfolio/admin typecheck
pnpm --filter @portfolio/admin lint
pnpm --filter @portfolio/admin test
pnpm --filter @portfolio/admin build
ls admin/out/index.html admin/out/_next/static  # debe existir

# Preview manual
pnpm --filter @portfolio/admin preview &
curl -sI http://localhost:3000/ | head -3        # 200
curl -sI http://localhost:3000/login/ | head -3  # 404 (page no existe aun, OK por ahora)
```

Si todo verde, fases 1-6 OK. Proceder con fases 7+ (features).

[< 03-estructura](03-estructura.md) | [Siguiente: 05-ui-components >](05-ui-components.md)
