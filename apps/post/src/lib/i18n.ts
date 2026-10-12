/**
 * @module i18n
 * @description Textos de UI de post por locale + helpers de rutas.
 */
import type { Locale } from './guides'

export const UI = {
  es: {
    siteName: 'post · the-full-stack',
    homeTitle: 'Guías técnicas — the-full-stack',
    homeDescription:
      'Guías paso a paso de self-hosting e infraestructura: servidores, notificaciones y nubes gratuitas, probadas en producción.',
    eyebrow: 'Guías técnicas',
    headline: 'Infraestructura propia, explicada paso a paso',
    lede: 'Guías largas y probadas: cada comando se ejecutó, cada error quedó documentado con su solución.',
    readGuide: 'Leer la guía',
    chapters: 'capítulos',
    minRead: 'min de lectura',
    by: 'Por',
    contents: 'Contenido',
    intro: 'Introducción',
    backToTop: 'Volver arriba',
    allGuides: 'Todas las guías',
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
    homeTitle: 'Technical guides — the-full-stack',
    homeDescription:
      'Step-by-step self-hosting and infrastructure guides: servers, notifications and free clouds, tested in production.',
    eyebrow: 'Technical guides',
    headline: 'Your own infrastructure, step by step',
    lede: 'Long, tested guides: every command was run, every error is documented with its fix.',
    readGuide: 'Read the guide',
    chapters: 'chapters',
    minRead: 'min read',
    by: 'By',
    contents: 'Contents',
    intro: 'Introduction',
    backToTop: 'Back to top',
    allGuides: 'All guides',
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

/** Path de una pagina en un locale (`/ntfy`, `/en/ntfy`, `/`, `/en/`). */
export function pathFor(locale: Locale, slug = ''): string {
  const base = locale === 'es' ? '' : '/en'
  return slug ? `${base}/${slug}` : `${base}/`
}

/** Fecha legible: "11 de octubre de 2026" / "October 11, 2026". */
export function formatDate(iso: string, locale: Locale): string {
  return new Intl.DateTimeFormat(locale === 'es' ? 'es-CL' : 'en-US', {
    dateStyle: 'long',
    timeZone: 'UTC',
  }).format(new Date(iso))
}
