/**
 * @description Tests para buildRedirects. Genera el contenido de
 *   _redirects de Cloudflare Pages con 1 regla activa:
 *   1. alias /sitemap.xml -> sitemap-index.xml (301)
 *
 *   El rewrite 200 /.well-known/api-catalog -> .json se ELIMINO en
 *   ai-audit-level-4: los archivos en .well-known/ no se uploadean
 *   (regla de dotfiles); ahora los sirven Pages Functions.
 */
import { describe, expect, it } from 'vitest'

import { buildRedirects } from '../../src/lib/build-redirects'

describe('buildRedirects', () => {
  it('Given se invoca When build Then incluye redirect 301 sitemap.xml -> sitemap-index.xml', () => {
    const out = buildRedirects()

    expect(out).toContain('/sitemap.xml /sitemap-index.xml 301')
  })

  it('Given se invoca When build Then NO incluye el rewrite legacy de api-catalog', () => {
    const out = buildRedirects()

    expect(out).not.toContain('/.well-known/api-catalog')
  })

  it('Given se invoca When inspecciono Then termina con newline (req Cloudflare Pages)', () => {
    const out = buildRedirects()

    expect(out.endsWith('\n')).toBe(true)
  })

  it('Given se invoca When cuento reglas Then hay exactamente 1 regla', () => {
    const out = buildRedirects()
    const reglas = out.split('\n').filter((linea) => linea.trim().length > 0)

    expect(reglas).toEqual(['/sitemap.xml /sitemap-index.xml 301'])
  })
})
