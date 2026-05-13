/**
 * @module theme-toggle
 * @description Lógica pura del theme toggle. Cicla system -> dark -> light.
 *   Persiste preferencia en localStorage. El BaseLayout debe correr applyTheme()
 *   ANTES de pintar para evitar FOUC.
 *
 *   API:
 *     applyTheme(value, doc?)   - aplica clase al <html>
 *     readStoredTheme(storage?) - lee preferencia persistida
 *     nextTheme(current)        - calcula el siguiente en el ciclo
 *     storeTheme(value, ...)    - persiste y aplica
 */

export type Theme = 'system' | 'dark' | 'light'

const STORAGE_KEY = 'theme'
const THEMES: Theme[] = ['system', 'dark', 'light']

/**
 * @function isTheme
 * @description Type guard.
 */
export function isTheme(value: unknown): value is Theme {
  return typeof value === 'string' && (THEMES as string[]).includes(value)
}

/**
 * @function readStoredTheme
 * @description Lee la preferencia guardada. Default 'system' si no hay nada.
 */
export function readStoredTheme(storage?: Storage): Theme {
  try {
    const s = storage ?? globalThis.localStorage
    const raw = s?.getItem(STORAGE_KEY)
    return isTheme(raw) ? raw : 'system'
  } catch {
    return 'system'
  }
}

/**
 * @function applyTheme
 * @description Aplica el theme al <html> via clases .dark / .light.
 *   - system: ambas removidas (sigue prefers-color-scheme via CSS)
 *   - dark: agrega .dark, remueve .light
 *   - light: agrega .light, remueve .dark
 */
export function applyTheme(value: Theme, doc?: Document): void {
  const d = doc ?? globalThis.document
  if (!d) return
  const root = d.documentElement
  root.classList.remove('dark', 'light')
  if (value === 'dark') root.classList.add('dark')
  else if (value === 'light') root.classList.add('light')
  root.dataset.theme = value
}

/**
 * @function nextTheme
 * @description Ciclo: system -> dark -> light -> system.
 */
export function nextTheme(current: Theme): Theme {
  const idx = THEMES.indexOf(current)
  const next = idx === -1 ? 0 : (idx + 1) % THEMES.length
  return THEMES[next] as Theme
}

/**
 * @function storeTheme
 * @description Persiste a localStorage y aplica el theme.
 */
export function storeTheme(
  value: Theme,
  storage?: Storage,
  doc?: Document,
): void {
  try {
    const s = storage ?? globalThis.localStorage
    s?.setItem(STORAGE_KEY, value)
  } catch {
    /* storage unavailable (SSR / private mode); ignore */
  }
  applyTheme(value, doc)
}
