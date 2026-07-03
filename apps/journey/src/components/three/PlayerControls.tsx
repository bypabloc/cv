/**
 * @component PlayerControls
 * @description Nucleo del walking-sim: WASD/flechas + mouse-look
 *   (PointerLock) con colision circulo-vs-AABB resuelta por eje (slide).
 *   Ademas actualiza la zona actual (sala/pasillo) y el interactable mas
 *   cercano; E activa el interactable, Escape cierra la ficha.
 */
import { PointerLockControls } from '@react-three/drei'
import { useFrame, useThree } from '@react-three/fiber'
import { useEffect, useMemo, useRef } from 'react'
import { Vector3 } from 'three'
import type { Box2 } from '../../lib/collision'
import { nearestInteractable, resolveMovement } from '../../lib/collision'
import {
  doorBlockerBox,
  EYE_HEIGHT,
  type JourneyLayout,
  PLAYER_RADIUS,
  WALK_SPEED,
  zoneAt,
} from '../../lib/layout'
import { useJourneyStore } from '../../lib/store'

interface PlayerControlsProps {
  layout: JourneyLayout
  walls: readonly Box2[]
}

interface MoveState {
  forward: boolean
  back: boolean
  left: boolean
  right: boolean
}

const MOVE_KEYS: Record<string, keyof MoveState> = {
  KeyW: 'forward',
  ArrowUp: 'forward',
  KeyS: 'back',
  ArrowDown: 'back',
  KeyA: 'left',
  ArrowLeft: 'left',
  KeyD: 'right',
  ArrowRight: 'right',
}

interface FrameCtx {
  layout: JourneyLayout
  walls: readonly Box2[]
  forward: Vector3
  side: Vector3
  up: Vector3
}

/** Camina con colision (slide) segun las teclas activas. */
function applyMovement(
  ctx: FrameCtx,
  cam: PerspectiveLike,
  keys: MoveState,
  store: ReturnType<typeof useJourneyStore.getState>,
  dt: number,
): void {
  const dirZ = (keys.forward ? 1 : 0) - (keys.back ? 1 : 0)
  const dirX = (keys.right ? 1 : 0) - (keys.left ? 1 : 0)
  if (dirZ === 0 && dirX === 0) {
    return
  }
  cam.getWorldDirection(ctx.forward)
  ctx.forward.y = 0
  ctx.forward.normalize()
  ctx.side.crossVectors(ctx.forward, ctx.up).normalize()
  const moveX = ctx.forward.x * dirZ + ctx.side.x * dirX
  const moveZ = ctx.forward.z * dirZ + ctx.side.z * dirX
  const len = Math.hypot(moveX, moveZ)
  if (len === 0) {
    return
  }
  const closedDoors = ctx.layout.doors
    .filter((door) => store.doorsOpen[door.corridorIndex] !== true)
    .map(doorBlockerBox)
  const step = (WALK_SPEED * dt) / len
  const next = resolveMovement(
    { x: cam.position.x, z: cam.position.z },
    { x: moveX * step, z: moveZ * step },
    PLAYER_RADIUS,
    [...ctx.walls, ...closedDoors],
  )
  cam.position.x = next.x
  cam.position.z = next.z
}

/** Actualiza zona actual + interactable mas cercano (solo si cambian). */
function updateProximity(
  cam: PerspectiveLike,
  layout: JourneyLayout,
  store: ReturnType<typeof useJourneyStore.getState>,
): void {
  const zone = zoneAt(layout, cam.position.z)
  if (zone.kind !== store.zone.kind || zone.index !== store.zone.index) {
    store.setZone(zone)
  }
  const active = nearestInteractable(
    store.interactables,
    cam.position.x,
    cam.position.z,
  )
  if (active !== store.activeInteractableId) {
    store.setActiveInteractable(active)
  }
}

interface PerspectiveLike {
  position: { x: number; y: number; z: number }
  getWorldDirection: (target: Vector3) => Vector3
}

export function PlayerControls({ layout, walls }: PlayerControlsProps) {
  const camera = useThree((state) => state.camera)
  const keys = useRef<MoveState>({
    forward: false,
    back: false,
    left: false,
    right: false,
  })
  const forward = useMemo(() => new Vector3(), [])
  const side = useMemo(() => new Vector3(), [])
  const up = useMemo(() => new Vector3(0, 1, 0), [])

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const move = MOVE_KEYS[event.code]
      if (move) {
        keys.current[move] = true
        return
      }
      const store = useJourneyStore.getState()
      if (event.code === 'KeyE') {
        store.activateCurrent()
      } else if (event.code === 'KeyM') {
        store.toggleTeleportMenu()
      } else if (event.code === 'Escape') {
        store.closeAllUi()
      }
    }
    const onKeyUp = (event: KeyboardEvent) => {
      const move = MOVE_KEYS[event.code]
      if (move) {
        keys.current[move] = false
      }
    }
    window.addEventListener('keydown', onKeyDown)
    window.addEventListener('keyup', onKeyUp)
    return () => {
      window.removeEventListener('keydown', onKeyDown)
      window.removeEventListener('keyup', onKeyUp)
    }
  }, [])

  // al abrir una ficha se libera el mouse (la UI necesita el cursor)
  useEffect(() => {
    return useJourneyStore.subscribe((state, prev) => {
      if (state.ficha && !prev.ficha) {
        document.exitPointerLock()
      }
    })
  }, [])

  useFrame((_, rawDt) => {
    const dt = Math.min(rawDt, 0.05)
    const store = useJourneyStore.getState()
    const teleport = store.consumeTeleport()
    if (teleport) {
      camera.position.x = teleport.x
      camera.position.z = teleport.z
    }
    if (store.isUiOpen()) {
      return
    }
    const ctx: FrameCtx = { layout, walls, forward, side, up }
    applyMovement(ctx, camera, keys.current, store, dt)
    camera.position.y = EYE_HEIGHT
    updateProximity(camera, layout, store)
  })

  return (
    <PointerLockControls
      makeDefault
      onLock={() => useJourneyStore.getState().setLocked(true)}
      onUnlock={() => useJourneyStore.getState().setLocked(false)}
    />
  )
}
