# 08 — Fase 2C: MCP Server Card

> **Anterior**: [07-fase-2b-mcp-tools.md](07-fase-2b-mcp-tools.md) · **Siguiente**: [09-fase-3-validar-skills.md](09-fase-3-validar-skills.md)
>
> **Cubre**: AC-11
>
> **Objetivo**: publicar `/.well-known/mcp/server-card.json` en cada
> niche con la descripcion del MCP server + lista de tools, para que
> isitagentready y agentes lo descubran automaticamente.

## Estrategia

El server card es un JSON estatico generado por el prebuild (mismo
patron que `api-catalog.json` y `_headers`). Vive en
`packages/seo/src/lib/build-mcp-server-card.ts`.

Schema basado en la spec MCP de modelcontextprotocol.io (Nov 2025):

```json
{
  "name": "portfolio-mcp",
  "version": "0.1.0",
  "protocolVersion": "2025-11-25",
  "description": "Pablo Contreras' portfolio MCP server — CV exploration tools",
  "endpoint": "https://the-full-stack.com/mcp",
  "transport": "http",
  "capabilities": {
    "tools": { "listChanged": false }
  },
  "tools": [
    {
      "name": "get_cv_section",
      "description": "Returns a section of Pablo Contreras' CV in Markdown.",
      "inputSchema": { "...": "..." }
    },
    { "name": "list_projects", "...": "..." },
    { "name": "search_experience", "...": "..." }
  ]
}
```

## Tarea 2C.1 — Builder

`packages/seo/src/lib/build-mcp-server-card.ts`:

```ts
import { TOOLS, PROTOCOL_VERSION } from '@portfolio/mcp'

interface ServerCardParams {
  siteUrl: string  // ej. 'https://the-full-stack.com'
}

export function buildMcpServerCard(params: ServerCardParams): string {
  const card = {
    name: 'portfolio-mcp',
    version: '0.1.0',
    protocolVersion: PROTOCOL_VERSION,
    description: "Pablo Contreras' portfolio MCP server — CV exploration tools",
    endpoint: `${params.siteUrl}/mcp`,
    transport: 'http',
    capabilities: { tools: { listChanged: false } },
    tools: TOOLS.map((t) => t.definition),
  }
  return `${JSON.stringify(card, null, 2)}\n`
}
```

NOTA: requiere que `@portfolio/mcp` exponga `TOOLS` y `PROTOCOL_VERSION`
en `src/index.ts`:

```ts
// packages/mcp/src/index.ts
export { handleRequest } from './lib/handle-request'
export { TOOLS } from './lib/tools'
export { PROTOCOL_VERSION } from './lib/types'
export type { ToolDefinition, JsonRpcRequest, JsonRpcResponse } from './lib/types'
```

## Tarea 2C.2 — Export desde `packages/seo`

`packages/seo/src/index.ts`:

```ts
export { buildMcpServerCard } from './lib/build-mcp-server-card'
// ...resto
```

## Tarea 2C.3 — Tests

`packages/seo/tests/unit/build-mcp-server-card.test.ts`:

```ts
describe('buildMcpServerCard', () => {
  it('Given siteUrl When build Then returns JSON valido con endpoint absoluto', () => {
    const out = buildMcpServerCard({ siteUrl: 'https://the-full-stack.com' })
    const parsed = JSON.parse(out)
    expect(parsed.endpoint).toBe('https://the-full-stack.com/mcp')
    expect(parsed.name).toBe('portfolio-mcp')
    expect(parsed.transport).toBe('http')
    expect(parsed.protocolVersion).toBe('2025-11-25')
  })

  it('Given build When inspect Then includes the 3 MCP tools', () => {
    const out = buildMcpServerCard({ siteUrl: 'https://x.com' })
    const parsed = JSON.parse(out)
    expect(parsed.tools).toHaveLength(3)
    expect(parsed.tools.map((t: any) => t.name)).toEqual([
      'get_cv_section',
      'list_projects',
      'search_experience',
    ])
  })

  it('Given se invoca When inspecciono Then termina con newline', () => {
    const out = buildMcpServerCard({ siteUrl: 'https://x.com' })
    expect(out.endsWith('\n')).toBe(true)
  })
})
```

