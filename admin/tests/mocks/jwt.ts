/**
 * @module tests/mocks/jwt
 * @description Helper para generar JWTs fake (no firmados) en tests/mocks.
 *   El frontend NO verifica firma (solo lee el `exp`), asi que basta con un
 *   header.payload.fakesig bien formado.
 */

export function nowSec(): number {
  return Math.floor(Date.now() / 1000)
}

function base64UrlEncode(s: string): string {
  return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

/**
 * @function makeJwt
 * @param {object} payload - claims (incluir `exp` en segundos)
 * @returns {string} JWT fake `header.payload.fakesignature`
 */
export function makeJwt(payload: Record<string, unknown>): string {
  const header = base64UrlEncode(JSON.stringify({ alg: 'HS256', typ: 'JWT' }))
  const body = base64UrlEncode(
    JSON.stringify({ exp: nowSec() + 900, ...payload }),
  )
  return `${header}.${body}.fakesignature`
}
