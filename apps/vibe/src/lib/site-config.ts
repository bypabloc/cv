/**
 * @module site-config (vibe)
 */
import { buildStrings } from '@portfolio/app-shared'
import type { Niche } from '@portfolio/content'

export const NICHE: Niche = 'vibe'
export const SITE_URL =
  import.meta.env.SITE_URL ?? 'https://vibe.the-full-stack.com'
export const OG_IMAGE = `${SITE_URL}/og-image.svg`

export const STRINGS = buildStrings({
  metaTitleEs: 'Pablo Contreras — Vibe Coding / Claude Code / Dev Tools',
  metaTitleEn: 'Pablo Contreras — Vibe Coding / Claude Code / Dev Tools',
  metaDescriptionEs:
    'Ingeniero que documenta workflows reales con Claude Code y Cursor. FastStruct (VS Code), este propio portfolio (monorepo Astro) y prompts que entregan producto.',
  metaDescriptionEn:
    'Engineer documenting real workflows with Claude Code and Cursor. FastStruct (VS Code), this portfolio (Astro monorepo) and prompts that ship product.',
  heroEyebrowEs: 'Pablo Contreras · Vibe Coding · Lima, Perú',
  heroEyebrowEn: 'Pablo Contreras · Vibe Coding · Lima, Peru',
  experienceSubtitleEs:
    'Roles donde integro IA en el día a día (Destacame actual).',
  experienceSubtitleEn:
    'Roles where I integrate AI into daily work (current role at Destacame).',
  projectsSubtitleEs:
    'FastStruct + monorepo Astro de este portfolio. Tools que uso para entregar.',
  projectsSubtitleEn:
    'FastStruct + Astro monorepo of this portfolio. Tools I use to ship.',
})
