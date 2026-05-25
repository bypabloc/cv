# Fase 4 — WebMCP runtime (navigator.modelContext)

> Objetivo: la homepage de cada app registra las tools del MCP Server
> Card en `navigator.modelContext.provideContext({tools: [...]})` para
> que un browser AI-aware (Chrome canary, ChatGPT Atlas) las descubra
> en runtime sin necesidad de fetch a `.well-known`. Cubre AC-11, AC-12.

## 1. Que es WebMCP — contexto rapido

WebMCP es una propuesta W3C en estado **Working Draft** del WebML CG
(`webmachinelearning.github.io/webmcp/`). Expone:

```ts
navigator.modelContext.provideContext({
  tools: [
    {
      name: 'cv.get_experiences',
      description: '...',
      inputSchema: { /* JSON Schema */ },
      execute: async (input) => { /* llama al API */ },
    },
  ],
})
```

Cuando un browser que la soporta (Chrome con flag, Atlas) carga la
pagina, la API queda registrada. Un agente que opera el browser puede
listar y ejecutar tools sin parsear DOM.

El scan de isitagentready.com verifica esto cargando la pagina con
Playwright y haciendo `await window.navigator.modelContext.listTools()`.

## 2. Componente compartido

Vive en `packages/app-shared/src/components/WebMCPRegistration.astro`.

### `packages/app-shared/src/components/WebMCPRegistration.astro`

```astro
---
/**
 * @component WebMCPRegistration
 * @description Registra las tools del portfolio en navigator.modelContext
 * cuando el browser soporta WebMCP. Feature-detected para no romper
 * navegadores sin soporte.
 *
 * @props {string} apiBase - URL del backend (ej. https://api.portfolio.the-full-stack.com)
 * @props {string} niche - generic | hub | fintech | architect | leader | vibe
 */
interface Props {
  apiBase: string
  niche: string
}
const { apiBase, niche } = Astro.props
const dataPayload = JSON.stringify({ apiBase, niche })
---

<script is:inline define:vars={{ dataPayload }}>
  (function () {
    'use strict'
    // Feature detect: WebMCP es API navigator.modelContext (W3C draft 2026).
    // Firefox/Safari no la soportan; Chrome stable solo con flag.
    if (
      typeof navigator === 'undefined' ||
      typeof navigator.modelContext === 'undefined' ||
      typeof navigator.modelContext.provideContext !== 'function'
    ) {
      return
    }

    const { apiBase, niche } = JSON.parse(dataPayload)

    function buildExecute(method, path) {
      return async function execute(input) {
        const url = new URL(path, apiBase)
        if (method === 'GET' && input) {
          for (const [k, v] of Object.entries(input)) {
            if (v != null) url.searchParams.set(k, String(v))
          }
        }
        const init = {
          method,
          headers: { Accept: 'application/json' },
        }
        if (method === 'POST') {
          init.headers['Content-Type'] = 'application/json'
          init.body = JSON.stringify(input ?? {})
        }
        const response = await fetch(url.toString(), init)
        if (!response.ok) {
          throw new Error(`${method} ${url}: HTTP ${response.status}`)
        }
        return response.json()
      }
    }

    navigator.modelContext.provideContext({
      tools: [
        {
          name: 'cv.get_experiences',
          description: `List work experiences from the CV (niche: ${niche})`,
          inputSchema: {
            type: 'object',
            properties: {
              niche: {
                type: 'string',
                enum: ['fintech', 'architect', 'leader', 'vibe', 'generic'],
              },
            },
          },
          execute: buildExecute('GET', '/cv?operation=cv&action=experiences'),
        },
        {
          name: 'cv.get_projects',
          description: 'List completed projects from the CV',
          inputSchema: {
            type: 'object',
            properties: { niche: { type: 'string' } },
          },
          execute: buildExecute('GET', '/cv?operation=cv&action=projects'),
        },
        {
          name: 'cv.get_skills',
          description: 'List technical and soft skills',
          inputSchema: { type: 'object', properties: {} },
          execute: buildExecute('GET', '/cv?operation=cv&action=skills'),
        },
        {
          name: 'nlweb.ask',
          description: 'Natural-language query over the CV (schema.org response)',
          inputSchema: {
            type: 'object',
            properties: {
              query: { type: 'string' },
              niche: { type: 'string' },
            },
            required: ['query'],
          },
          execute: buildExecute('POST', '/nlweb/ask'),
        },
      ],
    })
  })()
</script>
```

