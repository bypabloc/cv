/**
 * @module boot
 * @description Entry LIVIANO de la experiencia 3D (sin three, sin engine):
 *   detecta el tier en el cliente — en Static NO descarga el chunk 3D y el
 *   CV 2D del HTML queda visible (AC-2); en Full/Reduced muestra el loader
 *   (texto EXACTO del contrato E2E), carga el engine por dynamic import
 *   (chunk separado — AC-12) y gestiona salida/re-entrada.
 */
import type { JourneyHandle } from '../engine/app'
import type { Locale } from './rooms'
import { readTierEnv, resolveTier, type Tier } from './tiers'

const STRINGS = {
  es: { loading: 'Cargando el mundo 3D…', enter: 'Explorar en 3D' },
  en: { loading: 'Loading the 3D world…', enter: 'Explore in 3D' },
} as const

function probeWebgl2(): boolean {
  try {
    return document.createElement('canvas').getContext('webgl2') !== null
  } catch {
    return false
  }
}

function detectTier(): Tier {
  // reason: deviceMemory es API no estandar (solo Chromium), el narrow es
  // el mismo del MVP anterior
  const nav = navigator as Navigator & { deviceMemory?: number }
  return resolveTier(
    readTierEnv({
      webgl2: probeWebgl2(),
      matchMedia: (query) => window.matchMedia(query),
      userAgent: navigator.userAgent,
      maxTouchPoints: navigator.maxTouchPoints,
      deviceMemory: nav.deviceMemory,
    }),
  )
}

/** Oculta/restaura el fallback 2D y el scroll del documento. */
function setImmersive(on: boolean): void {
  const fallback = document.getElementById('cv-fallback')
  if (fallback) {
    fallback.style.display = on ? 'none' : ''
  }
  document.documentElement.style.overflow = on ? 'hidden' : ''
}

function mountReenterButton(
  tier: Exclude<Tier, 'static'>,
  locale: Locale,
): void {
  const btn = document.createElement('button')
  btn.type = 'button'
  btn.textContent = STRINGS[locale].enter
  btn.style.cssText =
    'position:fixed;bottom:18px;right:18px;z-index:60;' +
    'background:var(--color-primary,#4f6ef7);' +
    'color:var(--color-primary-contrast,#ffffff);border:none;' +
    'border-radius:var(--radius-pill,999px);padding:0.6rem 1.1rem;' +
    'cursor:pointer;font-size:0.9rem'
  btn.addEventListener('click', () => {
    btn.remove()
    void enter(tier, locale)
  })
  document.body.appendChild(btn)
}

async function enter(
  tier: Exclude<Tier, 'static'>,
  locale: Locale,
): Promise<void> {
  const t = STRINGS[locale]
  const overlay = document.createElement('div')
  overlay.style.cssText = 'position:fixed;inset:0;z-index:50;background:#0b0b10'
  const loader = document.createElement('div')
  loader.style.cssText =
    'position:absolute;inset:0;display:grid;place-items:center;' +
    'color:var(--color-grey-5,#f7f7f5);font-family:var(--font-sans,sans-serif)'
  loader.textContent = t.loading
  overlay.appendChild(loader)
  document.body.appendChild(overlay)
  setImmersive(true)
  try {
    // chunk 3D separado del HTML (dynamic import)
    const { startJourney } = await import('../engine/app')
    let handle: JourneyHandle | null = null
    handle = await startJourney({
      container: overlay,
      tier,
      locale,
      onExit: () => {
        handle?.dispose()
        handle = null
        overlay.remove()
        setImmersive(false)
        mountReenterButton(tier, locale)
      },
    })
    loader.remove()
  } catch (error) {
    console.error('[journey] no se pudo montar el mundo 3D', error)
    overlay.remove()
    setImmersive(false)
  }
}

/**
 * @function initJourney
 * @description Arranque desde las paginas Astro: lee el locale del
 *   `#journey-root`, decide el tier y monta (o no) la experiencia.
 */
export async function initJourney(): Promise<void> {
  const root = document.getElementById('journey-root')
  if (!root) {
    return
  }
  const locale: Locale = root.dataset.locale === 'en' ? 'en' : 'es'
  const tier = detectTier()
  if (tier === 'static') {
    return
  }
  await enter(tier, locale)
}
