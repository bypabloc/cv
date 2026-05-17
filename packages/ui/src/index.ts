/**
 * @module @portfolio/ui
 * @description Barrel TS del paquete. Los componentes Astro NO se re-exportan
 *   desde este barrel (un .astro no es un modulo TS) — se importan directo:
 *
 *   import BaseLayout from '@portfolio/ui/layouts/BaseLayout.astro'
 *   import Hero from '@portfolio/ui/components/Hero.astro'
 *   import TrackingPixel from '@portfolio/ui/components/TrackingPixel.astro'
 *
 *   import { applyTheme } from '@portfolio/ui'
 */

export { initMagneticCursor } from './lib/magnetic-cursor'
export { initMobileNav } from './lib/mobile-nav'
export {
  getNicheTokens,
  NICHE_TOKENS,
  type NicheTokens,
  nicheTokensToCssVars,
} from './lib/niche-tokens'
export { initNumberCounters } from './lib/number-counter'
export { deobfuscateEmail, obfuscateEmail } from './lib/obfuscate-email'
export { initRevealOnScroll } from './lib/reveal-on-scroll'
export type { Theme } from './lib/theme-toggle'
export {
  applyTheme,
  isTheme,
  nextTheme,
  readStoredTheme,
  storeTheme,
} from './lib/theme-toggle'
