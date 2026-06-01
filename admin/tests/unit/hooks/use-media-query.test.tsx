import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { useMediaQuery } from '@/hooks/use-media-query'

/**
 * @module tests/unit/hooks/use-media-query
 * @description Verifica useMediaQuery: estado inicial desde matchMedia, el
 *   handler 'change' que actualiza, y el cleanup que remueve el listener.
 */

type Handler = (e: MediaQueryListEvent) => void

function installMatchMedia(initial: boolean) {
  let registered: Handler | null = null
  const removeEventListener = vi.fn()
  const mql = {
    matches: initial,
    media: '(min-width: 1024px)',
    addEventListener: (_type: string, h: Handler) => {
      registered = h
    },
    removeEventListener,
  }
  const matchMedia = vi.fn(() => mql as unknown as MediaQueryList)
  ;(window as unknown as { matchMedia: typeof matchMedia }).matchMedia =
    matchMedia
  return {
    emitChange: (matches: boolean) =>
      registered?.({ matches } as MediaQueryListEvent),
    removeEventListener,
  }
}

describe('useMediaQuery', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('Given matchMedia true When render Then matches es true', () => {
    // Arrange
    installMatchMedia(true)

    // Act
    const { result } = renderHook(() => useMediaQuery('(min-width: 1024px)'))

    // Assert
    expect(result.current).toBe(true)
  })

  it('Given un change event When emite Then actualiza matches', () => {
    // Arrange
    const { emitChange } = installMatchMedia(false)
    const { result } = renderHook(() => useMediaQuery('(min-width: 1024px)'))

    // Act
    act(() => {
      emitChange(true)
    })

    // Assert
    expect(result.current).toBe(true)
  })

  it('Given un unmount When ocurre Then remueve el listener (cleanup)', () => {
    // Arrange
    const { removeEventListener } = installMatchMedia(false)
    const { unmount } = renderHook(() => useMediaQuery('(min-width: 1024px)'))

    // Act
    unmount()

    // Assert
    expect(removeEventListener).toHaveBeenCalledTimes(1)
  })
})
