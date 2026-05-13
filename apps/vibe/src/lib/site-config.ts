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
    'Ingeniero que documenta workflows reales con Claude Code (desde el lanzamiento, mayo 2025) y antes Claude web + FastStruct. FastStruct (VS Code), monorepo Astro de este portfolio y un CV builder construido en una sola noche.',
  metaDescriptionEn:
    'Engineer documenting real workflows with Claude Code (since launch, May 2025) and previously Claude web + FastStruct. FastStruct (VS Code), Astro monorepo of this portfolio and a CV builder shipped in a single night.',
  heroEyebrowEs: 'Pablo Contreras · Vibe Coding · Lima, Perú',
  heroEyebrowEn: 'Pablo Contreras · Vibe Coding · Lima, Peru',
  heroHeadlineEs: 'AI-Augmented Full Stack · Claude Code',
  heroHeadlineEn: 'AI-Augmented Full Stack · Claude Code',
  heroSummaryEs:
    'Llevo usando Claude Code desde su lanzamiento (mayo 2025). Antes ya pasaba contexto a Claude web con mi propia extensión FastStruct. Construyo herramientas que aceleran ese flujo y publico prompts reales. La IA es herramienta — el código lo reviso, testeo y mantengo yo.',
  heroSummaryEn:
    'I have been using Claude Code since launch (May 2025). Before that I was already piping context to Claude web with my own FastStruct extension. I build tools that accelerate that flow and publish real prompts. AI is a tool — I review, test and maintain the code myself.',
  nicheLabelEs: 'Vibe Coding',
  nicheLabelEn: 'Vibe Coding',
  experienceSubtitleEs:
    'Roles donde integro IA en el día a día (Destacame actual).',
  experienceSubtitleEn:
    'Roles where I integrate AI into daily work (current role at Destacame).',
  projectsSubtitleEs:
    'FastStruct + CV builder (bypabloc/cv) + monorepo Astro de este portfolio. Tools que uso para entregar.',
  projectsSubtitleEn:
    'FastStruct + CV builder (bypabloc/cv) + Astro monorepo of this portfolio. Tools I use to ship.',
  atsKeywords: [
    'AI-Augmented Developer',
    'Vibe Coding',
    'Claude Code',
    'Cursor',
    'Prompt Engineering',
    'Sub-agents',
    'MCP Servers',
    'GitHub Copilot',
    'VS Code Extension Development',
    'TypeScript',
    'Astro 6',
    'Python 3.14',
    'Developer Tools',
    'AI Workflow Documentation',
  ],
})
