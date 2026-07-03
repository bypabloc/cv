import { beforeEach, describe, expect, it } from 'vitest'
import { INITIAL_JOURNEY_STATE, useJourneyStore } from '../../../src/lib/store'

beforeEach(() => {
  useJourneyStore.setState({ ...INITIAL_JOURNEY_STATE }, false)
})

describe('menu de teletransporte', () => {
  it('Given el menu cerrado When se toglea Then abre, bloquea la UI y vuelve a cerrar', () => {
    useJourneyStore.getState().toggleTeleportMenu()

    expect(useJourneyStore.getState().teleportMenuOpen).toBe(true)
    expect(useJourneyStore.getState().isUiOpen()).toBe(true)

    useJourneyStore.getState().toggleTeleportMenu()

    expect(useJourneyStore.getState().teleportMenuOpen).toBe(false)
    expect(useJourneyStore.getState().isUiOpen()).toBe(false)
  })
})

describe('audio ambiente (opt-in)', () => {
  it('Given el estado inicial When se lee Then el audio arranca SIEMPRE apagado (autoplay policy)', () => {
    expect(useJourneyStore.getState().audioOn).toBe(false)
  })

  it('Given el audio apagado When se toglea Then enciende y vuelve a apagar', () => {
    useJourneyStore.getState().toggleAudio()

    expect(useJourneyStore.getState().audioOn).toBe(true)

    useJourneyStore.getState().toggleAudio()

    expect(useJourneyStore.getState().audioOn).toBe(false)
  })
})

describe('closeAllUi', () => {
  it('Given ficha, contacto y menu abiertos When se cierra todo Then la UI queda libre', () => {
    const s = useJourneyStore.getState()
    s.openFicha(0, 'retos')
    s.openContact()
    s.toggleTeleportMenu()

    useJourneyStore.getState().closeAllUi()

    const after = useJourneyStore.getState()
    expect(after.ficha).toBe(null)
    expect(after.contactOpen).toBe(false)
    expect(after.teleportMenuOpen).toBe(false)
    expect(after.isUiOpen()).toBe(false)
  })
})
