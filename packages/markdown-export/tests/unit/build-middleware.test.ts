/**
 * @description Tests para buildMarkdownMiddleware — genera el TS source
 *   de la Pages Function `_middleware.ts` que hace content negotiation
 *   para Accept: text/markdown.
 */
import { describe, expect, it } from 'vitest'

import { buildMarkdownMiddleware } from '../../src/lib/build-middleware'

describe('buildMarkdownMiddleware', () => {
  it('Given se invoca When inspecciono el output Then expone onRequest', () => {
    const out = buildMarkdownMiddleware()

    expect(out).toContain('export const onRequest')
    expect(out).toContain('Promise<Response>')
  })

  it('Given se invoca When inspecciono Then implementa el check de Accept: text/markdown', () => {
    const out = buildMarkdownMiddleware()

    expect(out).toContain("'accept'")
    expect(out).toContain("'text/markdown'")
    expect(out).toContain('.toLowerCase()')
  })

  it('Given se invoca When inspecciono Then resuelve / -> /index.md', () => {
    const out = buildMarkdownMiddleware()

    expect(out).toContain("/index.md'")
  })

  it('Given se invoca When inspecciono Then maneja /<path>/ -> /<path>/index.md', () => {
    const out = buildMarkdownMiddleware()

    expect(out).toContain('index.md')
    expect(out).toContain('endsWith(')
  })

  it('Given se invoca When inspecciono Then hace fetch via env.ASSETS', () => {
    const out = buildMarkdownMiddleware()

    expect(out).toContain('env.ASSETS.fetch')
  })

  it('Given se invoca When inspecciono Then setea Content-Type text/markdown en la response', () => {
    const out = buildMarkdownMiddleware()

    expect(out).toContain('text/markdown; charset=UTF-8')
  })

  it('Given se invoca When inspecciono Then incluye Vary: Accept', () => {
    const out = buildMarkdownMiddleware()

    expect(out).toContain('vary')
    expect(out).toMatch(/Accept/)
  })

  it('Given se invoca When inspecciono Then NO procesa requests POST/PUT/DELETE (solo GET)', () => {
    const out = buildMarkdownMiddleware()

    expect(out).toContain("request.method !== 'GET'")
  })

  it('Given se invoca When inspecciono Then en fallo cae al next() (no rompe la request)', () => {
    const out = buildMarkdownMiddleware()

    expect(out).toContain('next()')
  })

  it('Given se invoca When inspecciono Then es deterministico (mismo output multiples veces)', () => {
    const out1 = buildMarkdownMiddleware()
    const out2 = buildMarkdownMiddleware()

    expect(out1).toBe(out2)
  })
})
