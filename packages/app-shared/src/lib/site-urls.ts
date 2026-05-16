/**
 * @module site-urls
 * @description URLs absolutas de los 6 sitios del portfolio, derivadas de
 *   las env vars `BASE_DOMAIN` + `BASE_SCHEME` + `BASE_PORT` (+ `APEX_DOMAIN`
 *   opcional). Cualquier app puede leer estas URLs para enlazar a los otros
 *   sitios sin hardcodear el dominio.
 *
 *   Convencion:
 *   - Los 5 niches mapean a `<key>.<BASE_DOMAIN>`.
 *   - `generic` mapea al apex del ambiente:
 *     - Si `APEX_DOMAIN` esta definida, `generic` usa ese hostname. Esto
 *       cubre prod, donde los niches viven en `<niche>.portfolio.the-full-stack.com`
 *       (`BASE_DOMAIN=portfolio.the-full-stack.com`) pero el apex de generic
 *       es `the-full-stack.com` (`APEX_DOMAIN=the-full-stack.com`).
 *     - Si `APEX_DOMAIN` NO esta definida, `generic` usa `BASE_DOMAIN` tal
 *       cual. Esto cubre dev/stage/local, donde el apex del env coincide con
 *       el `BASE_DOMAIN` (`portfolio.dev.the-full-stack.com`, `localhost`).
 *   - `hub` es el selector multi-niche, NO es un niche del CV
 *     (Niche solo cubre fintech/architect/leader/vibe/generic).
 *   - Si `BASE_PORT` es el estandar del scheme (80 para http, 443 para https)
 *     o esta vacio, se omite del resultado.
 *
 *   Fallback (todas las env vacias o no definidas): produccion — niches en
 *   `<niche>.portfolio.the-full-stack.com`, apex generic en `the-full-stack.com`.
 *   Esto preserva el comportamiento de `pnpm run build` sin Docker.
 *
 * @example
 *   // BASE_DOMAIN=localhost BASE_SCHEME=http BASE_PORT=9970
 *   SITE_URLS.hub       // "http://hub.localhost:9970"
 *   SITE_URLS.generic   // "http://localhost:9970" (apex = BASE_DOMAIN)
 *
 *   // prod: BASE_DOMAIN=portfolio.the-full-stack.com APEX_DOMAIN=the-full-stack.com
 *   SITE_URLS.fintech   // "https://fintech.portfolio.the-full-stack.com"
 *   SITE_URLS.generic   // "https://the-full-stack.com" (apex via APEX_DOMAIN)
 */

/** Sitios desplegables del monorepo: los 5 niches + el hub selector. */
export type SiteKey =
  | 'generic'
  | 'hub'
  | 'fintech'
  | 'architect'
  | 'leader'
  | 'vibe'

// Defaults de prod: los niches cuelgan de `portfolio.the-full-stack.com`,
// el apex de generic es `the-full-stack.com`. Cubren `pnpm run build` sin
// env vars (build local de prueba) replicando produccion.
const DEFAULT_DOMAIN = 'portfolio.the-full-stack.com'
const DEFAULT_APEX = 'the-full-stack.com'
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
 *   Los 5 niches cuelgan de `BASE_DOMAIN`. `generic` usa `APEX_DOMAIN` si
 *   esta definida (caso prod, donde el apex difiere del dominio de los
 *   niches); si no, usa `BASE_DOMAIN` (caso dev/stage/local).
 *
 * @param {SiteKey} key - "generic" (apex) | "hub" | "fintech" | "architect" | "leader" | "vibe"
 * @returns {string} URL absoluta sin trailing slash
 */
export function buildSiteUrl(key: SiteKey): string {
  const baseDomain = readEnv('BASE_DOMAIN')
  const domain = baseDomain || DEFAULT_DOMAIN
  const scheme = readEnv('BASE_SCHEME') || DEFAULT_SCHEME
  const port = readEnv('BASE_PORT')
  // Apex de `generic`: APEX_DOMAIN si esta seteada. Si no:
  // - con BASE_DOMAIN definido (dev/stage/local) el apex = BASE_DOMAIN.
  // - sin ninguna env var, el apex = DEFAULT_APEX (fallback prod).
  const apexDomain =
    readEnv('APEX_DOMAIN') || (baseDomain ? domain : DEFAULT_APEX)

  const host = key === 'generic' ? apexDomain : `${key}.${domain}`
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
