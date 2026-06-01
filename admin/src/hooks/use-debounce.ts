'use client'

import { useEffect, useState } from 'react'

/**
 * @function useDebounce
 * @description Devuelve el valor tras `delay` ms sin cambios.
 * @param {T} value - Valor a debouncear
 * @param {number} delay - ms de espera (default 300)
 * @returns {T} valor debounceado
 */
export function useDebounce<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(id)
  }, [value, delay])
  return debounced
}
