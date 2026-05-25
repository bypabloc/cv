/**
 * @description Tests para buildRedirects. Genera el contenido de
 *   _redirects de Cloudflare Pages con alias /sitemap.xml -> sitemap-index.
 */
import { describe, expect, it } from 'vitest'

import { buildRedirects } from '../../src/lib/build-redirects'

describe('buildRedirects', () => {
  it('Given se invoca When build Then redirige sitemap.xml a sitemap-index.xml con 301', () => {
    const out = buildRedirects()

    expect(out).toBe('/sitemap.xml /sitemap-index.xml 301\n')
  })

  it('Given se invoca When inspecciono Then termina con newline (req Cloudflare Pages)', () => {
    const out = buildRedirects()

    expect(out.endsWith('\n')).toBe(true)
  })
})