## Tarea 2C.4 — Generar en prebuild de cada app

Modificar `apps/*/scripts/build-public-assets.mjs` (6 archivos) para
agregar al final del prebuild:

```js
// 7. .well-known/mcp/server-card.json
await write(
  '.well-known/mcp/server-card.json',
  buildMcpServerCard({ siteUrl: SITE_URL }),
)
```

(Y agregar `buildMcpServerCard` a los imports.)

## Tarea 2C.5 — Header Link para el server card

Actualizar `packages/seo/src/lib/build-headers.ts` para agregar un
Link header que anuncia el server card (para descubrimiento automatico
por agentes que no scanean `.well-known/`):

```ts
'  Link: </.well-known/mcp/server-card.json>; rel="mcp-server-card"; type="application/json"',
```

Y bloque de Content-Type:

```ts
'/.well-known/mcp/server-card.json',
'  Content-Type: application/json; charset=UTF-8',
'',
```

## Tarea 2C.6 — Actualizar `_headers.test.ts`

```ts
it('Given build When inspect Then mcp server card has correct Content-Type', () => {
  const out = buildHeaders()
  expect(out).toContain('/.well-known/mcp/server-card.json')
  expect(out).toMatch(
    /\/\.well-known\/mcp\/server-card\.json\s+Content-Type: application\/json/,
  )
})

it('Given build When inspect Then Link header includes mcp-server-card', () => {
  const out = buildHeaders()
  expect(out).toContain(
    '</.well-known/mcp/server-card.json>; rel="mcp-server-card"',
  )
})
```

## Tarea 2C.7 — Actualizar `.gitignore`

```
# .well-known files generados por prebuild (api-catalog.json + mcp/)
apps/*/public/.well-known/
```

(Ya existe `apps/*/public/.well-known/` en gitignore segun el codigo
actual; verificar que cubre `mcp/`.)

## Verificacion incremental

```bash
# Tests del builder
pnpm --filter @portfolio/seo run test
pnpm --filter @portfolio/seo exec vitest run --coverage

# Build de las 6 apps + verificacion del archivo
pnpm run build
for app in architect fintech generic hub leader vibe; do
  test -f apps/$app/dist/.well-known/mcp/server-card.json || echo "FALTA en $app"
  cat apps/$app/dist/.well-known/mcp/server-card.json | jq -r .endpoint
done
# ESPERADO: 6 URLs (una por niche/apex), JSON parseable

# Post-deploy a dev: verificar el archivo se sirve correctamente
# (Despues de la Fase 1A, sabemos que .json sirve OK sin SPA fallback)
curl -s https://generic.portfolio.dev.the-full-stack.com/.well-known/mcp/server-card.json | jq .name
# ESPERADO: "portfolio-mcp"
```

## Archivos afectados

### Crear

- `packages/seo/src/lib/build-mcp-server-card.ts`
- `packages/seo/tests/unit/build-mcp-server-card.test.ts`

### Modificar

- `packages/seo/src/index.ts` — export del nuevo builder
- `packages/seo/package.json` — agregar dep workspace `@portfolio/mcp`
- `packages/seo/src/lib/build-headers.ts` — 2 bloques nuevos (Content-Type + Link)
- `packages/seo/tests/unit/build-headers.test.ts` — 2 tests nuevos
- `apps/architect/scripts/build-public-assets.mjs` — generar server card
- `apps/fintech/scripts/build-public-assets.mjs` — generar server card
- `apps/generic/scripts/build-public-assets.mjs` — generar server card
- `apps/hub/scripts/build-public-assets.mjs` — generar server card
- `apps/leader/scripts/build-public-assets.mjs` — generar server card
- `apps/vibe/scripts/build-public-assets.mjs` — generar server card
- `packages/mcp/src/index.ts` — re-exports de `TOOLS` y `PROTOCOL_VERSION`

## Done

- [ ] Builder + tests verdes (coverage >= 80%)
- [ ] 6 server cards generados en `apps/*/dist/.well-known/mcp/server-card.json`
- [ ] Header `Link: ` actualizado con `mcp-server-card`
- [ ] Lint + typecheck verde
- [ ] Commit `feat(seo,mcp): publica /.well-known/mcp/server-card.json + Link header`