### Por que `is:inline` + `define:vars`

- `is:inline`: el script se renderiza tal cual, sin pasar por el bundler
  Astro. Importante: el script corre temprano en el lifecycle del
  documento sin esperar a hydration ni a un chunk JS aparte.
- `define:vars`: inyecta `apiBase` y `niche` de forma segura (Astro
  escapa el JSON). NO usar template strings con `${}` que se expanden
  en build-time porque rompe el sandbox.

### Por que `JSON.parse` en lugar de pasar las vars directas

Astro `define:vars` inyecta el JSON serializado como `var dataPayload = "..."` (string). Para evitar problemas de quoting, se parsea explicitamente.

## 3. Wire-up: usar el componente en el layout base de cada app

### `apps/<app>/src/layouts/BaseLayout.astro` (modificar)

```astro
---
import { WebMCPRegistration } from '@portfolio/app-shared'
import { resolveApiBase } from '@portfolio/seo'

const apiBase = resolveApiBase(new URL(Astro.url))
const niche = '<APP>'  // generic | hub | fintech | architect | leader | vibe
// ... rest of frontmatter
---
<html>
  <head>
    <!-- ... otros heads ... -->
    <WebMCPRegistration apiBase={apiBase} niche={niche} />
  </head>
  <body>
    <slot />
  </body>
</html>
```

> El componente registra las tools en el `<head>` para que esten
> disponibles ANTES de que la pagina termine de renderizar. Si un
> agente carga la pagina y pregunta inmediatamente, las tools ya
> estan.

## 4. Exportar desde `@portfolio/app-shared`

### `packages/app-shared/src/index.ts`

```ts
export { default as WebMCPRegistration } from './components/WebMCPRegistration.astro'
```

## 5. Tests (Vitest happy-dom para feature-detect, Playwright para WebMCP real)

### Unit (`packages/app-shared/tests/unit/components/web-mcp-registration.test.ts`)

happy-dom NO implementa `navigator.modelContext`. El test verifica que:

1. El componente compila a un `<script>` con el codigo esperado
2. Ejecutado en un entorno sin `navigator.modelContext`, no lanza

```ts
import { describe, expect, it } from 'vitest'
import { experimental_AstroContainer as AstroContainer } from 'astro/container'
import WebMCPRegistration from '../../../src/components/WebMCPRegistration.astro'

describe('WebMCPRegistration', () => {
  it('Given props apiBase y niche When render Then incluye script inline [AC-11]', async () => {
    const container = await AstroContainer.create()
    const html = await container.renderToString(WebMCPRegistration, {
      props: { apiBase: 'https://api.example.com', niche: 'fintech' },
    })
    expect(html).toContain('<script')
    expect(html).toContain('navigator.modelContext')
    expect(html).toContain('cv.get_experiences')
    expect(html).toContain('nlweb.ask')
  })

  it('Given env sin navigator.modelContext When script corre Then no lanza [AC-12]', async () => {
    const container = await AstroContainer.create()
    const html = await container.renderToString(WebMCPRegistration, {
      props: { apiBase: 'https://api.example.com', niche: 'generic' },
    })
    // Extraer el script y ejecutarlo en un sandbox simulado
    const scriptMatch = html.match(/<script[^>]*>([\s\S]*?)<\/script>/)
    const scriptBody = scriptMatch![1]
    // Globals minimos: solo navigator vacio
    const fakeNavigator = {}  // no .modelContext
    const fn = new Function('navigator', scriptBody)
    expect(() => fn(fakeNavigator)).not.toThrow()
  })
})
```

### E2E con Playwright + browser flag (`tests/feature/specs/ai-readiness/webmcp.spec.ts`)

