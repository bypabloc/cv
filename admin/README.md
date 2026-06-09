# @portfolio/admin

> Panel admin SPA del portfolio. Next.js 16 (`output: 'export'`) + React 19
> + shadcn/ui + Tanstack Query v5 + Zustand 5. Deployado a Cloudflare Pages
> en `admin.portfolio.{dev|prod}.the-full-stack.com`.

## Que es

Frontend de gestion del owner: autenticacion (login/register/MFA/WebAuthn),
gestion de la cuenta (perfil, seguridad, contrasena, email, sesiones) y
administracion de otros usuarios. Consume los Lambdas `auth` y `users` del
backend serverless. La UI de metricas la entrega el plan `b-analytics-api`,
montada en este mismo app shell.

## Stack

- Next.js 16.2.6 (`output: 'export'`, App Router, React Compiler stable)
- React 19.2.6 (ref-as-prop, `useActionState`, `useOptimistic`)
- TypeScript 6 strict + Biome v2 (sin ESLint)
- Tailwind v4 (`@theme` inline) + shadcn/ui (Radix)
- Tanstack Query v5 (+ persist localStorage) + Zustand 5
- react-hook-form + Zod + sonner + lucide-react + Recharts
- MSW v2 (mocks) + Vitest + Testing Library + Playwright

## Comandos

```bash
pnpm --filter @portfolio/admin dev          # dev server (localhost:3000)
NEXT_PUBLIC_USE_MSW=true pnpm --filter @portfolio/admin dev   # con mocks
pnpm --filter @portfolio/admin build        # genera out/
pnpm --filter @portfolio/admin preview       # sirve out/ en :3000
pnpm --filter @portfolio/admin lint
pnpm --filter @portfolio/admin typecheck
pnpm --filter @portfolio/admin test
pnpm --filter @portfolio/admin test:coverage
```

## Estructura

Hybrid Atomic Design: `src/components/ui/` (genericos shadcn + custom) +
`src/features/<X>/` (un dominio por carpeta: `auth`, `admin-shell`,
`settings`, `sessions-mgmt`, `users-admin`). Detalle en
`.claude/docs/admin/` (knowledge tree) y `.claude/rules/admin.md`.

## Auth (resumen)

Tokens en `localStorage` via Zustand `persist` (`refreshToken` +
`refreshExpiry` + `user` persistidos; `accessToken` + `tempToken` solo en
memoria). NO HttpOnly cookies (SPA cross-origin). Defensa: CSP estricta +
SRI + access JWT corto (15 min) + family_id refresh rotation backend.
Mutex client-side garantiza 1 sola `/session/refresh` in-flight.
