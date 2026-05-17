# SPEC-200: Mapa de eventos — clicks, embudo, engagement

**Estado**: draft
**Fase**: 2
**Autor**: Pablo Contreras
**Fecha**: 2026-05-17
**Areas afectadas**: `serverless/migrations/`, `packages/content/`,
`packages/ui/`, `serverless/src/tracking_pixel/`
**Dependencias**: SPEC-101 (catalogo), SPEC-102 (pixel con `event_id`)
**Paralelizable con**: SPEC-201

> Anterior: [SPEC-102](SPEC-102-trackingpixel-page-load.md) | Siguiente: [SPEC-201](SPEC-201-cookiebanner-gdpr.md)

## 0. Contexto requerido

> Una sesion sin contexto previo DEBE leer esto antes de implementar.
> Esta spec depende de Fase 1 completa (SPEC-101 + SPEC-102 en `main`).

### Leer antes de empezar

| Archivo / recurso | Por que |
| ----------------- | ------- |
| [README.md](README.md) de esta carpeta | Decisiones del interview, mapa de las 2 fases |
| [SPEC-101](SPEC-101-catalogo-event-types.md) seccion 0 | Los UUID literales de TODO el catalogo (este spec siembra el resto) |
| [SPEC-102](SPEC-102-trackingpixel-page-load.md) | El pixel y `event_id` que esta spec extiende |
| `serverless/migrations/006_event_types.sql` | El seed creado en Fase 1, que aqui se amplia (migration `008`) |
| `serverless/migrations/007_tracking_event_columns.sql` | Las columnas de tracking; aqui se agrega `event_props` (migration `009`) |
| `packages/content/src/lib/event-types.ts` | El modulo de constantes a ampliar |
| `packages/ui/src/components/TrackingPixel.astro` | Pasa a usar `track-event.ts` en vez de logica inline |
| `packages/ui/src/components/Nav.astro`, `ProjectCard.astro`, `ExperienceCard.astro`, `ThemeToggle.astro` | Elementos a marcar con `data-track` |
| `packages/ui/src/components/ContactFormReact.tsx` | Emite los eventos del embudo de contacto |
| `packages/ui/src/lib/reveal-on-scroll.ts` | Patron `IntersectionObserver` reutilizable para `scroll-depth.ts` |
| `serverless/src/tracking_pixel/schemas.py`, `persistence.py` | Aceptar/persistir `event_props` |
| `serverless/src/stream_processor/pg_writer.py` | Replicar `event_props` a Neon |

### Rules del proyecto aplicables

- `.claude/rules/astro-landing.md` — componentes Astro, TS strict, Biome
- `.claude/rules/neon-management.md` — migrations `008`/`009`, branch Neon
- `.claude/rules/python.md` — backend `tracking_pixel`/`stream_processor`
- `.claude/rules/design-system.md` — si se toca UI

### Decisiones del interview que aplican

- Catalogo en SQL como fuente de verdad; constantes TS replican los UUID.
- Eventos a mapear: navegacion, clicks, embudo de contacto, engagement.
- Toda emision respeta `cf_consent` (gating de SPEC-201).
- `event_id` por evento (de SPEC-102) se mantiene en cada emision.

## 1. Contexto

Fase 1 deja el pixel emitiendo solo `page_load`. El objetivo del tracking es
saber QUE ve el usuario, DONDE hace mas click y SI llega a contacto. Esta spec
amplia el catalogo `event_types` con todos los eventos relevantes y emite cada
uno desde el frontend.

### Hallazgos de exploracion

- El form de contacto es `packages/ui/src/components/ContactFormReact.tsx`
  (React island, `client:load`), montado via `ContactFormReact.astro`. Tiene
  `data-testid`: `contact-form`, `contact-submit`, `contact-status`,
  `contact-sent-card`, `error-{field}`.
- Elementos clickeables clave sin atributo de tracking:
  - `Nav.astro`: `.site-nav__link` (items), `.site-nav__locale` (idioma).
  - `ProjectCard.astro`: `.proj-card__link` (Live / Repo, `target="_blank"`).
  - `ExperienceCard.astro`: `.exp-card__company` (link externo opcional).
  - `ThemeToggle.astro`: `#theme-toggle`.
  - Descarga de CV: `cvHref="/cv.html"` pasado a `CvSections`.
- `packages/ui/src/lib/reveal-on-scroll.ts` ya usa un `IntersectionObserver`
  vanilla — patron reutilizable para medir scroll depth.
- SPEC-101 dejo `event_types` con un seed de un solo elemento (`page_load`).
- SPEC-102 dejo `TrackingPixel.astro` con la funcion de envio y `event_id` por
  evento.

## 2. Solucion propuesta

Tres bloques: ampliar el catalogo, dar al frontend una API de emision de
eventos, y atachear los eventos a los elementos del UI.

