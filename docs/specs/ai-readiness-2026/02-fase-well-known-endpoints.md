# Fase 1 — well-known endpoints (Astro)

> Objetivo: las 6 apps publican los 3 endpoints JSON tipados que el
> scan busca: `api-catalog`, `mcp/server-card.json`, `agent-skills/index.json`.
> Cubre AC-1, AC-2, AC-3, AC-4.

## 1. Datos compartidos: `packages/seo/src/data/`

### `packages/seo/src/data/mcp-tools.ts`

Fuente unica de verdad de las tools que el portfolio expone. La leen:
el MCP Server Card (este fase), el WebMCP runtime (fase 4) y el
Agent Skills index. Tipado estricto via Zod.

```ts
import { z } from 'zod'

export const McpToolSchema = z.object({
  name: z.string(),                       // ej. 'cv.get_experiences'
  description: z.string(),
  inputSchema: z.object({
    type: z.literal('object'),
    properties: z.record(z.unknown()),
    required: z.array(z.string()).optional(),
  }),
  endpoint: z.object({
    method: z.enum(['GET', 'POST']),
    url: z.string(),                      // URL relativa al api base
  }),
  category: z.enum(['cv', 'nlweb', 'contact']),
})
export type McpTool = z.infer<typeof McpToolSchema>

export const MCP_TOOLS: readonly McpTool[] = [
  {
    name: 'cv.get_experiences',
    description: 'List work experiences from the CV, filterable by niche',
    inputSchema: {
      type: 'object',
      properties: {
        niche: { type: 'string', enum: ['fintech', 'architect', 'leader', 'vibe', 'generic'] },
      },
    },
    endpoint: { method: 'GET', url: '/cv?operation=cv&action=experiences' },
    category: 'cv',
  },
  {
    name: 'cv.get_projects',
    description: 'List completed projects from the CV, filterable by niche',
    inputSchema: { /* idem */ },
    endpoint: { method: 'GET', url: '/cv?operation=cv&action=projects' },
    category: 'cv',
  },
  {
    name: 'cv.get_skills',
    description: 'List technical and soft skills',
    inputSchema: { type: 'object', properties: {} },
    endpoint: { method: 'GET', url: '/cv?operation=cv&action=skills' },
    category: 'cv',
  },
  {
    name: 'nlweb.ask',
    description: 'Natural-language query over the CV (schema.org response)',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string' },
        niche: { type: 'string', enum: ['fintech', 'architect', 'leader', 'vibe', 'generic'] },
      },
      required: ['query'],
    },
    endpoint: { method: 'POST', url: '/nlweb/ask' },
    category: 'nlweb',
  },
] as const
```

### `packages/seo/src/data/api-base.ts`

Resolver de la URL del API por stage (NO hardcodear).

```ts
export function resolveApiBase(siteUrl: URL): string {
  // siteUrl es la URL de la app que sirve el endpoint
  // Devuelve la URL del backend para ese stage
  const host = siteUrl.host
  if (host.endsWith('.dev.the-full-stack.com')) return 'https://api.portfolio.dev.the-full-stack.com'
  if (host.endsWith('.stage.the-full-stack.com')) return 'https://api.portfolio.stage.the-full-stack.com'
  if (host === 'the-full-stack.com' || host.endsWith('.portfolio.the-full-stack.com')) {
    return 'https://api.portfolio.the-full-stack.com'
  }
  // local: la API local no existe — apuntar a dev como fallback
  return 'https://api.portfolio.dev.the-full-stack.com'
}
```

## 2. Builders nuevos en `packages/seo/src/lib/`

### `build-api-catalog.ts`

```ts
import { MCP_TOOLS } from '../data/mcp-tools'
import { resolveApiBase } from '../data/api-base'

export interface ApiCatalogInput {
  siteUrl: URL
}

export interface ApiCatalogLinkset {
  linkset: Array<{
    anchor: string
    'service-desc'?: Array<{ href: string; type: string }>
    'service-doc'?: Array<{ href: string }>
    status?: Array<{ href: string }>
  }>
}

export function buildApiCatalog({ siteUrl }: ApiCatalogInput): ApiCatalogLinkset {
  const apiBase = resolveApiBase(siteUrl)
  return {
    linkset: [
      {
        anchor: `${apiBase}/cv`,
        'service-desc': [{ href: `${apiBase}/cv?operation=cv&action=get`, type: 'application/json' }],
        'service-doc': [{ href: `${siteUrl.origin}/llms.txt` }],
      },
      {
        anchor: `${apiBase}/nlweb/ask`,
        'service-desc': [{ href: `${siteUrl.origin}/.well-known/mcp/server-card.json`, type: 'application/json' }],
      },
    ],
  }
}
```

### `build-mcp-server-card.ts`

Conforme a SEP-2127. La spec esta en draft, los campos `serverInfo`,
`transport`, `capabilities`, `tools` son estables segun el scan.

