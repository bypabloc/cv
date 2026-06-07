/**
 * @module validate-build-env
 * @description Guards de build-time para env vars criticas. Lanza error
 *   si una env var requerida esta vacia o es incoherente con `BASE_DOMAIN`.
 *
 *   Existe porque el bug original era SILENT: el build sin
 *   `PUBLIC_API_ENDPOINT` generaba un `data-api-endpoint` ausente y el
 *   script de tracking se autodesactivaba. Con estos guards, el build
 *   FALLA en CI antes de subir el artifact roto a Cloudflare Pages.
 *
 *   Estrategia "vacio + match contra BASE_DOMAIN":
 *   - Si la env var esta vacia -> error claro pidiendo setearla.
 *   - Si `BASE_DOMAIN` esta seteado (caso CI/deploy) -> la URL debe
 *     derivar de `BASE_DOMAIN`. Si no matchea, error con ambos valores.
 *   - Si `BASE_DOMAIN` NO esta seteado (caso build local sin env vars)
 *     -> solo se valida que no este vacia.
 */

/**
 * @function validateApiEndpoint
 * @description Garantiza que `apiEndpoint` no esta vacio y, si `BASE_DOMAIN`
 *   esta presente en el env, que matchea `https://api.${BASE_DOMAIN}`.
 *
 * @param {string | undefined} apiEndpoint - Valor de `PUBLIC_API_ENDPOINT`
 * @returns {string} Mismo valor (validado)
 * @throws {Error} Si esta vacio o no matchea `BASE_DOMAIN`
 *
 * @example
 *   const api = validateApiEndpoint(import.meta.env.PUBLIC_API_ENDPOINT)
 *   // throw "PUBLIC_API_ENDPOINT vacio..." si no esta seteada
 *   // throw "PUBLIC_API_ENDPOINT (...) no matchea BASE_DOMAIN..." si no coincide
 */
export function validateApiEndpoint(apiEndpoint: string | undefined): string {
  if (!apiEndpoint) {
    throw new Error(
      'PUBLIC_API_ENDPOINT vacio en el build. Setealo en el env del job ' +
        'de CI (deploy-apps.yml: vars.PUBLIC_API_ENDPOINT del GH Environment) ' +
        'o en docker/env/client/.{env} para builds locales.',
    )
  }
  // El endpoint NUNCA debe ser el host crudo de API Gateway
  // (`*.execute-api.<region>.amazonaws.com`): esos endpoints son efimeros
  // (se recrean/borran al re-provisionar) y un dia dejan de resolver
  // -> ERR_NAME_NOT_RESOLVED en el browser. SIEMPRE el dominio custom
  // estable `api.portfolio.<env>.the-full-stack.com`. Este guard aplica
  // en TODOS los builds, incluido local (un crudo borrado fue justo el
  // bug que rompio el admin/tracking en local).
  if (apiEndpoint.includes('.execute-api.')) {
    throw new Error(
      `PUBLIC_API_ENDPOINT (${apiEndpoint}) usa el host crudo de API ` +
        'Gateway (*.execute-api.*.amazonaws.com), que es efimero y puede ' +
        'dejar de resolver. Usa el dominio custom ' +
        'api.portfolio.<env>.the-full-stack.com. En docker/env/client/.local ' +
        'apunta al de dev: https://api.portfolio.dev.the-full-stack.com',
    )
  }
  const baseDomain = readBaseDomain()
  // El match estricto solo aplica en builds remotos (dev/stage/prod).
  // En local docker BASE_DOMAIN=localhost pero PUBLIC_API_ENDPOINT apunta
  // al API custom de dev (api.portfolio.dev.the-full-stack.com), no a
  // api.localhost (no existe un backend local). Por eso el match estricto
  // contra BASE_DOMAIN se omite para localhost, pero el guard anti-crudo
  // de arriba SI corre en local.
  if (baseDomain && !isLocalBuild(baseDomain)) {
    const expected = `https://api.${baseDomain}`
    if (apiEndpoint !== expected) {
      throw new Error(
        `PUBLIC_API_ENDPOINT (${apiEndpoint}) no matchea BASE_DOMAIN ` +
          `(${baseDomain}). Esperado: ${expected}. Revisa las GitHub ` +
          'Environment Variables del env destino (dev/stage/prod).',
      )
    }
  }
  return apiEndpoint
}

/**
 * Detecta builds de desarrollo local donde BASE_DOMAIN=localhost (caso
 * docker local). En esos builds, `api.localhost` no existe — el dev
 * apunta a un AWS API Gateway real. El match estricto NO aplica.
 */
function isLocalBuild(baseDomain: string): boolean {
  return baseDomain === 'localhost' || baseDomain.endsWith('.localhost')
}

/**
 * @function validateTurnstileSitekey
 * @description Garantiza que `sitekey` no esta vacio. Turnstile NO requiere
 *   match contra `BASE_DOMAIN` (cada widget tiene su propia allowlist de
 *   hostnames declarada en el dashboard Cloudflare).
 *
 * @param {string | undefined} sitekey - Valor de `PUBLIC_TURNSTILE_SITEKEY`
 * @returns {string} Mismo valor (validado)
 * @throws {Error} Si esta vacio
 *
 * @example
 *   const key = validateTurnstileSitekey(import.meta.env.PUBLIC_TURNSTILE_SITEKEY)
 */
export function validateTurnstileSitekey(sitekey: string | undefined): string {
  if (!sitekey) {
    throw new Error(
      'PUBLIC_TURNSTILE_SITEKEY vacio en el build. Setealo en el env del ' +
        'job de CI (deploy-apps.yml: vars.PUBLIC_TURNSTILE_SITEKEY del GH ' +
        'Environment, 1 widget por env) o en docker/env/client/.{env} ' +
        'para builds locales.',
    )
  }
  return sitekey
}

/**
 * Lee `BASE_DOMAIN` del env, soportando `import.meta.env` (Vite/Astro) y
 * `process.env` (Node). Devuelve string vacio si no esta seteado.
 */
function readBaseDomain(): string {
  type EnvBag = Record<string, string | undefined>
  const importMetaEnv = (import.meta as unknown as { env?: EnvBag }).env
  if (importMetaEnv) {
    const fromImportMeta = importMetaEnv.BASE_DOMAIN
    if (fromImportMeta !== undefined && fromImportMeta !== '') {
      return fromImportMeta
    }
  }
  if (typeof process !== 'undefined' && process.env) {
    const fromProcess = process.env.BASE_DOMAIN
    if (fromProcess !== undefined && fromProcess !== '') {
      return fromProcess
    }
  }
  return ''
}
