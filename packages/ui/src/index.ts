/**
 * @module @portfolio/ui
 * @description Barrel TS del paquete. Los componentes Astro NO se re-exportan
 *   desde este barrel (un .astro no es un modulo TS) — se importan directo:
 *
 *   import BaseLayout from '@portfolio/ui/layouts/BaseLayout.astro'
 *   import Hero from '@portfolio/ui/components/Hero.astro'
 *   import TrackingPixel from '@portfolio/ui/components/TrackingPixel.astro'
 *   import CookieBanner from '@portfolio/ui/components/CookieBanner.astro'
 *
 *   import { applyTheme, readConsent } from '@portfolio/ui'
 */

export { buildClickProps, initClickTracking } from './lib/click-tracking'
export type { ConsentValue } from './lib/cookie-consent'
export {
  CONSENT_CHANGED_EVENT,
  isConsentValue,
  REOPEN_BANNER_EVENT,
  readConsent,
  STORAGE_KEY,
  writeConsent,
} from './lib/cookie-consent'
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
export {
  computeScrollPercent,
  initScrollDepth,
  SCROLL_THRESHOLDS,
} from './lib/scroll-depth'
export type { Theme } from './lib/theme-toggle'
export {
  applyTheme,
  isTheme,
  nextTheme,
  readStoredTheme,
  storeTheme,
} from './lib/theme-toggle'
export {
  buildTrackPayload,
  configureTracking,
  generateEventId,
  getSessionId,
  hasTrackingConsent,
  isTrackingForced,
  resetTrackingConfig,
  sendBeaconPayload,
  type TrackEventPayload,
  type TrackingConfig,
  trackEvent,
} from './lib/track-event'
