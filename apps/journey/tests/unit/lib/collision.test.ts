import { describe, expect, it } from 'vitest'
import {
  circleIntersectsBox,
  collides,
  nearestInteractable,
  resolveMovement,
} from '../../../src/lib/collision'

const WALL = { minX: 2, maxX: 3, minZ: -10, maxZ: 10 }

describe('circleIntersectsBox', () => {
  it('Given un circulo lejos del box When se testea Then no intersecta', () => {
    expect(circleIntersectsBox(0, 0, 0.35, WALL)).toBe(false)
  })

  it('Given un circulo tocando el borde When se testea Then intersecta', () => {
    expect(circleIntersectsBox(1.8, 0, 0.35, WALL)).toBe(true)
  })

  it('Given un circulo dentro del box When se testea Then intersecta', () => {
    expect(circleIntersectsBox(2.5, 0, 0.35, WALL)).toBe(true)
  })

  it('Given un circulo en diagonal a la esquina When la distancia supera el radio Then no intersecta', () => {
    // esquina (2,-10); distancia desde (1.7,-10.3) = sqrt(0.09+0.09) ~ 0.424
    expect(circleIntersectsBox(1.7, -10.3, 0.35, WALL)).toBe(false)
    expect(circleIntersectsBox(1.8, -10.2, 0.35, WALL)).toBe(true)
  })
})

describe('collides', () => {
  it('Given varios boxes When alguno intersecta Then retorna true', () => {
    const far = { minX: 50, maxX: 51, minZ: 0, maxZ: 1 }

    expect(collides(2.5, 0, 0.35, [far, WALL])).toBe(true)
    expect(collides(0, 0, 0.35, [far, WALL])).toBe(false)
  })
})

describe('resolveMovement', () => {
  it('Given un movimiento libre When se resuelve Then aplica el delta completo', () => {
    const next = resolveMovement({ x: 0, z: 0 }, { x: 0.5, z: -0.25 }, 0.35, [
      WALL,
    ])

    expect(next).toEqual({ x: 0.5, z: -0.25 })
  })

  it('Given un muro en X When se avanza en diagonal Then desliza sobre el muro (bloquea X, conserva Z)', () => {
    const next = resolveMovement({ x: 1.5, z: 0 }, { x: 0.4, z: 0.4 }, 0.35, [
      WALL,
    ])

    expect(next).toEqual({ x: 1.5, z: 0.4 })
  })

  it('Given un muro en Z When se avanza en diagonal Then desliza sobre el muro (bloquea Z, conserva X)', () => {
    const wallZ = { minX: -10, maxX: 10, minZ: 2, maxZ: 3 }
    const next = resolveMovement({ x: 0, z: 1.5 }, { x: 0.4, z: 0.4 }, 0.35, [
      wallZ,
    ])

    expect(next).toEqual({ x: 0.4, z: 1.5 })
  })

  it('Given una esquina cerrada When se avanza contra ambos ejes Then no se mueve', () => {
    const wallZ = { minX: -10, maxX: 10, minZ: 2, maxZ: 3 }
    const next = resolveMovement({ x: 1.5, z: 1.5 }, { x: 0.4, z: 0.4 }, 0.35, [
      WALL,
      wallZ,
    ])

    expect(next).toEqual({ x: 1.5, z: 1.5 })
  })
})

describe('nearestInteractable', () => {
  const items = {
    puerta: { id: 'puerta', x: 0, z: 5, radius: 3 },
    cuaderno: { id: 'cuaderno', x: 2, z: 2, radius: 3 },
  }

  it('Given dos interactables When el jugador esta en rango de uno Then retorna su id', () => {
    expect(nearestInteractable(items, 0, 7)).toBe('puerta')
  })

  it('Given dos interactables en rango When se resuelve Then gana el mas cercano', () => {
    // (1,4): puerta distSq=2, cuaderno distSq=5 -> gana puerta
    expect(nearestInteractable(items, 1, 4)).toBe('puerta')
  })

  it('Given ninguno en rango When se resuelve Then retorna null', () => {
    expect(nearestInteractable(items, -10, -10)).toBe(null)
  })
})
