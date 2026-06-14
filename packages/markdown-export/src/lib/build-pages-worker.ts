/**
 * @module build-pages-worker
 * @description Genera el TS source de `_worker.ts` (Cloudflare Pages
 *   Advanced Mode). UN solo Worker monolitico que maneja todo el routing:
 *
 *   - POST/OPTIONS /mcp -> MCP server (delega a @portfolio/mcp).
 *   - GET /.well-known/api-catalog.json -> JSON estatico inlineado.
 *   - GET /.well-known/mcp/server-card.json -> JSON estatico inlineado.
 *   - GET con Accept: text/markdown -> fetch interno del .md gemelo.
 *   - Default: delega a env.ASSETS.fetch (asset estatico o SPA fallback).
 *
 *   Razon: las Pages Functions en `dist/functions/` NO se ejecutan en
 *   Cloudflare Pages prod (solo en wrangler dev local). El Advanced Mode
 *   con `dist/_worker.js` SI funciona universalmente.
 *
 *   Generado por code en build-time + bundleado con esbuild para inlinear
 *   los JSON snapshots. Mismo source en los 6 niches.
 */

/**
 * @function buildPagesWorker
 * @description Devuelve el TS source de `_worker.ts` listo para
 *   compilarse a `dist/_worker.js` con esbuild.
 *
 * @returns {string} TypeScript source completo del Worker.
 */
export function buildPagesWorker(): string {
  return `/**
 * @function _worker (Cloudflare Pages Advanced Mode)
 * @description Single Worker que maneja todo el routing del site.
 *   Generado por \`@portfolio/markdown-export\` (buildPagesWorker).
 *   NO editar — regenerar via postbuild si cambian las reglas.
 */
import { createSnapshotProvider, handleRequest } from '@portfolio/mcp'
import type { CvSnapshot } from '@portfolio/mcp'
import cvSnapshot from './_worker-data/cv-snapshot.json'
import apiCatalog from './_worker-data/api-catalog.json'
import mcpServerCard from './_worker-data/mcp-server-card.json'
import agentCard from './_worker-data/agent-card.json'
import agentSkills from './_worker-data/agent-skills.json'

interface Env {
  ASSETS: { fetch: (request: Request) => Promise<Response> }
}

const dataProvider = createSnapshotProvider(cvSnapshot as unknown as CvSnapshot)

const corsHeaders: Record<string, string> = {
  'access-control-allow-origin': '*',
}

async function handleMcpPost(request: Request): Promise<Response> {
  const body = await request.text()
  const response = await handleRequest(body, dataProvider)
  return new Response(JSON.stringify(response), {
    status: 200,
    headers: {
      ...corsHeaders,
      'content-type': 'application/json; charset=UTF-8',
      'cache-control': 'no-store',
    },
  })
}

function handleMcpOptions(): Response {
  return new Response(null, {
    status: 204,
    headers: {
      ...corsHeaders,
      'access-control-allow-methods': 'POST, OPTIONS',
      'access-control-allow-headers': 'content-type',
      'access-control-max-age': '86400',
    },
  })
}

function jsonResponse(payload: unknown, contentType: string): Response {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: {
      ...corsHeaders,
      'content-type': \`\${contentType}; charset=UTF-8\`,
      'cache-control': 'public, max-age=3600',
    },
  })
}

function methodNotAllowed(allow: string): Response {
  return new Response('', {
    status: 405,
    headers: { ...corsHeaders, allow },
  })
}

// Rutas que NO existen en este sitio estatico (el portfolio publico no tiene
// auth de agentes / OAuth). Devuelven 404 honesto en vez del SPA fallback
// (que serviria el HTML del home con 200, confundiendo a los agentes).
const NOT_FOUND_PATHS = new Set([
  '/.well-known/openid-configuration',
  '/.well-known/oauth-authorization-server',
  '/.well-known/oauth-protected-resource',
  '/auth.md',
])

function notFound(): Response {
  return new Response('', { status: 404, headers: { ...corsHeaders } })
}

async function tryMarkdownNegotiation(
  request: Request,
  env: Env,
): Promise<Response | null> {
  if (request.method !== 'GET') return null
  const accept = request.headers.get('accept') ?? ''
  if (!accept.toLowerCase().includes('text/markdown')) return null

  const url = new URL(request.url)
  const original = url.pathname
  let mdPath: string
  if (original === '/' || original === '') {
    mdPath = '/index.md'
  } else if (original.endsWith('/')) {
    mdPath = \`\${original}index.md\`
  } else if (original.endsWith('.md')) {
    mdPath = original
  } else {
    mdPath = \`\${original}/index.md\`
  }

  url.pathname = mdPath
  const mdRequest = new Request(url.toString(), {
    method: 'GET',
    headers: request.headers,
  })

  try {
    const mdResponse = await env.ASSETS.fetch(mdRequest)
    if (mdResponse.ok) {
      return new Response(mdResponse.body, {
        status: 200,
        headers: {
          'content-type': 'text/markdown; charset=UTF-8',
          'cache-control': 'public, max-age=3600',
          vary: 'Accept',
        },
      })
    }
  } catch {
    // env.ASSETS no disponible o fallo: continuar al asset original
  }
  return null
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url)

    // Routing por path
    if (url.pathname === '/mcp') {
      if (request.method === 'POST') return handleMcpPost(request)
      if (request.method === 'OPTIONS') return handleMcpOptions()
      return methodNotAllowed('POST, OPTIONS')
    }

    // RFC 9727 pide la ruta SIN .json; servimos ambas con el mismo linkset.
    if (
      url.pathname === '/.well-known/api-catalog' ||
      url.pathname === '/.well-known/api-catalog.json'
    ) {
      if (request.method !== 'GET') return methodNotAllowed('GET')
      return jsonResponse(apiCatalog, 'application/linkset+json')
    }

    if (url.pathname === '/.well-known/mcp/server-card.json') {
      if (request.method !== 'GET') return methodNotAllowed('GET')
      return jsonResponse(mcpServerCard, 'application/json')
    }

    if (url.pathname === '/.well-known/agent-card.json') {
      if (request.method !== 'GET') return methodNotAllowed('GET')
      return jsonResponse(agentCard, 'application/json')
    }

    if (url.pathname === '/.well-known/agent-skills/index.json') {
      if (request.method !== 'GET') return methodNotAllowed('GET')
      return jsonResponse(agentSkills, 'application/json')
    }

    // OAuth / OIDC: no existen en este sitio -> 404 honesto (no SPA fallback).
    if (NOT_FOUND_PATHS.has(url.pathname)) {
      return notFound()
    }

    // Content negotiation Accept: text/markdown
    const mdResponse = await tryMarkdownNegotiation(request, env)
    if (mdResponse !== null) return mdResponse

    // Default: asset estatico (incluye SPA fallback al index.html)
    return env.ASSETS.fetch(request)
  },
}
`
}
