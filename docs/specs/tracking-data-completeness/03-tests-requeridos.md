# 03. Tests requeridos

> Seccion 6 del [plan-format](../../../.claude/rules/plan-format.md).
> TDD obligatorio: cada test referencia al menos un AC (`[AC-N]`).

[← 02](02-diagramas-flujo-er.md) · [README](README.md) · [04 →](04-archivos-afectados.md)

## 6.A. TDD flows (logica nueva)

| Archivo | Test (WHEN/THEN) | AC |
|---------|------------------|----|
| `packages/ui/src/lib/build-track-payload.ts` (NUEVO) | WHEN URL=`/projects?utm_source=ln&utm_medium=organic` THEN payload trae `utm_source='ln'`, `utm_medium='organic'`, `utm_campaign=''`, `utm_content=''` | AC-9 |
| `packages/ui/src/lib/build-track-payload.ts` | WHEN window.innerWidth=1280, innerHeight=800, devicePixelRatio=2 THEN payload trae viewport como integers, devicePixelRatio=2 | AC-6 |
| `packages/ui/src/lib/build-track-payload.ts` | WHEN document.referrer='' THEN payload trae `referrer=''` (NUNCA null/undefined) | AC-2 |
| `packages/ui/src/lib/stagger.ts` (NUEVO) | WHEN container con 4 items y IntersectionObserver fires THEN cada item recibe `--stagger-idx` 0..3 + clase `stagger-visible` con delay incremental | AC-11 |
| `packages/ui/src/lib/stagger.ts` | WHEN observer reobserva el mismo item THEN `unobserve()` previene el segundo trigger (`once: true`) | AC-11 |
| `serverless/lambda/services/tracking_pixel/core/services/tracking_service.py` | WHEN parse_user_agent recibe Chrome iOS WebView UA THEN devuelve `browser='Chrome Mobile', os='iOS', device_type='mobile'` | AC-4 |
| `shared/lambda_kit/http_dispatch.py` | WHEN headers={'cloudfront-viewer-country':'US'} THEN meta.country='US' | AC-3 |
| `shared/lambda_kit/http_dispatch.py` | WHEN headers={'CloudFront-Viewer-Country':'US'} (mayus) THEN meta.country='US' (case-insensitive) | AC-3 |

## 6.B. Unit tests (Vitest, happy-dom)

Coverage v8 >= 80% per-file en archivos modificados.

### `packages/ui/tests/unit/lib/build-track-payload.test.ts` (NUEVO)

```typescript
describe('buildTrackPayload', () => {
  it('Given URL with utm_* When build Then all 4 utm fields populated [AC-9]', () => {})
  it('Given URL without query When build Then utm_* are empty strings [AC-9]', () => {})
  it('Given document with title When build Then page_title matches document.title [AC-2]', () => {})
  it('Given window.innerWidth=1920 When build Then viewport_width === 1920 [AC-6]', () => {})
  it('Given devicePixelRatio=3 When build Then devicePixelRatio === 3 [AC-6]', () => {})
  it('Given document.referrer empty When build Then referrer === "" [AC-2]', () => {})
  it('Given location.pathname=/projects/foo When build Then page_path === "/projects/foo" [AC-2]', () => {})
  it('Given no utm + no referrer When build Then ALL 9 required fields present as string [AC-1]', () => {})
})
```

Mockear: `window`, `document`, `location`, `navigator` via happy-dom
helpers. NO mockear utilities propias.

### `packages/ui/tests/unit/lib/stagger.test.ts` (NUEVO)

```typescript
describe('applyStagger', () => {
  it('Given container with 4 items When called Then each item gets --stagger-idx [AC-11]', () => {})
  it('Given items not in viewport When IO fires Then no item is visible [AC-11]', () => {})
  it('Given item in viewport When IO fires Then unobserve is called (once:true) [AC-11]', () => {})
  it('Given prefers-reduced-motion When stagger applied Then items are immediately visible [AC-11]', () => {})
})
```

### `packages/ui/tests/unit/components/NicheDropdown.test.ts` (NUEVO)

```typescript
describe('NicheDropdown', () => {
  it('Given trigger When click Then aria-expanded toggles true/false [AC-12]', () => {})
  it('Given menu open When click outside Then menu hidden [AC-12]', () => {})
  it('Given menu open When Escape Then closes and trigger focused [AC-12]', () => {})
  it('Given astro:before-swap When fires Then AbortController.abort called [AC-12]', () => {})
  it('Given 3x astro:after-swap When fires Then exactly 1 doc.click listener per instance [AC-12]', () => {})
})
```

