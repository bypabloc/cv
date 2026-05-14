/**
 * @description Tests para readUrl() y syncUrl(). Cubre AC-11 (URL update via
 *   history.replaceState) y AC-19 (filtros persisten al cambiar locale).
 *
 *   Usa happy-dom (configurado en vitest.config) para tener window/history.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { readUrl, syncUrl } from '../../src/sync-url'
import { emptyFilterState } from '../../src/types'

describe('readUrl [AC-11, AC-12]', () => {
  beforeEach(() => {
    window.history.replaceState({}, '', '/about')
  })

  it('Given URL with no query params Then returns empty state', () => {
    expect(readUrl()).toEqual(emptyFilterState())
  })

  it('Given URL with ?tech=Vue Then returns state with tech=[Vue]', () => {
    window.history.replaceState({}, '', '/about?tech=Vue')
    expect(readUrl().tech).toEqual(['Vue'])
  })

  it('Given URL with full query Then parses all dimensions', () => {
    window.history.replaceState(
      {},
      '',
      '/about?tech=Vue,Django&seniority=senior&type=web',
    )
    const state = readUrl()
    expect(state.tech).toEqual(['Vue', 'Django'])
    expect(state.seniority).toEqual(['senior'])
    expect(state.projectType).toEqual(['web'])
  })
})

describe('syncUrl [AC-11, AC-13]', () => {
  let replaceStateSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    window.history.replaceState({}, '', '/about')
    replaceStateSpy = vi.spyOn(window.history, 'replaceState')
  })

  afterEach(() => {
    replaceStateSpy.mockRestore()
  })

  it('Given filters state Then calls replaceState with new URL', () => {
    syncUrl({ ...emptyFilterState(), tech: ['Vue'] })
    expect(replaceStateSpy).toHaveBeenCalledOnce()
    const [, , url] = replaceStateSpy.mock.calls[0] as [
      unknown,
      unknown,
      string,
    ]
    expect(url).toContain('tech=Vue')
    expect(url).toContain('/about')
  })

  it('Given empty state Then URL has no query string [AC-13]', () => {
    syncUrl(emptyFilterState())
    const [, , url] = replaceStateSpy.mock.calls[0] as [
      unknown,
      unknown,
      string,
    ]
    expect(url).toBe('/about')
  })

  it('Given multi-dimension state Then URL has all params', () => {
    syncUrl({
      ...emptyFilterState(),
      tech: ['Vue'],
      seniority: ['senior'],
      hideConfidential: true,
    })
    const [, , url] = replaceStateSpy.mock.calls[0] as [
      unknown,
      unknown,
      string,
    ]
    expect(url).toContain('tech=Vue')
    expect(url).toContain('seniority=senior')
    expect(url).toContain('hideConfidential=1')
  })

  it('Given path with hash Then preserves hash', () => {
    window.history.replaceState({}, '', '/about#section')
    syncUrl({ ...emptyFilterState(), tech: ['Vue'] })
    // syncUrl es la ultima llamada (la 1ra fue el setup del hash).
    const lastCall = replaceStateSpy.mock.calls.at(-1) as [
      unknown,
      unknown,
      string,
    ]
    const [, , url] = lastCall
    expect(url).toContain('#section')
  })

  it('Given path /en/about Then preserves locale path [AC-19]', () => {
    // El primer replaceState lo hace el setup del path (consumido por spy).
    window.history.replaceState({}, '', '/en/about')
    syncUrl({ ...emptyFilterState(), tech: ['Vue'] })
    // La llamada de syncUrl es la SEGUNDA (la primera fue el setup del path).
    const lastCall = replaceStateSpy.mock.calls.at(-1) as [
      unknown,
      unknown,
      string,
    ]
    const [, , url] = lastCall
    expect(url).toContain('/en/about')
    expect(url).toContain('tech=Vue')
  })
})
