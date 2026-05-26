# 06 — Fase 2A: MCP Server endpoint (Cloudflare Pages Functions)

> **Anterior**: [05-fase-1c-cloudflare-transform-rule.md](05-fase-1c-cloudflare-transform-rule.md) · **Siguiente**: [07-fase-2b-mcp-tools.md](07-fase-2b-mcp-tools.md)
>
> **Cubre**: AC-7
>
> **Objetivo**: endpoint POST `/mcp` que implementa el protocolo MCP
> (JSON-RPC 2.0), corriendo en Cloudflare Pages Functions (Free tier,
> 100k req/dia).

## Estrategia

MCP usa JSON-RPC 2.0 sobre HTTP. El cliente (agente, ej. Claude) envia
requests con `method`:

- `initialize` — handshake, devuelve `capabilities` + `serverInfo`
- `tools/list` — lista los tools disponibles
- `tools/call` — ejecuta un tool con `arguments`
- `resources/list` (opcional) — lista resources
- `prompts/list` (opcional) — lista prompts

Para llegar a Level 3-4 de isitagentready solo necesitamos
`initialize` + `tools/list` + `tools/call`.

### Por que Cloudflare Pages Functions y NO Lambda AWS

| Aspecto | Pages Functions | Lambda AWS |
|---------|-----------------|------------|
| Free tier | 100k req/dia | 1M req/mes + 400k GB-sec |
| Latencia | <50ms (edge) | ~200ms cold start |
| Co-locacion | Mismo dominio que sitio | Subdominio separado (CORS) |
| Patron del proyecto | Encaja con `functions/` de Pages | Requiere extender `lambda-controller` |
| Deploy | Automatico con `wrangler pages deploy` | Devtools serverless provision |

**Decision**: Pages Functions. Codigo en TypeScript, runtime
Cloudflare Workers.

## Tarea 2A.1 — Crear paquete `@portfolio/mcp` (nuevo)

Codigo compartido entre las 6 apps. Cada `apps/*/functions/mcp.ts` es
un wrapper thin que importa del paquete.

```
packages/mcp/
├── package.json
├── tsconfig.json
├── vitest.config.ts
├── src/
│   ├── index.ts                    # re-exports
│   ├── lib/
│   │   ├── handle-request.ts       # router JSON-RPC principal
│   │   ├── handle-initialize.ts    # method=initialize
│   │   ├── handle-tools-list.ts    # method=tools/list
│   │   ├── handle-tools-call.ts    # method=tools/call (delega a tools/)
│   │   ├── jsonrpc.ts              # parsing/encoding JSON-RPC 2.0
│   │   ├── errors.ts               # tipos de error MCP
│   │   ├── tools/                  # (vacia en Fase 2A, llena en 2B)
│   │   └── types.ts                # tipos JSON-RPC + MCP
└── tests/unit/
    ├── handle-initialize.test.ts
    ├── handle-tools-list.test.ts
    ├── jsonrpc.test.ts
    └── errors.test.ts
```

### `package.json`

```json
{
  "name": "@portfolio/mcp",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "main": "./src/index.ts",
  "scripts": {
    "test": "vitest run",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "@portfolio/content": "workspace:*",
    "@portfolio/markdown-export": "workspace:*"
  }
}
```

NOTA: el SDK oficial `@modelcontextprotocol/sdk` esta diseñado para
Node.js con stdio transport. En Cloudflare Workers necesitamos
implementar el HTTP transport manualmente, asi que NO se usa el SDK.
El protocolo es simple JSON-RPC 2.0; la implementacion completa son
~200 lineas.

### `src/lib/types.ts`

```ts
export interface JsonRpcRequest {
  jsonrpc: '2.0'
  id: number | string | null
  method: string
  params?: unknown
}

export interface JsonRpcResponseSuccess {
  jsonrpc: '2.0'
  id: number | string | null
  result: unknown
}

export interface JsonRpcResponseError {
  jsonrpc: '2.0'
  id: number | string | null
  error: { code: number; message: string; data?: unknown }
}

export type JsonRpcResponse = JsonRpcResponseSuccess | JsonRpcResponseError

export const PROTOCOL_VERSION = '2025-11-25' as const

export interface ServerInfo {
  name: string
  version: string
}

export interface Capabilities {
  tools?: { listChanged?: boolean }
  resources?: { listChanged?: boolean }
  prompts?: { listChanged?: boolean }
}

export interface ToolDefinition {
  name: string
  description: string
  inputSchema: {
    type: 'object'
    properties: Record<string, unknown>
    required?: string[]
  }
}
```

### `src/lib/errors.ts`

Tipos de error JSON-RPC + MCP-specific (segun spec
modelcontextprotocol.io):

