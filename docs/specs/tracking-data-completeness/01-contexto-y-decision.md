# 01. Contexto, solucion y criterios de aceptacion

> Secciones 1-3 del [plan-format](../../../.claude/rules/plan-format.md).

[← README](README.md) · [02 →](02-diagramas-flujo-er.md)

## 1. Contexto / Problema

Tras el refactor `direct-neon-writes` (commit `61be572`, mergeado a `dev`)
el backend escribe el pageview directo a Neon (`tracking_pixel` Lambda).
Sin embargo la tabla `tracking_events` deja 11 columnas siempre null en
produccion porque el pipeline esta incompleto:

### Hallazgos de exploracion

- **Frontend `packages/ui/src/lib/track-event.ts`**: hoy
  `buildTrackPayload` solo arma 7 campos (`operation`, `action`,
  `session_id`, `event_id`, `event_type_id`, `page_url`, `niche`,
  `event_props`). NO captura `page_title`, `page_path`, `referrer`,
  `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term`,
  `viewport_width`, `viewport_height`, `devicePixelRatio`. → 9 columnas
  null en cada fila.

- **Lambda `tracking_pixel`** (`core/models/tracking.py`): la Pydantic
  `TrackEventModel` declara esos campos como `Optional[str/int] = None`.
  Acepta lo que llegue. → no es un bug del Lambda, es que el front no
  manda nada.

- **Country**: `http_dispatch.py` lee del header `cf-ipcountry`
  (Cloudflare). PERO el endpoint `/track` va **directo browser →
  API Gateway Regional**. No pasa por Cloudflare. → `country` siempre
  llega `None`. AWS verificado: `api.portfolio.dev` es
  `endpointType=REGIONAL`. CloudFront-Viewer-Country tampoco llega
  (regional no esta detras de CF).

- **UA parsing**: `shared/observability/ua_parser.py` (existente) es un
  regex custom mantenido a mano. No cubre WebView de iOS, navegadores
  embebidos, bots modernos, ni Sec-CH-UA. → `browser_version` queda
  vacio en buena parte de los UAs reales.

- **Columna legacy `stream_event_id`**: introducida cuando habia
  `stream_processor` (DynamoDB Streams → Neon). Tras
  `direct-neon-writes`, el campo se pone a `None` en cada insert. Queda
  vivo solo en el modelo SQLAlchemy. Sin uso.

- **View transitions de Astro**: NO habilitadas. El portfolio es 100%
  hard navigation. Si en el futuro se habilita ClientRouter sin tocar
  el tracking, `document.title`/`location.href` cambian sin disparar
  el pageview.

- **Navbar bug (NicheDropdown + MobileNavDrawer)**:
  - **Desktop** (`packages/ui/src/components/NicheDropdown.astro`): el
    trigger tiene toggle (click → expand/collapse) y handlers de Escape
    y outside-click. El bug reportado: en re-bind tras navegacion
    (`astro:after-swap` o tras view transitions activadas en este
    plan), los listeners del nivel `document.addEventListener('click',
    ...)` se ACUMULAN — uno nuevo por cada re-mount sin remover el
    anterior. El sintoma visible es el dropdown que aparece
    "desplegado y no se cierra" (los listeners viejos se ejecutan
    sobre nodos huerfanos del DOM previo). Adicional: el `data-bound`
    flag previene re-binding del trigger pero NO del listener
    `document.click` ni de `keydown` → la fuga de listeners crece con
    cada nav. Fix: usar `AbortController` por instancia + cleanup en
    `astro:before-swap`.
  - **Mobile** (`packages/ui/src/components/MobileNavDrawer.astro`
    lineas 91-115): la seccion `dropdownItems` renderiza un
    `<span>` titulo + `<ul>` con TODOS los items siempre visibles.
    NO hay toggle: en mobile la lista de niches se ve completa al
    abrir el drawer, ocupando casi toda la pantalla. UX inconsistente
    con el desktop (que SI colapsa). Fix: convertir la seccion en un
    `<details>`/`<summary>` o button + collapse con `aria-expanded`,
    cerrado por default. Estado persiste mientras el drawer este
    abierto (cerrar el drawer resetea).

## 2. Solucion Propuesta

Plan en 4 ejes ortogonales, ejecutables en gran parte en paralelo:

### Eje A — Infraestructura (commits 2-4)