1. **Migration `008_event_types_seed.sql`**: `INSERT` del resto de tipos de
   evento en `event_types`. Grupos:
   - Navegacion: `page_load` (ya existe), `spa_navigation`.
   - Clicks: `cta_click`, `nav_click`, `project_link_click`,
     `experience_link_click`, `cv_download`, `theme_toggle`,
     `external_link_click`.
   - Embudo de contacto: `contact_view`, `contact_form_start`,
     `contact_form_submit`, `contact_form_success`, `contact_form_error`.
   - Engagement: `scroll_depth`, `page_exit`.
2. **`event-types.ts`**: agregar las constantes nuevas a `EVENT_TYPES` (mismos
   UUID del seed).
3. **`packages/ui/src/lib/track-event.ts` (nuevo)**: modulo cliente con una
   funcion `trackEvent(eventTypeId, props?)` que arma el payload (genera
   `event_id`, adjunta `session_id`, `page_url`, `event_props` opcional) y hace
   `sendBeacon` a `/track`. `TrackingPixel.astro` pasa a usar este modulo en
   vez de tener la logica inline.
4. **Atachear listeners**: agregar `data-track="<code>"` a los elementos
   clickeables (Nav, ProjectCard, ExperienceCard, ThemeToggle, CV download) y
   un inicializador `initClickTracking()` que delega un unico listener en
   `document` (event delegation) leyendo `data-track`.
5. **Embudo de contacto**: emitir `contact_view` al montar la pagina
   `/contact`, `contact_form_start` al primer foco de un campo,
   `contact_form_submit`/`success`/`error` desde `ContactFormReact.tsx`.
6. **Engagement**: `initScrollDepth()` (reutiliza el patron de
   `reveal-on-scroll`) emite `scroll_depth` al cruzar 25/50/75/100 %;
   `page_exit` via `visibilitychange` -> `hidden`.
7. **Backend**: `tracking_pixel/schemas.py` acepta un `event_props` opcional
   (JSON libre acotado) para datos especificos del evento (ej. el href del
   link clickeado); `persistence.py` lo escribe; `stream_processor` lo
   replica a una columna `event_props jsonb` nueva en `tracking_events`
   (migration `009`).

### Decisiones clave

- **Decision 1: event delegation con `data-track`** — un solo listener en
  `document` lee el atributo `data-track` del elemento (o ancestro) clickeado.
  Evita N listeners y funciona con contenido que aparece tras navegacion SPA.
- **Decision 2: `event_props` como JSONB** — cada tipo de evento tiene datos
  propios (href de un link, profundidad de scroll, campo del form). Un JSONB
  acotado evita una columna por atributo y mantiene el schema estable.
- **Decision 3: el embudo se emite desde donde ocurre** — `contact_view` al
  cargar `/contact`, los eventos de formulario desde el componente React que
  ya conoce su ciclo de vida. No se infieren server-side.
- **Decision 4: `scroll_depth` con umbrales discretos** — 25/50/75/100 %, un
  evento por umbral cruzado, no streaming continuo. Acota el volumen.
- **Decision 5: respeta consentimiento** — toda emision pasa por la misma
  verificacion de `cf_consent` que el pixel (ver SPEC-201). Sin consentimiento,
  cero eventos.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given la migration `008` aplicada, When se consulta `event_types`,
  Then existen todas las filas de los grupos navegacion, clicks, embudo y
  engagement, cada una con `code_name` unico y `description`.
- **AC-2**: Given `EVENT_TYPES`, When se importa cualquier constante nueva
  (ej. `EVENT_TYPES.CTA_CLICK`), Then su valor coincide con el UUID del seed
  `008` (test de paridad cubre todo el catalogo).
- **AC-3**: Given un elemento con `data-track="cta_click"`, When el usuario
  hace click, Then se envia `POST /track` con `event_type_id` = UUID de
  `cta_click` y `event_props` con el contexto del elemento.
- **AC-4**: Given el usuario abre la pagina `/contact`, When la pagina termina
  de cargar, Then se emite el evento `contact_view`.
- **AC-5**: Given el usuario hace foco por primera vez en un campo del form de
  contacto, When ocurre el `focus`, Then se emite `contact_form_start` una sola
  vez (no se repite en focos posteriores).
- **AC-6**: Given el usuario envia el form de contacto con exito, When la
  respuesta es `201`, Then se emite `contact_form_submit` seguido de
  `contact_form_success`.
- **AC-7**: Given el envio del form falla (4XX/5XX), When se recibe el error,
  Then se emite `contact_form_error` con el codigo del error en `event_props`.
- **AC-8**: Given el usuario scrollea una pagina larga, When cruza el 25, 50,
  75 y 100 %, Then se emite un `scroll_depth` por cada umbral, una sola vez
  cada uno.
