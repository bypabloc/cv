# Fase 2 — Markdown content negotiation + Link headers

> Objetivo: cuando un agente envia `Accept: text/markdown`, el sitio
> retorna markdown del HTML; y la homepage incluye headers `Link` con
> rels `api-catalog`, `mcp`, `service-doc`. Cubre AC-5, AC-6, AC-7.

## 1. Middleware Astro compartido

Vive en `packages/app-shared/src/middleware/ai-content.ts` y se importa
desde `apps/<app>/src/middleware.ts` (Astro requiere un middleware por
app pero puede re-exportar).

### `packages/app-shared/src/middleware/ai-content.ts`

```ts
import type { APIContext, MiddlewareNext } from 'astro'
import TurndownService from 'turndown'

const turndown = new TurndownService({
  headingStyle: 'atx',
  codeBlockStyle: 'fenced',
  bulletListMarker: '-',
})
turndown.remove(['script', 'style', 'noscript'])

const LINK_HEADER_VALUE = [
  '</.well-known/api-catalog>; rel="api-catalog"',
  '</.well-known/mcp/server-card.json>; rel="mcp"; type="application/json"',
  '</.well-known/agent-skills/index.json>; rel="agent-skills"; type="application/json"',
  '</llms.txt>; rel="service-doc"',
].join(', ')

export async function aiContentMiddleware(
  context: APIContext,
  next: MiddlewareNext,
): Promise<Response> {
  const accept = context.request.headers.get('accept') ?? ''
  const wantsMarkdown = /text\/markdown/i.test(accept)

  // Get downstream response (HTML)
  const response = await next()

  // Path 1: agente pide markdown
  if (wantsMarkdown && response.headers.get('content-type')?.includes('text/html')) {
    const html = await response.text()
    const markdown = htmlToMarkdown(html)
    return new Response(markdown, {
      status: response.status,
      headers: {
        'Content-Type': 'text/markdown; charset=utf-8',
        'Vary': 'Accept',
        'Cache-Control': 'public, max-age=3600',
        'Link': LINK_HEADER_VALUE,
        'X-Markdown-Tokens': String(markdown.split(/\s+/).length),
      },
    })
  }

  // Path 2: HTML normal — agregar Link header solo a la homepage
  const url = new URL(context.request.url)
  if (url.pathname === '/' || /^\/(en|es)\/?$/.test(url.pathname)) {
    response.headers.set('Link', LINK_HEADER_VALUE)
  }

  return response
}

function htmlToMarkdown(html: string): string {
  // Extraer solo el <main> si existe, sino body
  const mainMatch = html.match(/<main[^>]*>([\s\S]*?)<\/main>/i)
  const content = mainMatch ? mainMatch[1] : html
  return turndown.turndown(content)
}
```

### Tests unit

`packages/app-shared/tests/unit/middleware/ai-content.test.ts`:

```ts
import { describe, expect, it } from 'vitest'
import { aiContentMiddleware } from '../../../src/middleware/ai-content'

function makeContext(url: string, headers: Record<string, string>) {
  return {
    request: new Request(url, { headers }),
    url: new URL(url),
  } as unknown as Parameters<typeof aiContentMiddleware>[0]
}

describe('aiContentMiddleware', () => {
  it('Given Accept text/markdown When middleware Then returns markdown [AC-5]', async () => {
    const next = async () => new Response('<html><body><main><h1>Title</h1></main></body></html>', {
      headers: { 'content-type': 'text/html' },
    })
    const ctx = makeContext('https://the-full-stack.com/', { accept: 'text/markdown' })
    const result = await aiContentMiddleware(ctx, next)
    expect(result.headers.get('content-type')).toBe('text/markdown; charset=utf-8')
    expect(await result.text()).toBe('# Title')
  })

  it('Given Accept text/html When middleware Then returns HTML unchanged [AC-6]', async () => {
    const html = '<html><body>X</body></html>'
    const next = async () => new Response(html, { headers: { 'content-type': 'text/html' } })
    const ctx = makeContext('https://the-full-stack.com/', { accept: 'text/html' })
    const result = await aiContentMiddleware(ctx, next)
    expect(await result.text()).toBe(html)
  })

  it('Given path / When middleware Then sets Link header [AC-7]', async () => {
    const next = async () => new Response('<html>x</html>', { headers: { 'content-type': 'text/html' } })
    const ctx = makeContext('https://the-full-stack.com/', { accept: 'text/html' })
    const result = await aiContentMiddleware(ctx, next)
    expect(result.headers.get('Link')).toContain('rel="api-catalog"')
    expect(result.headers.get('Link')).toContain('rel="mcp"')
  })

  it('Given path /about When middleware Then NO Link header [AC-7]', async () => {
    const next = async () => new Response('<html>x</html>', { headers: { 'content-type': 'text/html' } })
    const ctx = makeContext('https://the-full-stack.com/about', { accept: 'text/html' })
    const result = await aiContentMiddleware(ctx, next)
    expect(result.headers.get('Link')).toBe(null)
  })
})
```

