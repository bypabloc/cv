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
    // El effect solo corre en cliente (React no ejecuta effects en SSR), por
    // lo que window siempre existe aqui.
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
      // El setter solo se invoca desde un event handler cliente: window existe.
      window.localStorage.setItem(key, JSON.stringify(next))
    },
    [key],
  )

  return [value, setStored]
}
