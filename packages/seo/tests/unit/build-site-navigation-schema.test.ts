/**
 * @description Tests para buildSiteNavigationSchema. Emite un ItemList de
 *   schema.org SiteNavigationElement que ayuda a Google a entender la
 *   estructura del sitio (favorece los sitelinks).
 */
import { describe, expect, it } from 'vitest'
import { buildSiteNavigationSchema } from '../../src/lib/build-site-navigation-schema'

describe('buildSiteNavigationSchema', () => {
  it('Given nav items When build Then returns valid ItemList JSON-LD', () => {
    const ld = buildSiteNavigationSchema({
      siteUrl: 'https://the-full-stack.com',
      items: [
        { name: 'Home', path: '/' },
        { name: 'About', path: '/about' },
      ],
    })
    const parsed = JSON.parse(ld)
    expect(parsed['@context']).toBe('https://schema.org')
    expect(parsed['@type']).toBe('ItemList')
    expect(parsed.itemListElement).toHaveLength(2)
  })

  it('Given nav items When build Then each element is a SiteNavigationElement with absolute url', () => {
    const ld = buildSiteNavigationSchema({
      siteUrl: 'https://the-full-stack.com/',
      items: [{ name: 'Certificates', path: '/certificates' }],
    })
    const parsed = JSON.parse(ld)
    const first = parsed.itemListElement[0]
    expect(first['@type']).toBe('SiteNavigationElement')
    expect(first.position).toBe(1)
    expect(first.name).toBe('Certificates')
    expect(first.url).toBe('https://the-full-stack.com/certificates')
  })

  it('Given a root path When build Then resolves to siteUrl without double slash', () => {
    const ld = buildSiteNavigationSchema({
      siteUrl: 'https://the-full-stack.com/',
      items: [{ name: 'Home', path: '/' }],
    })
    const parsed = JSON.parse(ld)
    expect(parsed.itemListElement[0].url).toBe('https://the-full-stack.com/')
  })

  it('Given several items When build Then positions are sequential from 1', () => {
    const ld = buildSiteNavigationSchema({
      siteUrl: 'https://the-full-stack.com',
      items: [
        { name: 'Home', path: '/' },
        { name: 'About', path: '/about' },
        { name: 'Certificates', path: '/certificates' },
      ],
    })
    const parsed = JSON.parse(ld)
    const positions = parsed.itemListElement.map(
      (e: { position: number }) => e.position,
    )
    expect(positions).toEqual([1, 2, 3])
  })
})