```ts
import { expect, test } from '@playwright/test'

/**
 * NOTE: WebMCP no esta soportado en Chromium stable (mayo 2026).
 * Test corre con flag --enable-features=WebMCP. Si la flag no esta,
 * el test se skipea (no rompe la suite).
 */
test.describe('WebMCP runtime', () => {
  test.use({
    launchOptions: {
      args: ['--enable-features=WebMCP'],
    },
  })

  test('homepage registers WebMCP tools [AC-11]', async ({ page }) => {
    await page.goto('http://localhost:9970/')
    const tools = await page.evaluate(async () => {
      // @ts-expect-error WebMCP draft
      const ctx = navigator.modelContext
      if (!ctx || !ctx.listTools) return null
      return ctx.listTools()
    })
    test.skip(tools === null, 'WebMCP no soportado en este browser')
    expect(tools.length).toBeGreaterThanOrEqual(3)
    const names = tools.map((t: { name: string }) => t.name)
    expect(names).toContain('cv.get_experiences')
    expect(names).toContain('nlweb.ask')
  })

  test('page works without WebMCP support [AC-12]', async ({ page }) => {
    // Browser default (sin flag) — el feature-detect NO debe romper
    await page.goto('http://localhost:9970/')
    const errors: string[] = []
    page.on('pageerror', (e) => errors.push(e.message))
    await page.waitForLoadState('networkidle')
    expect(errors).toEqual([])
  })
})
```

## 6. Verificacion incremental

```bash
# Tests unit
python devtools/run.py test_runner --module=pkg-app-shared --type=unit

# Build de las 6 apps — el componente debe compilar sin errores
for app in generic hub fintech architect leader vibe; do
  pnpm --filter @portfolio/$app run build
done

# E2E (con stack levantado)
python devtools/run.py docker up --env=local
python devtools/run.py test_runner --module=feature --type=feature --env=local

# Manual: abrir Chrome con la flag y verificar
google-chrome --enable-features=WebMCP http://localhost:9970/
# En devtools console:
#   await navigator.modelContext.listTools()
```

## 7. Riesgos / mitigaciones

| Riesgo | Mitigacion |
|--------|-----------|
| `navigator.modelContext` API muta antes de GA | Tomar el snapshot del scan del 22-May-2026 como contrato (`provideContext({tools})`). Si cambia, refactor en una rule update |
| Script inline rompe CSP del portfolio | El portfolio tiene CSP con `script-src 'self' 'unsafe-inline'` (verificar en headers). Si no, agregar hash del script inline |
| El bundle Astro mueve el script a un chunk JS | `is:inline` lo previene. Verificar con `pnpm run build && grep -r 'navigator.modelContext' dist/` |
| Browsers sin la API muestran warning en console | El feature-detect retorna silenciosamente. Verificable con AC-12 |
| Las URLs del API embebidas pueden quedar desactualizadas si cambian | Vienen de `resolveApiBase(siteUrl)` ya tipado. Si cambia el dominio, el cambio es 1 linea en `packages/seo/src/data/api-base.ts` |

## 8. Notas

- Las tools que registra el WebMCP **son las mismas** del MCP Server
  Card (fase 1). Coordinacion via la constante `MCP_TOOLS` de
  `packages/seo/src/data/mcp-tools.ts`. **TODO**: refactorizar este
  componente para leer de ahi en lugar de duplicar la lista.

  Anti-patron: tener 2 listas (una en TS, otra en el script inline). El
  refactor consiste en que el componente Astro lea `MCP_TOOLS` en su
  frontmatter, lo serialice a JSON y lo inyecte:

  ```astro
  ---
  import { MCP_TOOLS } from '@portfolio/seo'
  const toolsPayload = JSON.stringify(MCP_TOOLS)
  ---
  <script is:inline define:vars={{ apiBase, niche, toolsPayload }}>
    // ... parse toolsPayload, construir execute per-tool
  </script>
  ```

  Se prefiere esta variante DEFINITIVA — la version "hardcoded" arriba
  es solo ilustrativa. La implementacion real lee de `MCP_TOOLS`.

- WebMCP esta detras de un flag en Chrome canary; ChatGPT Atlas lo
  soporta sin flag. La cuota de usuarios reales que activa la API es
  baja en 2026 pero el scan lo verifica — necesario para subir el
  score.
