# 06. Commits

> Seccion 9 del [plan-format](../../../.claude/rules/plan-format.md).
> Cada commit deja el repo verde + lleva verificacion incremental
> ANTES de commitear. Idioma: espanol. Sin atribucion IA.

[← 05](05-descomposicion-paralelizacion.md) · [README](README.md) · [07 →](07-paralelizacion-worktrees.md)

## Resumen secuencial (15 commits)

```text
1.  docs(specs): plan tracking-data-completeness
─── base secuencial ──────────────────────────────────────
2.  chore(devtools): provisioner soporta endpointType=EDGE
3.  feat(infra): api.portfolio.dev -> Edge-Optimized
4.  feat(infra): api.portfolio.stage + api.portfolio (prod) -> Edge-Optimized
5.  refactor(db): drop stream_event_id de tracking_events
6.  feat(lambda): TrackEventModel exige 9 campos required
7.  refactor(lambda): ua-parser oficial reemplaza regex custom
8.  feat(lambda): leer country de cloudfront-viewer-country
─── paralelizable con worktrees (ver capitulo 07) ───────
9.  feat(frontend): build-track-payload con 9 campos required
10. feat(frontend): ClientRouter + view transitions globales
11. fix(ui): NicheDropdown AbortController + drawer details
12. feat(frontend): HeroIdentity + ProjectCard transition:name
─── base secuencial ──────────────────────────────────────
13. test(feature): E2E tracking + view-transitions + navbar
14. chore(deploy): aplicar EDGE + migration + truncate + redeploy
15. chore(plan): verificacion E2E final + git rm -r del plan
```

## Plantilla por commit

Cada entrada documenta:

- **Que cambia** (resumen 1 linea, Conventional Commits)
- **AC cubiertos** (referencia a [01](01-contexto-y-decision.md))
- **Verify** (comando que se ejecuta ANTES de commitear)
- **Mensaje sugerido** (subject + body en Conventional Commits espanol)

---

## C1 — docs(specs): plan

- **Que cambia**: carpeta `docs/specs/tracking-data-completeness/`
  completa (12 archivos).
- **AC**: ninguno (planificacion).
- **Verify**: `ls docs/specs/tracking-data-completeness/ | wc -l` ≥ 12.
- **Mensaje**:
  ```
  docs(specs): plan tracking-data-completeness

  - Carpeta docs/specs/tracking-data-completeness/ con 12 capitulos
  - 14 AC numerados (BDD) cubriendo backend + frontend + infra
  - Decisiones no-reabribles: edge-optimized, ua-parser, truncate,
    view transitions, navbar fix
  ```

## C2 — chore(devtools): provisioner EDGE

- **Que cambia**: `devtools/serverless/provisioner.py` agrega soporte
  para `endpointType: EDGE` en api_gateway. Tests unit nuevos.
- **AC**: AC-8 (parcial — la infra real en C3/C4).
- **Verify**:
  ```bash
  python devtools/run.py test_runner --module=devtools --type=unit -- -k provisioner_supports_endpoint_type_edge
  ```
- **Mensaje**:
  ```
  chore(devtools): provisioner soporta endpointType=EDGE en api_gateway

  - Lee endpointType del yaml (REGIONAL o EDGE); default REGIONAL
  - Si el estado actual del custom domain difiere del yaml, recrea
  - Tests unit para create EDGE y para drift detection
  ```

## C3 — feat(infra): api.portfolio.dev -> EDGE

- **Que cambia**: `api_gateway/portfolio-api.yaml` pasa `endpointType: EDGE`. Estado local del provisioner para dev.
- **AC**: AC-8 (dev).
- **Verify**: `python devtools/run.py serverless tests --type=unit -- -k provisioner` verde. El apply real ocurre en C14.
- **Mensaje**:
  ```
  feat(infra): api.portfolio.dev configurado como Edge-Optimized

  - portfolio-api.yaml dev pasa endpointType: EDGE
  - CloudFront-Viewer-Country llegara como header al Lambda
  - Apply real en commit 14 (con DNS TTL bajo, ventana fuera de hora pico)
  ```

## C4 — feat(infra): stage + prod -> EDGE

