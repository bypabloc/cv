'use client'

import { type ReactNode, useEffect, useState } from 'react'

/**
 * @component MswProvider
 * @description Arranca el worker MSW en el browser cuando
 *   `NEXT_PUBLIC_USE_MSW === 'true'`. En cualquier otro caso es passthrough
 *   inmediato. Bloquea el render hasta que el worker este listo SOLO si MSW
 *   esta activo (evita requests sin mock en el arranque).
 *
 * @props {ReactNode} children - Arbol de la app
 */
export function MswProvider({ children }: { children: ReactNode }) {
  const useMsw = process.env.NEXT_PUBLIC_USE_MSW === 'true'
  const [ready, setReady] = useState(!useMsw)

  useEffect(() => {
    if (!useMsw || typeof window === 'undefined') return
    let active = true
    void (async () => {
      const { worker } = await import('@tests/mocks/browser')
      await worker.start({ onUnhandledRequest: 'bypass' })
      if (active) setReady(true)
    })()
    return () => {
      active = false
    }
  }, [useMsw])

  if (!ready) return null
  return <>{children}</>
}
