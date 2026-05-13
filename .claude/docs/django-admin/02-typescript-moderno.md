[Anterior: 01-dynamic-admin](01-dynamic-admin.md) | [Siguiente: 03-custom-views-templates](03-custom-views-templates.md)

# 02. TypeScript Moderno en Django Admin

> TypeScript strict, esbuild, HTMX, Alpine.js, ES modules, Fetch API tipado, y patrones para interactividad en el admin de Django 6. NUNCA depender de jQuery. Typing obligatorio en todas las funciones.

## Build pipeline: esbuild + tsc

esbuild transpila TypeScript a JavaScript. `tsc --noEmit` verifica tipos sin emitir. Ambos corren por separado.

### Estructura de directorios

```
server/apps/<app>/
├── static-src/<app>/           # Source TypeScript
│   ├── package.json
│   ├── tsconfig.json
│   ├── build.ts
│   └── src/
│       ├── types/
│       │   ├── django-admin.d.ts   # Tipos Django admin DOM
│       │   ├── htmx.d.ts           # Declaraciones HTMX
│       │   └── globals.d.ts        # Window extensions (Alpine, etc.)
│       ├── utils/
│       │   ├── dom.ts              # Helpers DOM tipados
│       │   └── api.ts              # Fetch wrapper tipado
│       ├── schedule_toggle.ts
│       └── chart-dashboard.ts
└── static/<app>/
    ├── js/
    │   └── schedule_toggle.js      # Output IIFE (para Media.js)
    └── admin/
        └── chart-dashboard.mjs     # Output ESM (para script type=module)
```

### tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "noEmit": true,
    "isolatedModules": true,
    "baseUrl": ".",
    "paths": {
      "@utils/*": ["src/utils/*"],
      "@types/*": ["src/types/*"]
    }
  },
  "include": ["src/**/*.ts"],
  "exclude": ["node_modules"]
}
```

Notas:
- `noEmit: true` — esbuild emite, `tsc` solo verifica tipos
- `isolatedModules: true` — compatible con esbuild (transpila archivos aislados)
- `moduleResolution: "bundler"` — recomendado para proyectos con bundler (2025+)
- `noUncheckedIndexedAccess: true` — agrega `| undefined` a accesos de array

### package.json

```json
{
  "scripts": {
    "build": "node build.js",
    "watch": "node build.js --watch",
    "typecheck": "tsc --noEmit"
  },
  "devDependencies": {
    "esbuild": "^0.25.0",
    "typescript": "^5.8.0"
  }
}
```

### build.js (esbuild config)

```javascript
const esbuild = require('esbuild')
const isWatch = process.argv.includes('--watch')

const iifeConfig = {
  entryPoints: ['src/schedule_toggle.ts', 'src/image_selector.ts'],
  outdir: '../static/<app>/js',
  bundle: false,
  platform: 'browser',
  target: 'es2022',
  format: 'iife',
  minify: !isWatch,
  sourcemap: isWatch ? 'inline' : false,
}

const esmConfig = {
  entryPoints: ['src/chart-dashboard.ts'],
  outdir: '../static/<app>/admin',
  bundle: true,
  platform: 'browser',
  target: 'es2022',
  format: 'esm',
  outExtension: { '.js': '.mjs' },
  minify: !isWatch,
}

if (isWatch) {
  Promise.all([
    esbuild.context(iifeConfig).then(ctx => ctx.watch()),
    esbuild.context(esmConfig).then(ctx => ctx.watch()),
  ])
} else {
  Promise.all([
    esbuild.build(iifeConfig),
    esbuild.build(esmConfig),
  ])
}
```

## Como cargar JS compilado en el admin

### Via `Media` class (recomendado)

```python
@admin.register(ScheduledApiCall)
class ScheduledApiCallAdmin(admin.ModelAdmin):
    class Media:
        js = ('scheduler/js/schedule_toggle.js',)  # Output de esbuild
        css = {
            'all': ('scheduler/css/admin_custom.css',),
        }
```

Ubicacion del output: `server/apps/<app>/static/<app>/js/<filename>.js`

### Via widget `Media`

```python
class ImageCheckboxSelect(forms.CheckboxSelectMultiple):
    class Media:
        js = ('publications/js/image_selector.js',)
```

### Via template override (para ES modules)

```html
<!-- server/templates/admin/base_site.html -->
{% extends "admin/base_site.html" %}
{% load static %}

{% block extrahead %}
{{ block.super }}
<script type="module" src="{% static 'myapp/admin/chart-dashboard.mjs' %}"></script>
{% endblock %}
```

## Helpers DOM tipados

Helpers reutilizables para evitar repetir `instanceof` checks en cada archivo:

```typescript
// utils/dom.ts

