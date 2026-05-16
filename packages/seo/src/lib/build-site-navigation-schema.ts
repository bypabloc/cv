/**
 * @function buildSiteNavigationSchema
 * @description Construye un schema.org ItemList de SiteNavigationElement para
 *   JSON-LD. Describe las paginas principales del sitio de forma estructurada,
 *   lo que ayuda a Google a entender la jerarquia de navegacion y favorece la
 *   aparicion de sitelinks en los resultados de busqueda de marca.
 *
 *   No garantiza sitelinks (Google los genera por su algoritmo), pero da una
 *   senal estructurada explicita de cuales son las secciones canonicas.
 *
 * @param input - siteUrl base + items de navegacion (name + path relativo)
 * @returns JSON-LD stringificado (listo para <script type="application/ld+json">)
 *
 * @example
 *   const ld = buildSiteNavigationSchema({
 *     siteUrl: 'https://the-full-stack.com',
 *     items: [
 *       { name: 'Home', path: '/' },
 *       { name: 'About', path: '/about' },
 *       { name: 'Certificates', path: '/certificates' },
 *     ],
 *   })
 *   //  '{"@context":"https://schema.org","@type":"ItemList",...}'
 */

interface NavSchemaItem {
  /** Etiqueta visible de la pagina. */
  name: string
  /** Path relativo desde el siteUrl (ej. '/about', '/'). */
  path: string
}

interface BuildSiteNavigationSchemaInput {
  /** URL absoluta del sitio (con o sin trailing slash). */
  siteUrl: string
  /** Paginas principales a declarar como nodos de navegacion. */
  items: NavSchemaItem[]
}

interface SiteNavigationElementLd {
  '@type': 'SiteNavigationElement'
  position: number
  name: string
  url: string
}

interface ItemListLd {
  '@context': 'https://schema.org'
  '@type': 'ItemList'
  itemListElement: SiteNavigationElementLd[]
}

export function buildSiteNavigationSchema(
  input: BuildSiteNavigationSchemaInput,
): string {
  const base = input.siteUrl.replace(/\/$/, '')

  const itemListElement: SiteNavigationElementLd[] = input.items.map(
    (item, index) => ({
      '@type': 'SiteNavigationElement',
      position: index + 1,
      name: item.name,
      url: `${base}${item.path}`,
    }),
  )

  const ld: ItemListLd = {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    itemListElement,
  }

  return JSON.stringify(ld)
}
