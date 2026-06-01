import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useDebounce } from '@/hooks/use-debounce'

/**
 * @module tests/unit/hooks/use-debounce
 * @description Verifica que useDebounce devuelve el valor tras `delay` ms sin
 *   cambios, usando fake timers.
 */

describe('useDebounce', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('Given un valor inicial When render Then devuelve el valor de inmediato', () => {
    // Arrange + Act
    const { result } = renderHook(() => useDebounce('hola', 300))

    // Assert
    expect(result.current).toBe('hola')
  })

  it('Given un cambio When pasan menos ms que delay Then conserva el viejo', () => {
    // Arrange
    const { result, rerender } = renderHook(
      ({ value }: { value: string }) => useDebounce(value, 300),
      { initialProps: { value: 'a' } },
    )

    // Act
    rerender({ value: 'b' })
    act(() => {
      vi.advanceTimersByTime(200)
    })

    // Assert
    expect(result.current).toBe('a')
  })

  it('Given un cambio When pasa el delay completo Then devuelve el nuevo valor', () => {
    // Arrange
    const { result, rerender } = renderHook(
      ({ value }: { value: string }) => useDebounce(value, 300),
      { initialProps: { value: 'a' } },
    )

    // Act
    rerender({ value: 'b' })
    act(() => {
      vi.advanceTimersByTime(300)
    })

    // Assert
    expect(result.current).toBe('b')
  })

  it('Given un delay por defecto When no se pasa Then usa 300ms', () => {
    // Arrange
    const { result, rerender } = renderHook(
      ({ value }: { value: number }) => useDebounce(value),
      { initialProps: { value: 1 } },
    )

    // Act
    rerender({ value: 2 })
    act(() => {
      vi.advanceTimersByTime(300)
    })

    // Assert
    expect(result.current).toBe(2)
  })
})
