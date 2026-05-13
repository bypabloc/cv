/**
 * @module niche-tokens
 * @description Mapeo type-safe de niches a tokens visuales (accent, glow,
 *   gradient, mood). Consumido por SitePageLayout para inyectar variables
 *   CSS dinamicas sin fragmentar el bundle por app.
 *
 *   Cada nicho tiene una identidad visual distintiva:
 *   - generic:   electric blue, full-stack confiable
 *   - hub:       multi-accent, selector / wayfinder
 *   - fintech:   cyan teal, LATAM compliance
 *   - architect: rose-pink, sistemas / microservicios
 *   - leader:    amber gold, liderazgo / gestion
 *   - vibe:      purple-violet, AI-augmented
 */
import type { Niche } from '@portfolio/content'

export interface NicheTokens {
  /** Color principal del nicho (hex) */
  accent: string
  /** RGB triplet del accent, para usar en rgba(var(--niche-accent-rgb), x) */
  accentRgb: string
  /** Color glow para sombras y mesh gradients */
  glow: string
  /** Gradient lineal de identidad */
  gradient: string
  /** Mood tipografico: 'sans' (default) o 'mono' (vibe + architect labels) */
  mood: 'sans' | 'mono'
  /** Etiqueta humana corta del nicho */
  label: string
}

/**
 * Tabla de tokens por nicho. Hub es la landing maestra y usa multi-accent.
 */
export const NICHE_TOKENS: Record<Niche | 'hub', NicheTokens> = {
  generic: {
    accent: '#4f6ef7',
    accentRgb: '79, 110, 247',
    glow: 'rgba(79, 110, 247, 0.35)',
    gradient: 'linear-gradient(135deg, #4f6ef7 0%, #b97cf2 100%)',
    mood: 'sans',
    label: 'Full Stack',
  },
  hub: {
    accent: '#9b9bff',
    accentRgb: '155, 155, 255',
    glow: 'rgba(155, 155, 255, 0.32)',
    gradient:
      'linear-gradient(135deg, #4f6ef7 0%, #38d9d6 35%, #f06e9c 70%, #f4b740 100%)',
    mood: 'sans',
    label: 'Hub',
  },
  fintech: {
    accent: '#38d9d6',
    accentRgb: '56, 217, 214',
    glow: 'rgba(56, 217, 214, 0.35)',
    gradient: 'linear-gradient(135deg, #38d9d6 0%, #4f6ef7 100%)',
    mood: 'sans',
    label: 'Fintech LATAM',
  },
  architect: {
    accent: '#f06e9c',
    accentRgb: '240, 110, 156',
    glow: 'rgba(240, 110, 156, 0.32)',
    gradient: 'linear-gradient(135deg, #f06e9c 0%, #b97cf2 100%)',
    mood: 'mono',
    label: 'Architect',
  },
  leader: {
    accent: '#f4b740',
    accentRgb: '244, 183, 64',
    glow: 'rgba(244, 183, 64, 0.32)',
    gradient: 'linear-gradient(135deg, #f4b740 0%, #f06e9c 100%)',
    mood: 'sans',
    label: 'Tech Lead',
  },
  vibe: {
    accent: '#b97cf2',
    accentRgb: '185, 124, 242',
    glow: 'rgba(185, 124, 242, 0.40)',
    gradient: 'linear-gradient(135deg, #b97cf2 0%, #4f6ef7 100%)',
    mood: 'mono',
    label: 'Vibe Coding',
  },
}

/**
 * @function getNicheTokens
 * @description Retorna los tokens visuales de un nicho. Type-safe.
 *
 * @param {Niche | 'hub'} niche - Identificador del nicho
 * @returns {NicheTokens} Tokens del nicho
 *
 * @example
 *   const { accent, gradient } = getNicheTokens('fintech')
 *   // accent === '#38d9d6'
 */
export function getNicheTokens(niche: Niche | 'hub'): NicheTokens {
  return NICHE_TOKENS[niche]
}

/**
 * @function nicheTokensToCssVars
 * @description Construye un string `style="..."` con las custom vars CSS
 *   del nicho, listo para inyectar en el root de SitePageLayout.
 *
 * @param {Niche | 'hub'} niche - Identificador del nicho
 * @returns {string} String con CSS custom props
 *
 * @example
 *   nicheTokensToCssVars('vibe')
 *   // "--niche-accent: #b97cf2; --niche-accent-rgb: 185, 124, 242; ..."
 */
export function nicheTokensToCssVars(niche: Niche | 'hub'): string {
  const t = getNicheTokens(niche)
  return [
    `--niche-accent: ${t.accent}`,
    `--niche-accent-rgb: ${t.accentRgb}`,
    `--niche-glow: ${t.glow}`,
    `--niche-gradient: ${t.gradient}`,
    `--niche-mood: ${t.mood}`,
  ].join('; ')
}
