# 07 — Fase 2B: MCP tools (`get_cv_section`, `list_projects`, `search_experience`)

> **Anterior**: [06-fase-2a-mcp-server-endpoint.md](06-fase-2a-mcp-server-endpoint.md) · **Siguiente**: [08-fase-2c-mcp-server-card.md](08-fase-2c-mcp-server-card.md)
>
> **Cubre**: AC-8, AC-9, AC-10
>
> **Objetivo**: implementar las 3 tools del MCP server que consultan el
> CV via `@portfolio/content`.

## Estrategia

Cada tool es un modulo en `packages/mcp/src/lib/tools/<tool-name>.ts`
con:

- `definition: ToolDefinition` (nombre, descripcion, inputSchema)
- `execute(args: T): Promise<{ content: Array<{ type: 'text', text: string }> }>`

El handler `tools/call` ruta por nombre + valida args + invoca `execute`.
Si el tool no existe → error TOOL_NOT_FOUND (-32001). Si execute lanza
→ error TOOL_EXECUTION_ERROR (-32002).

## Tarea 2B.1 — Tool 1: `get_cv_section`

```
packages/mcp/src/lib/tools/get-cv-section.ts
```

```ts
import { profile, experiences, projects, skills, education } from '@portfolio/content'
import type { ToolDefinition } from '../types'

const SECTIONS = ['about', 'experience', 'projects', 'skills', 'education', 'contact'] as const
type Section = typeof SECTIONS[number]

interface Args {
  section: Section
}

export const definition: ToolDefinition = {
  name: 'get_cv_section',
  description: "Returns a section of Pablo Contreras' CV in Markdown.",
  inputSchema: {
    type: 'object',
    properties: {
      section: {
        type: 'string',
        enum: [...SECTIONS],
        description: 'Which CV section to fetch',
      },
    },
    required: ['section'],
  },
}

export async function execute(args: Args) {
  if (!SECTIONS.includes(args.section)) {
    throw new Error(`unknown section: ${args.section}`)
  }
  let md = ''
  switch (args.section) {
    case 'about':
      md = `# About\n\n${profile.bio.en}\n`
      break
    case 'experience':
      md = '# Experience\n\n' + experiences.map((e) =>
        `## ${e.role.en} @ ${e.company} (${e.start} - ${e.end ?? 'Present'})\n\n` +
        e.achievements.en.map((a) => `- ${a}`).join('\n')
      ).join('\n\n')
      break
    case 'projects':
      md = '# Projects\n\n' + projects.map((p) =>
        `## ${p.name}\n\n${p.description.en}\n\n**Tech**: ${p.techStack.join(', ')}`
      ).join('\n\n')
      break
    // ...skills, education, contact analogos
    default:
      md = `# ${args.section}\n\n(not yet implemented)\n`
  }
  return { content: [{ type: 'text' as const, text: md }] }
}
```

NOTA: los nombres exactos de campos en `@portfolio/content` deben
verificarse en `packages/content/src/schemas.ts`. Si la API real difiere,
adaptar.

## Tarea 2B.2 — Tool 2: `list_projects`

```
packages/mcp/src/lib/tools/list-projects.ts
```

```ts
import { projects } from '@portfolio/content'
import type { ToolDefinition } from '../types'

interface Args {
  tech_stack?: string  // ej. 'Astro', 'Vue', 'AWS'
}

export const definition: ToolDefinition = {
  name: 'list_projects',
  description: "Lists Pablo's projects, optionally filtered by tech stack keyword.",
  inputSchema: {
    type: 'object',
    properties: {
      tech_stack: {
        type: 'string',
        description: 'Optional filter (case-insensitive) by tech stack',
      },
    },
  },
}

export async function execute(args: Args) {
  const filter = args.tech_stack?.toLowerCase()
  const filtered = filter
    ? projects.filter((p) =>
        p.techStack.some((t) => t.toLowerCase().includes(filter))
      )
    : [...projects]
  const payload = filtered.map((p) => ({
    name: p.name,
    description: p.description.en,
    techStack: p.techStack,
    url: p.url,
  }))
  return {
    content: [{ type: 'text' as const, text: JSON.stringify(payload, null, 2) }],
  }
}
```

## Tarea 2B.3 — Tool 3: `search_experience`

```
packages/mcp/src/lib/tools/search-experience.ts
```

```ts
import { experiences } from '@portfolio/content'
import type { ToolDefinition } from '../types'