export function getInput(id: string): HTMLInputElement | null {
  const el = document.getElementById(id)
  return el instanceof HTMLInputElement ? el : null
}

export function getSelect(id: string): HTMLSelectElement | null {
  const el = document.getElementById(id)
  return el instanceof HTMLSelectElement ? el : null
}

export function getTextarea(id: string): HTMLTextAreaElement | null {
  const el = document.getElementById(id)
  return el instanceof HTMLTextAreaElement ? el : null
}

export function queryDiv(
  selector: string,
  parent: ParentNode = document,
): HTMLDivElement | null {
  return parent.querySelector<HTMLDivElement>(selector)
}

export function getTypedElement<T extends HTMLElement>(
  id: string,
  ctor: abstract new (...args: never[]) => T,
): T | null {
  const el = document.getElementById(id)
  return el instanceof ctor ? el : null
}
```

### Tabla de tipos por selector Django admin

| Selector | Tipo TypeScript |
|----------|----------------|
| `#id_<campo>` texto/numero | `HTMLInputElement` |
| `#id_<campo>` select/choice | `HTMLSelectElement` |
| `#id_<campo>` textarea | `HTMLTextAreaElement` |
| `.form-row.field-<nombre>` | `HTMLDivElement` |
| `#<model>_form` | `HTMLFormElement` |
| `input[name="csrfmiddlewaretoken"]` | `HTMLInputElement` |
| `fieldset.module h2` | `HTMLHeadingElement` |
| `.inline-group` | `HTMLDivElement` |
| `.add-row a` | `HTMLAnchorElement` |
| `.submit-row` | `HTMLDivElement` |

## Patron IIFE tipado

Patron obligatorio del proyecto para scripts cargados via `Media.js`:

```typescript
;(function (): void {
  'use strict'

  function init(): void {
    const element = document.getElementById('id_some_field')
    if (!element) return  // Guard: salir si no estamos en la pagina correcta
    // ...
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init)
  } else {
    init()
  }
})()
```

Nota: `;` inicial previene bugs de ASI al concatenar archivos.

## Toggle de campos condicional

Patron con tipos estrictos:

```typescript
;(function (): void {
  'use strict'

  function setRowVisibility(fieldNames: readonly string[], visible: boolean): void {
    for (const name of fieldNames) {
      const row = document.querySelector<HTMLDivElement>(`.form-row.field-${name}`)
      if (row) row.style.display = visible ? '' : 'none'
    }
  }

  function toggleScheduleFields(): void {
    const scheduleType = document.getElementById('id_schedule_type')
    if (!(scheduleType instanceof HTMLSelectElement)) return

    const INTERVAL_FIELDS = ['interval_every', 'interval_period'] as const
    const CRONTAB_FIELDS = [
      'cron_minute', 'cron_hour', 'cron_day_of_month',
      'cron_month_of_year', 'cron_day_of_week', 'cron_timezone',
    ] as const

    function update(): void {
      const val: string = scheduleType.value
      setRowVisibility(INTERVAL_FIELDS, val === 'interval')
      setRowVisibility(CRONTAB_FIELDS, val === 'crontab')
    }

    scheduleType.addEventListener('change', update)
    update()
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', toggleScheduleFields)
  } else {
    toggleScheduleFields()
  }
})()
```

Selectores clave del DOM admin de Django:

| Selector | Que selecciona |
|----------|---------------|
| `#id_<fieldname>` | Input/select de un campo |
| `.form-row.field-<fieldname>` | Row completa (label + input + help text) |
| `fieldset.module h2` | Header de un fieldset |
| `.inline-group` | Container de un inline |
| `.add-row a` | Link "Add another" en inlines |
| `#<model>_form` | El form principal |
| `.submit-row` | Barra de botones submit |

## Inyectar botones en fieldset headers

```typescript
function injectButton(headerText: string, buttonText: string, handler: () => void): void {
  const headers = document.querySelectorAll<HTMLHeadingElement>('fieldset.module h2')

  for (const h2 of headers) {
    if (!h2.textContent?.includes(headerText)) continue

    const btn = document.createElement('button')
    btn.type = 'button'
    btn.textContent = buttonText
    btn.style.cssText = [
      'margin-left:12px',
      'cursor:pointer',
      'font-size:.8rem',
      'padding:2px 10px',
      'border:1px solid rgba(255,255,255,0.4)',
      'border-radius:4px',
      'background:rgba(255,255,255,0.15)',
      'color:inherit',
    ].join(';')
    btn.addEventListener('click', handler)
    h2.appendChild(btn)
    break
  }
}
```

