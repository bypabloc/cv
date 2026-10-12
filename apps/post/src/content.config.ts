/**
 * @config content
 * @description Coleccion `guides`: un .md por capitulo en
 *   `src/content/guides/<locale>/<guia>/`. Sin frontmatter (los .md son
 *   la fuente tal cual); titulo y metadatos se derivan del cuerpo.
 */

import { defineCollection } from 'astro:content'
import { glob } from 'astro/loaders'

export const collections = {
  guides: defineCollection({
    loader: glob({ pattern: '**/*.md', base: './src/content/guides' }),
  }),
}