- **AC-9**: Given el usuario abandona la pestana, When ocurre `visibilitychange`
  a `hidden`, Then se emite `page_exit`.
- **AC-10**: Given el backend recibe un body de `/track` con `event_props`,
  When valida y persiste, Then `event_props` se guarda en DynamoDB y se
  replica a la columna `event_props jsonb` de `tracking_events`.
- **AC-11**: Given un body con `event_props` que excede el tamano maximo
  permitido, When valida, Then responde `400 INVALID_INPUT`.
- **AC-12**: Given el usuario NO dio consentimiento, When interactua (click,
  scroll, navega), Then NO se emite ningun evento.

## 4. Diagrama de Flujo (Antes y Despues)

### Antes

```text
TrackingPixel emite solo page_load (SPEC-102).
Clicks, embudo y engagement: no se trackean.
```

### Despues

```text
carga pagina        -> page_load
navegacion SPA      -> spa_navigation
click en [data-track] (delegado en document)
                    -> cta_click | nav_click | project_link_click | ...
abre /contact       -> contact_view
1er foco en campo   -> contact_form_start
submit form         -> contact_form_submit -> success | error
scroll 25/50/75/100 -> scroll_depth (x4)
deja la pestana     -> page_exit

cada emision: trackEvent(typeId, props)
              -> genera event_id -> POST /track { ..., event_props }
              (solo si hay consentimiento)
```

## 5. Diagrama ER

```text
event_types: filas nuevas (seed 008), sin cambio de estructura.

tracking_events (modificado)
┌──────────────────────────────┐
│ ... (columnas de SPEC-101)   │
│ event_props   jsonb   (*)    │   <- columna nueva (migration 009)
└──────────────────────────────┘

(*) event_props: datos especificos por tipo de evento. Nullable.
DynamoDB TrackingTable: event_props como atributo Map del item.
```

## 6. Tests Requeridos

### 6.B. Unit Tests

**Frontend (Vitest, `packages/ui/tests/unit/` y `packages/content/`):**

- `event-types.test.ts` (ampliar el de SPEC-101): paridad del catalogo
  completo SQL <-> TS `[AC-2]`.
- `track-event.test.ts`: `trackEvent` arma el payload con `event_id`,
  `session_id`, `event_type_id`, `event_props`; respeta consentimiento `[AC-12]`.
- `click-tracking.test.ts`: el listener delegado resuelve `data-track` del
  elemento o ancestro `[AC-3]`.
- `scroll-depth.test.ts`: emite un evento por umbral, sin repetir `[AC-8]`.

**Backend (pytest, `serverless/tests/`):**

- `tracking_pixel/test_schemas.py`: `event_props` opcional aceptado; exceso de
  tamano -> `ValidationError` `[AC-10][AC-11]`.
- `stream_processor`: `INSERT` incluye `event_props` `[AC-10]`.

### 6.C. Typecheck

- `pnpm exec tsc --noEmit` + `pnpm exec astro check`; `serverless typecheck`.

### 6.D. E2E Tests (Playwright)

`tests/feature/tracking/`:

- `click-events.spec.ts`: click en CTA / nav / project link -> `POST /track`
  con el `event_type_id` correcto `[AC-3]`.
- `contact-funnel.spec.ts`: abrir `/contact` -> `contact_view`; focar campo ->
  `contact_form_start`; enviar (con bypass Turnstile) -> los eventos
  `contact_form_submit` y `contact_form_success` `[AC-4..AC-7]`.
- `engagement.spec.ts`: scroll de una pagina larga -> 4 `scroll_depth`;
  cerrar pestana -> `page_exit` `[AC-8][AC-9]`.

## 7. Archivos Afectados

### Crear

- `serverless/migrations/008_event_types_seed.sql` + `.down.sql` — `INSERT` /
  `DELETE` del resto de tipos de evento.
  - Por que: completar el catalogo con todos los eventos mapeados.
  - Verificar: branch Neon, `migrate up`/`down`, `[AC-1]`.
- `serverless/migrations/009_tracking_event_props.sql` + `.down.sql` —
  `ALTER TABLE tracking_events ADD COLUMN event_props jsonb`.
  - Por que: almacenar datos especificos por tipo de evento.
  - Verificar: branch Neon, `[AC-10]`.
- `packages/ui/src/lib/track-event.ts` — funcion `trackEvent(typeId, props?)`:
  arma payload, genera `event_id`, gating de consentimiento, `sendBeacon`.
  - Por que: API unica de emision; el resto del codigo solo la invoca.
  - Verificar: `track-event.test.ts`.
- `packages/ui/src/lib/click-tracking.ts` — `initClickTracking()`: listener
  delegado en `document` que lee `data-track`.
  - Verificar: `click-tracking.test.ts` `[AC-3]`.
