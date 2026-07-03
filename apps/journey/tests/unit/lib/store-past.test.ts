import { beforeEach, describe, expect, it } from 'vitest'
import { INITIAL_JOURNEY_STATE, useJourneyStore } from '../../../src/lib/store'

beforeEach(() => {
  useJourneyStore.setState({ ...INITIAL_JOURNEY_STATE }, false)
})

describe('portal al pasado', () => {
  it('Given el presente When se entra al pasado de la sala 1 Then past=1 y se pide el teleport a su sala espejo', () => {
    useJourneyStore.getState().enterPast(1, { x: 40, z: 20.6 })

    const s = useJourneyStore.getState()
    expect(s.past).toBe(1)
    expect(s.teleportTarget).toEqual({ x: 40, z: 20.6 })
  })

  it('Given el pasado When se sale Then past=null y se teletransporta al punto de retorno', () => {
    useJourneyStore.getState().enterPast(0, { x: 40, z: 4 })
    useJourneyStore.getState().exitPast({ x: 1, z: 5 })

    const s = useJourneyStore.getState()
    expect(s.past).toBe(null)
    expect(s.teleportTarget).toEqual({ x: 1, z: 5 })
  })

  it('Given un teleport pendiente When se consume Then el target queda null', () => {
    useJourneyStore.getState().requestTeleport({ x: 3, z: 9 })

    const target = useJourneyStore.getState().consumeTeleport()

    expect(target).toEqual({ x: 3, z: 9 })
    expect(useJourneyStore.getState().teleportTarget).toBe(null)
  })

  it('Given ningun teleport pendiente When se consume Then retorna null', () => {
    expect(useJourneyStore.getState().consumeTeleport()).toBe(null)
  })
})

describe('panel de contacto (CTA de la CIMA)', () => {
  it('Given el panel cerrado When se abre Then la UI queda abierta (bloquea controles)', () => {
    useJourneyStore.getState().openContact()

    expect(useJourneyStore.getState().contactOpen).toBe(true)
    expect(useJourneyStore.getState().isUiOpen()).toBe(true)
  })

  it('Given el panel abierto When se cierra Then la UI queda libre', () => {
    useJourneyStore.getState().openContact()
    useJourneyStore.getState().closeContact()

    expect(useJourneyStore.getState().contactOpen).toBe(false)
    expect(useJourneyStore.getState().isUiOpen()).toBe(false)
  })
})