```ts
export const ERROR_CODES = {
  PARSE_ERROR: -32700,
  INVALID_REQUEST: -32600,
  METHOD_NOT_FOUND: -32601,
  INVALID_PARAMS: -32602,
  INTERNAL_ERROR: -32603,
  // MCP-specific
  TOOL_NOT_FOUND: -32001,
  TOOL_EXECUTION_ERROR: -32002,
} as const

export function makeError(
  id: number | string | null,
  code: number,
  message: string,
  data?: unknown,
): JsonRpcResponseError {
  return { jsonrpc: '2.0', id, error: { code, message, data } }
}
```

### `src/lib/jsonrpc.ts`

```ts
export function parseRequest(raw: string): JsonRpcRequest | null {
  try {
    const parsed = JSON.parse(raw)
    if (parsed.jsonrpc !== '2.0' || typeof parsed.method !== 'string') {
      return null
    }
    return parsed as JsonRpcRequest
  } catch {
    return null
  }
}

export function makeSuccess(
  id: number | string | null,
  result: unknown,
): JsonRpcResponseSuccess {
  return { jsonrpc: '2.0', id, result }
}
```

### `src/lib/handle-initialize.ts`

```ts
import { makeSuccess, type JsonRpcResponseSuccess } from './jsonrpc'
import { PROTOCOL_VERSION, type Capabilities, type ServerInfo } from './types'

export function handleInitialize(
  id: number | string | null,
): JsonRpcResponseSuccess {
  const capabilities: Capabilities = { tools: { listChanged: false } }
  const serverInfo: ServerInfo = {
    name: 'portfolio-mcp',
    version: '0.1.0',
  }
  return makeSuccess(id, {
    protocolVersion: PROTOCOL_VERSION,
    capabilities,
    serverInfo,
  })
}
```

### `src/lib/handle-tools-list.ts`

```ts
import { makeSuccess } from './jsonrpc'
import { TOOLS } from './tools'  // export desde Fase 2B

export function handleToolsList(id: number | string | null) {
  return makeSuccess(id, { tools: TOOLS.map((t) => t.definition) })
}
```

(En Fase 2A, `TOOLS = []`; en Fase 2B se llena con las 3 tools.)

### `src/lib/handle-request.ts`

```ts
import { parseRequest, makeSuccess } from './jsonrpc'
import { makeError, ERROR_CODES } from './errors'
import { handleInitialize } from './handle-initialize'
import { handleToolsList } from './handle-tools-list'
import { handleToolsCall } from './handle-tools-call'

export async function handleRequest(
  body: string,
): Promise<JsonRpcResponse> {
  const req = parseRequest(body)
  if (!req) return makeError(null, ERROR_CODES.PARSE_ERROR, 'Parse error')

  switch (req.method) {
    case 'initialize':
      return handleInitialize(req.id)
    case 'tools/list':
      return handleToolsList(req.id)
    case 'tools/call':
      return handleToolsCall(req.id, req.params)
    default:
      return makeError(req.id, ERROR_CODES.METHOD_NOT_FOUND,
        `Method not found: ${req.method}`)
  }
}
```

## Tarea 2A.2 — Tests unitarios

### `tests/unit/handle-initialize.test.ts`

```ts
describe('handleInitialize', () => {
  it('Given id=1 When invoked Then returns JSON-RPC response with serverInfo + capabilities', () => {
    const out = handleInitialize(1)
    expect(out).toEqual({
      jsonrpc: '2.0',
      id: 1,
      result: {
        protocolVersion: '2025-11-25',
        capabilities: { tools: { listChanged: false } },
        serverInfo: { name: 'portfolio-mcp', version: '0.1.0' },
      },
    })
  })
})
```

### `tests/unit/jsonrpc.test.ts`

```ts
describe('parseRequest', () => {
  it('Given valid JSON-RPC 2.0 When parse Then returns parsed object', () => {
    const out = parseRequest('{"jsonrpc":"2.0","id":1,"method":"initialize"}')
    expect(out).toEqual({ jsonrpc: '2.0', id: 1, method: 'initialize' })
  })

  it('Given missing jsonrpc=2.0 When parse Then returns null', () => {
    expect(parseRequest('{"id":1,"method":"x"}')).toBe(null)
  })

  it('Given invalid JSON When parse Then returns null', () => {
    expect(parseRequest('not json')).toBe(null)
  })

  it('Given missing method When parse Then returns null', () => {
    expect(parseRequest('{"jsonrpc":"2.0","id":1}')).toBe(null)
  })
})
```

### `tests/unit/errors.test.ts`

```ts
describe('makeError', () => {
  it('Given code+message When build Then returns JSON-RPC error envelope', () => {
    const out = makeError(1, -32601, 'Method not found')
    expect(out).toEqual({
      jsonrpc: '2.0',
      id: 1,
      error: { code: -32601, message: 'Method not found' },
    })
  })
})
```

## Tarea 2A.3 — Crear Pages Functions wrapper en cada app