- **Que cambia**: idem C3 para stage y prod.
- **AC**: AC-8 (stage, prod).
- **Verify**: tests provisioner verdes.
- **Mensaje**:
  ```
  feat(infra): api.portfolio.stage y api.portfolio (prod) -> Edge-Optimized

  - Mismo patron que dev (commit 3)
  - 3 envs alineados; apply real en commit 14
  ```

## C5 — refactor(db): drop stream_event_id

- **Que cambia**: migration Alembic + modelo + repository.
- **AC**: AC-5.
- **Verify**:
  ```bash
  # En branch Neon de prueba:
  alembic -c shared/db/alembic.ini upgrade head
  alembic -c shared/db/alembic.ini downgrade -1
  alembic -c shared/db/alembic.ini upgrade head
  # En el repo:
  rg "stream_event_id" serverless/ packages/ | wc -l   # 0
  ```
- **Mensaje**:
  ```
  refactor(db): drop stream_event_id de tracking_events

  - Migration b2c3d4e5f6a7_drop_stream_event_id (upgrade + downgrade)
  - Modelo SQLAlchemy y repository sin la columna
  - tracking_service ya no setea stream_event_id en el neon_payload
  - Columna legacy del refactor direct-neon-writes; sin consumers vivos
  ```

## C6 — feat(lambda): Pydantic required

- **Que cambia**: `TrackEventModel` con 9 fields required + 13 tests unit.
- **AC**: AC-1, AC-2, AC-9.
- **Verify**:
  ```bash
  python devtools/run.py serverless tests --type=coverage --lambda=tracking_pixel
  ```
  Cero rojos. Coverage per-file ≥80%.
- **Mensaje**:
  ```
  feat(lambda): TrackEventModel exige 9 campos required

  - page_path, page_url, page_title, viewport_width, viewport_height,
    utm_source, utm_medium, utm_campaign, utm_content son required
  - referrer queda opcional (default '')
  - HTTP 400 INVALID_REQUEST si falta algun campo required
  - 13 unit tests nuevos (1 por escenario), AAA + Given/When/Then
  ```

## C7 — refactor(lambda): ua-parser

- **Que cambia**: regex custom -> `ua-parser` oficial. `pyproject.toml`
  con la dep nueva. Tests del shared.
- **AC**: AC-4.
- **Verify**:
  ```bash
  cd serverless/lambda/shared/observability && uv lock --upgrade-package ua-parser
  python devtools/run.py serverless tests --type=coverage --shared
  rg "_PARSER_REGEX" serverless/lambda/shared/observability/ | wc -l   # 0
  ```
- **Mensaje**:
  ```
  refactor(lambda): ua-parser oficial reemplaza regex custom

  - shared/observability/ua_parser.py usa ua_parser.user_agent_parser
  - 9 tests nuevos: Chrome iOS, Android WebView, Firefox, Safari,
    Edge, Googlebot + 3 tests del replace
  - Borrado el regex custom (cubrira casos que el regex erraba)
  - +5MB al zip aceptado (zip actual <30MB)
  ```

## C8 — feat(lambda): cloudfront-viewer-country

- **Que cambia**: `http_dispatch.py` lee
  `cloudfront-viewer-country` (case-insensitive) con fallback a
  `cf-ipcountry`.
- **AC**: AC-3.
- **Verify**:
  ```bash
  python devtools/run.py serverless tests --type=coverage --shared
  ```
- **Mensaje**:
  ```
  feat(lambda): leer country de header cloudfront-viewer-country

  - http_dispatch.extract_meta intenta cloudfront-viewer-country primero,
    luego cf-ipcountry como fallback (compat con tests + Cloudflare)
  - Case-insensitive lookup
  - Tests: lower, upper, fallback none
  ```

## C9 — feat(frontend): build-track-payload

- **Que cambia**: extrae el constructor del payload a un modulo
  testeable + lo extiende con los 9 campos faltantes.
- **AC**: AC-1, AC-2, AC-6, AC-9.
- **Verify**:
  ```bash
  pnpm --filter @portfolio/ui exec vitest run --coverage
  pnpm exec biome check packages/ui/
  pnpm exec tsc --noEmit
  ```
