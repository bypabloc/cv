/**
 * @module @portfolio/ui
 * @description Barrel TS del paquete. Componentes Astro se importan directo:
 *
 *   import BaseLayout from '@portfolio/ui/layouts/BaseLayout.astro'
 *   import Hero from '@portfolio/ui/components/Hero.astro'
 *
 *   import { applyTheme } from '@portfolio/ui'
 */

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
