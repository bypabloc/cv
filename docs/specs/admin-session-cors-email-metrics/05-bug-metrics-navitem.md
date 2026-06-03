# 05 — Bug 4: nav-item `/metrics` da 404

[<- 04](04-bug-email-unificado.md) | [Commits ->](06-commits.md)

Solo frontend (admin). NO redeploy backend.

## Causa raiz

`admin/src/features/admin-shell/lib/nav-items.ts:25` declara
`{ href: ROUTES.admin.metrics, label: "Metricas", icon: BarChart3 }`. NO existe
page `admin/src/app/(admin)/metrics/` -> 404 (Cloudflare sirve el SPA
fallback). El plan `b-analytics-api` (que monta `/metrics`) esta PENDING.

Nada redirige a `/metrics`: `(admin)/page.tsx` solo saluda; `(admin)/layout.tsx`
no tiene logica de redirect. El unico consumo es el nav-item.

## Diseno (decision: quitar la entrada)

- `admin/src/features/admin-shell/lib/nav-items.ts` — eliminar la entrada
  `metrics` (linea 25). Cambio minimo, sin codigo muerto ni UI confusa.
- `admin/src/lib/routes.ts` — CONSERVAR `ROUTES.admin.metrics` (lo usara el
  plan `b-analytics-api`).

## Tests

- `admin/tests/unit/features/admin-shell/lib/nav-items.test.ts` (NUEVO):
  ningun `href` de `NAV_ITEMS` == `/metrics` [AC-12].
- Revisar tests del sidebar (`sidebar.tsx`/`mobile-sidebar.tsx`) si cuentan
  items.
