# 06 — Fase 3: admin UI — feature `cv-management`

> Forms por seccion espejando el sitio publico, es/en lado a lado, niches
> + reorden por prioridad, boton Publicar. [Volver al README](README.md).

## 3.1 Rutas y navegacion

La ruta `/cv` y el nav item ya existen (placeholder). Sub-rutas nuevas
bajo `admin/src/app/(admin)/cv/`:

```text
/cv                      # overview: cards por seccion + boton Publicar + estado
/cv/profile              # perfil + stats + headline/summary (i18n)
/cv/experiences          # lista + form (bullets, skills, niches, prioridad)
/cv/projects             # lista + form (case study, metricas, stack)
/cv/education            # lista + form
/cv/certificates         # lista + form
/cv/awards               # lista + form
/cv/languages            # lista + form
/cv/endorsements         # lista + form (referencias)
/cv/publications         # lista + form
/cv/skills               # categorias de skills (orden de skills incluido)
```

Layout `cv/layout.tsx`: sub-nav lateral o tabs con las 10 secciones (los
mismos nombres que el sitio publico — ver capturas `tmp/prod-screenshots/`).

Reglas transversales de la feature:

- **Admin-only (AC-13)**: el nav item "Gestion CV" pasa a
  `adminOnly: true` y las pages de `/cv/**` usan el mismo guard que
  `users-admin` (el backend responde 404 a no-admins; la UI lo trata como
  "no autorizado", nunca como "no existe").
- **`data-testid` obligatorio** en todo elemento interactivo (cards,
  botones de reorden, items del editor bilang, tag-inputs, publish):
  los E2E ([12-specs-e2e-admin.md](12-specs-e2e-admin.md)) seleccionan
  SOLO por `data-testid`, nunca por texto. Nomenclatura: `cv-section-card-
  <seccion>`, `cv-entity-new`, `cv-entity-card`, `cv-entity-move-up/down`,
  `bilang-item-up/down`, `cv-publish-button`, etc. — congelar los ids en
  esta fase.
- **Campos BiLang**: ambos locales (es y en) son requeridos en el Zod
  schema (el sitio publica ambos idiomas); el error señala el locale
  faltante.

## 3.2 Feature `admin/src/features/cv-management/`

Estructura estandar del repo:

- `api/cv-admin-client.ts`: 1 metodo por action del contrato
  ([02-arquitectura-flujos.md](02-arquitectura-flujos.md)) via `apiFetch`
  (`POST /cv-admin`, `{operation:'content'|'publish', action, data}`).
  Lectura: `api/cv-read-client.ts` con `GET /cv` publico (querystring
  `operation/action`) — los datos llegan BiLang completos.
- `api/query-keys.ts`: `cvKeys.section('experiences')`, `cvKeys.catalogs()`,
  `cvKeys.publishStatus()`.
- `hooks/`: `use-cv-section(section)` (useQuery, staleTime 30s),
  `use-upsert-entity(section)` / `use-delete-entity(section)` /
  `use-reorder(section)` (useMutation + invalidate de la seccion),
  `use-catalogs()`, `use-publish()` + `use-publish-status()`.
- `types.ts`: tipos espejo del contrato (BiLang = `Partial<{es, en}>`).
- `validation.ts`: Zod schemas por entidad (slug kebab-case, fechas,
  bullets no vacios, niches del catalogo) — mirror de los Pydantic.

## 3.3 Componentes clave

- `section-list.tsx`: lista de cards por seccion (titulo, badges de
  niches, fechas) + selector de **niche activo** que define el orden
  mostrado; botones subir/bajar por card (reorden = mutation `reorder`
  con la lista resultante). Empty state + skeletons.
- `bilang-field.tsx`: par de inputs/textarea es | en lado a lado para
  campos BiLang (label unico, dos columnas, responsive a 1 columna).
- `bilang-list-editor.tsx`: editor de listas paralelas es/en (bullets de
  experiencia: responsibilities/achievements) con agregar/eliminar/
  reordenar items.
- `niche-priority-picker.tsx`: checkboxes de niches (catalogo) + input de
  prioridad por niche marcado.
- `entity-form-dialog.tsx` (generico) + forms especificos:
  `experience-form.tsx` (role BiLang, company, country, fechas, seniority,
  bullets, skills tecnicas/blandas como tag-input con sugerencias del
  catalogo), `project-form.tsx` (descripcion, links, metricas key/value
  ordenadas, stack tag-input, case study problem/process/result BiLang),
  `profile-form.tsx`, y un `simple-entity-form.tsx` parametrizado para
  las entidades planas.
- `publish-card.tsx`: boton "Publicar cambios" con AlertDialog de
  confirmacion → `use-publish()` → toast + link a GitHub Actions; muestra
  `publish-status` (ultimo run del ref).

Reglas UI del repo: shadcn primitives, tokens CSS (sin hex inline),
sonner para toasts, `Skeleton` para loading, sin Framer Motion.

## 3.4 Página overview `/cv`

Cards-resumen por seccion (conteo de entradas, link a la sub-ruta) +
`publish-card`. Reemplaza el Alert "Proximamente".

## Tests requeridos (seccion 6 de esta fase)

- 6.B Unit (Vitest + Testing Library + happy-dom, mirror en
  `admin/tests/unit/features/cv-management/`): hooks (con QueryClient de
  test + MSW), `bilang-field`, `bilang-list-editor`, `section-list`
  (reorden), `experience-form` (hidratacion + submit), `publish-card`
  (confirmacion + toast). Asserts exactos, BDD en `it()`.
- MSW: `admin/tests/mocks/handlers/cv-admin.ts` (operations content +
  publish, contrato flat + Envelope) y fixtures de GET /cv.
- 6.C Typecheck: `pnpm --filter @portfolio/admin typecheck`.
- Coverage >= 80% per-file en lo creado/modificado.

## Archivos afectados (Fase 3)

### Crear

- `admin/src/features/cv-management/**` (api, hooks, components, types,
  validation, index)
  - Verificar: `pnpm --filter @portfolio/admin test:coverage`
- `admin/src/app/(admin)/cv/layout.tsx` + 10 `page.tsx` de sub-rutas
  - Verificar: `pnpm --filter @portfolio/admin build` + rutas en `admin/out/`
- `admin/tests/mocks/handlers/cv-admin.ts` + tests unit mirror
  - Verificar: `pnpm --filter @portfolio/admin test`

### Modificar

- `admin/src/app/(admin)/cv/page.tsx` — placeholder → overview real
  - Verificar: render test + build
- `admin/src/lib/routes.ts` — sub-rutas `cv.*`
  - Verificar: typecheck
- `admin/src/lib/env.ts` — (solo si hace falta una var nueva; el endpoint
  ya existe via `NEXT_PUBLIC_API_ENDPOINT`)
  - Verificar: build sin ZodError
