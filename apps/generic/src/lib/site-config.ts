/**
 * @module site-config (generic)
 * @description Config especifica del sitio generic. Delega strings al paquete
 *   compartido y solo declara los overrides.
 */
import { buildStrings } from '@portfolio/app-shared'
import type { Niche } from '@portfolio/content'

export const NICHE: Niche = 'generic'

export const SITE_URL =
  import.meta.env.SITE_URL ?? 'https://hub.the-full-stack.com'

export const OG_IMAGE = `${SITE_URL}/og-image.svg`

export const STRINGS = buildStrings({
  metaTitleEs: 'Pablo Contreras — Ingeniero Full Stack senior',
  metaTitleEn: 'Pablo Contreras — Senior Full Stack Engineer',
  metaDescriptionEs:
    'Ingeniero Full Stack con 8+ años en Vue, Nuxt, Django, AWS y fintech LATAM (Chile, México). Portfolio + experiencia + proyectos.',
  metaDescriptionEn:
    'Senior Full Stack Engineer with 8+ years in Vue, Nuxt, Django, AWS and LATAM fintech (Chile, Mexico). Portfolio + experience + projects.',
})