## 2. Wire-up en cada app

### `apps/<app>/src/middleware.ts`

```ts
import { aiContentMiddleware } from '@portfolio/app-shared'

export const onRequest = aiContentMiddleware
```

(Astro detecta `src/middleware.ts` automaticamente cuando
`output: 'static'` o hybrid).

### `apps/<app>/astro.config.ts` — agregar adapter si no lo tiene

El output del portfolio es `static`, pero el middleware corre **solo en
deploy** porque Astro static no soporta middleware en runtime. Para
Cloudflare Pages se necesita el adapter `@astrojs/cloudflare`:

```ts
import { defineConfig } from 'astro/config'
import cloudflare from '@astrojs/cloudflare'

export default defineConfig({
  output: 'static',
  adapter: cloudflare({
    mode: 'directory',  // genera functions/ dir con el middleware
    functionPerRoute: false,
  }),
  // ... resto de la config
})
```

> Si la app ya tiene `output: 'static'` puro sin adapter, agregar el
> adapter NO la convierte en SSR — solo permite el middleware como
> Cloudflare Worker. Las paginas siguen siendo static.
>
> **VERIFICACION CRITICA**: probar que `pnpm run build` sigue generando
> archivos `.html` estaticos en `dist/`, no en `functions/`. Si el
> build movio paginas a functions, el adapter esta mal configurado.

### Devdep nueva

```bash
pnpm --filter @portfolio/app-shared add -D turndown @types/turndown
pnpm --filter @portfolio/hub add -D @astrojs/cloudflare
pnpm --filter @portfolio/generic add -D @astrojs/cloudflare
# ... repetir para las 6 apps
```

## 3. Build asset ya existente: `cv.html`

El prebuild script de cada app ya genera `cv.html` (CV ATS-friendly).
NO se modifica. Es lo que linkea el agent-skills.

## 4. Tests E2E (Playwright)

`tests/feature/specs/ai-readiness/content-negotiation.spec.ts`:

```ts
import { expect, test } from '@playwright/test'

const APPS = [
  { url: 'http://localhost:9970', name: 'generic' },
  { url: 'http://hub.localhost:9970', name: 'hub' },
  { url: 'http://fintech.localhost:9970', name: 'fintech' },
  { url: 'http://architect.localhost:9970', name: 'architect' },
  { url: 'http://leader.localhost:9970', name: 'leader' },
  { url: 'http://vibe.localhost:9970', name: 'vibe' },
]

test.describe('AI content negotiation', () => {
  for (const app of APPS) {
    test(`${app.name}: Accept markdown returns markdown [AC-5]`, async ({ request }) => {
      const response = await request.get(app.url, {
        headers: { Accept: 'text/markdown' },
      })
      expect(response.status()).toBe(200)
      expect(response.headers()['content-type']).toContain('text/markdown')
    })

    test(`${app.name}: homepage has Link header [AC-7]`, async ({ request }) => {
      const response = await request.get(app.url)
      const link = response.headers().link ?? ''
      expect(link).toContain('rel="api-catalog"')
      expect(link).toContain('rel="mcp"')
    })

    test(`${app.name}: /about does NOT have Link header [AC-7]`, async ({ request }) => {
      const response = await request.get(`${app.url}/about`)
      const link = response.headers().link ?? ''
      expect(link).toBe('')
    })
  }
})
```

## 5. Verificacion incremental

```bash
# Tests unit del middleware
python devtools/run.py test_runner --module=pkg-app-shared --type=unit

# Build de una app — verificar que pnpm build sigue funcionando
pnpm --filter @portfolio/hub run build

# Local: levantar stack y probar markdown
python devtools/run.py docker up --env=local
curl -sI -H 'Accept: text/markdown' http://localhost:9970/ | head -5
curl -sI http://localhost:9970/ | grep -i '^link:'
```

## 6. Riesgos / mitigaciones

| Riesgo | Mitigacion |
|--------|-----------|
| `@astrojs/cloudflare` adapter convierte paginas estaticas a SSR | Verificar tras el primer build que `dist/index.html` existe. Si no, revisar config `mode: 'directory'` |
| `turndown` agrega ~50KB al bundle | Solo se carga server-side (Worker), NO al cliente. Verificar con `pnpm run build && ls -la dist/_astro/` |
| Markdown de un SPA-style page sin `<main>` queda vacio | Fallback a body completo, ya implementado |
| `Vary: Accept` header confunde a CDN cache | Cloudflare maneja correctamente Vary. Verificar con `curl -I` que se respetan ambos cache slots |

## 7. Notas

- Astro 6 soporta middleware **solo** con un adapter (cloudflare,
  node, vercel). El portfolio ya esta en Cloudflare Pages — la
  adopcion del adapter es un cambio menor.
- Si el adapter resulta invasivo, alternativa **Plan B**: implementar
  el markdown negotiation como Cloudflare Worker independiente
  configurado en el dashboard de Pages (no en el codigo). Cubre el AC
  pero queda fuera del repo.
