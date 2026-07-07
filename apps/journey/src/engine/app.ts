/**
 * @module app (engine)
 * @description startJourney: composicion del motor vanilla — renderer por
 *   tier (DPR capado, NoToneMapping, sombra solo full), luces globales
 *   hemi + direccional, jugador chibi, RAF unico con degradacion
 *   automatica (FPS < 30 por 5 s -> baja DPR y apaga acentos), log de
 *   presupuesto en DEV (AC-14) y dispose TOTAL al salir.
 */
import {
  Clock,
  DirectionalLight,
  HemisphereLight,
  NoToneMapping,
  PerspectiveCamera,
  Scene,
  SRGBColorSpace,
  Vector3,
  WebGLRenderer,
} from 'three'
import {
  buildLayout,
  buildPastRooms,
  buildPastWallBoxes,
  buildWallBoxes,
} from '../lib/layout'
import { buildRooms, type Locale, type RoomId } from '../lib/rooms'
import { ambientAudio, sfx } from './audio'
import {
  type CharacterSpec,
  configureCharacters,
  makeCharacter,
} from './character'
import { createControls } from './controls'
import { createHud } from './hud'
import { configureLoaders } from './loaders'
import { createPostFx } from './postfx'
import { createEngineState, type EngineState, type EngineTier } from './state'
import { configureToon, disposeDeep, disposeToonPool } from './toon'
import { createWorld } from './world'

export interface JourneyHandle {
  dispose(): void
}

export interface StartOptions {
  container: HTMLElement
  tier: EngineTier
  locale: Locale
  onExit: () => void
}

/** Jugador: short negro, hoodie azul Destacame, jeans — sin accesorios
 *  (el badge blanco en el pecho se elimino a pedido del usuario). */
const PLAYER_SPEC: CharacterSpec = {
  skin: '#e8b48c',
  hair: { style: 'short', color: '#181410' },
  top: '#0052cc',
  bottom: '#31435e',
  faceSeed: 5,
}

/** Perfil que suena: la sala segun la zona (en pasillo, la sala destino)
 *  o el pasado que se visita (tratamiento sepia unificado). */
function audioTarget(
  state: EngineState,
  rooms: readonly { id: RoomId }[],
): { room: RoomId; past: boolean } {
  if (state.past !== null) {
    return { room: rooms[state.past]?.id ?? 'aula', past: true }
  }
  const index =
    state.zone.kind === 'corridor' ? state.zone.index + 1 : state.zone.index
  return { room: rooms[index]?.id ?? 'aula', past: false }
}

