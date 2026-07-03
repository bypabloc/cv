/**
 * @component Journey3D
 * @description Isla de entrada de la experiencia 3D (client:only). Detecta
 *   el tier en el cliente: en Static NO carga three (el fallback CV 2D del
 *   HTML queda visible); en Full/Reduced oculta el fallback y carga la app
 *   3D por dynamic import (chunk separado — AC-14).
 */
import { lazy, Suspense, useEffect, useState } from 'react'
import type { Locale } from '../lib/rooms'
import { readTierEnv, resolveTier, type Tier } from '../lib/tiers'

const JourneyApp = lazy(() => import('./three/JourneyApp'))

interface Journey3DProps {
  locale: Locale
}

function probeWebgl2(): boolean {
  try {
    return document.createElement('canvas').getContext('webgl2') !== null
  } catch {
    return false
  }
}

function detectTier(): Tier {
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

const STRINGS = {
  es: { loading: 'Cargando el mundo 3D…', enter: 'Explorar en 3D' },
  en: { loading: 'Loading the 3D world…', enter: 'Explore in 3D' },
} as const

export default function Journey3D({ locale }: Journey3DProps) {
  const [tier, setTier] = useState<Tier | null>(null)
  const [exited, setExited] = useState(false)

  useEffect(() => {
    setTier(detectTier())
  }, [])

  const active = tier !== null && tier !== 'static' && !exited

  // en 3D activo: se oculta el fallback 2D y se bloquea el scroll de fondo
  useEffect(() => {
    const fallback = document.getElementById('cv-fallback')
    if (fallback) {
      fallback.style.display = active ? 'none' : ''
    }
    document.documentElement.style.overflow = active ? 'hidden' : ''
    return () => {
      document.documentElement.style.overflow = ''
    }
  }, [active])

  if (tier === null || tier === 'static') {
    return null
  }

  if (exited) {
    return (
      <button
        type="button"
        onClick={() => setExited(false)}
        style={{
          position: 'fixed',
          bottom: 18,
          right: 18,
          zIndex: 60,
          background: 'var(--color-primary, #4f6ef7)',
          color: 'var(--color-primary-contrast, #ffffff)',
          border: 'none',
          borderRadius: 'var(--radius-pill, 999px)',
          padding: '0.6rem 1.1rem',
          cursor: 'pointer',
          fontSize: '0.9rem',
        }}
      >
        {STRINGS[locale].enter}
      </button>
    )
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 50,
        background: '#07070b',
      }}
    >
      <Suspense
        fallback={
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'grid',
              placeItems: 'center',
              color: 'var(--color-grey-5, #f7f7f5)',
              fontFamily: 'var(--font-sans, sans-serif)',
            }}
          >
            {STRINGS[locale].loading}
          </div>
        }
      >
        <JourneyApp
          tier={tier}
          locale={locale}
          onExit={() => setExited(true)}
        />
      </Suspense>
    </div>
  )
}
