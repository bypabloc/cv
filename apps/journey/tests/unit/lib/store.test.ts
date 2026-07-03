import { beforeEach, describe, expect, it, vi } from 'vitest'
import { INITIAL_JOURNEY_STATE, useJourneyStore } from '../../../src/lib/store'

beforeEach(() => {
  useJourneyStore.setState({ ...INITIAL_JOURNEY_STATE }, false)
})

describe('useJourneyStore', () => {
  it('Given el estado inicial When se lee Then arranca en la sala 0, tier full y sin UI abierta', () => {
    const s = useJourneyStore.getState()

    expect(s.tier).toBe('full')
    expect(s.locale).toBe('es')
    expect(s.zone).toEqual({ kind: 'room', index: 0 })
    expect(s.doorsOpen).toEqual({})
    expect(s.ficha).toBe(null)
    expect(s.isUiOpen()).toBe(false)
  })

  it('Given configure When se setea tier y locale Then el estado los refleja', () => {
    useJourneyStore.getState().configure('reduced', 'en')

    expect(useJourneyStore.getState().tier).toBe('reduced')
    expect(useJourneyStore.getState().locale).toBe('en')
  })

  it('Given una puerta cerrada When se abre Then queda abierta (idempotente)', () => {
    useJourneyStore.getState().openDoor(0)
    useJourneyStore.getState().openDoor(0)

    expect(useJourneyStore.getState().doorsOpen).toEqual({ 0: true })
  })

  it('Given una ficha abierta When se consulta la UI Then bloquea los controles y Close la libera', () => {
    useJourneyStore.getState().openFicha(1, 'retos')

    expect(useJourneyStore.getState().ficha).toEqual({
      roomIndex: 1,
      kind: 'retos',
    })
    expect(useJourneyStore.getState().isUiOpen()).toBe(true)

    useJourneyStore.getState().closeFicha()

    expect(useJourneyStore.getState().ficha).toBe(null)
    expect(useJourneyStore.getState().isUiOpen()).toBe(false)
  })

  it('Given un interactable registrado When se activa el actual Then invoca su onActivate', () => {
    const onActivate = vi.fn()
    const s = useJourneyStore.getState()
    s.registerInteractable({
      id: 'door-0',
      x: 0,
      z: 14,
      radius: 2,
      label: { es: 'Abrir', en: 'Open' },
      onActivate,
    })
    s.setActiveInteractable('door-0')

    useJourneyStore.getState().activateCurrent()

    expect(onActivate).toHaveBeenCalledTimes(1)
  })

  it('Given ningun interactable activo When se activa Then no lanza', () => {
    expect(() => useJourneyStore.getState().activateCurrent()).not.toThrow()
  })

  it('Given un interactable When se desregistra Then desaparece y se limpia el activo', () => {
    const s = useJourneyStore.getState()
    s.registerInteractable({
      id: 'ficha-1',
      x: 1,
      z: 1,
      radius: 2,
      label: { es: 'Leer', en: 'Read' },
      onActivate: () => undefined,
    })
    s.setActiveInteractable('ficha-1')

    useJourneyStore.getState().unregisterInteractable('ficha-1')

    expect(useJourneyStore.getState().interactables).toEqual({})
    expect(useJourneyStore.getState().activeInteractableId).toBe(null)
  })

  it('Given el pointer lock When cambia Then el estado lo refleja', () => {
    useJourneyStore.getState().setLocked(true)

    expect(useJourneyStore.getState().isLocked).toBe(true)
  })

  it('Given un cambio de zona When se setea Then el estado lo refleja', () => {
    useJourneyStore.getState().setZone({ kind: 'corridor', index: 0 })

    expect(useJourneyStore.getState().zone).toEqual({
      kind: 'corridor',
      index: 0,
    })
  })
})
