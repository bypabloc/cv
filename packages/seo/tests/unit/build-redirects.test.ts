/**
 * @description Tests para buildRedirects. Genera el contenido de
 *   _redirects de Cloudflare Pages con 2 reglas activas:
 *   1. alias /sitemap.xml -> sitemap-index.xml (301)
 *   2. rewrite 200 /.well-known/api-catalog -> .json (evita SPA fallback)
 */
import { describe, expect, it } from 'vitest'

import { buildRedirects } from '../../src/lib/build-redirects'

describe('buildRedirects', () => {
  it('Given se invoca When build Then incluye redirect 301 sitemap.xml -> sitemap-index.xml', () => {
    const out = buildRedirects()

    expect(out).toContain('/sitemap.xml /sitemap-index.xml 301')
  })

  it('Given se invoca When build Then incluye rewrite 200 api-catalog -> .json', () => {
    const out = buildRedirects()

    expect(out).toContain(
      '/.well-known/api-catalog /.well-known/api-catalog.json 200',
    )
  })

  it('Given se invoca When inspecciono Then termina con newline (req Cloudflare Pages)', () => {
    const out = buildRedirects()

    expect(out.endsWith('\n')).toBe(true)
  })

  it('Given se invoca When cuento reglas Then hay exactamente 2 reglas (sin lineas vacias intermedias)', () => {
    const out = buildRedirects()
    const reglas = out.split('\n').filter((linea) => linea.trim().length > 0)

    expect(reglas).toEqual([
      '/sitemap.xml /sitemap-index.xml 301',
      '/.well-known/api-catalog /.well-known/api-catalog.json 200',
    ])
  })
})
