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

export interface Vec2Like {
  x: number
  z: number
}

export interface JourneyStateData {
  tier: Tier
  locale: Locale
  zone: Zone
  doorsOpen: Record<number, boolean>
  ficha: { roomIndex: number; kind: FichaKind } | null
  interactables: Record<string, Interactable>
  activeInteractableId: string | null
  isLocked: boolean
  /** Indice de la sala cuyo "antes" se esta visitando (portal al pasado). */
  past: number | null
  /** Teleport pendiente que PlayerControls consume en el proximo frame. */
  teleportTarget: Vec2Like | null
  /** Panel de contacto (CTA de la CIMA). */
  contactOpen: boolean
  /** Menu de teletransporte (tecla M). */
  teleportMenuOpen: boolean
  /** Audio ambiente: SIEMPRE arranca apagado (autoplay policy, opt-in). */
  audioOn: boolean
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
  enterPast: (roomIndex: number, spawn: Vec2Like) => void
  exitPast: (returnTo: Vec2Like) => void
  requestTeleport: (target: Vec2Like) => void
  consumeTeleport: () => Vec2Like | null
  openContact: () => void
  closeContact: () => void
  toggleTeleportMenu: () => void
  toggleAudio: () => void
  closeAllUi: () => void
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
  past: null,
  teleportTarget: null,
  contactOpen: false,
  teleportMenuOpen: false,
  audioOn: false,
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
  enterPast: (roomIndex, spawn) =>
    set({ past: roomIndex, teleportTarget: spawn }),
  exitPast: (returnTo) => set({ past: null, teleportTarget: returnTo }),
  requestTeleport: (target) => set({ teleportTarget: target }),
  consumeTeleport: () => {
    const target = get().teleportTarget
    if (target) {
      set({ teleportTarget: null })
    }
    return target
  },
  openContact: () => set({ contactOpen: true }),
  closeContact: () => set({ contactOpen: false }),
  toggleTeleportMenu: () =>
    set((state) => ({ teleportMenuOpen: !state.teleportMenuOpen })),
  toggleAudio: () => set((state) => ({ audioOn: !state.audioOn })),
  closeAllUi: () =>
    set({ ficha: null, contactOpen: false, teleportMenuOpen: false }),
  isUiOpen: () => {
    const state = get()
    return state.ficha !== null || state.contactOpen || state.teleportMenuOpen
  },
}))
