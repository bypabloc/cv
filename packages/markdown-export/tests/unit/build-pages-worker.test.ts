/**
 * @description Tests para buildPagesWorker — TS source de _worker.js
 *   (Cloudflare Pages Advanced Mode). Single Worker monolitico que
 *   maneja MCP, .well-known/*.json, Accept: text/markdown y fallback
 *   a assets estaticos.
 */
import { describe, expect, it } from 'vitest'

import { buildPagesWorker } from '../../src/lib/build-pages-worker'

describe('buildPagesWorker', () => {
  it('Given se invoca When inspecciono Then exporta default fetch handler', () => {
    const out = buildPagesWorker()

    expect(out).toContain('export default')
    expect(out).toContain('async fetch(request: Request')
  })

  it('Given se invoca When inspecciono Then importa createSnapshotProvider y handleRequest de @portfolio/mcp', () => {
    const out = buildPagesWorker()

    expect(out).toContain("from '@portfolio/mcp'")
    expect(out).toContain('createSnapshotProvider')
    expect(out).toContain('handleRequest')
  })

  it('Given se invoca When inspecciono Then importa los 3 JSON snapshots del _worker-data', () => {
    const out = buildPagesWorker()

    expect(out).toContain("from './_worker-data/cv-snapshot.json'")
    expect(out).toContain("from './_worker-data/api-catalog.json'")
    expect(out).toContain("from './_worker-data/mcp-server-card.json'")
  })

  it('Given se invoca When inspecciono Then maneja POST /mcp y OPTIONS /mcp', () => {
    const out = buildPagesWorker()

    expect(out).toContain("url.pathname === '/mcp'")
    expect(out).toContain("request.method === 'POST'")
    expect(out).toContain("request.method === 'OPTIONS'")
  })

  it('Given se invoca When inspecciono Then maneja GET /.well-known/api-catalog.json', () => {
    const out = buildPagesWorker()

    expect(out).toContain("'/.well-known/api-catalog.json'")
    expect(out).toContain('application/linkset+json')
  })

  it('Given se invoca When inspecciono Then maneja GET /.well-known/mcp/server-card.json', () => {
    const out = buildPagesWorker()

    expect(out).toContain("'/.well-known/mcp/server-card.json'")
  })

  it('Given se invoca When inspecciono Then incluye content negotiation Accept: text/markdown', () => {
    const out = buildPagesWorker()

    expect(out).toContain("'text/markdown'")
    expect(out).toContain('tryMarkdownNegotiation')
    expect(out).toContain('vary')
  })

  it('Given se invoca When inspecciono Then el default es env.ASSETS.fetch (asset estatico + SPA fallback)', () => {
    const out = buildPagesWorker()

    expect(out).toContain('return env.ASSETS.fetch(request)')
  })

  it('Given se invoca When inspecciono Then devuelve 405 para metodos no soportados de los endpoints custom', () => {
    const out = buildPagesWorker()

    expect(out).toContain('methodNotAllowed')
    expect(out).toContain('status: 405')
  })

  it('Given se invoca When inspecciono Then es deterministico', () => {
    const out1 = buildPagesWorker()
    const out2 = buildPagesWorker()

    expect(out1).toBe(out2)
  })
})