```ts
import { MCP_TOOLS } from '../data/mcp-tools'
import { resolveApiBase } from '../data/api-base'

export interface McpServerCardInput {
  siteUrl: URL
  niche: string  // 'generic' | 'hub' | 'fintech' | 'architect' | 'leader' | 'vibe'
}

export function buildMcpServerCard({ siteUrl, niche }: McpServerCardInput) {
  const apiBase = resolveApiBase(siteUrl)
  return {
    $schema: 'https://modelcontextprotocol.io/schemas/server-card-1.0.json',
    serverInfo: {
      name: `the-full-stack-portfolio-${niche}`,
      version: '1.0.0',
      description: `Pablo Contreras CV and projects, focused on ${niche}`,
    },
    transport: {
      type: 'http',
      url: apiBase,
    },
    capabilities: ['tools', 'resources'],
    tools: MCP_TOOLS.map((t) => ({
      name: t.name,
      description: t.description,
      inputSchema: t.inputSchema,
    })),
    resources: [
      {
        uri: `${siteUrl.origin}/cv.html`,
        name: 'CV (ATS-friendly HTML)',
        mimeType: 'text/html',
      },
      {
        uri: `${siteUrl.origin}/llms.txt`,
        name: 'LLM-friendly content map',
        mimeType: 'text/plain',
      },
    ],
  }
}
```

### `build-agent-skills.ts`

Conforme a Cloudflare Agent Skills Discovery RFC v0.2.0. Cada skill
incluye `sha256` del propio body del skill (no del recurso linkeado)
para detectar cambios.

```ts
import { createHash } from 'node:crypto'

export interface AgentSkillsInput {
  siteUrl: URL
}

export function buildAgentSkills({ siteUrl }: AgentSkillsInput) {
  const origin = siteUrl.origin
  const skills = [
    {
      name: 'download-cv',
      type: 'document',
      description: 'Download Pablo Contreras CV in PDF or HTML format',
      url: `${origin}/cv.html`,
    },
    {
      name: 'search-cv',
      type: 'api',
      description: 'Search Pablo Contreras experience, projects, and skills',
      url: `${origin}/.well-known/mcp/server-card.json`,
    },
    {
      name: 'contact',
      type: 'form',
      description: 'Contact Pablo Contreras via the website contact form',
      url: `${origin}/contact`,
    },
    {
      name: 'ask-nlweb',
      type: 'api',
      description: 'Ask natural-language questions about the CV (NLWeb)',
      url: `${origin}/.well-known/mcp/server-card.json`,
    },
  ]
  return {
    $schema: 'https://agentskills.io/schemas/skills-index-0.2.0.json',
    skills: skills.map((s) => ({
      ...s,
      sha256: createHash('sha256').update(JSON.stringify(s)).digest('hex'),
    })),
  }
}
```

### Exportar en `packages/seo/src/index.ts`

```ts
export { buildApiCatalog } from './lib/build-api-catalog'
export { buildMcpServerCard } from './lib/build-mcp-server-card'
export { buildAgentSkills } from './lib/build-agent-skills'
export { MCP_TOOLS, McpToolSchema } from './data/mcp-tools'
export type { McpTool } from './data/mcp-tools'
```

## 3. Endpoints Astro por app

Cada app crea **3 archivos**. Patron repetible (apps/generic, apps/hub,
apps/fintech, apps/architect, apps/leader, apps/vibe). Diferencia entre
apps: solo el campo `niche` del `buildMcpServerCard`.

### `apps/<app>/src/pages/.well-known/api-catalog.ts`

```ts
import type { APIRoute } from 'astro'
import { buildApiCatalog } from '@portfolio/seo'

export const GET: APIRoute = ({ site }) => {
  const body = buildApiCatalog({ siteUrl: site! })
  return new Response(JSON.stringify(body, null, 2), {
    status: 200,
    headers: {
      'Content-Type': 'application/linkset+json',
      'Cache-Control': 'public, max-age=3600',
    },
  })
}
```

### `apps/<app>/src/pages/.well-known/mcp/server-card.json.ts`

```ts
import type { APIRoute } from 'astro'
import { buildMcpServerCard } from '@portfolio/seo'

export const GET: APIRoute = ({ site }) => {
  const body = buildMcpServerCard({ siteUrl: site!, niche: '<APP>' })
  return new Response(JSON.stringify(body, null, 2), {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'public, max-age=3600',
    },
  })
}
```

> El `<APP>` se reemplaza por `generic`, `hub`, `fintech`, etc.
> El parametro `site` viene de `astro.config.ts#site` (cada app lo
> tiene declarado).

### `apps/<app>/src/pages/.well-known/agent-skills/index.json.ts`

```ts
import type { APIRoute } from 'astro'
import { buildAgentSkills } from '@portfolio/seo'

export const GET: APIRoute = ({ site }) => {
  const body = buildAgentSkills({ siteUrl: site! })
  return new Response(JSON.stringify(body, null, 2), {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'public, max-age=3600',
    },
  })
}
```