interface Args {
  keyword: string
}

export const definition: ToolDefinition = {
  name: 'search_experience',
  description: 'Searches experiences (role, company, achievements, tech) by keyword.',
  inputSchema: {
    type: 'object',
    properties: {
      keyword: {
        type: 'string',
        description: 'Case-insensitive substring to match',
      },
    },
    required: ['keyword'],
  },
}

export async function execute(args: Args) {
  if (!args.keyword || args.keyword.trim().length === 0) {
    throw new Error('keyword must be non-empty')
  }
  const kw = args.keyword.toLowerCase()
  const matches = experiences.filter((e) => {
    const haystack = [
      e.role.en,
      e.company,
      ...e.achievements.en,
      ...(e.skillsTechnical ?? []),
    ].join(' ').toLowerCase()
    return haystack.includes(kw)
  })
  const payload = matches.map((e) => ({
    role: e.role.en,
    company: e.company,
    start: e.start,
    end: e.end,
    achievements: e.achievements.en,
  }))
  return {
    content: [{ type: 'text' as const, text: JSON.stringify(payload, null, 2) }],
  }
}
```

## Tarea 2B.4 — Registro central de tools

`packages/mcp/src/lib/tools/index.ts`:

```ts
import * as getCvSection from './get-cv-section'
import * as listProjects from './list-projects'
import * as searchExperience from './search-experience'

export const TOOLS = [
  getCvSection,
  listProjects,
  searchExperience,
] as const

export type ToolModule = typeof TOOLS[number]

export function getToolByName(name: string): ToolModule | null {
  return TOOLS.find((t) => t.definition.name === name) ?? null
}
```

## Tarea 2B.5 — Completar `handle-tools-call.ts`

```ts
import { makeSuccess } from './jsonrpc'
import { makeError, ERROR_CODES } from './errors'
import { getToolByName } from './tools'

interface CallParams {
  name: string
  arguments?: Record<string, unknown>
}