- **Mensaje**:
  ```
  feat(frontend): build-track-payload con 9 campos required

  - packages/ui/src/lib/build-track-payload.ts (nuevo modulo)
  - Captura page_path, page_url, page_title, referrer, utm_*,
    viewport_*, devicePixelRatio del browser
  - URLSearchParams para utm_*; default '' cuando no hay query
  - Triggers en astro:page-load con guard firstLoad (anti doble-fire)
  - 8 unit tests Vitest con happy-dom
  ```

## C10 — feat(frontend): ClientRouter + view transitions

- **Que cambia**: agrega `<ClientRouter />` al BaseLayout + crea
  `view-transitions.css` global + modulo de stagger + script clip-path
  del theme toggle.
- **AC**: AC-7, AC-11.
- **Verify**:
  ```bash
  pnpm exec astro check
  pnpm run build   # las 6 apps OK
  pnpm --filter @portfolio/ui exec vitest run --coverage
  pnpm run dev     # smoke manual: fade entre pages
  ```
- **Mensaje**:
  ```
  feat(frontend): ClientRouter + view transitions globales

  - <ClientRouter /> en BaseLayout (6 apps)
  - packages/ui/src/styles/view-transitions.css (fade 300ms default,
    stagger keyframes, reduced-motion strict)
  - packages/ui/src/lib/stagger.ts (IntersectionObserver once:true)
  - ThemeToggle con circular clip-path en startViewTransition
  ```

## C11 — fix(ui): NicheDropdown + MobileNavDrawer

- **Que cambia**: `NicheDropdown` con `AbortController` + cleanup en
  `astro:before-swap`. `MobileNavDrawer` con `<details>` colapsable.
- **AC**: AC-12, AC-13.
- **Verify**:
  ```bash
  pnpm --filter @portfolio/ui exec vitest run --coverage
  pnpm exec astro check
  # Smoke desktop + mobile en dev server
  ```
- **Mensaje**:
  ```
  fix(ui): NicheDropdown sin listener-leak + MobileNavDrawer colapsable

  - NicheDropdown: AbortController por instancia, cleanup en
    astro:before-swap (resuelve dropdown que no cerraba tras nav)
  - MobileNavDrawer: seccion dropdownItems pasa a <details>+<summary>
    cerrado por default. Reset al cerrar el drawer
  - Tests unit nuevos cubren toggle, outside-click, Escape,
    cross-nav stability, drawer reset
  ```

## C12 — feat(frontend): HeroIdentity + ProjectCard transitions

- **Que cambia**: componente nuevo `HeroIdentity.astro` con
  `transition:name='hero-identity'`. Modifica `ProjectCard.astro` con
  `transition:name='project-{slug}'`. Pages que lo consumen.
- **AC**: AC-11.
- **Verify**:
  ```bash
  rg "transition:name" apps/ packages/  # solo hero-identity y project-{slug}
  pnpm run build  # 6 apps OK
  ```
- **Mensaje**:
  ```
  feat(frontend): HeroIdentity + ProjectCard con transition:name

  - HeroIdentity.astro (packages/app-shared) reutilizable en 6 apps
  - Block hero (name + role) usa transition:name='hero-identity'
  - ProjectCard thumbnail usa transition:name='project-{slug}'
  - Pages /index, /about, /experience consumen HeroIdentity
  - Pages /projects/[slug] (donde existen) declaran el mismo name
  ```

## C13 — test(feature): Playwright E2E

- **Que cambia**: 3 specs nuevos en `tests/feature/specs/`.
- **AC**: AC-2, AC-6, AC-9, AC-11, AC-12, AC-13, AC-14.
- **Verify**:
  ```bash
  python devtools/run.py docker up --env=local
  python devtools/run.py test_runner --module=feature --type=feature --env=local
  ```
- **Mensaje**:
  ```
  test(feature): E2E tracking + view-transitions + navbar

  - tests/feature/specs/tracking-pageview.spec.ts (6 apps; valida 11 campos
    en el body del sendBeacon)
  - tests/feature/specs/view-transitions.spec.ts (fade + hero morph +
    reduced-motion respect)
  - tests/feature/specs/navbar.spec.ts (desktop toggle, mobile details,
    breakpoint resize 1280->375)
  ```

## C14 — chore(deploy): aplicar todo en cloud

- **Que cambia**: NO codigo. Solo operaciones AWS + Neon. Estado local
  del provisioner se mueve a S3.
