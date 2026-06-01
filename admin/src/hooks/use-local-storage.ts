'use client'

import { useCallback, useEffect, useState } from 'react'

/**
 * @function useLocalStorage
 * @description Estado sincronizado con localStorage (type-safe, JSON).
 * @param {string} key - clave de localStorage
 * @param {T} initialValue - valor por defecto
 * @returns {[T, (v: T) => void]} valor + setter persistente
 */
export function useLocalStorage<T>(
  key: string,
  initialValue: T,
): [T, (value: T) => void] {
  const [value, setValue] = useState<T>(initialValue)

  useEffect(() => {
    if (typeof window === 'undefined') return
    try {
      const raw = window.localStorage.getItem(key)
      if (raw !== null) setValue(JSON.parse(raw) as T)
    } catch {
      // valor por defecto ya seteado
    }
  }, [key])

  const setStored = useCallback(
    (next: T) => {
      setValue(next)
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(key, JSON.stringify(next))
      }
    },
    [key],
  )

  return [value, setStored]
}