export async function startJourney(opts: StartOptions): Promise<JourneyHandle> {
  const { container, tier, locale } = opts
  configureToon({ anisotropy: tier === 'full' ? 4 : 2 })
  configureCharacters({ shadows: tier === 'full' ? 'cast' : 'blob' })

  // datos (los mismos modulos puros del MVP)
  const rooms = buildRooms()
  const layout = buildLayout(rooms)
  const walls = buildWallBoxes(layout)
  const pastRooms = buildPastRooms(layout)
  const pastWalls = buildPastWallBoxes(pastRooms)
  const state = createEngineState(tier, locale)

  // canvas dentro de un wrap propio (recibe el filter sepia del pasado)
  const canvasWrap = document.createElement('div')
  canvasWrap.style.cssText = 'position:absolute;inset:0'
  container.appendChild(canvasWrap)

  const renderer = new WebGLRenderer({
    antialias: true,
    powerPreference: 'high-performance',
  })
  const maxDpr = tier === 'full' ? 2 : 1.5
  const dpr = Math.min(window.devicePixelRatio, maxDpr)
  renderer.setPixelRatio(dpr)
  renderer.setSize(container.clientWidth, container.clientHeight)
  renderer.outputColorSpace = SRGBColorSpace
  // colores planos manga: sin tone mapping (decision 3 del plan)
  renderer.toneMapping = NoToneMapping
  renderer.shadowMap.enabled = tier === 'full'
  canvasWrap.appendChild(renderer.domElement)
  configureLoaders(renderer)

  const camera = new PerspectiveCamera(
    66,
    container.clientWidth / Math.max(container.clientHeight, 1),
    0.05,
    80,
  )
  const scene = new Scene()
  // el composer corre a resolucion CAPADA (moderada) — palanca #1 de
  // fill-rate; el halftone disimula la baja de nitidez. El DPR del renderer
  // (para el blit final + shadow map) se mantiene. El contorno de los
  // personajes ya no va por OutlinePass: es el shell skinned de toon.ts.
  let composerDpr = Math.min(dpr, 1.25)
  const postFx = createPostFx({
    renderer,
    scene,
    camera,
    width: container.clientWidth,
    height: container.clientHeight,
    pixelRatio: composerDpr,
  })

  // luces globales: 1 hemisferio + 1 direccional (sombra 1024 solo full).
  // Cielo mas claro + suelo levantado (menos crush en sombra) + mas
  // intensidad -> paleta clara/pastel (pedido del dueno 2026-07-07).
  const hemi = new HemisphereLight('#eaf0ff', '#8a8478', 1.7)
  const sun = new DirectionalLight('#fff6ea', 1.35)
  sun.position.set(4, 8, -4)
  if (tier === 'full') {
    sun.castShadow = true
    sun.shadow.mapSize.set(1024, 1024)
    sun.shadow.bias = -0.0004
    sun.shadow.normalBias = 0.02
    sun.shadow.camera.near = 0.5
    sun.shadow.camera.far = 30
  }
  scene.add(hemi, sun, sun.target)

  const player = makeCharacter(PLAYER_SPEC)
  scene.add(player.group)

  // HUD (DOM) — el boton Tour: reduced siempre, full solo con ?tour
  const showTourButton =
    tier === 'reduced' ||
    new URLSearchParams(window.location.search).has('tour')
  const hud = createHud({
    container,
    canvasWrap,
    locale,
    rooms,
    state,
    showTourButton,
    actions: {
      onExit: () => opts.onExit(),
      onTeleport: (index) => {
        void world.teleportToRoom(index)
      },
      onToggleAudio: (on) => {
        if (on) {
          sfx.unlock()
          sfx.setMuted(false)
          const target = audioTarget(state, rooms)
          ambientAudio.enable(target.room, target.past)
        } else {
          sfx.setMuted(true)
          ambientAudio.disable()
        }
      },
      onToggleCamera: () => controls.toggleCameraMode(),
      onStartTour: () => controls.startTour(),
      onStopTour: () => controls.stopTour(),
    },
  })

  // sincroniza HUD + audio con la zona/pasado actual del estado
  function syncZoneUi(): void {
    hud.setZoneFromState()
    if (state.audioOn) {
      const target = audioTarget(state, rooms)
      ambientAudio.setRoom(target.room, target.past)
    }
  }

  const controls = createControls({
    camera,
    player,
    layout,
    pastRooms,
    walls: [...walls, ...pastWalls],
    state,
    hud,
    canvas: renderer.domElement,
    touch: hud.touch ?? undefined,
    onZoneChange: (zone) => {
      world.setZone(zone)
      syncZoneUi()
    },
    toggleTeleport: () => hud.toggleTeleport(),
    closeUi: () => hud.closeAll(),
    onTourStart: () => {
      // el riel del tour setea la posicion directo (sin colision): cruza
      // los vanos sin abrir nada — los portales no tienen estado abierto.
      hud.setTour(true)
    },
    onTourStop: () => hud.setTour(false),
  })

  const world = createWorld({
    scene,
    renderer,
    camera,
    rooms,
    layout,
    pastRooms,
    state,
    fade: (on, style) => hud.fade(on, style),
    setPastMode: (on) => hud.setPastMode(on),
    ui: {
      openFicha: (roomIndex, kind) => hud.openFicha(roomIndex, kind),
      openContact: () => hud.openContact(),
      openStory: (title, paragraphs) => hud.openStory(title, paragraphs),
      openDialog: (npc, onClose) => hud.openDialog(npc, onClose),
      openShowcase: (ref) => hud.openShowcase(ref),
    },
    teleportPlayer: (x, z) => controls.teleport(x, z),
    shadowLight: tier === 'full' ? sun : undefined,
    onZoneApplied: () => syncZoneUi(),
  })

  function onResize(): void {
    camera.aspect = container.clientWidth / Math.max(container.clientHeight, 1)
    camera.updateProjectionMatrix()
    renderer.setSize(container.clientWidth, container.clientHeight)
    postFx.resize(container.clientWidth, container.clientHeight)
  }
  window.addEventListener('resize', onResize)

  // el audio (ambiente + SFX) arranca en el PRIMER gesto del usuario
  // (autoplay policy) — sin configurar nada; el toggle del HUD silencia todo
  function unlockAudio(): void {
    window.removeEventListener('pointerdown', unlockAudio)
    window.removeEventListener('keydown', unlockAudio)
    if (!state.audioOn) {
      return
    }
    sfx.unlock()
    const target = audioTarget(state, rooms)
    ambientAudio.enable(target.room, target.past)
  }
  window.addEventListener('pointerdown', unlockAudio)
  window.addEventListener('keydown', unlockAudio)

  // proyeccion 3D -> pantalla para la burbuja de habla del HUD
  const projectVec = new Vector3()
  function projectToScreen(
    x: number,
    y: number,
    z: number,
  ): { x: number; y: number; behind: boolean } {
    projectVec.set(x, y, z).project(camera)
    return {
      x: (projectVec.x * 0.5 + 0.5) * container.clientWidth,
      y: (-projectVec.y * 0.5 + 0.5) * container.clientHeight,
      behind: projectVec.z > 1,
    }
  }

  // RAF unico: controls -> world -> render (+ degradacion + budget DEV)
  const clock = new Clock()
  let raf = 0
  let lowFpsTime = 0
  let accentsOn = true
  // -5 => el primer log de presupuesto sale en el primer frame (AC-14)
  let lastBudgetLog = -5
  // pasos del jugador por distancia recorrida (zancada ~0.62 m)
  let stride = 0
  let lastPx = player.group.position.x
  let lastPz = player.group.position.z

  function degrade(dt: number): void {
    if (1 / dt < 30) {
      lowFpsTime += dt
    } else {
      lowFpsTime = 0
    }
    if (lowFpsTime <= 5) {
      return
    }
    lowFpsTime = 0
    if (composerDpr > 0.85) {
      // baja la resolucion INTERNA del composer: el renderer.setPixelRatio ya
      // no afecta el fill-rate (todo pasa por el composer, que tiene su propio
      // pixelRatio). Piso 0.85 — mas abajo los puntos del halftone se agrandan.
      composerDpr = Math.max(0.85, composerDpr - 0.2)
      postFx.setPixelRatio(composerDpr)
    } else if (accentsOn) {
      accentsOn = false
      world.setAccentsEnabled(false)
    }
  }

  function frame(): void {
    raf = requestAnimationFrame(frame)
    const dt = Math.min(clock.getDelta(), 0.05)
    const t = clock.elapsedTime
    controls.update(t, dt)
    world.update(t, dt)
    hud.updateBubble(projectToScreen)
    // audio posicional: listener en el jugador + pasos por zancada
    const px = player.group.position.x
    const pz = player.group.position.z
    sfx.setListener(px, pz)
    const moved = Math.hypot(px - lastPx, pz - lastPz)
    lastPx = px
    lastPz = pz
    if (moved > 1) {
      stride = 0 // teleport/portal: no cuenta como zancada
    } else {
      stride += moved
      if (stride > 0.62) {
        stride = 0
        sfx.stepAt(px, pz, true)
      }
    }
    sfx.update(dt)
    postFx.render()
    if (dt > 0) {
      degrade(dt)
    }
    if (import.meta.env.DEV && t - lastBudgetLog > 5) {
      lastBudgetLog = t
      // biome-ignore lint/suspicious/noConsole: log de presupuesto AC-14 (solo DEV)
      console.debug(
        '[journey]',
        `calls=${renderer.info.render.calls}`,
        `tris=${renderer.info.render.triangles}`,
        `geoms=${renderer.info.memory.geometries}`,
        `texs=${renderer.info.memory.textures}`,
      )
    }
  }

  await world.init()
  hud.setZoneFromState()
  frame()

  if (import.meta.env.DEV) {
    // introspeccion para los smokes con browser (solo DEV, cero en prod)
    const w = window as Window & {
      __journeyDebug?: {
        player: { x: number; y: number; z: number }
        state: EngineState
        info: WebGLRenderer['info']
        scene: Scene
        camera: PerspectiveCamera
      }
    }
    w.__journeyDebug = {
      player: player.group.position,
      state,
      info: renderer.info,
      scene,
      camera,
    }
  }

  return {
    dispose() {
      cancelAnimationFrame(raf)
      window.removeEventListener('resize', onResize)
      window.removeEventListener('pointerdown', unlockAudio)
      window.removeEventListener('keydown', unlockAudio)
      ambientAudio.disable()
      sfx.dispose()
      controls.dispose()
      world.dispose()
      hud.dispose()
      scene.remove(player.group)
      player.dispose()
      disposeDeep(player.group)
      disposeToonPool()
      postFx.dispose()
      renderer.dispose()
      canvasWrap.remove()
    },
  }
}
