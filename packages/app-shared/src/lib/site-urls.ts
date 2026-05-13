/**
 * @module site-urls
 * @description URLs absolutas de los 6 sitios del portfolio, derivadas de
 *   las env vars `BASE_DOMAIN` + `BASE_SCHEME` + `BASE_PORT`. Cualquier app
 *   puede leer estas URLs para enlazar a los otros sitios sin hardcodear el
 *   dominio de produccion.
 *
 *   Convencion:
 *   - `generic` mapea al apex (sin subdominio): `https://the-full-stack.com`
 *   - `hub` es el selector multi-niche, NO es un niche del CV
 *     (Niche solo cubre fintech/architect/leader/vibe/generic)
 *   - El resto mapea a `<key>.<BASE_DOMAIN>`
 *   - Si `BASE_PORT` es el estandar del scheme (80 para http, 443 para https)
 *     o esta vacio, se omite del resultado.
 *
 *   Fallback (todas las env vacias o no definidas): produccion (the-full-stack.com).
 *   Esto preserva el comportamiento de `pnpm run build` sin Docker.
 *
 * @example
 *   // BASE_DOMAIN=localhost BASE_SCHEME=http BASE_PORT=9970
 *   SITE_URLS.hub       // "http://hub.localhost:9970"
 *   buildSiteUrl('hub') // idem
 *
 *   // BASE_DOMAIN=the-full-stack.com BASE_SCHEME=https BASE_PORT=
 *   SITE_URLS.fintech   // "https://fintech.the-full-stack.com"
 *   SITE_URLS.generic   // "https://the-full-stack.com" (apex, sin subdominio)
 */

/** Sitios desplegables del monorepo: los 5 niches + el hub selector. */
export type SiteKey =
  | 'generic'
  | 'hub'
  | 'fintech'
  | 'architect'
  | 'leader'
  | 'vibe'

const DEFAULT_DOMAIN = 'the-full-stack.com'
const DEFAULT_SCHEME = 'https'

type EnvBag = Record<string, string | undefined>

function readEnv(name: string): string {
  // Soporta tanto Vite/Astro (`import.meta.env`) como Node (`process.env`)
  // sin depender de un runtime especifico.
  const importMetaEnv = (import.meta as unknown as { env?: EnvBag }).env
  if (importMetaEnv) {
    const fromImportMeta = importMetaEnv[name]
    if (fromImportMeta !== undefined && fromImportMeta !== '') {
      return fromImportMeta
    }
  }
  if (typeof process !== 'undefined' && process.env) {
    const fromProcess = process.env[name]
    if (fromProcess !== undefined && fromProcess !== '') {
      return fromProcess
    }
  }
  return ''
}

function isStandardPort(scheme: string, port: string): boolean {
  return (
    (scheme === 'http' && port === '80') ||
    (scheme === 'https' && port === '443')
  )
}

/**
 * @function buildSiteUrl
 * @description Construye la URL absoluta del sitio para un site key dado.
 *
 * @param {SiteKey} key - "generic" (apex) | "hub" | "fintech" | "architect" | "leader" | "vibe"
 * @returns {string} URL absoluta sin trailing slash
 */
export function buildSiteUrl(key: SiteKey): string {
  const domain = readEnv('BASE_DOMAIN') || DEFAULT_DOMAIN
  const scheme = readEnv('BASE_SCHEME') || DEFAULT_SCHEME
  const port = readEnv('BASE_PORT')

  const host = key === 'generic' ? domain : `${key}.${domain}`
  const portSuffix = port && !isStandardPort(scheme, port) ? `:${port}` : ''

  return `${scheme}://${host}${portSuffix}`
}

/**
 * @const SITE_URLS
 * @description Mapa estatico `SiteKey -> URL absoluta`. Evaluado al cargar
 *   el modulo (build time en Astro). Util para iterar todos los sitios.
 */
export const SITE_URLS: Record<SiteKey, string> = {
  generic: buildSiteUrl('generic'),
  hub: buildSiteUrl('hub'),
  fintech: buildSiteUrl('fintech'),
  architect: buildSiteUrl('architect'),
  leader: buildSiteUrl('leader'),
  vibe: buildSiteUrl('vibe'),
}
