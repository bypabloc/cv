/**
 * @module guides
 * @description Arma una guia (README + 12 capitulos) desde la coleccion
 *   `guides`. Los .md no tienen frontmatter: titulo, descripcion, tags y
 *   titulos de capitulo se leen del cuerpo.
 */
import { type CollectionEntry, getCollection } from 'astro:content'

export type Locale = 'es' | 'en'
export const LOCALES: readonly Locale[] = ['es', 'en']
/** Orden de la portada: la mas reciente primero. */
export const GUIDE_SLUGS = [
  'claude-code-mode',
  'agent-synapse',
  'agents-handoff',
  'ntfy',
  'oracle',
] as const
export type GuideSlug = (typeof GUIDE_SLUGS)[number]
/** Fecha de publicacion de cada guia (YYYY-MM-DD). */
const PUBLISHED: Record<GuideSlug, string> = {
  'claude-code-mode': '2026-11-22',
  'agent-synapse': '2026-11-22',
  'agents-handoff': '2026-11-18',
  ntfy: '2026-10-11',
  oracle: '2026-10-11',
}
/** Ultima actualizacion de contenido (YYYY-MM-DD), solo si difiere de la publicacion. */
const UPDATED: Partial<Record<GuideSlug, string>> = {
  'agents-handoff': '2026-11-22',
}

export interface Chapter {
  id: string
  number: string
  title: string
  entry: CollectionEntry<'guides'>
}

export interface Guide {
  slug: GuideSlug
  locale: Locale
  published: string
  /** Fecha de la ultima actualizacion; igual a `published` si nunca cambio. */
  updated: string
  title: string
  description: string
  tags: string[]
  minutes: number
  readme: CollectionEntry<'guides'>
  chapters: Chapter[]
}

const WORDS_PER_MINUTE = 200

function plain(md: string): string {
  return md.replace(/[*`_]/g, '').trim()
}

function fileName(entry: CollectionEntry<'guides'>): string {
  return (entry.filePath ?? '').split('/').pop() ?? ''
}

function match(body: string, re: RegExp): string {
  return plain(re.exec(body)?.[1] ?? '')
}

/**
 * @function loadGuide
 * @description Devuelve la guia `slug` en `locale` con sus capitulos
 *   ordenados por numero.
 * @throws {Error} Si la guia no tiene README.md
 */
export async function loadGuide(
  locale: Locale,
  slug: GuideSlug,
): Promise<Guide> {
  const dir = `/guides/${locale}/${slug}/`
  const entries = (await getCollection('guides'))
    .filter((e) => e.filePath?.includes(dir))
    .sort((a, b) => fileName(a).localeCompare(fileName(b)))
  const readme = entries.find((e) => fileName(e) === 'README.md')
  if (!readme) throw new Error(`Guia sin README.md: ${dir}`)
  const body = readme.body ?? ''
  const lastLine = body.trim().split('\n').pop() ?? ''
  const words = entries.reduce(
    (n, e) => n + (e.body ?? '').split(/\s+/).length,
    0,
  )

  return {
    slug,
    locale,
    published: PUBLISHED[slug],
    updated: UPDATED[slug] ?? PUBLISHED[slug],
    title: match(body, /^# (.+)$/m),
    description: match(body, /^> (.+)$/m),
    tags: [...lastLine.matchAll(/`([^`]+)`/g)].map((m) => m[1] ?? ''),
    minutes: Math.round(words / WORDS_PER_MINUTE),
    readme,
    chapters: entries
      .filter((e) => e !== readme)
      .map((entry) => {
        const id = fileName(entry).replace(/\.md$/, '')
        return {
          id,
          number: id.slice(0, 2),
          title: match(entry.body ?? '', /^# (.+)$/m),
          entry,
        }
      }),
  }
}

/**
 * @function guideMarkdown
 * @description La guia completa como un solo Markdown (README + capitulos)
 *   para `/<slug>.md`. Los links entre capitulos (`NN-x.md[#a]`,
 *   `README.md`) se reescriben a anclas absolutas de la pagina HTML, igual
 *   que hace remark-guide.
 * @example guideMarkdown(guide, 'https://post.the-full-stack.com/ntfy/')
 */
export function guideMarkdown(guide: Guide, pageUrl: string): string {
  return [guide.readme, ...guide.chapters.map((c) => c.entry)]
    .map((e) => (e.body ?? '').trim())
    .join('\n\n---\n\n')
    .replace(
      /\]\((\d\d-[\w-]+)\.md(?:#([^)]+))?\)/g,
      (_, id: string, anchor?: string) =>
        `](${pageUrl}#${id}${anchor ? `--${anchor}` : ''})`,
    )
    .replace(/\]\(README\.md\)/g, `](${pageUrl})`)
    .concat('\n')
}

/** Todas las guias de un locale, en el orden de GUIDE_SLUGS. */
export function loadGuides(locale: Locale): Promise<Guide[]> {
  return Promise.all(GUIDE_SLUGS.map((slug) => loadGuide(locale, slug)))
}
