/**
 * @module i18n
 * @description Textos de UI de post por locale + helpers de rutas.
 */
import type { Locale } from './guides'

export const UI = {
  es: {
    siteName: 'post · the-full-stack',
    homeTitle: 'Posts — the-full-stack',
    homeDescription:
      'Posts de Pablo Contreras: guías, notas y todo lo que vale la pena compartir.',
    eyebrow: 'Por Pablo Contreras',
    headline: 'Posts',
    lede: 'Guías, notas y todo lo que vale la pena compartir.',
    navLabel: 'Navegación principal',
    tags: 'Etiquetas',
    chapters: 'capítulos',
    minRead: 'min de lectura',
    by: 'Por',
    contents: 'Contenido',
    intro: 'Introducción',
    backToTop: 'Volver arriba',
    allGuides: 'Todos los posts',
    copy: 'Copiar',
    copied: 'Copiado',
    skip: 'Saltar al contenido',
    theme: 'Cambiar tema (actual: {theme})',
    themeNames: { system: 'sistema', dark: 'oscuro', light: 'claro' },
    langLabel: 'English',
    portfolio: 'Portfolio',
    footer: 'Escrito por',
  },
  en: {
    siteName: 'post · the-full-stack',
    homeTitle: 'Posts — the-full-stack',
    homeDescription:
      "Pablo Contreras's posts: guides, notes and anything worth sharing.",
    eyebrow: 'By Pablo Contreras',
    headline: 'Posts',
    lede: 'Guides, notes and anything worth sharing.',
    navLabel: 'Main navigation',
    tags: 'Tags',
    chapters: 'chapters',
    minRead: 'min read',
    by: 'By',
    contents: 'Contents',
    intro: 'Introduction',
    backToTop: 'Back to top',
    allGuides: 'All posts',
    copy: 'Copy',
    copied: 'Copied',
    skip: 'Skip to content',
    theme: 'Toggle theme (current: {theme})',
    themeNames: { system: 'system', dark: 'dark', light: 'light' },
    langLabel: 'Español',
    portfolio: 'Portfolio',
    footer: 'Written by',
  },
} as const

export const AUTHOR = 'Pablo Contreras'

/**
 * Path de una pagina en un locale (`/ntfy/`, `/en/ntfy/`, `/`, `/en/`).
 * Con barra final: Cloudflare Pages redirige (308) `/ntfy` -> `/ntfy/`.
 */
export function pathFor(locale: Locale, slug = ''): string {
  const base = locale === 'es' ? '' : '/en'
  return slug ? `${base}/${slug}/` : `${base}/`
}

/**
 * Recorta un texto a `max` caracteres (meta description: Google muestra
 * ~155). Prefiere cortar en la ultima coma (cierra una idea); si no hay
 * una razonable, corta en limite de palabra.
 * @example truncate('uno, dos tres cuatro', 12) // 'uno…'
 */
export function truncate(text: string, max = 155): string {
  if (text.length <= max) return text
  const head = text.slice(0, max - 1)
  const comma = head.lastIndexOf(',')
  const cut =
    comma > max * 0.5 ? head.slice(0, comma) : head.replace(/\s+\S*$/, '')
  return `${cut}…`
}

/** Fecha legible: "11 de octubre de 2026" / "October 11, 2026". */
export function formatDate(iso: string, locale: Locale): string {
  return new Intl.DateTimeFormat(locale === 'es' ? 'es-CL' : 'en-US', {
    dateStyle: 'long',
    timeZone: 'UTC',
  }).format(new Date(iso))
}