`apps/*/functions/mcp.ts` (6 archivos, todos iguales):

```ts
import { handleRequest } from '@portfolio/mcp'

interface CfContext {
  request: Request
}

export const onRequestPost = async (ctx: CfContext): Promise<Response> => {
  const body = await ctx.request.text()
  const response = await handleRequest(body)
  return new Response(JSON.stringify(response), {
    status: 200,
    headers: {
      'content-type': 'application/json',
      'access-control-allow-origin': '*',
    },
  })
}

export const onRequestOptions = (): Response => {
  return new Response(null, {
    status: 204,
    headers: {
      'access-control-allow-origin': '*',
      'access-control-allow-methods': 'POST, OPTIONS',
      'access-control-allow-headers': 'content-type',
    },
  })
}
```

Asi `https://<dominio>/mcp` responde a POST.

## Tarea 2A.4 — Configurar wrangler para Functions

Cada `apps/*/wrangler.toml` (si no existe) o config equivalente:

```toml
name = "portfolio-<niche>"
compatibility_date = "2026-05-25"
pages_build_output_dir = "./dist"

[[functions]]
directory = "./functions"
```

NOTA: actualmente las apps probablemente NO tienen `wrangler.toml`
(usan deploy via API). Verificar como se gestionan las Pages Functions
en el deploy actual de devtools antes de tomar la decision final. Si
las Functions requieren un `wrangler.toml` que el deploy de devtools
hoy no respeta, este plan tiene que extender `devtools/cloudflare_setup`
para incluirlas. Ver Tarea 2A.5.

## Tarea 2A.5 — Verificar integracion con devtools cloudflare_setup

Antes de empezar Fase 2A, leer `devtools/cloudflare_setup/` y verificar:

1. El `wrangler pages deploy` actual sube `apps/*/functions/`
   automaticamente si existen?
2. Si no, que cambio se necesita en el provisioner de Pages?
3. Hay limites del Free tier (100k req/dia) que monitorear?

Si el deploy actual SI sube `functions/` automaticamente (es el default
de wrangler con `--functions ./functions`), no hay cambios en devtools.
Si NO, agregar tarea: "extender cloudflare_setup para subir functions
del Pages project".

## Verificacion incremental

```bash
# Tests del paquete
pnpm --filter @portfolio/mcp run test
pnpm --filter @portfolio/mcp run typecheck

# Coverage >= 80%
pnpm --filter @portfolio/mcp exec vitest run --coverage

# Probar endpoint local con wrangler
pnpm --filter @portfolio/generic run build
npx wrangler pages dev apps/generic/dist --port 8788

# En otra terminal:
curl -X POST http://localhost:8788/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
# ESPERADO: {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-11-25",...}}
```

## Archivos afectados

### Crear

- `packages/mcp/package.json`
- `packages/mcp/tsconfig.json`
- `packages/mcp/vitest.config.ts`
- `packages/mcp/src/index.ts`
- `packages/mcp/src/lib/handle-request.ts`
- `packages/mcp/src/lib/handle-initialize.ts`
- `packages/mcp/src/lib/handle-tools-list.ts`
- `packages/mcp/src/lib/handle-tools-call.ts` (stub que retorna TOOL_NOT_FOUND, completado en 2B)
- `packages/mcp/src/lib/jsonrpc.ts`
- `packages/mcp/src/lib/errors.ts`
- `packages/mcp/src/lib/types.ts`
- `packages/mcp/src/lib/tools/index.ts` (export `TOOLS = []`, completado en 2B)
- `packages/mcp/tests/unit/handle-initialize.test.ts`
- `packages/mcp/tests/unit/handle-tools-list.test.ts`
- `packages/mcp/tests/unit/jsonrpc.test.ts`
- `packages/mcp/tests/unit/errors.test.ts`
- `apps/architect/functions/mcp.ts`
- `apps/fintech/functions/mcp.ts`
- `apps/generic/functions/mcp.ts`
- `apps/hub/functions/mcp.ts`
- `apps/leader/functions/mcp.ts`
- `apps/vibe/functions/mcp.ts`
  - Verificar (todos): `wrangler pages dev` local responde a `POST /mcp`

### Modificar

- `pnpm-workspace.yaml` — agregar `packages/mcp` si glob explicito

## Done

- [ ] Paquete `@portfolio/mcp` con handlers initialize + tools/list + skeleton
- [ ] Coverage >= 80% per-file
- [ ] 6 wrappers en `apps/*/functions/mcp.ts`
- [ ] `wrangler pages dev` local: `POST /mcp` responde a `initialize`
- [ ] Lint + typecheck verde
- [ ] Commit 1: `feat(mcp): paquete @portfolio/mcp con handlers initialize + tools/list`
- [ ] Commit 2: `feat(apps): expone endpoint /mcp en Pages Functions de los 6 niches`
