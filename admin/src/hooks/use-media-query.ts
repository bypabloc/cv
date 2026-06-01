'use client'

import { useEffect, useState } from 'react'

/**
 * @function useMediaQuery
 * @description Reactivo a un media query (ej. '(min-width: 1024px)').
 * @param {string} query - Media query CSS
 * @returns {boolean} si el query matchea actualmente
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false)
  useEffect(() => {
    if (typeof window === 'undefined') return
    const mql = window.matchMedia(query)
    setMatches(mql.matches)
    const handler = (e: MediaQueryListEvent) => setMatches(e.matches)
    mql.addEventListener('change', handler)
    return () => mql.removeEventListener('change', handler)
  }, [query])
  return matches
}