export async function handleToolsCall(
  id: number | string | null,
  params: unknown,
) {
  const p = params as CallParams | undefined
  if (!p?.name) {
    return makeError(id, ERROR_CODES.INVALID_PARAMS, 'missing name')
  }
  const tool = getToolByName(p.name)
  if (!tool) {
    return makeError(id, ERROR_CODES.TOOL_NOT_FOUND, `tool not found: ${p.name}`)
  }
  try {
    const result = await tool.execute(p.arguments ?? {})
    return makeSuccess(id, result)
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e)
    return makeError(id, ERROR_CODES.TOOL_EXECUTION_ERROR, msg)
  }
}
```

## Tarea 2B.6 — Tests

### `tests/unit/tools/get-cv-section.test.ts`

```ts
describe('get_cv_section', () => {
  it('Given section=about When execute Then returns Markdown with About header', async () => {
    const out = await execute({ section: 'about' })
    expect(out.content[0].type).toBe('text')
    expect(out.content[0].text).toMatch(/^# About\n/)
  })

  it('Given section=experience When execute Then includes all experiences', async () => {
    const out = await execute({ section: 'experience' })
    expect(out.content[0].text).toContain('# Experience')
    // numero de matches de "## " debe ser experiences.length
    const headerCount = (out.content[0].text.match(/^## /gm) ?? []).length
    expect(headerCount).toBe(experiences.length)
  })

  it('Given unknown section When execute Then throws', async () => {
    await expect(execute({ section: 'unknown' as never })).rejects.toThrow()
  })
})
```

### `tests/unit/tools/list-projects.test.ts`

```ts
describe('list_projects', () => {
  it('Given no filter When execute Then returns all projects', async () => {
    const out = await execute({})
    const data = JSON.parse(out.content[0].text)
    expect(data).toHaveLength(projects.length)
  })

  it('Given filter=Astro When execute Then returns projects with Astro stack', async () => {
    const out = await execute({ tech_stack: 'Astro' })
    const data = JSON.parse(out.content[0].text)
    data.forEach((p: any) => {
      expect(p.techStack.some((t: string) =>
        t.toLowerCase().includes('astro'),
      )).toBe(true)
    })
  })

  it('Given filter=nonexistent When execute Then returns empty array', async () => {
    const out = await execute({ tech_stack: 'XYZNOTEXIST' })
    expect(JSON.parse(out.content[0].text)).toEqual([])
  })
})
```

### `tests/unit/tools/search-experience.test.ts`

```ts
describe('search_experience', () => {
  it('Given keyword matching a role When execute Then returns matches', async () => {
    // asume que existe al menos un experience con "Senior" en role
    const out = await execute({ keyword: 'Senior' })
    const data = JSON.parse(out.content[0].text)
    expect(data.length).toBeGreaterThan(0)
  })

  it('Given empty keyword When execute Then throws', async () => {
    await expect(execute({ keyword: '' })).rejects.toThrow('non-empty')
  })

  it('Given keyword that matches nothing When execute Then returns empty array', async () => {
    const out = await execute({ keyword: 'ZZZNONEXISTENT' })
    expect(JSON.parse(out.content[0].text)).toEqual([])
  })
})
```

### `tests/unit/handle-tools-call.test.ts`

```ts
describe('handleToolsCall', () => {
  it('Given valid tool name + args When invoked Then returns success', async () => {
    const out = await handleToolsCall(1, {
      name: 'get_cv_section',
      arguments: { section: 'about' },
    })
    expect('result' in out).toBe(true)
  })

  it('Given unknown tool When invoked Then returns TOOL_NOT_FOUND', async () => {
    const out = await handleToolsCall(1, { name: 'nonexistent' })
    expect('error' in out && out.error.code).toBe(-32001)
  })

  it('Given missing name When invoked Then returns INVALID_PARAMS', async () => {
    const out = await handleToolsCall(1, {})
    expect('error' in out && out.error.code).toBe(-32602)
  })

  it('Given tool that throws When invoked Then returns TOOL_EXECUTION_ERROR', async () => {
    const out = await handleToolsCall(1, {
      name: 'search_experience',
      arguments: { keyword: '' },
    })
    expect('error' in out && out.error.code).toBe(-32002)
  })
})
```

## Tarea 2B.7 — Actualizar `handle-tools-list.test.ts` para 3 tools

```ts
it('Given Fase 2B complete When invoked Then returns 3 tools with stable order', () => {
  const out = handleToolsList(1)
  const tools = (out.result as any).tools
  expect(tools).toHaveLength(3)
  expect(tools.map((t: any) => t.name)).toEqual([
    'get_cv_section',
    'list_projects',
    'search_experience',
  ])
})
```

## Verificacion incremental

```bash
# Tests + coverage
pnpm --filter @portfolio/mcp run test
pnpm --filter @portfolio/mcp exec vitest run --coverage
# ESPERADO: >= 80% per-file

# Probar endpoint local end-to-end con wrangler
pnpm --filter @portfolio/generic run build
npx wrangler pages dev apps/generic/dist --port 8788

# En otra terminal:
curl -X POST http://localhost:8788/mcp -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | jq .result.tools[].name
# ESPERADO: "get_cv_section" "list_projects" "search_experience"

curl -X POST http://localhost:8788/mcp -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_cv_section","arguments":{"section":"about"}}}' \
  | jq .result.content[0].text
# ESPERADO: "# About\n\n..."
```

## Archivos afectados

### Crear

- `packages/mcp/src/lib/tools/get-cv-section.ts`
- `packages/mcp/src/lib/tools/list-projects.ts`
- `packages/mcp/src/lib/tools/search-experience.ts`
- `packages/mcp/tests/unit/tools/get-cv-section.test.ts`
- `packages/mcp/tests/unit/tools/list-projects.test.ts`
- `packages/mcp/tests/unit/tools/search-experience.test.ts`
- `packages/mcp/tests/unit/handle-tools-call.test.ts`

### Modificar

- `packages/mcp/src/lib/tools/index.ts` — registrar las 3 tools
- `packages/mcp/src/lib/handle-tools-call.ts` — implementacion completa
- `packages/mcp/tests/unit/handle-tools-list.test.ts` — actualizar para 3 tools

## Done

- [ ] 3 tools implementadas con tests verdes
- [ ] Coverage >= 80% per-file en el paquete
- [ ] Endpoint local responde correctamente a `tools/list` y `tools/call`
- [ ] Commit 1: `feat(mcp): implementa tools get_cv_section + list_projects + search_experience`
- [ ] Commit 2: `feat(mcp): handle-tools-call ruta por nombre + error TOOL_NOT_FOUND/TOOL_EXECUTION_ERROR`
