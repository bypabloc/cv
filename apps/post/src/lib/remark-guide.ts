/**
 * @module remark-guide
 * @description Adapta los .md de una guia (escritos como capitulos sueltos)
 *   para renderizarlos juntos en UNA pagina, sin tocar las fuentes:
 *   - quita el `**NN**` y el `[← Índice](README.md)` de cada capitulo;
 *   - el `# Titulo` del capitulo pasa a `<h2 id="NN-slug">`; el del README
 *     se quita (la pagina pinta su propio h1);
 *   - prefija los ids de los headings con el capitulo (sin duplicados);
 *   - reescribe `NN-x.md[#a]` -> `#NN-x[--a]` y `README.md` -> `#top`;
 *   - convierte el unico ```mermaid (flowchart simple) en una figura HTML.
 */
import type {
  Code,
  Heading,
  Link,
  Nodes,
  Paragraph,
  Root,
  RootContent,
} from 'mdast'

interface FileLike {
  path?: string
  history: string[]
}

const CHAPTER_LINK = /^(\d\d-[\w-]+)\.md(?:#(.+))?$/

/**
 * @function slugify
 * @description Slug estilo GitHub: minusculas, conserva letras/numeros
 *   unicode, espacios -> guion.
 * @example slugify('Registro `A` sin proxy') // 'registro-a-sin-proxy'
 */
export function slugify(text: string): string {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^\p{L}\p{N}\s-]/gu, '')
    .replace(/\s+/g, '-')
}

function textOf(node: Nodes): string {
  if ('value' in node && typeof node.value === 'string') return node.value
  if ('children' in node) return node.children.map(textOf).join('')
  return ''
}

function isChapterNumber(node: RootContent): boolean {
  return (
    node.type === 'paragraph' &&
    node.children.length === 1 &&
    node.children[0]?.type === 'strong' &&
    /^\d+$/.test(textOf(node.children[0]))
  )
}

function isBackToIndex(node: RootContent): boolean {
  if (node.type !== 'paragraph') return false
  const links = (node as Paragraph).children.filter(
    (c) => c.type !== 'text' || c.value.trim(),
  )
  return (
    links.length === 1 &&
    links[0]?.type === 'link' &&
    links[0].url === 'README.md'
  )
}

function rewriteUrl(url: string, prefix: string): string {
  if (url === 'README.md') return '#top'
  const m = CHAPTER_LINK.exec(url)
  if (m) return m[2] ? `#${m[1]}--${slugify(m[2])}` : `#${m[1]}`
  if (url.startsWith('#')) return `#${prefix}--${slugify(url.slice(1))}`
  return url
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

/**
 * Renderiza un `flowchart` mermaid de aristas `A["x"] -->|label| B["y"]`
 * como lista de pasos. ponytail: parser minimo para el unico diagrama de
 * las guias; si aparecen diagramas complejos, pre-renderizar a SVG.
 */
export function flowchartToHtml(source: string): string {
  const labels = new Map<string, string>()
  const edge =
    /(\w+)(?:\["([^"]+)"\])?\s*-->\s*(?:\|"?([^|"]*)"?\|)?\s*(\w+)(?:\["([^"]+)"\])?/
  const rows: string[] = []
  const label = (id: string) =>
    escapeHtml(labels.get(id) ?? id).replace(/\\n/g, '<br>')
  for (const line of source.split('\n')) {
    const m = edge.exec(line)
    if (!m) continue
    const [, from = '', fromLabel, via = '', to = '', toLabel] = m
    if (fromLabel) labels.set(from, fromLabel)
    if (toLabel) labels.set(to, toLabel)
    rows.push(
      `<li><span class="flow__node">${label(from)}</span>` +
        `<span class="flow__edge">${escapeHtml(via).replace(/\\n/g, '<br>')}</span>` +
        `<span class="flow__node">${label(to)}</span></li>`,
    )
  }
  return `<figure class="flow"><ol>${rows.join('')}</ol></figure>`
}

function walk(node: Nodes, prefix: string): void {
  if (node.type === 'link') {
    const link = node as Link
    link.url = rewriteUrl(link.url, prefix)
  }
  if ('children' in node) for (const child of node.children) walk(child, prefix)
}

function setId(heading: Heading, id: string): void {
  heading.data = { ...heading.data, hProperties: { id } }
}

/** Decide si un nodo top-level queda y asigna los ids de los headings. */
function keepAndTag(
  node: RootContent,
  chapter: string,
  prefix: string,
): boolean {
  if (isChapterNumber(node) || isBackToIndex(node)) return false
  if (node.type !== 'heading') return true
  if (node.depth === 1) {
    if (chapter === 'README') return false
    node.depth = 2
    setId(node, chapter)
    return true
  }
  setId(node, `${prefix}--${slugify(textOf(node))}`)
  return true
}

/**
 * @function remarkGuide
 * @description Plugin remark (ver docstring del modulo). Solo actua sobre
 *   archivos bajo `/guides/`; el resto del markdown queda intacto.
 */
export function remarkGuide() {
  return (tree: Root, file: FileLike) => {
    const path = file.path ?? file.history[0] ?? ''
    if (!path.includes('/guides/')) return
    const chapter = (path.split('/').pop() ?? '').replace(/\.md$/, '')
    const isReadme = chapter === 'README'
    const prefix = isReadme ? 'intro' : chapter
    // El h1 y la `> descripcion` del README los pinta la cabecera de la pagina.
    const introQuote = isReadme
      ? tree.children.findIndex((n) => n.type === 'blockquote')
      : -1

    tree.children = tree.children.filter(
      (node, i) => i !== introQuote && keepAndTag(node, chapter, prefix),
    )
    // El `---` que seguia al titulo del capitulo sobra en la pagina larga.
    if (
      tree.children[0]?.type === 'heading' &&
      tree.children[1]?.type === 'thematicBreak'
    ) {
      tree.children.splice(1, 1)
    }

    tree.children = tree.children.map((node): RootContent => {
      if (node.type === 'code' && (node as Code).lang === 'mermaid') {
        return { type: 'html', value: flowchartToHtml((node as Code).value) }
      }
      return node
    })
    walk(tree, prefix)
  }
}