## Event delegation para contenido dinamico

```typescript
// MAL: event listeners directos (no funciona con inlines dinamicos)
document.querySelectorAll<HTMLInputElement>('.inline-row input').forEach((input) => {
  input.addEventListener('change', handler)  // Se pierde al agregar rows
})

// BIEN: event delegation en el container
const container = document.getElementById('id_selected_images')
if (container) {
  container.addEventListener('change', (e: Event) => {
    const target = e.target
    if (target instanceof HTMLInputElement && target.type === 'checkbox') {
      enforceLimit()
    }
  })
}
```

## Fetch API tipado

### Wrapper con discriminated union

```typescript
// utils/api.ts

type ApiSuccess<T> = { ok: true; data: T }
type ApiError = { ok: false; status: number; message: string }
type ApiResult<T> = ApiSuccess<T> | ApiError

function getCsrfToken(): string {
  const input = document.querySelector<HTMLInputElement>(
    'input[name="csrfmiddlewaretoken"]',
  )
  if (input?.value) return input.value

  const match = document.cookie.match(/csrftoken=([^;]+)/)
  return match?.[1] ?? ''
}

async function adminFetch<T>(
  url: string,
  options: RequestInit = {},
): Promise<ApiResult<T>> {
  try {
    const response = await fetch(url, {
      ...options,
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(),
        ...options.headers,
      },
    })

    if (!response.ok) {
      return { ok: false, status: response.status, message: response.statusText }
    }

    const data = (await response.json()) as T
    return { ok: true, data }
  } catch (error) {
    return { ok: false, status: 0, message: String(error) }
  }
}

export { adminFetch, getCsrfToken }
export type { ApiResult }
```

### Uso con tipos inferidos

```typescript
interface JobStatusResponse {
  jobs: Record<string, 'pending' | 'running' | 'done' | 'failed'>
  all_done: boolean
}

const result = await adminFetch<JobStatusResponse>(
  `/admin/scheduler/job-status/?ids=${ids}`,
)

if (!result.ok) {
  console.error(`HTTP ${result.status}: ${result.message}`)
  return
}

// result.data tipado como JobStatusResponse sin cast
updateUI(result.data.jobs)
```

## Polling de status tipado

```typescript
interface PollConfig<T> {
  url: string
  interval: number
  onData: (data: T) => boolean  // Retorna true para continuar polling
  onError?: (status: number) => void
  maxRetries?: number
}

async function pollStatus<T>(config: PollConfig<T>): Promise<void> {
  const { url, interval, onData, onError, maxRetries = 10 } = config
  let retries = 0

  async function poll(): Promise<void> {
    const result = await adminFetch<T>(url)

    if (!result.ok) {
      retries++
      onError?.(result.status)
      if (retries < maxRetries) {
        setTimeout(poll, interval * 2)  // Backoff on error
      }
      return
    }

    retries = 0
    const shouldContinue = onData(result.data)
    if (shouldContinue) {
      setTimeout(poll, interval)
    }
  }

  await poll()
}

// Uso
pollStatus<JobStatusResponse>({
  url: `/admin/products/product/job-status/?job_ids=${jobIds.join(',')}`,
  interval: 2000,
  onData: (data) => {
    updateProgressUI(data.jobs)
    return !data.all_done
  },
})
```

## `json_script` template tag para pasar datos tipados

En el template:

```html
{{ timing_stats_json|json_script:"timing-stats-data" }}
{{ product_list|json_script:"product-data" }}
```

En TypeScript:

```typescript
function getJsonData<T>(elementId: string): T | null {
  const el = document.getElementById(elementId)
  if (!el?.textContent) return null

  try {
    return JSON.parse(el.textContent) as T
  } catch {
    return null
  }
}

interface TimingStats {
  avg_ms: number
  p99_ms: number
  total_calls: number
}

const timingStats = getJsonData<TimingStats>('timing-stats-data')
if (timingStats) {
  console.log(`Avg: ${timingStats.avg_ms}ms`)  // Tipado
}
```

## `data-` attributes para datos simples

```python
# En el widget
def build_attrs(self, base_attrs, extra_attrs=None):
    attrs = super().build_attrs(base_attrs, extra_attrs)
    attrs['data-max-images'] = str(self._max_images)
    attrs['data-category-id'] = str(self._category_id)
    return attrs
```

```typescript
function getDataAttr(el: HTMLElement, name: string, fallback: number): number {
  const raw = el.dataset[name]
  if (raw === undefined) return fallback
  const parsed = Number.parseInt(raw, 10)
  return Number.isNaN(parsed) ? fallback : parsed
}

const maxImages = getDataAttr(container, 'maxImages', 2)
const categoryId = container.dataset.categoryId ?? ''
```

