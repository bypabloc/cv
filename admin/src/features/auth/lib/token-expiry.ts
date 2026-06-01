import { jwtDecode } from 'jwt-decode'

/**
 * @module token-expiry
 * @description Helpers para leer el `exp` de un JWT (sin verificar firma;
 *   eso lo hace el backend). Usados por el auth timer y el callback.
 */

/**
 * @function getJwtExpiry
 * @param {string} token - JWT
 * @returns {number | null} epoch ms del exp, o null si no decodea
 */
export function getJwtExpiry(token: string): number | null {
  try {
    const { exp } = jwtDecode<{ exp: number }>(token)
    return exp * 1000
  } catch {
    return null
  }
}

/**
 * @function isJwtExpired
 * @param {string} token - JWT
 * @returns {boolean} true si expiro o no decodea
 */
export function isJwtExpired(token: string): boolean {
  const exp = getJwtExpiry(token)
  if (exp === null) return true
  return Date.now() >= exp
}
