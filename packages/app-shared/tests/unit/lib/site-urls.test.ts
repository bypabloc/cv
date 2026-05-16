/**
 * @description Tests para SITE_URLS y buildSiteUrl.
 *   Cubre los 4 escenarios de env (local, prod, fallback, puertos estandar)
 *   y mapea 1:1 a los AC del plan.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

describe('SITE_URLS', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  afterEach(() => {
    vi.unstubAllEnvs()
  })

  describe('local env (BASE_DOMAIN=localhost, BASE_SCHEME=http, BASE_PORT=9970)', () => {
    beforeEach(() => {
      vi.stubEnv('BASE_DOMAIN', 'localhost')
      vi.stubEnv('BASE_SCHEME', 'http')
      vi.stubEnv('BASE_PORT', '9970')
    })

    it('Given env local When read SITE_URLS.generic Then returns "http://localhost:9970" [AC-1]', async () => {
      const { SITE_URLS } = await import('../../../src/lib/site-urls')
      expect(SITE_URLS.generic).toBe('http://localhost:9970')
    })

    it('Given env local When read SITE_URLS.hub Then returns "http://hub.localhost:9970" [AC-1]', async () => {
      const { SITE_URLS } = await import('../../../src/lib/site-urls')
      expect(SITE_URLS.hub).toBe('http://hub.localhost:9970')
    })

    it('Given env local When read SITE_URLS.fintech Then returns "http://fintech.localhost:9970" [AC-1]', async () => {
      const { SITE_URLS } = await import('../../../src/lib/site-urls')
      expect(SITE_URLS.fintech).toBe('http://fintech.localhost:9970')
    })

    it('Given env local When read SITE_URLS.architect Then returns "http://architect.localhost:9970" [AC-1]', async () => {
      const { SITE_URLS } = await import('../../../src/lib/site-urls')
      expect(SITE_URLS.architect).toBe('http://architect.localhost:9970')
    })

    it('Given env local When read SITE_URLS.leader Then returns "http://leader.localhost:9970" [AC-1]', async () => {
      const { SITE_URLS } = await import('../../../src/lib/site-urls')
      expect(SITE_URLS.leader).toBe('http://leader.localhost:9970')
    })

    it('Given env local When read SITE_URLS.vibe Then returns "http://vibe.localhost:9970" [AC-1]', async () => {
      const { SITE_URLS } = await import('../../../src/lib/site-urls')
      expect(SITE_URLS.vibe).toBe('http://vibe.localhost:9970')
    })
  })

  describe('prod env component-based (BASE_DOMAIN=portfolio.the-full-stack.com, APEX_DOMAIN=the-full-stack.com)', () => {
    beforeEach(() => {
      vi.stubEnv('BASE_DOMAIN', 'portfolio.the-full-stack.com')
      vi.stubEnv('APEX_DOMAIN', 'the-full-stack.com')
      vi.stubEnv('BASE_SCHEME', 'https')
      vi.stubEnv('BASE_PORT', '')
    })

    it('Given env prod When read SITE_URLS.generic Then returns the apex "https://the-full-stack.com" [AC-2]', async () => {
      const { SITE_URLS } = await import('../../../src/lib/site-urls')
      expect(SITE_URLS.generic).toBe('https://the-full-stack.com')
    })

    it('Given env prod When read SITE_URLS.hub Then returns "https://hub.portfolio.the-full-stack.com" [AC-2]', async () => {
      const { SITE_URLS } = await import('../../../src/lib/site-urls')
      expect(SITE_URLS.hub).toBe('https://hub.portfolio.the-full-stack.com')
    })

    it('Given env prod When read SITE_URLS.fintech Then returns "https://fintech.portfolio.the-full-stack.com" [AC-2]', async () => {
      const { SITE_URLS } = await import('../../../src/lib/site-urls')
      expect(SITE_URLS.fintech).toBe(
        'https://fintech.portfolio.the-full-stack.com',
      )
    })

    it('Given env prod When read SITE_URLS.vibe Then returns "https://vibe.portfolio.the-full-stack.com" [AC-2]', async () => {
      const { SITE_URLS } = await import('../../../src/lib/site-urls')
      expect(SITE_URLS.vibe).toBe('https://vibe.portfolio.the-full-stack.com')
    })
  })

  describe('fallback (no env vars defined)', () => {
    beforeEach(() => {
      vi.stubEnv('BASE_DOMAIN', '')
      vi.stubEnv('BASE_SCHEME', '')
      vi.stubEnv('BASE_PORT', '')
    })

    it('Given no env vars When read SITE_URLS.generic Then falls back to the apex "https://the-full-stack.com" [AC-3]', async () => {
      const { SITE_URLS } = await import('../../../src/lib/site-urls')
      expect(SITE_URLS.generic).toBe('https://the-full-stack.com')
    })

    it('Given no env vars When read SITE_URLS.vibe Then falls back to "https://vibe.portfolio.the-full-stack.com" [AC-3]', async () => {
      const { SITE_URLS } = await import('../../../src/lib/site-urls')
      expect(SITE_URLS.vibe).toBe('https://vibe.portfolio.the-full-stack.com')
    })
  })

  describe('standard ports omitted', () => {
    it('Given BASE_PORT=80 + BASE_SCHEME=http When read SITE_URLS.generic Then omits port [AC-4]', async () => {
      vi.stubEnv('BASE_DOMAIN', 'example.local')
      vi.stubEnv('BASE_SCHEME', 'http')
      vi.stubEnv('BASE_PORT', '80')
      const { SITE_URLS } = await import('../../../src/lib/site-urls')
      expect(SITE_URLS.generic).toBe('http://example.local')
    })

    it('Given BASE_PORT=443 + BASE_SCHEME=https When read SITE_URLS.hub Then omits port [AC-4]', async () => {
      vi.stubEnv('BASE_DOMAIN', 'example.com')
      vi.stubEnv('BASE_SCHEME', 'https')
      vi.stubEnv('BASE_PORT', '443')
      const { SITE_URLS } = await import('../../../src/lib/site-urls')
      expect(SITE_URLS.hub).toBe('https://hub.example.com')
    })

    it('Given non-standard port When read SITE_URLS.fintech Then includes port', async () => {
      vi.stubEnv('BASE_DOMAIN', 'staging.example.com')
      vi.stubEnv('BASE_SCHEME', 'https')
      vi.stubEnv('BASE_PORT', '8443')
      const { SITE_URLS } = await import('../../../src/lib/site-urls')
      expect(SITE_URLS.fintech).toBe('https://fintech.staging.example.com:8443')
    })
  })
})

describe('buildSiteUrl', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  afterEach(() => {
    vi.unstubAllEnvs()
  })

  it('Given niche "hub" + env local When call buildSiteUrl Then returns same as SITE_URLS.hub', async () => {
    vi.stubEnv('BASE_DOMAIN', 'localhost')
    vi.stubEnv('BASE_SCHEME', 'http')
    vi.stubEnv('BASE_PORT', '9970')
    const { buildSiteUrl } = await import('../../../src/lib/site-urls')
    expect(buildSiteUrl('hub')).toBe('http://hub.localhost:9970')
  })

  it('Given niche "generic" + env prod When call buildSiteUrl Then returns apex domain', async () => {
    vi.stubEnv('BASE_DOMAIN', 'the-full-stack.com')
    vi.stubEnv('BASE_SCHEME', 'https')
    vi.stubEnv('BASE_PORT', '')
    const { buildSiteUrl } = await import('../../../src/lib/site-urls')
    expect(buildSiteUrl('generic')).toBe('https://the-full-stack.com')
  })
})
