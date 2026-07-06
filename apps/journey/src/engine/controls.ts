/**
 * @module controls (engine)
 * @description Camaras e input del motor vanilla: 3a persona DEFAULT
 *   (orbita con drag + seguimiento con lerp + clamp por zona) y POV con
 *   pointer-lock (tecla V alterna, colision identica en ambos — AC-5).
 *   Teclado + joystick tactil + boton de accion (AC-8) y tour opcional
 *   que mueve AL JUGADOR sobre el riel de lib/tour.
 */
import type { PerspectiveCamera } from 'three'
import type { Box2 } from '../lib/collision'
import { circleIntersectsBox, resolveMovement } from '../lib/collision'
import {
  doorBlockerBox,
  EYE_HEIGHT,
  type JourneyLayout,
  type PastRoomLayout,
  PLAYER_RADIUS,
  WALK_SPEED,
  type Zone,
  zoneAt,
} from '../lib/layout'
import {
  buildTourTimeline,
  type TourTimeline,
  tourPoseAt,
  tourTimeForRoom,
} from '../lib/tour'
import type { CharacterHandle } from './character'
import {
  activateCurrent,
  type CameraMode,
  collectObstacles,
  type EngineState,
  type InteractableBubble,
  isUiOpen,
  nearestInteractableIn,
} from './state'

export interface ControlsHud {
  showPrompt(label: string | null): void
  /** Burbuja de habla suelta del NPC activo (null la oculta). */
  setBubble(bubble: InteractableBubble | null): void
  setCameraMode(mode: CameraMode): void
  setPointerLocked(locked: boolean): void
}

export interface TouchElements {
  joystick: HTMLElement
  stick: HTMLElement
  actionButton: HTMLElement
}

export interface ControlsDeps {
  camera: PerspectiveCamera
  player: CharacterHandle
  layout: JourneyLayout
  pastRooms: readonly PastRoomLayout[]
  /** Muros + muros del pasado (datos, viven siempre). */
  walls: readonly Box2[]
  state: EngineState
  hud: ControlsHud
  canvas: HTMLCanvasElement
  touch?: TouchElements
  onZoneChange(zone: Zone): void
  toggleTeleport(): void
  closeUi(): void
  onTourStart?(): void
  onTourStop?(): void
}