### `packages/ui/tests/unit/components/MobileNavDrawer.test.ts` (NUEVO)

```typescript
describe('MobileNavDrawer', () => {
  it('Given dropdownItems prop When rendered Then <details> exists and is closed [AC-13]', () => {})
  it('Given summary click When triggered Then details.open === true [AC-13]', () => {})
  it('Given dialog close event When fires Then all details collapse [AC-13]', () => {})
})
```

### Lambda — `serverless/lambda/services/tracking_pixel/tests/unit/`

Path mirroring desde `core/`. Estandar de testing del proyecto:
**un archivo por escenario**, docstring Given/When/Then, Arrange-Act-Assert.

```
tests/unit/
├── test_track_event_model_required_page_path.py     # AC-1
├── test_track_event_model_required_viewport.py      # AC-1
├── test_track_event_model_required_utm_all.py       # AC-1 + AC-9
├── test_track_event_model_optional_referrer.py      # AC-2
├── test_tracking_service_persists_full_row.py      # AC-2
├── test_tracking_service_uses_country_meta.py      # AC-3
├── test_parse_ua_chrome_ios.py                      # AC-4
├── test_parse_ua_android_webview.py                 # AC-4
├── test_parse_ua_firefox.py                         # AC-4
├── test_parse_ua_safari.py                          # AC-4
├── test_parse_ua_edge.py                            # AC-4
├── test_parse_ua_googlebot.py                       # AC-4
└── test_handler_returns_400_when_page_path_missing.py  # AC-1
```

### Shared — `serverless/lambda/shared/tests/`

```
shared/tests/lambda_kit/
├── test_http_dispatch_country_cloudfront_lower.py   # AC-3
├── test_http_dispatch_country_cloudfront_upper.py   # AC-3
├── test_http_dispatch_country_fallback_none.py      # AC-3

shared/tests/observability/
├── test_ua_parser_replaces_regex_chrome.py          # AC-4
├── test_ua_parser_replaces_regex_safari.py          # AC-4
└── test_ua_parser_replaces_regex_bot.py             # AC-4
```

### Devtools — `devtools/tests/unit/src/serverless/`

```
serverless/
├── test_provisioner_supports_endpoint_type_edge.py  # AC-8
└── test_provisioner_recreates_domain_on_endpoint_change.py  # AC-8
```

## 6.C. Typecheck

Despues de cada commit que toca TypeScript / Astro:

```bash
pnpm exec tsc --noEmit
pnpm exec astro check
```

Falla = no commit.

## 6.D. Feature tests E2E (Playwright, OBLIGATORIO antes del PR)

Suite en `tests/feature/specs/`. Cubre flujos completos cross-app.

### `tests/feature/specs/tracking-pageview.spec.ts` (NUEVO)

```typescript
import { test, expect } from '@playwright/test'

const APPS = ['generic', 'hub', 'fintech', 'architect', 'leader', 'vibe']

for (const app of APPS) {
  test(`POST /track body trae 11 campos esperados — ${app} [AC-2, AC-6, AC-9]`, async ({ page }) => {
    const host = app === 'generic' ? 'localhost' : `${app}.localhost`
    const trackRequest = page.waitForRequest((req) =>
      req.url().includes('/track') && req.method() === 'POST',
    )

    await page.goto(`http://${host}:9970/?utm_source=test&utm_medium=playwright`)
    const req = await trackRequest
    const body = JSON.parse(req.postData() ?? '{}')

    expect(body.data.page_path).toBe('/')
    expect(body.data.page_url).toContain(`http://${host}`)
    expect(body.data.page_title).toBeTruthy()
    expect(body.data.viewport_width).toBeGreaterThan(0)
    expect(body.data.viewport_height).toBeGreaterThan(0)
    expect(body.data.utm_source).toBe('test')
    expect(body.data.utm_medium).toBe('playwright')
    expect(body.data.utm_campaign).toBe('')
    expect(body.data.utm_content).toBe('')
    expect(body.data.referrer).toBeDefined()
    expect(typeof body.data.referrer).toBe('string')
  })
}
```

### `tests/feature/specs/view-transitions.spec.ts` (NUEVO)

```typescript
import { test, expect } from '@playwright/test'

test('navegacion entre /home y /experience aplica fade transition [AC-11]', async ({ page }) => {
  await page.goto('http://localhost:9970/')
  const transitionStart = page.evaluate(() => {
    return new Promise<boolean>((resolve) => {
      document.addEventListener('astro:before-preparation', () => resolve(true), { once: true })
    })
  })
  await page.click('nav a[href="/experience"]')
  expect(await transitionStart).toBe(true)
})