Recrear los 3 custom domains (`api.portfolio.dev`, `api.portfolio.stage`,
`api.portfolio`) como **Edge-Optimized**. AWS pone CloudFront por delante
automaticamente y el header `cloudfront-viewer-country` empieza a llegar
al Lambda en cada request. devtools provisiona esto via
`api_gateway/portfolio-api.yaml`.

### Eje B — Backend (commits 5-8)

- Migration Alembic `b2c3d4e5f6a7_drop_stream_event_id` (drop columna +
  modelo `TrackingEvent` sin la columna + repository limpio).
- Pydantic `TrackEventModel`: 9 campos pasan de `Optional` a required
  (acepta string vacio `''` como valor valido cuando aplica).
- `parse_user_agent` regex → `ua-parser` (uap-python). Borrar el modulo
  viejo + tests obsoletos.
- `http_dispatch.py`: leer `cloudfront-viewer-country` (case-insensitive)
  cuando `cf-ipcountry` esta ausente. Mantener fallback para tests.

### Eje C — Frontend (commits 9-11)

- `buildTrackPayload`: capturar 9 campos faltantes desde
  `document`/`window`/`location`. Parser de UTM desde `URLSearchParams`.
  Default `''` cuando no aplica.
- `BaseLayout.astro` de cada app: agregar `<ClientRouter />`. View
  transitions activas para navegacion entre paginas internas. Detalle de
  estilos y `transition:name` en
  [10-view-transitions-design.md](10-view-transitions-design.md).
- `TrackingPixel.astro`: hookear `astro:page-load` (cubre primera carga +
  client-side nav). Guard `firstLoad` evita doble disparo en la primera.
- View transitions (4 patrones acordados):
  1. Default page nav: **fade 300ms** (default Astro, ease-in-out).
  2. Shared element: **Hero identity** (`transition:name='hero-identity'`)
     en el bloque "Pablo Contreras / Senior Full Stack". Vuela suavemente
     entre paginas que lo contengan.
  3. Shared element: **Project card → detalle** (`transition:name='project-{slug}'`)
     en cada `ProjectCard` y en el hero de `/projects/[slug]`. Solo aplica
     en apps que ya tengan paginas de detalle; en las demas, los cards no
     declaran `transition:name` (graceful degradation).
  4. Shared element: **Theme toggle circular clip-path**. Al cambiar
     dark/light, el nuevo tema crece desde el button con `clip-path`
     circular. Firefox cae a cross-fade automatico (no soporta clip-path
     en view-transitions).
  5. Stagger: en listas (experiences/projects/skills), fade-in + 8px
     translateY con `animation-delay: calc(var(--idx) * 40ms)`,
     `duration: 400ms ease-out`. Solo en la PRIMERA carga del componente
     (`once: true` via IntersectionObserver), NO en cada nav.
  6. `prefers-reduced-motion: reduce` → strict: `@view-transition
     { navigation: none }` + todas las animaciones a `0.01s`. WCAG 2.2.
- Tests Vitest del parser UTM + trigger de `astro:page-load` + tests para
  el modulo de stagger (`packages/ui/src/lib/stagger.ts`).
- **Navbar fix (NicheDropdown + MobileNavDrawer)**:
  - `NicheDropdown.astro`: refactor del script para usar
    `AbortController` por instancia. Cleanup en `astro:before-swap`
    (remueve los listeners `document.click`/`keydown` antes del swap).
    `data-bound` se descarta — el cleanup explicito lo reemplaza. Se
    mantiene el comportamiento (Escape, outside-click, toggle).
  - `MobileNavDrawer.astro`: la seccion `dropdownItems` se renderiza
    con `<details>` + `<summary>`. Cerrada por default (`hidden`
    attribute o `details` sin `open`). El summary muestra el label
    (ej. "Otras vistas") + chevron rotativo. Anidado dentro del
    drawer; el cierre del drawer mantiene el estado o resetea — se
    elige reset al cerrar para coherencia.
  - Detalle de codigo + tests E2E en
    [11-navbar-dropdown-fix.md](11-navbar-dropdown-fix.md).

### Eje D — Deploy y verificacion (commits 12-14)

- Playwright valida que el body del sendBeacon trae los 11 campos
  esperados, en las 6 apps.
- Deploy a dev → migration + truncate → verificar 1 pageview real → deploy
  a stage → prod.
- Verificacion E2E final + remover la carpeta del plan.

### Decisiones clave

