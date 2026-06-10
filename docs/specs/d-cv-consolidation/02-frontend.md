# 02 — Frontend admin: /cv, get-all, tab activo, textareas, sweep UI

> [README](README.md) | [01-backend](01-backend.md) | [03-commits](03-commits-verificacion.md)

## URL /cv-admin -> /cv

- `features/cv-management/api/cv-admin-client.ts`: el string `/cv-admin`
  existe SOLO en `content()` (L37) y `publishOp()` (L44) -> `/cv`.
- MSW: `admin/tests/mocks/handlers/cv-admin.ts` `http.post(${API}/cv)`
  (convive con el GET del mismo path: handlers por metodo) + handler de
  `get-all`.
- Tests unit del arbol cv-management que asertan `/cv-admin`.

## content.get-all en el overview (AC-1)

- `cv-admin-client.ts`: `getAll()` = `content('get-all', {})`.
- `query-keys.ts`: `cvKeys.fullCv()` colgada de `cvKeys.all`
  (['cv-management', ...]) — hereda la exclusion de persistencia
  localStorage y el barrido de invalidaciones.
- Hook `use-full-cv.ts` (useQuery, staleTime 0 — 1 request por mount).
- `cv-overview.tsx`: las 10 SectionCard derivan su conteo del get-all (se
  elimina el useCvSection por card). `publications` muestra conteo real.
- Mutations (upsert/delete/reorder/publish): invalidar tambien
  `cvKeys.fullCv()` (o invalidar por `cvKeys.all`).
- Las paginas por seccion NO cambian su lectura (niche filter server-side).

## Tab activo (AC-5)

- `cv-shell.tsx`: reemplazar `pathname === href` por el patron del sidebar
  (`pathname === href || pathname.startsWith(href + '/')`) normalizando el
  trailing slash. Cuidado: `/cv` matchea como prefijo de `/cv/profile/` —
  el tab Resumen solo activo en `/cv` o `/cv/` exactos.

## Textareas (AC-6)

- `components/ui/textarea.tsx`: `min-h-28` aprox + `field-sizing-content`
  (auto-grow, Tailwind v4) + `resize-y` + `max-h` razonable.
- `bilang-field.tsx` y `simple-entity-form.tsx`: heredan del base.
- `packages/ui/src/components/ContactFormReact.*`: revisar consistencia
  (ya tiene rows=6 + resize vertical + min-height 120px — es la referencia).

## Sweep UI con playwright (D-8)

Recorrer contra el admin local (`pnpm --filter @portfolio/admin dev`
apuntando al API de dev) o dev desplegado: overview, 10 secciones, dialogs
de create/edit/delete, reorder, publish card, dark + light, viewport
desktop + mobile. Capturas en `tmp/d-cv-consolidation/ui/`. Aplicar
mejoras visuales/UX iterando (espaciado, jerarquia, estados vacios,
loading skeletons, consistencia de botones) y re-capturar.