test('hero-identity flies entre home y about [AC-11]', async ({ page }) => {
  await page.goto('http://localhost:9970/')
  const beforeBox = await page.locator('[transition\\:name="hero-identity"]').boundingBox()
  await page.click('nav a[href="/about"]')
  await page.waitForLoadState('networkidle')
  const afterBox = await page.locator('[transition\\:name="hero-identity"]').boundingBox()
  expect(beforeBox).not.toEqual(afterBox)  // El elemento se movio (morph)
})

test('prefers-reduced-motion disables view transitions [AC-11]', async ({ browser }) => {
  const ctx = await browser.newContext({ reducedMotion: 'reduce' })
  const page = await ctx.newPage()
  await page.goto('http://localhost:9970/')
  await page.click('nav a[href="/experience"]')
  // Esperar URL change inmediato (sin esperar animacion)
  await expect(page).toHaveURL(/\/experience/, { timeout: 100 })
})
```

### `tests/feature/specs/navbar.spec.ts` (NUEVO)

Bateria completa documentada en
[11-navbar-dropdown-fix.md](11-navbar-dropdown-fix.md) (seccion "Tests E2E").
Cubre:

- Desktop: toggle, outside-click, Escape, cross-navigation stability [AC-12]
- Mobile: drawer + `<details>` colapsado por default, expand/collapse,
  reset al cerrar [AC-13]
- Breakpoint resize 1280→375 [AC-14]

Las 6 apps en bucle.

## 6.E. Coverage gates

```bash
# Frontend per-file >= 80%
pnpm exec vitest run --coverage --coverage.thresholds.perFile=80

# Lambda per-file >= 80%
python devtools/run.py serverless tests --type=coverage --lambda=tracking_pixel
python devtools/run.py serverless tests --type=coverage --shared
```

Archivos excluidos de coverage gates:
- Configs (`*.config.ts`, `astro.config.ts`)
- Migrations (`alembic/versions/*.py`)
- Fixtures (`tests/**/_helpers.py`, `_fixtures/`)
- Generated (`build/`, `.astro/`)

## 6.F. Mapeo AC → tests (trazabilidad)

| AC | Tests que lo cubren |
|----|---------------------|
| AC-1 | Pydantic required (3 unit), handler 400 (1 unit), build-payload required keys (1 unit) |
| AC-2 | service persists full row (1 unit), build-payload referrer (1 unit), feature tracking-pageview (6 E2E) |
| AC-3 | http_dispatch country lower/upper/fallback (3 unit), service uses meta.country (1 unit) |
| AC-4 | 6 unit (Chrome iOS, Android WebView, Firefox, Safari, Edge, Googlebot) + 3 shared replace tests |
| AC-5 | migration upgrade + downgrade tests (en `serverless/tests/integration/` o manual con neon branch) |
| AC-6 | build-payload viewport/devicePixelRatio (2 unit) + tracking-pageview E2E |
| AC-7 | tracking-pageview con 1 + 2 navs (count = 3 requests, 1 hard-load + 2 SPA) |
| AC-8 | provisioner unit tests + verificacion manual `aws apigateway get-domain-name` |
| AC-9 | build-payload utm (1 unit) + tracking-pageview con/sin utm (E2E) |
| AC-10 | coverage gates en CI (per-file ≥80%) |
| AC-11 | view-transitions E2E (3 tests) + stagger unit (4 tests) |
| AC-12 | NicheDropdown unit (5 tests) + navbar.spec desktop (4 tests) |
| AC-13 | MobileNavDrawer unit (3 tests) + navbar.spec mobile (2 tests) |
| AC-14 | navbar.spec breakpoint transition (1 test) |

## 6.G. NO mockear

- Pydantic models propios
- Controllers/services del Lambda
- Utilities propias de `packages/ui/src/lib/`
- DB Neon en tests integration (usar branch real)

## 6.H. SI mockear

- `db_session` + `insert_tracking` en tests unit del Lambda (ya hay
  fixture `mock_neon_writes` en `conftest.py`)
- `boto3` clients (DynamoDB, SSM, KMS) en tests unit
- `fetch`/`sendBeacon` en tests Vitest del frontend
- `IntersectionObserver` en tests de stagger (`vi.stubGlobal('IntersectionObserver', ...)`)
- View transitions API en tests Vitest (no esta en happy-dom; mock via `vi.spyOn(document, 'startViewTransition')`)

---

Siguiente: [04. Archivos afectados →](04-archivos-afectados.md)