- **Decision 1**: PK actual `(session_id, page_id, created_at)` se mantiene.
  Razon: la tabla esta particionada por `created_at` (PG exige la partition
  key en la PK). Cambiar la PK obliga a recrear la tabla; no aporta valor
  funcional (page_id ya es unico por si solo, `(session_id, page_id)` ya
  es unico tambien).
- **Decision 2**: Solo dropear `stream_event_id`. Razon: la columna no
  tiene consumers vivos; el refactor `direct-neon-writes` la dejo huerfana.
- **Decision 3**: Custom domains a Edge-Optimized (NO CF distribution
  propia, NO GeoIP local). Razon: cero infra nueva, cero costo extra,
  CloudFront-Viewer-Country exacto y gratis.
- **Decision 4**: `ua-parser` oficial (NO regex custom, NO `user-agents`
  lib). Razon: regex specs mantenidos por la comunidad, mejor accuracy en
  WebView/mobile/bots; +5MB al zip es aceptable (zip actual ≤30MB).
- **Decision 5**: Truncate `tracking_events` en dev Y prod. Razon: los
  datos pre-direct-neon-writes son de test, sin valor analitico. Empezar
  limpio. Backfill no aporta.
- **Decision 6**: View transitions activas + tracking en `astro:page-load`.
  Razon: el portfolio se siente mas pulido con view transitions; el
  trigger uniforme cubre el caso futuro de SPA nav sin doble disparo.
- **Decision 7** (transitions): fade 300ms default + 3 shared elements
  (hero identity, project card morph, theme toggle clip-path) + stagger
  ON 40ms en listas + strict reduced-motion. Razon: combinacion validada
  como "wow sin cringe" en portfolios de referencia 2025-2026, baja
  exposicion a colisiones de `transition:name`, accesibilidad por
  default. Detalle de codigo en
  [10-view-transitions-design.md](10-view-transitions-design.md).
- **Decision 8** (navbar): refactor del NicheDropdown a
  `AbortController` + cleanup en `astro:before-swap`. Mobile drawer
  usa `<details>` + `<summary>` cerrado por default. Razon: el bug
  visible empeora cuando se activan view transitions (mas re-mounts);
  resolverlo en el mismo plan evita regresion. `<details>` es solucion
  nativa sin JS extra para mobile. Detalle de codigo en
  [11-navbar-dropdown-fix.md](11-navbar-dropdown-fix.md).

## 3. Criterios de Aceptacion (BDD)

Numerados AC-1..AC-10. Fuente de verdad para tests del capitulo
[03-tests-requeridos.md](03-tests-requeridos.md).

- **AC-1** (Pydantic required):
  Given un POST `/track` con `data` sin `page_path`,
  When el Lambda valida el payload,
  Then responde HTTP 400 con `code=INVALID_REQUEST` y `detail`
  enumerando el campo faltante.

- **AC-2** (full pageview persiste):
  Given un POST `/track` con los 9 campos required + `referrer` no vacio +
  `cloudfront-viewer-country=US`,
  When el Lambda procesa el evento,
  Then la fila resultante en `tracking_events` trae las 11 columnas
  populadas: `page_path`, `page_url`, `page_title`, `referrer`,
  `utm_source..utm_content`, `viewport_width`, `viewport_height`,
  `country`, `browser_version`.

- **AC-3** (country desde CloudFront):
  Given el event de API Gateway trae `headers['cloudfront-viewer-country']=US`,
  When el handler extrae el meta,
  Then `meta.country='US'`. Si el header viene en mayusculas
  (`CloudFront-Viewer-Country`), tambien matchea (case-insensitive).

- **AC-4** (ua-parser cubre casos reales):
  Given los User-Agent: Chrome iOS, Chrome Android WebView, Firefox,
  Safari macOS, Edge, Googlebot,
  When `parse_user_agent` corre,
  Then devuelve `browser_name`, `browser_version`, `os_name`, `device_type`
  con los valores correctos (asserts EXACTOS contra la tabla del capitulo
  [03](03-tests-requeridos.md)).

- **AC-5** (migration limpia stream_event_id):
  Given una DB Neon con la migration aplicada `7c4d9e1b2a3f` (init unified),
  When se aplica `b2c3d4e5f6a7_drop_stream_event_id`,
  Then la columna `stream_event_id` ya no existe en `tracking_events`.
  El `downgrade()` la recrea con el mismo tipo y nullable.

- **AC-6** (viewport real desde el browser):
  Given el frontend dispara el pageview en un Chromium real,
  When inspeccionas el body del sendBeacon,
  Then `viewport_width === window.innerWidth` y
  `viewport_height === window.innerHeight` (numeros, no strings).