- `packages/ui/src/lib/scroll-depth.ts` — `initScrollDepth()`: umbrales
  25/50/75/100 % via `IntersectionObserver` / scroll listener.
  - Verificar: `scroll-depth.test.ts` `[AC-8]`.
- Tests unit y E2E listados en la seccion 6.
  - Verificar: Vitest + `test_runner --module=feature`.

### Modificar

- `packages/content/src/lib/event-types.ts` — agregar las constantes de los
  grupos clicks, embudo, engagement.
  - Por que: exponer los UUID nuevos al frontend.
  - Verificar: `event-types.test.ts` paridad completa `[AC-2]`.
- `packages/ui/src/components/TrackingPixel.astro` — usar `track-event.ts` en
  vez de la logica inline; inicializar `initClickTracking()` y
  `initScrollDepth()`; emitir `spa_navigation` y `page_exit`.
  - Por que: centralizar la emision; activar clicks/engagement.
  - Verificar: E2E `[AC-3][AC-8][AC-9]`.
- `packages/ui/src/components/Nav.astro` — `data-track="nav_click"` en
  `.site-nav__link`.
  - Verificar: `click-events.spec.ts` `[AC-3]`.
- `packages/ui/src/components/ProjectCard.astro` —
  `data-track="project_link_click"` en `.proj-card__link`.
  - Verificar: `[AC-3]`.
- `packages/ui/src/components/ExperienceCard.astro` —
  `data-track="experience_link_click"` en `.exp-card__company`.
- `packages/ui/src/components/ThemeToggle.astro` —
  `data-track="theme_toggle"` en `#theme-toggle`.
- Componente / link de descarga de CV — `data-track="cv_download"` en el link
  a `cv.html`.
- `packages/ui/src/components/ContactFormReact.tsx` — emitir
  `contact_form_start` (primer foco), `contact_form_submit`,
  `contact_form_success`, `contact_form_error` via `trackEvent`.
  - Por que: el componente conoce su ciclo de vida; el embudo se mide en origen.
  - Verificar: `contact-funnel.spec.ts` `[AC-5..AC-7]`.
- `apps/*/src/pages/contact.astro` — emitir `contact_view` al cargar (o
  hacerlo desde `ContactFormReact` al montar).
  - Verificar: `[AC-4]`.
- `serverless/src/tracking_pixel/schemas.py` — `event_props` opcional (dict
  acotado en tamano).
  - Verificar: `test_schemas.py` `[AC-10][AC-11]`.
- `serverless/src/tracking_pixel/persistence.py` — escribir `event_props`.
- `serverless/src/stream_processor/pg_writer.py` — `INSERT` con `event_props`.
  - Verificar: test de `pg_writer` `[AC-10]`.

## 8. Descomposicion para Paralelizacion

| Tarea | Archivos | AC | Depende de | Paralelizable con |
| ------- | ---------- | ----- | ------------ | ------------------- |
| T1 | `008_*.sql`, `009_*.sql`, `event-types.ts` | AC-1,2 | SPEC-101 | T2 |
| T2 | backend `schemas.py`/`persistence.py`/`pg_writer.py` + tests | AC-10,11 | SPEC-101 | T1 |
| T3 | `track-event.ts`, `click-tracking.ts`, `scroll-depth.ts` + tests | AC-3,8,12 | T1 | — |
| T4 | `TrackingPixel.astro` + `data-track` en componentes | AC-3,8,9 | T3 | T5 |
| T5 | `ContactFormReact.tsx` + `contact.astro` | AC-4,5,6,7 | T3 | T4 |
| T6 | E2E specs | AC-3..AC-9 | T4,T5 | — |

## 9. Validacion y Definition of Done

### Pre-implementacion

- [ ] Fase 1 en `main` y verificada
- [ ] SPEC-201 alineado: el gating de consentimiento existe
- [ ] UUID del seed `008` decididos y anotados
- [ ] Tests TDD escritos y fallando (Red)

### Definition of Done

- [ ] AC-1 a AC-12 cubiertos por tests que pasan
- [ ] Coverage >= 80% per-file en archivos modificados
- [ ] Migrations `008`/`009` probadas `up`/`down` en branch Neon
- [ ] `pnpm exec tsc --noEmit` + `pnpm exec astro check` sin errores
- [ ] `pnpm exec biome check .` sin errores
- [ ] `pnpm run build` de las 6 apps exitoso
- [ ] `serverless` lint/format/typecheck/validate pasan
- [ ] E2E de tracking verdes contra el stack local
- [ ] Smoke en dev: cada grupo de eventos visible en `tracking_events`

> Anterior: [SPEC-102](SPEC-102-trackingpixel-page-load.md) | Siguiente: [SPEC-201](SPEC-201-cookiebanner-gdpr.md)