## Event typing — Django admin events

### Declaraciones de tipos

```typescript
// types/django-admin.d.ts

interface FormsetEventDetail {
  formsetName: string
}

declare global {
  interface DocumentEventMap {
    'formset:added': CustomEvent<FormsetEventDetail>
    'formset:removed': CustomEvent<FormsetEventDetail>
  }
}

export {}
```

### Uso con tipos inferidos

```typescript
document.addEventListener('formset:added', (event) => {
  // TypeScript infiere: event es CustomEvent<FormsetEventDetail>
  const newRow = event.target
  const formsetName: string = event.detail.formsetName

  if (!(newRow instanceof HTMLElement)) return
  if (formsetName !== 'author_set') return
  initializeRow(newRow)
})

document.addEventListener('formset:removed', (_event) => {
  // Cleanup si es necesario
})
```

### Custom events propios

```typescript
interface StatusChangedDetail {
  objectId: string
  newStatus: 'pending' | 'running' | 'done' | 'failed'
}

declare global {
  interface DocumentEventMap {
    'admin:status-changed': CustomEvent<StatusChangedDetail>
  }
}

function dispatchStatusChanged(detail: StatusChangedDetail): void {
  document.dispatchEvent(
    new CustomEvent<StatusChangedDetail>('admin:status-changed', {
      bubbles: true,
      detail,
    }),
  )
}
```

## HTMX en Django Admin

### Declaraciones de tipos

```typescript
// types/htmx.d.ts

declare namespace Htmx {
  function process(element: Element): void
  function trigger(element: Element | string, event: string, detail?: unknown): void
  function ajax(
    verb: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE',
    path: string,
    context: Element | string | {
      target?: Element | string
      swap?: string
      values?: Record<string, string>
    },
  ): Promise<void>
  const config: {
    defaultSwapStyle: string
    defaultSettleDelay: number
    historyCacheSize: number
    [key: string]: unknown
  }
}

declare const htmx: typeof Htmx
```

### Setup

```python
class Media:
    js = ('admin/js/vendor/htmx.min.js',)
```

### Procesar nuevos elementos HTMX

```typescript
document.addEventListener('formset:added', (event) => {
  const target = event.target
  if (target instanceof Element) {
    htmx.process(target)  // Tipado correctamente
  }
})
```

### Templates HTMX (sin cambios — HTML puro)

```html
<!-- Inline partial updates -->
<div id="status-panel"
     hx-get="{% url 'admin:myapp_model_status' object.pk %}"
     hx-trigger="every 5s"
     hx-swap="innerHTML">
  {% include "admin/myapp/model/_status_partial.html" %}
</div>

<!-- Form submission parcial -->
<button type="button"
        hx-post="{% url 'admin:products_product_process_enqueue' %}?ids={{ object.pk }}"
        hx-target="#process-result"
        hx-swap="innerHTML"
        hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>
  Process Now
</button>
<div id="process-result"></div>
```

### View para HTMX partial (Python — sin cambios)

```python
def get_urls(self):
    custom = [
        path(
            '<uuid:pk>/status/',
            self.admin_site.admin_view(self.status_partial_view),
            name='myapp_model_status',
        ),
    ]
    return custom + super().get_urls()

def status_partial_view(self, request, pk):
    obj = self.get_object(request, pk)
    return TemplateResponse(
        request,
        'admin/myapp/model/_status_partial.html',
        {'object': obj},
    )
```

## Alpine.js para reactividad ligera

### Declaraciones de tipos

```typescript
// types/globals.d.ts

interface Window {
  Alpine: {
    data(name: string, component: (...args: unknown[]) => object): void
    store(name: string, data: object): void
    start(): void
  }
}
```

### Componente Alpine tipado

```typescript
interface ScheduleTypeData {
  scheduleType: string
  isInterval(): boolean
  isCrontab(): boolean
}

function scheduleTypeComponent(initialValue: string): ScheduleTypeData {
  return {
    scheduleType: initialValue,
    isInterval(): boolean {
      return this.scheduleType === 'interval'
    },
    isCrontab(): boolean {
      return this.scheduleType === 'crontab'
    },
  }
}

document.addEventListener('alpine:init', () => {
  window.Alpine.data('scheduleType', (initial: unknown) =>
    scheduleTypeComponent(String(initial ?? 'interval')),
  )
})
```

### Templates Alpine (HTML puro — sin cambios)

