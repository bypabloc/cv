/**
 * @function obfuscateEmail
 * @description Codifica un email a base64 url-safe para anti-scraping básico.
 *   El script inline del componente lo decodifica solo en cliente.
 *
 *   Usa btoa/atob (disponibles en browser y Node 22+). El stack del portfolio
 *   garantiza Node >=22 (ver .nvmrc).
 *
 * @param email - Direccion de email a obfuscar
 * @returns Base64 sin padding
 *
 * @example
 *   obfuscateEmail('a@b.com')  // "YUBiLmNvbQ"
 */
export function obfuscateEmail(email: string): string {
  if (!email.includes('@')) {
    throw new Error('obfuscateEmail: input must contain "@"')
  }
  const bytes = new TextEncoder().encode(email)
  let binary = ''
  for (const b of bytes) {
    binary += String.fromCharCode(b)
  }
  return btoa(binary).replace(/=+$/u, '')
}

/**
 * @function deobfuscateEmail
 * @description Inversa de obfuscateEmail. Solo se usa en cliente (en el script
 *   inline del ContactLinks component).
 */
export function deobfuscateEmail(encoded: string): string {
  const padded = encoded + '='.repeat((4 - (encoded.length % 4)) % 4)
  const binary = atob(padded)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i)
  }
  return new TextDecoder().decode(bytes)
}
