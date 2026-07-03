/**
 * @module store
 * @description Estado global del journey (zustand): tier, locale, zona
 *   actual, puertas abiertas, ficha abierta, pointer lock y el registro de
 *   interactables por proximidad. Los controles se deshabilitan mientras
 *   cualquier UI (ficha) esta abierta.
 */
import { create } from 'zustand'
import type { Zone } from './layout'
import type { Locale } from './rooms'
import type { Tier } from './tiers'

export interface Interactable {
  id: string
  x: number
  z: number
  radius: number
  label: Record<Locale, string>
  onActivate: () => void
}

export type FichaKind = 'retos' | 'aprendizajes'

export interface JourneyStateData {
  tier: Tier
  locale: Locale
  zone: Zone
  doorsOpen: Record<number, boolean>
  ficha: { roomIndex: number; kind: FichaKind } | null
  interactables: Record<string, Interactable>
  activeInteractableId: string | null
  isLocked: boolean
}

export interface JourneyState extends JourneyStateData {
  configure: (tier: Tier, locale: Locale) => void
  setZone: (zone: Zone) => void
  openDoor: (index: number) => void
  openFicha: (roomIndex: number, kind: FichaKind) => void
  closeFicha: () => void
  registerInteractable: (item: Interactable) => void
  unregisterInteractable: (id: string) => void
  setActiveInteractable: (id: string | null) => void
  activateCurrent: () => void
  setLocked: (locked: boolean) => void
  isUiOpen: () => boolean
}

export const INITIAL_JOURNEY_STATE: JourneyStateData = {
  tier: 'full',
  locale: 'es',
  zone: { kind: 'room', index: 0 },
  doorsOpen: {},
  ficha: null,
  interactables: {},
  activeInteractableId: null,
  isLocked: false,
}

export const useJourneyStore = create<JourneyState>()((set, get) => ({
  ...INITIAL_JOURNEY_STATE,
  configure: (tier, locale) => set({ tier, locale }),
  setZone: (zone) => set({ zone }),
  openDoor: (index) =>
    set((state) => ({ doorsOpen: { ...state.doorsOpen, [index]: true } })),
  openFicha: (roomIndex, kind) => set({ ficha: { roomIndex, kind } }),
  closeFicha: () => set({ ficha: null }),
  registerInteractable: (item) =>
    set((state) => ({
      interactables: { ...state.interactables, [item.id]: item },
    })),
  unregisterInteractable: (id) =>
    set((state) => {
      const rest = { ...state.interactables }
      delete rest[id]
      return {
        interactables: rest,
        activeInteractableId:
          state.activeInteractableId === id ? null : state.activeInteractableId,
      }
    }),
  setActiveInteractable: (id) => set({ activeInteractableId: id }),
  activateCurrent: () => {
    const { activeInteractableId, interactables } = get()
    if (activeInteractableId) {
      interactables[activeInteractableId]?.onActivate()
    }
  },
  setLocked: (locked) => set({ isLocked: locked }),
  isUiOpen: () => get().ficha !== null,
}))