- **AC**: AC-2 + AC-3 + AC-5 + AC-8 (verificacion en cloud).
- **Verify**: bateria del capitulo [08-verificacion-e2e.md](08-verificacion-e2e.md).
- **Procedimiento** (ventana coordinada):
  1. **DNS TTL bajo**: 10 min antes, bajar TTL del CNAME a 60s en Cloudflare.
  2. **DEV**:
     ```bash
     export AWS_PROFILE=tfs-dev
     python devtools/run.py serverless provision-infra --stage=dev --aws-profile=tfs-dev
     python devtools/run.py serverless run --lambda=db --stage=dev --event=events/migrate.json --aws-profile=tfs-dev
     python devtools/run.py serverless run --lambda=db --stage=dev --event=events/truncate-tracking.json --aws-profile=tfs-dev
     python devtools/run.py serverless deploy --lambda=tracking_pixel --stage=dev --aws-profile=tfs-dev
     python devtools/run.py serverless deploy --lambda=contact_form --stage=dev --aws-profile=tfs-dev
     ```
  3. **Verificar dev**: curl /track desde browser real + SELECT * FROM tracking_events LIMIT 1
  4. **STAGE**: idem dev con `--stage=stage --aws-profile=tfs-stage` (si existe; si no, posponer stage).
  5. **PROD**: idem con `--stage=prod --aws-profile=tfs-prod`.
- **Mensaje**:
  ```
  chore(deploy): aplicar Edge-Optimized + migration + truncate + redeploy

  - dev/stage/prod: custom domain pasa a Edge-Optimized
  - Migration b2c3d4e5f6a7 aplicada (drop stream_event_id)
  - tracking_events truncado (datos pre-direct-neon sin valor analitico)
  - tracking_pixel + contact_form redeploy en los 3 envs
  - DNS TTL bajado a 60s 10min antes; revertido a 3600s al cierre
  ```

## C15 — chore(plan): verificacion E2E + delete plan folder

- **Que cambia**: ejecutar la bateria final del capitulo
  [08](08-verificacion-e2e.md) y eliminar `docs/specs/tracking-data-completeness/`.
- **AC**: todos (cierre).
- **Verify**: la bateria entera en VERDE:
  ```bash
  pnpm exec biome check .
  pnpm exec tsc --noEmit
  pnpm exec astro check
  pnpm exec vitest run --coverage
  pnpm run build
  python devtools/run.py serverless tests --type=coverage
  python devtools/run.py test_runner --module=feature --type=feature --env=local
  ```
  TODOS verdes. Coverage per-file >=80%. Cero tests rojos.
- **Mensaje**:
  ```
  chore(plan): verificacion E2E final + cierre plan tracking-data-completeness

  - Bateria full en verde: lint + typecheck + unit + coverage + build
    + feature E2E (6 apps)
  - Verificacion smoke en dev/stage/prod: filas en Neon con 11 cols pobladas,
    cloudfront-viewer-country presente, view transitions activas
  - git rm -r docs/specs/tracking-data-completeness/ (carpeta del plan,
    ya cumple su funcion; queda en git log)
  ```

## Resumen de secuencia y dependencias

```text
C1 (base)
 |
 +-> C2 (provisioner) -> C3 (dev yaml) ----> C14 (apply dev)
 |                       C4 (stage+prod) --> C14 (apply stage+prod)
 |
 +-> C5 (DB migration) ------------------> C14 (apply migration)
 +-> C6 (Pydantic required) -------------> C14 (deploy Lambda)
 +-> C7 (ua-parser swap) ----------------> C14 (deploy Lambda)
 +-> C8 (cloudfront-viewer-country) -----> C14 (deploy Lambda)
 |
 +-> C9 (build-track-payload) ----+
 +-> C10 (ClientRouter + VT) -----+--> C13 (Playwright) -> C15 (final)
 +-> C11 (navbar fix) ------------+
 +-> C12 (HeroIdentity + cards)---+
```

## PR

UN solo PR `feature/tracking-data-completeness -> dev`. Despues, el
flujo estandar `dev -> stage` y `stage -> main` lo promociona (ver
[git-workflow.md](../../../.claude/rules/git-workflow.md)).

---

Siguiente: [07. Paralelizacion con git worktrees →](07-paralelizacion-worktrees.md)
