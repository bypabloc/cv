/**
 * @module collision
 * @description Colision 2D (plano XZ) del walking-sim: circulo del jugador
 *   contra cajas AABB (muros y puertas cerradas). Resolucion por eje
 *   (axis-separated) -> el jugador DESLIZA sobre los muros en vez de
 *   frenarse en seco. Cero physics engine (decision del plan: sin Rapier).
 */

export interface Box2 {
  minX: number
  maxX: number
  minZ: number
  maxZ: number
}

export interface Vec2 {
  x: number
  z: number
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max)
}

/** Interseccion circulo-AABB via punto mas cercano del box al centro. */
export function circleIntersectsBox(
  cx: number,
  cz: number,
  radius: number,
  box: Box2,
): boolean {
  const nearestX = clamp(cx, box.minX, box.maxX)
  const nearestZ = clamp(cz, box.minZ, box.maxZ)
  const dx = cx - nearestX
  const dz = cz - nearestZ
  return dx * dx + dz * dz < radius * radius
}

export function collides(
  x: number,
  z: number,
  radius: number,
  boxes: readonly Box2[],
): boolean {
  return boxes.some((box) => circleIntersectsBox(x, z, radius, box))
}

/**
 * @function resolveMovement
 * @description Aplica un delta de movimiento resolviendo por eje: si el
 *   destino en X colisiona, se cancela solo X (idem Z) -> slide.
 */
export function resolveMovement(
  pos: Vec2,
  delta: Vec2,
  radius: number,
  boxes: readonly Box2[],
): Vec2 {
  let x = pos.x + delta.x
  if (collides(x, pos.z, radius, boxes)) {
    x = pos.x
  }
  let z = pos.z + delta.z
  if (collides(x, z, radius, boxes)) {
    z = pos.z
  }
  return { x, z }
}

export interface InteractablePoint {
  id: string
  x: number
  z: number
  radius: number
}

/**
 * @function nearestInteractable
 * @description Id del interactable mas cercano dentro de su radio, o null.
 *   Es el sistema de interaccion por PROXIMIDAD del MVP (sin raycast).
 */
export function nearestInteractable(
  items: Record<string, InteractablePoint>,
  x: number,
  z: number,
): string | null {
  let bestId: string | null = null
  let bestDistSq = Number.POSITIVE_INFINITY
  for (const item of Object.values(items)) {
    const dx = item.x - x
    const dz = item.z - z
    const distSq = dx * dx + dz * dz
    if (distSq <= item.radius * item.radius && distSq < bestDistSq) {
      bestDistSq = distSq
      bestId = item.id
    }
  }
  return bestId
}
