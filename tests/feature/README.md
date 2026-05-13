# Feature tests (Playwright E2E) - Portfolio

> Suite E2E shared para las 6 apps Astro del portfolio. Container Playwright
> aislado (`docker/dockerfiles/local/feature/Dockerfile`) con chromium +
> webkit pre-instalados.

## Estructura

```
tests/feature/
├── playwright.config.ts    # Config: 5 projects (desktop+mobile, chromium+webkit, tablet)
├── package.json             # @playwright/test aislado (no parte del workspace)
├── tsconfig.json
├── fixtures/
│   ├── index.ts             # `test`, `expect`, `subdomainUrl()` helper
│   └── api/
│       └── api-client.ts    # Cliente HTTP reusable (stub para futuro API)
├── helpers/
│   ├── screenshot.ts        # Capture + adjuntar al report
│   └── inspect-overlay.ts   # Debug overlay (gated by DEBUG_INSPECT=1)
└── <feature>/<feature>.spec.ts  # Tus specs van aqui
```

## Convencion para escribir tests

- BDD-style en `test()`: `Given <state> When <action> Then <outcome>`
- 1 carpeta por feature/area: `tests/feature/<area>/<area>.spec.ts`
- Importar fixtures: `import { test, expect, subdomainUrl } from '../fixtures/index.js'`
- Para navegar a un subdominio:
  ```ts
  await page.goto(subdomainUrl('hub') + '/')       // hub.localhost
  await page.goto(subdomainUrl() + '/about')       // localhost/about
  ```
- Asserts EXACTOS (`toHaveText('Pablo')`, no `toContainText(/p/)`)
- Selectors via `data-testid="..."` cuando sea custom; sino role/text

## Correr tests

### Local con Docker (recomendado)

```bash
# 1. Levantar el stack (nginx + 6 apps)
cd <portfolio root>
docker compose -p portfolio -f docker/docker-compose/local.yml up -d --build

# 2. Levantar el container feature (Playwright)
docker compose -p portfolio -f docker/docker-compose/local.yml \
  --profile feature up -d feature

# 3. Esperar a que el container este ready
docker exec portfolio-feature-local test -f /tmp/.feature-ready && echo ready

# 4. Ejecutar tests
docker exec portfolio-feature-local pnpm test

# 5. Ver reporte HTML
docker exec portfolio-feature-local pnpm exec playwright show-report --host 0.0.0.0
```

### Local sin Docker (solo si tenes browsers de Playwright instalados)

```bash
cd tests/feature
pnpm install --ignore-workspace
pnpm exec playwright install chromium webkit
pnpm test
```

## Variables de entorno

| Var | Default | Uso |
|-----|---------|-----|
| `PROXY_PORT` | `9970` | Puerto donde nginx expone el stack |
| `CI` | (unset) | Si `true`: reporters github + blob + json, retries=2 |
| `DEBUG_INSPECT` | `0` | Si `1`: `inspectOverlay()` hace `page.pause()` con overlay |

## Notas

- `network_mode: host` en el container feature: Playwright accede directo
  a `localhost:PROXY_PORT`. Las entradas `*.localhost` se inyectan al
  `/etc/hosts` del container via `feature-entrypoint.sh`.
- Los browsers (chromium + webkit) se instalan en `~/.cache/ms-playwright`
  dentro del container al primer `pnpm exec playwright install`.
- En CI, los reporters `github` (annotations) + `blob` (rerun support) +
  `json` (programatic access) + `html` (visual report) corren en paralelo.