export interface Controls {
  update(t: number, dt: number): void
  /** Mueve al jugador (esclusa/teleport/portal) y re-encaja la camara. */
  teleport(x: number, z: number): void
  toggleCameraMode(): void
  startTour(): void
  stopTour(): void
  dispose(): void
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

const CAM_DISTANCE = 4.2
const CAM_HEIGHT = 2.2
const CAM_MARGIN = 0.35
const HEAD_LOOK_Y = 1.2

export function createControls(deps: ControlsDeps): Controls {
  const { camera, player, layout, state, hud, canvas } = deps
  const keys: MoveState = {
    forward: false,
    back: false,
    left: false,
    right: false,
  }
  const joy = { x: 0, y: 0 }
  const pos = { x: 0, z: 0 }
  // yaw 0 => la camara mira hacia +Z (el recorrido avanza en +Z)
  let yaw = 0
  let pitch = 0.14
  let povPitch = 0
  let time = 0
  let timeline: TourTimeline | null = null
  let tourOffset = 0
  let lastTourX = 0
  let lastTourZ = 0

  // spawn: primer cuarto de la sala 0 (como el MVP actual)
  const firstRoom = layout.rooms[0]
  pos.z = firstRoom ? firstRoom.z - firstRoom.depth / 4 : 2
  player.group.position.set(pos.x, 0, pos.z)
  player.group.rotation.y = 0

  // -------------------------------------------------------------------------
  // Movimiento + colision (identica en 3a persona y POV)
  // -------------------------------------------------------------------------

  function closedDoorBoxes(): Box2[] {
    return layout.doors
      .filter((door) => !state.doorsOpen.has(door.corridorIndex))
      .map(doorBlockerBox)
  }

  function applyMovement(dt: number): boolean {
    if (state.playerSeat) {
      return false // sentado: sin WASD hasta levantarse con E
    }
    const ix = (keys.right ? 1 : 0) - (keys.left ? 1 : 0) + joy.x
    const iz = (keys.back ? 1 : 0) - (keys.forward ? 1 : 0) + joy.y
    const mag = Math.hypot(ix, iz)
    if (mag < 0.05) {
      return false
    }
    const nx = ix / Math.max(mag, 1)
    const nz = iz / Math.max(mag, 1)
    const sinY = Math.sin(yaw)
    const cosY = Math.cos(yaw)
    // base relativa a la camara: forward = (sinψ, cosψ) y right = f×up =
    // (-cosψ, sinψ). W (iz=-1) avanza hacia donde mira; D/joystick-derecha
    // (ix=+1) se mueve a la DERECHA de la pantalla.
    const dirX = -cosY * nx - sinY * nz
    const dirZ = sinY * nx - cosY * nz
    const step = WALK_SPEED * dt
    const candidates = [
      ...deps.walls,
      ...closedDoorBoxes(),
      ...collectObstacles(state),
    ]
    // anti-atasco: una caja que YA contiene al jugador (un NPC que camino
    // sobre el, un teleport) no bloquea — siempre se puede salir
    const blockers = candidates.filter(
      (box) => !circleIntersectsBox(pos.x, pos.z, PLAYER_RADIUS, box),
    )
    const next = resolveMovement(
      pos,
      { x: dirX * step, z: dirZ * step },
      PLAYER_RADIUS,
      blockers,
    )
    pos.x = next.x
    pos.z = next.z
    player.group.position.x = pos.x
    player.group.position.z = pos.z
    // el personaje rota hacia la direccion de movimiento (3a persona)
    if (state.cameraMode === 'third') {
      player.group.rotation.y = Math.atan2(dirX, dirZ)
    } else {
      player.group.rotation.y = yaw + Math.PI
    }
    return true
  }

  // -------------------------------------------------------------------------
  // Camara
  // -------------------------------------------------------------------------

  interface ZoneRect {
    x: number
    z: number
    width: number
    depth: number
    height: number
  }

  function activeZoneRect(): ZoneRect | null {
    if (state.past !== null) {
      return deps.pastRooms[state.past] ?? null
    }
    if (state.zone.kind === 'room') {
      return layout.rooms[state.zone.index] ?? null
    }
    return layout.corridors[state.zone.index] ?? null
  }

  function updateThirdCamera(dt: number, snap: boolean): void {
    const horizontal = CAM_DISTANCE * Math.cos(pitch)
    let cx = pos.x - Math.sin(yaw) * horizontal
    let cz = pos.z - Math.cos(yaw) * horizontal
    let cy = CAM_HEIGHT + CAM_DISTANCE * Math.sin(pitch) * 0.8
    // clamp al rectangulo de la zona activa (sin raycast: cajas conocidas)
    const rect = activeZoneRect()
    if (rect) {
      const minX = rect.x - rect.width / 2 + CAM_MARGIN
      const maxX = rect.x + rect.width / 2 - CAM_MARGIN
      const minZ = rect.z - rect.depth / 2 + CAM_MARGIN
      const maxZ = rect.z + rect.depth / 2 - CAM_MARGIN
      cx = Math.min(Math.max(cx, minX), maxX)
      cz = Math.min(Math.max(cz, minZ), maxZ)
      cy = Math.min(cy, rect.height - 0.15)
    }
    if (snap) {
      camera.position.set(cx, cy, cz)
    } else {
      const k = 1 - 0.001 ** dt
      camera.position.x += (cx - camera.position.x) * k
      camera.position.y += (cy - camera.position.y) * k
      camera.position.z += (cz - camera.position.z) * k
    }
    camera.lookAt(pos.x, HEAD_LOOK_Y, pos.z)
  }

  function updatePovCamera(): void {
    camera.position.set(pos.x, EYE_HEIGHT, pos.z)
    camera.rotation.order = 'YXZ'
    camera.rotation.y = yaw + Math.PI
    camera.rotation.x = povPitch
    camera.rotation.z = 0
  }

  function updateCamera(dt: number, snap = false): void {
    if (state.cameraMode === 'pov') {
      updatePovCamera()
    } else {
      updateThirdCamera(dt, snap)
    }
  }

  // -------------------------------------------------------------------------
  // Proximidad + zona
  // -------------------------------------------------------------------------

  let lastPromptText: string | null = null

  function updateProximity(): void {
    const active = nearestInteractableIn(state.interactables, pos.x, pos.z)
    const item = active ? state.interactables.get(active) : null
    if (active !== state.activeId) {
      state.activeId = active
      hud.setBubble(item?.bubble ?? null)
    }
    // el label puede mutar tras activar (toggles): refresco por TEXTO
    const label = item ? item.label[state.locale] : null
    if (label !== lastPromptText) {
      lastPromptText = label
      hud.showPrompt(label)
    }
  }

  function updateZone(): void {
    if (state.past !== null) {
      return
    }
    const zone = zoneAt(layout, pos.z)
    if (zone.kind !== state.zone.kind || zone.index !== state.zone.index) {
      deps.onZoneChange(zone)
    }
  }

  // -------------------------------------------------------------------------
  // Tour (riel opcional — mueve al jugador, la camara 3a lo sigue sola)
  // -------------------------------------------------------------------------

  function updateTour(): void {
    if (!timeline) {
      return
    }
    const pose = tourPoseAt(timeline, time + tourOffset)
    pos.x = pose.x
    pos.z = pose.z
    player.group.position.x = pos.x
    player.group.position.z = pos.z
    const moved = Math.hypot(pose.x - lastTourX, pose.z - lastTourZ)
    player.setWalking(moved > 0.002)
    if (moved > 0.002) {
      player.group.rotation.y = Math.atan2(
        pose.lookX - pose.x,
        pose.lookZ - pose.z,
      )
      // la camara mira en la direccion del riel
      yaw = Math.atan2(pose.lookX - pose.x, pose.lookZ - pose.z)
    }
    lastTourX = pose.x
    lastTourZ = pose.z
  }

  // -------------------------------------------------------------------------
  // Input: teclado
  // -------------------------------------------------------------------------

  function onActionKey(code: string): void {
    if (code === 'KeyE') {
      if (!isUiOpen(state)) {
        activateCurrent(state, { x: pos.x, z: pos.z })
      }
    } else if (code === 'KeyV') {
      controls.toggleCameraMode()
    } else if (code === 'KeyM') {
      deps.toggleTeleport()
    } else if (code === 'Escape') {
      deps.closeUi()
    }
  }

  function onKeyDown(event: KeyboardEvent): void {
    const move = MOVE_KEYS[event.code]
    if (move) {
      keys[move] = true
      if (state.tourOn) {
        controls.stopTour()
      }
      return
    }
    onActionKey(event.code)
  }

  function onKeyUp(event: KeyboardEvent): void {
    const move = MOVE_KEYS[event.code]
    if (move) {
      keys[move] = false
    }
  }

  // -------------------------------------------------------------------------
  // Input: puntero (drag 3a persona + pointer-lock POV)
  // -------------------------------------------------------------------------

  let dragId: number | null = null
  let lastX = 0
  let lastY = 0
  // en touch NO hay pointer-lock: el POV tambien mira con drag
  const coarsePointer = window.matchMedia('(pointer: coarse)').matches

  function onCanvasPointerDown(event: PointerEvent): void {
    if (state.cameraMode === 'pov' && !coarsePointer) {
      if (document.pointerLockElement !== canvas && !isUiOpen(state)) {
        canvas.requestPointerLock()
      }
      return
    }
    dragId = event.pointerId
    lastX = event.clientX
    lastY = event.clientY
  }

  function onPointerMove(event: PointerEvent): void {
    if (event.pointerId === joyPointerId) {
      moveJoystick(event)
      return
    }
    if (dragId !== event.pointerId) {
      return
    }
    const dx = event.clientX - lastX
    const dy = event.clientY - lastY
    yaw -= dx * 0.005
    if (state.cameraMode === 'pov') {
      povPitch = Math.min(Math.max(povPitch - dy * 0.005, -1.35), 1.35)
    } else {
      pitch = Math.min(Math.max(pitch + dy * 0.004, -0.15), 0.55)
    }
    lastX = event.clientX
    lastY = event.clientY
  }

  function onPointerUp(event: PointerEvent): void {
    if (event.pointerId === dragId) {
      dragId = null
    }
    if (event.pointerId === joyPointerId) {
      resetJoystick()
    }
  }

  function onMouseMove(event: MouseEvent): void {
    if (document.pointerLockElement !== canvas) {
      return
    }
    yaw -= event.movementX * 0.0024
    povPitch = Math.min(
      Math.max(povPitch - event.movementY * 0.0024, -1.35),
      1.35,
    )
  }

  function onPointerLockChange(): void {
    hud.setPointerLocked(document.pointerLockElement === canvas)
  }

  // -------------------------------------------------------------------------
  // Input: joystick tactil + boton de accion
  // -------------------------------------------------------------------------

  let joyPointerId: number | null = null
  let joyCenterX = 0
  let joyCenterY = 0

  function onJoystickDown(event: PointerEvent): void {
    joyPointerId = event.pointerId
    const rect = deps.touch?.joystick.getBoundingClientRect()
    if (rect) {
      joyCenterX = rect.left + rect.width / 2
      joyCenterY = rect.top + rect.height / 2
    }
    if (state.tourOn) {
      controls.stopTour()
    }
  }

  function moveJoystick(event: PointerEvent): void {
    const max = 44
    let dx = event.clientX - joyCenterX
    let dy = event.clientY - joyCenterY
    const d = Math.hypot(dx, dy)
    if (d > max) {
      dx *= max / d
      dy *= max / d
    }
    if (deps.touch) {
      deps.touch.stick.style.transform = `translate(${dx}px, ${dy}px)`
    }
    joy.x = dx / max
    joy.y = dy / max
  }

  function resetJoystick(): void {
    joyPointerId = null
    joy.x = 0
    joy.y = 0
    if (deps.touch) {
      deps.touch.stick.style.transform = 'translate(0, 0)'
    }
  }

  function onActionButton(): void {
    if (!isUiOpen(state)) {
      activateCurrent(state, { x: pos.x, z: pos.z })
    }
  }

  // -------------------------------------------------------------------------
  // Wiring
  // -------------------------------------------------------------------------

  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('keyup', onKeyUp)
  canvas.addEventListener('pointerdown', onCanvasPointerDown)
  window.addEventListener('pointermove', onPointerMove)
  window.addEventListener('pointerup', onPointerUp)
  window.addEventListener('pointercancel', onPointerUp)
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('pointerlockchange', onPointerLockChange)
  deps.touch?.joystick.addEventListener('pointerdown', onJoystickDown)
  deps.touch?.actionButton.addEventListener('pointerdown', onActionButton)

  const controls: Controls = {
    update(_t, dt) {
      time += dt
      if (isUiOpen(state)) {
        // la UI necesita el cursor: soltar el lock y congelar el riel
        if (document.pointerLockElement === canvas) {
          document.exitPointerLock()
        }
        if (state.tourOn) {
          tourOffset -= dt
        }
        if (state.playerSeat) {
          player.setPose('sit')
        } else {
          player.setWalking(false)
        }
        player.update(time, dt)
        updateCamera(dt)
        return
      }
      if (state.tourOn) {
        updateTour()
      } else if (state.playerSeat) {
        // sentado: posicion/orientacion fijas de la silla + pose sit; el
        // interactable de la silla (radio 1.4) sigue activo para levantarse
        pos.x = state.playerSeat.x
        pos.z = state.playerSeat.z
        player.group.position.set(pos.x, 0, pos.z)
        player.group.rotation.y = state.playerSeat.rotationY
        player.setPose('sit')
      } else {
        player.setWalking(applyMovement(dt))
      }
      updateZone()
      updateProximity()
      player.update(time, dt)
      updateCamera(dt)
    },

    teleport(x, z) {
      // cualquier teleport (esclusa, HUD, portal, cruce de puerta) levanta
      // al jugador: la sala nueva nunca arranca con el movimiento congelado
      state.playerSeat = null
      pos.x = x
      pos.z = z
      player.group.position.x = x
      player.group.position.z = z
      if (state.tourOn && timeline) {
        const zone = zoneAt(layout, z)
        tourOffset = tourTimeForRoom(timeline, zone.index) - time
      }
      updateCamera(0, true)
    },

    toggleCameraMode() {
      if (state.cameraMode === 'third') {
        state.cameraMode = 'pov'
        player.setVisible(false)
        hud.setCameraMode('pov')
        povPitch = 0
        if (!isUiOpen(state) && !coarsePointer) {
          canvas.requestPointerLock()
        }
      } else {
        state.cameraMode = 'third'
        player.setVisible(true)
        hud.setCameraMode('third')
        if (document.pointerLockElement === canvas) {
          document.exitPointerLock()
        }
      }
    },

    startTour() {
      if (state.tourOn) {
        return
      }
      if (state.cameraMode === 'pov') {
        controls.toggleCameraMode()
      }
      timeline ??= buildTourTimeline(layout)
      state.tourOn = true
      tourOffset = tourTimeForRoom(timeline, state.zone.index) - time
      lastTourX = pos.x
      lastTourZ = pos.z
      deps.onTourStart?.()
    },

    stopTour() {
      if (!state.tourOn) {
        return
      }
      state.tourOn = false
      player.setWalking(false)
      deps.onTourStop?.()
    },

    dispose() {
      window.removeEventListener('keydown', onKeyDown)
      window.removeEventListener('keyup', onKeyUp)
      canvas.removeEventListener('pointerdown', onCanvasPointerDown)
      window.removeEventListener('pointermove', onPointerMove)
      window.removeEventListener('pointerup', onPointerUp)
      window.removeEventListener('pointercancel', onPointerUp)
      document.removeEventListener('mousemove', onMouseMove)
      document.removeEventListener('pointerlockchange', onPointerLockChange)
      deps.touch?.joystick.removeEventListener('pointerdown', onJoystickDown)
      deps.touch?.actionButton.removeEventListener(
        'pointerdown',
        onActionButton,
      )
      if (document.pointerLockElement === canvas) {
        document.exitPointerLock()
      }
    },
  }

  // camara inicial detras del jugador
  updateCamera(0, true)

  return controls
}