- **AC-7** (astro:page-load sin doble disparo):
  Given una carga inicial del home + 2 navegaciones internas via ClientRouter,
  When monitoreas los POST `/track` con Playwright,
  Then hay exactamente 3 requests al endpoint, con `page_path` distintos
  y `event_type_id=pageview`. Cero requests duplicados en la primera
  carga.

- **AC-8** (Edge-Optimized en los 3 envs):
  Given los 3 custom domains migrados,
  When `aws apigateway get-domain-name --domain-name ...` por env,
  Then `endpointConfiguration.types[0] === 'EDGE'` en dev, stage y prod.
  El endpoint sigue respondiendo HTTP 200 a `/health` y `/track`.

- **AC-9** (utm parser robusto):
  Given URLs con/sin query string utm,
  When el frontend arma el payload,
  Then `utm_source/medium/campaign/content` son siempre string (`''`
  cuando no hay query), nunca `undefined` ni `null` en el JSON enviado.
  URLs validas: `/`, `/?utm_source=linkedin`,
  `/?utm_source=x&utm_medium=organic&utm_campaign=q2`.

- **AC-10** (coverage + TDD):
  Given los archivos modificados por este plan,
  When se ejecuta `pnpm exec vitest run --coverage` y
  `serverless tests --type=coverage --lambda=tracking_pixel`,
  Then la coverage per-file de cada archivo modificado es >= 80%.
  Cada test referencia al menos un AC explicito en su `it(...)` o
  docstring.

- **AC-11** (view transitions activas y reduced-motion respetado):
  Given las 6 apps con `<ClientRouter />` en `BaseLayout`,
  When un usuario navega entre dos paginas del mismo subdominio,
  Then se aplica fade 300ms (default Astro). El bloque
  `transition:name='hero-identity'` morphea entre las dos paginas si
  existe en ambas. Theme toggle hace circular clip-path en
  Chrome/Edge/Safari (fade en Firefox). El stagger fade-in dispara
  exactamente UNA vez por lista (primera carga). Con
  `prefers-reduced-motion: reduce`, las transitions tienen duration
  `0.01s` y `@view-transition { navigation: none }` esta activo. Hay
  cero colisiones de `transition:name` (`docs/diagrams/`-style audit
  manual + Playwright snapshot).

- **AC-12** (NicheDropdown desktop estable cross-navigation):
  Given el `NicheDropdown` montado en una page del subdominio,
  When el usuario navega a otra page (via ClientRouter), vuelve, y
  hace click 3 veces alternando expand/collapse,
  Then el dropdown abre y cierra correctamente cada vez. Click fuera
  del dropdown lo cierra. Escape lo cierra y devuelve focus al
  trigger. `aria-expanded` refleja el estado real. NO hay listeners
  fugados (auditable con `getEventListeners(document)` en DevTools:
  como maximo 1 `click` y 1 `keydown` por instancia activa).

- **AC-13** (MobileNavDrawer dropdown colapsable):
  Given el viewport en mobile (< 768px) y el drawer abierto,
  When inspeccionas la seccion "Otras vistas",
  Then se renderiza como `<details>` cerrado por default. Click en
  `<summary>` lo expande, mostrando los 5 items con animacion suave.
  Otro click lo cierra. Al cerrar el drawer (X o backdrop), la
  seccion vuelve a estado cerrado en la proxima apertura.
  `aria-expanded` del summary refleja el estado.

- **AC-14** (E2E navbar across breakpoints):
  Given los specs Playwright `tests/feature/specs/navbar.spec.ts`,
  When se ejecutan en chromium con viewport 1280x800 y 375x667,
  Then:
  - viewport 1280: el NicheDropdown trigger es visible en el nav
    horizontal; click → menu aparece con 5 items; click outside →
    menu se cierra; Escape → menu se cierra y trigger recibe focus.
  - viewport 375: el nav-inline esta oculto y el hamburger visible;
    click hamburger → `<dialog>` abre; "Otras vistas" aparece como
    `<details>` cerrado; click summary → expand; click X → drawer
    cierra; reabrir → details vuelve a estar cerrado.
  - resize 1280 → 375 con dropdown abierto en desktop → al cruzar
    el breakpoint 768px el dropdown desktop se oculta sin freeze
    visual; abrir hamburger refleja el mismo set de items.

---

Siguiente: [02. Diagramas de flujo y ER →](02-diagramas-flujo-er.md)