```html
<div x-data="{ tab: 'basic' }">
  <div style="display:flex;gap:8px;margin-bottom:16px">
    <button type="button" @click="tab = 'basic'"
            :style="tab === 'basic' ? 'font-weight:bold' : ''">
      Basic Info
    </button>
    <button type="button" @click="tab = 'advanced'"
            :style="tab === 'advanced' ? 'font-weight:bold' : ''">
      Advanced
    </button>
  </div>

  <div x-show="tab === 'basic'">{{ basic_fieldset }}</div>
  <div x-show="tab === 'advanced'">{{ advanced_fieldset }}</div>
</div>
```

## ES Modules con TypeScript

esbuild emite `.mjs` con `format: 'esm'`. Django los carga via `<script type="module">`:

```html
{% block extrahead %}
{{ block.super }}
<script type="module" src="{% static 'myapp/admin/chart-dashboard.mjs' %}"></script>
{% endblock %}
```

```typescript
// chart-dashboard.ts — esbuild emite chart-dashboard.mjs
import { Chart } from '/static/admin/js/vendor/chart.esm.js'

interface ChartData {
  labels: string[]
  datasets: Array<{
    label: string
    data: number[]
  }>
}

const ctx = document.getElementById('stats-chart')
if (ctx instanceof HTMLCanvasElement) {
  const data = getJsonData<ChartData>('chart-data')
  if (data) {
    new Chart(ctx, { type: 'line', data })
  }
}
```

Nota: archivos `.js` cargados via `Media.js` usan `<script>` normal (IIFE). Para ES modules, usar template override con `type="module"`.

## Inline formset tipado

```typescript
;(function (): void {
  'use strict'

  function initializeRow(row: HTMLElement): void {
    const selects = row.querySelectorAll<HTMLSelectElement>('select')
    for (const select of selects) {
      select.addEventListener('change', handleSelectChange)
    }
  }

  function handleSelectChange(e: Event): void {
    const target = e.target
    if (!(target instanceof HTMLSelectElement)) return
    // Logica del cambio
  }

  // Django admin dispara estos eventos al agregar/remover inline rows
  document.addEventListener('formset:added', (event) => {
    const newRow = event.target
    if (newRow instanceof HTMLElement) {
      initializeRow(newRow)
    }
  })

  document.addEventListener('formset:removed', (_event) => {
    // Cleanup si es necesario
  })
})()
```

## Mejores practicas TypeScript en admin

1. **Tipos explicitos en todas las funciones** — parametros y retorno, sin excepciones
2. **SIEMPRE IIFE** — nunca variables globales en scripts `Media.js`
3. **Guard clause con `instanceof`** — `if (!(el instanceof HTMLSelectElement)) return`
4. **`as const` en arrays constantes** — para inferir tipos literales
5. **`readonly` en parametros que no mutan** — `readonly string[]` en vez de `string[]`
6. **Discriminated unions para API responses** — `{ ok: true; data: T } | { ok: false; ... }`
7. **Helpers DOM tipados** — reutilizar `getInput()`, `getSelect()`, etc.
8. **Event delegation** sobre listeners directos para contenido dinamico
9. **`json_script` con generico** — `getJsonData<T>(id)` para datos del template
10. **Fetch API tipado** — nunca `XMLHttpRequest`, siempre `adminFetch<T>()`
11. **CSRF token** en cada POST (cookie `csrftoken` o input hidden)
12. **`defer`** o DOMContentLoaded — nunca scripts bloqueantes
13. **No jQuery** — vanilla TS es suficiente para todo lo que necesita admin
14. **Progressive enhancement** — el admin debe funcionar sin JS (JS mejora la UX)
15. **No `any`** — usar `unknown` + narrowing cuando el tipo no es conocido

## Cuando usar cada herramienta

| Necesidad | Herramienta | Razon |
|-----------|-------------|-------|
| Show/hide campos | Vanilla TS (IIFE) | Simple, sin dependencias, tipado |
| Form validation client-side | Vanilla TS | Complementa server-side validation |
| AJAX calls / polling | `adminFetch<T>()` | Tipado, discriminated union, CSRF |
| Partial page updates | HTMX + tipos `.d.ts` | Declarativo, sin TS custom |
| Estado reactivo en form | Alpine.js + tipos | Ligero (17KB), declarativo |
| Charts / visualizaciones | ES module + libreria | Chart.js, D3.js via `.mjs` |
| Inline row management | `formset:added` event | Django built-in, tipado via `DocumentEventMap` |
| Drag-and-drop sorting | Sortable.js + `@types` | Libreria especializada |

[Anterior: 01-dynamic-admin](01-dynamic-admin.md) | [Siguiente: 03-custom-views-templates](03-custom-views-templates.md)
