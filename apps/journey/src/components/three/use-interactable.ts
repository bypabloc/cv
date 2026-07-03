/**
 * @module use-interactable
 * @description Hook que registra un interactable de proximidad en el store
 *   mientras el componente vive (y `enabled`). El caller DEBE memoizar el
 *   item (useMemo) — el efecto re-registra si la referencia cambia.
 */
import { useEffect } from 'react'
import { type Interactable, useJourneyStore } from '../../lib/store'

export function useInteractable(item: Interactable, enabled = true): void {
  const register = useJourneyStore((s) => s.registerInteractable)
  const unregister = useJourneyStore((s) => s.unregisterInteractable)

  useEffect(() => {
    if (!enabled) {
      return undefined
    }
    register(item)
    return () => unregister(item.id)
  }, [item, enabled, register, unregister])
}