## 4. Tests unit (Vitest, en `packages/seo/tests/unit/lib/`)

Mirror del path. Cada test cubre un AC.

### `tests/unit/lib/build-api-catalog.test.ts`

```ts
import { describe, expect, it } from 'vitest'
import { buildApiCatalog } from '../../../src/lib/build-api-catalog'

describe('buildApiCatalog', () => {
  it('Given prod URL the-full-stack.com When build Then api base prod [AC-1]', () => {
    const result = buildApiCatalog({ siteUrl: new URL('https://the-full-stack.com') })
    expect(result.linkset[0].anchor).toBe('https://api.portfolio.the-full-stack.com/cv')
  })

  it('Given dev URL When build Then api base dev [AC-1]', () => {
    const result = buildApiCatalog({ siteUrl: new URL('https://portfolio.dev.the-full-stack.com') })
    expect(result.linkset[0].anchor).toBe('https://api.portfolio.dev.the-full-stack.com/cv')
  })

  it('Given any URL When build Then linkset has >= 2 entries [AC-1]', () => {
    const result = buildApiCatalog({ siteUrl: new URL('https://the-full-stack.com') })
    expect(result.linkset.length).toBe(2)
  })
})
```

### `tests/unit/lib/build-mcp-server-card.test.ts`

```ts
import { describe, expect, it } from 'vitest'
import { buildMcpServerCard } from '../../../src/lib/build-mcp-server-card'

describe('buildMcpServerCard', () => {
  it('Given niche=fintech When build Then serverInfo.name encodes niche [AC-2]', () => {
    const result = buildMcpServerCard({
      siteUrl: new URL('https://fintech.portfolio.the-full-stack.com'),
      niche: 'fintech',
    })
    expect(result.serverInfo.name).toBe('the-full-stack-portfolio-fintech')
  })

  it('Given any input When build Then declares >= 3 tools [AC-2]', () => {
    const result = buildMcpServerCard({
      siteUrl: new URL('https://the-full-stack.com'),
      niche: 'generic',
    })
    expect(result.tools.length).toBe(4)  // 3 cv + 1 nlweb
  })

  it('Given any input When build Then capabilities = [tools, resources] [AC-2]', () => {
    const result = buildMcpServerCard({
      siteUrl: new URL('https://the-full-stack.com'),
      niche: 'generic',
    })
    expect(result.capabilities).toEqual(['tools', 'resources'])
  })
})
```

### `tests/unit/lib/build-agent-skills.test.ts`

```ts
import { describe, expect, it } from 'vitest'
import { buildAgentSkills } from '../../../src/lib/build-agent-skills'

describe('buildAgentSkills', () => {
  it('Given any URL When build Then array skills tiene 4 entries [AC-3]', () => {
    const result = buildAgentSkills({ siteUrl: new URL('https://the-full-stack.com') })
    expect(result.skills.length).toBe(4)
  })

  it('Given any URL When build Then cada skill tiene sha256 [AC-3]', () => {
    const result = buildAgentSkills({ siteUrl: new URL('https://the-full-stack.com') })
    expect(result.skills.every((s) => /^[a-f0-9]{64}$/.test(s.sha256))).toBe(true)
  })
})
```

## 5. Verificacion incremental

Tras cada commit de esta fase:

```bash
# Tests unit del paquete @portfolio/seo
python devtools/run.py test_runner --module=pkg-seo --type=unit

# Typecheck
pnpm --filter @portfolio/seo run typecheck

# Build de una app (toma la mas chica, hub)
pnpm --filter @portfolio/hub run build

# Verificar que los 3 endpoints generaron archivos
ls apps/hub/dist/.well-known/api-catalog
ls apps/hub/dist/.well-known/mcp/server-card.json
ls apps/hub/dist/.well-known/agent-skills/index.json
```

> Astro genera estos endpoints como `.json` o sin extension segun el
> archivo. `api-catalog.ts` -> `api-catalog` (sin ext); el scan lo
> espera asi. Verificar con `curl` que el content-type es correcto.

## 6. Notas de implementacion

- El path `.well-known/mcp/server-card.json` requiere carpeta intermedia
  `pages/.well-known/mcp/` y el archivo `server-card.json.ts`. Astro
  genera `server-card.json` como archivo estatico (la doble extension
  `.json.ts` se resuelve correctamente — verificar con
  `pnpm run build` antes de avanzar).

- El `Content-Type: application/linkset+json` puede tener problemas con
  el nginx local del Docker stack (no esta en mime.types). Verificar y
  agregar a `docker/nginx/conf.d/mime.types` si aplica (es solo para
  local; en Cloudflare Pages el Worker setea el header explicito).

- El `cv.html` referenciado en `resources` ya existe (lo genera el
  prebuild script de cada app). NO crear nuevo archivo.
