/**
 * @module build-website-schema
 * @description Genera JSON-LD schema.org `WebSite` para el `<head>` del
 *   home. Complementa al `ProfilePage` existente: dice "el nombre del
 *   sitio" + idiomas soportados a crawlers IA y Google.
 *
 *   Si en el futuro el sitio tiene buscador interno, se puede agregar
 *   `potentialAction: SearchAction`. Por ahora NO aplica.
 */

interface WebSiteSchemaParams {
  /** URL absoluta de la home. Ej: 'https://the-full-stack.com'. */
  siteUrl: string
  /** Nombre humano del sitio. Ej: 'Pablo Contreras — Portfolio'. */
  name: string
  /** Idiomas soportados. Default ['es', 'en']. */
  inLanguage?: readonly string[]
}

/**
 * @function buildWebSiteSchema
 * @description Devuelve el objeto JSON-LD listo para serializar.
 *
 * @param {WebSiteSchemaParams} params
 * @returns {Record<string, unknown>} Schema.org WebSite serializable.
 *
 * @example
 *   buildWebSiteSchema({
 *     siteUrl: 'https://the-full-stack.com',
 *     name: 'Pablo Contreras — Portfolio',
 *   })
 *   // {'@context':'https://schema.org','@type':'WebSite',name,url,inLanguage}
 */
export function buildWebSiteSchema(
  params: WebSiteSchemaParams,
): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: params.name,
    url: params.siteUrl,
    inLanguage: [...(params.inLanguage ?? ['es', 'en'])],
  }
}
