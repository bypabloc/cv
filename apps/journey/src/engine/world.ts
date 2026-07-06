/**
 * @module world (engine)
 * @description Zone manager del motor vanilla: manifest WORLD data-driven
 *   (chunk por sala via dynamic import), shells cacheados por zona
 *   (muros/piso/techo/portal — baratos, viven hasta el exit), carga por
 *   ESCLUSA (cruzar el portal libera el contenido de la sala anterior y
 *   precarga la siguiente con renderer.compile), fade si la precarga no
 *   llego, teleport y portal al pasado. Regla de memoria: 1 solo content de
 *   sala vivo (AC-3/AC-4).
 */
import {
  Color,
  type DirectionalLight,
  Fog,
  Group,
  Mesh,
  type PerspectiveCamera,
  PointLight,
  type Scene,
  type WebGLRenderer,
} from 'three'
import type { Box2 } from '../lib/collision'
import {
  buildPastWallBoxes,
  buildWallBoxes,
  type JourneyLayout,
  type PastRoomLayout,
  type RoomLayout,
  type WallBox,
  type Zone,
} from '../lib/layout'
import type { Locale, RoomDef, RoomId } from '../lib/rooms'
import { sfx } from './audio'
import type { OpenDialog } from './dialog'
import { futurePortal } from './rooms/props'
import {
  type EngineState,
  type FichaKind,
  type Interactable,
  registerInteractable,
  type ShowcaseRef,
  unregisterInteractable,
} from './state'
import { type RoomTheme, THEMES, type ThemeZoneId } from './themes'
import {
  disposeDeep,
  inkFloorTexture,
  inkWallTexture,
  mergedBoxes,
  toonMat,
  unitGeo,
} from './toon'

// ---------------------------------------------------------------------------
// Contratos (congelados para las factories de sala — plan seccion 8)
// ---------------------------------------------------------------------------

export interface WorldActions {
  openFicha(roomIndex: number, kind: FichaKind): void
  openContact(): void
  enterPast(roomIndex: number, spawn: { x: number; z: number }): void
  /** Panel DOM de texto libre (la reseña del cuaderno de cada sala). */
  openStory(title: string, paragraphs: readonly string[]): void
  /** Panel de conversacion con un NPC (arbol de dialogo del HUD). */
  openDialog: OpenDialog
  /** Panel HTML operable del showcase de software (E cicla demos). */
  openShowcase(ref: ShowcaseRef): void
}

export interface RoomCtx {
  def: RoomDef
  room: RoomLayout
  theme: RoomTheme
  locale: Locale
  state: EngineState
  actions: WorldActions
}

export interface RoomBuild {
  group: Group
  interactables: Interactable[]
  /** Colliders del contenido (props + NPCs), evaluados por frame. */
  colliders?(): readonly Box2[]
  update?(t: number, dt: number): void
  /** Libera SOLO lo propio (no el pool toon): tipicamente disposeDeep. */
  dispose(): void
}

export type RoomFactory = (ctx: RoomCtx) => RoomBuild

export interface PastCtx {
  def: RoomDef
  pastRoom: PastRoomLayout
  theme: RoomTheme
  locale: Locale
  state: EngineState
  /** Punto de retorno en la sala presente (lo calcula world). */
  returnTo: { x: number; z: number }
  actions: {
    exitPast(returnTo: { x: number; z: number }): void
    /** Panel DOM expandible (la historia "antes de la uni"). */
    openStory(title: string, paragraphs: readonly string[]): void
    /** Panel de conversacion con un NPC (arbol de dialogo del HUD). */
    openDialog: OpenDialog
  }
}

export type PastFactory = (ctx: PastCtx) => RoomBuild

/** Manifest data-driven: agregar sala = 1 entrada aqui + 1 factory. */
export const WORLD: Record<
  RoomId,
  { load: () => Promise<{ default: RoomFactory }> }
> = {
  aula: { load: () => import('./rooms/aula') },
  corpoelec: { load: () => import('./rooms/corpoelec') },
  ipasme: { load: () => import('./rooms/ipasme') },
  iai: { load: () => import('./rooms/iai') },
  asesoria: { load: () => import('./rooms/asesoria') },
  cofasa: { load: () => import('./rooms/cofasa') },
  dibal: { load: () => import('./rooms/dibal') },
  goodmeal: { load: () => import('./rooms/goodmeal') },
  destacame: { load: () => import('./rooms/destacame') },
  futuro: { load: () => import('./rooms/futuro') },
}

const loadPast = (): Promise<{ default: PastFactory }> =>
  import('./rooms/past/index')

// ---------------------------------------------------------------------------
// createWorld
// ---------------------------------------------------------------------------

export interface WorldDeps {
  scene: Scene
  renderer: WebGLRenderer
  camera: PerspectiveCamera
  rooms: readonly RoomDef[]
  layout: JourneyLayout
  pastRooms: readonly PastRoomLayout[]
  state: EngineState
  /** Fade de esclusa/teleport ('dark'), de sueño para los portales al
   *  pasado ('dream' — white-out con blur) o de cruce de puerta ('warp' —
   *  franja de luz, "viaje al futuro"). Lo implementa el HUD. */
  fade(on: boolean, style?: 'dark' | 'dream' | 'warp'): Promise<void>
  /** Sepia + grano del pasado (overlay CSS del HUD). */
  setPastMode(on: boolean): void
  ui: {
    openFicha(roomIndex: number, kind: FichaKind): void
    openContact(): void
    openStory(title: string, paragraphs: readonly string[]): void
    openDialog: OpenDialog
    openShowcase(ref: ShowcaseRef): void
  }
  /** Mueve al jugador (lo implementa controls). */
  teleportPlayer(x: number, z: number): void
  /** Luz direccional con sombra (solo full) para ceñir su frustum. */
  shadowLight?: DirectionalLight
  /**
   * Se llama cuando el world cambia la zona/pasado por su cuenta
   * (teleport, portal): el app sincroniza HUD + audio.
   */
  onZoneApplied?(): void
}

export interface World {
  /** Monta sala 0 + shells iniciales (el loader del boot cubre esto). */
  init(): Promise<void>
  /** Reporta el cambio de zona (lo llama controls/tour). */
  setZone(zone: Zone): void
  /** Cruce por el portal del vano: warp, teleport a la sala siguiente y
   *  re-registro del interactable (mismo patron que el portal al pasado). */
  crossPortal(index: number): Promise<void>
  teleportToRoom(index: number): Promise<void>
  enterPast(roomIndex: number, spawn: { x: number; z: number }): Promise<void>
  exitPast(returnTo: { x: number; z: number }): Promise<void>
  /** Degradacion automatica: apaga/enciende los acentos por zona. */
  setAccentsEnabled(on: boolean): void
  update(t: number, dt: number): void
  dispose(): void
}

type ShellKey = `room-${number}` | `corridor-${number}` | `past-${number}`

export function createWorld(deps: WorldDeps): World {
  const { scene, renderer, camera, rooms, layout, pastRooms, state } = deps
  const wallBoxes = buildWallBoxes(layout)
  const pastWallBoxes = buildPastWallBoxes(pastRooms)

  const shells = new Map<ShellKey, Group>()
  const mountedShells = new Set<ShellKey>()
  const contents = new Map<number, RoomBuild>()
  const pending = new Map<number, Promise<void>>()
  const wantedContent = new Set<number>()
  /** Update (vortice del portal al futuro) por sala de ORIGEN. */
  const roomPortals = new Map<number, (t: number) => void>()
  /** Cruces en curso (guard de re-entrada del portal). */
  const crossing = new Set<number>()
  const accentLights: PointLight[] = []
  let pastBuild: RoomBuild | null = null
  let disposed = false

  // theme actual (lerp en update para no "saltar" al cambiar de zona)
  const background = new Color(THEMES.corridor.sky)
  const fog = new Fog(background.clone(), 12, 70)
  const targetSky = new Color(THEMES.corridor.sky)
  const targetFog = new Color(THEMES.corridor.fog)
  scene.background = background
  scene.fog = fog

  const actions: WorldActions = {
    openFicha: deps.ui.openFicha,
    openContact: deps.ui.openContact,
    openStory: deps.ui.openStory,
    openDialog: deps.ui.openDialog,
    openShowcase: deps.ui.openShowcase,
    enterPast: (roomIndex, spawn) => {
      void world.enterPast(roomIndex, spawn)
    },
  }

  // -------------------------------------------------------------------------
  // Shells
  // -------------------------------------------------------------------------

  /** TODOS los muros de una zona fusionados en 1 mesh (presupuesto AC-10). */
  function wallsMesh(boxes: readonly WallBox[], theme: RoomTheme): Mesh {
    const mesh = mergedBoxes(
      boxes.map((box) => ({
        w: box.maxX - box.minX,
        h: box.height,
        d: box.maxZ - box.minZ,
        x: (box.minX + box.maxX) / 2,
        y: box.height / 2,
        z: (box.minZ + box.maxZ) / 2,
      })),
      toonMat('#ffffff', {
        map: inkWallTexture(theme),
        gradient: theme.gradient,
      }),
    )
    mesh.receiveShadow = true
    return mesh
  }

  function floorMesh(
    x: number,
    z: number,
    width: number,
    depth: number,
    theme: RoomTheme,
    repeat: { x: number; y: number },
  ): Mesh {
    const texture = inkFloorTexture(theme)
    texture.repeat.set(repeat.x, repeat.y)
    const mesh = new Mesh(
      unitGeo().plane,
      toonMat('#ffffff', { map: texture, gradient: theme.gradient }),
    )
    mesh.rotation.x = -Math.PI / 2
    mesh.scale.set(width, depth, 1)
    mesh.position.set(x, 0, z)
    mesh.receiveShadow = true
    return mesh
  }

  function ceilingMesh(
    x: number,
    z: number,
    width: number,
    depth: number,
    height: number,
    theme: RoomTheme,
  ): Mesh {
    const dim = `#${new Color(theme.wall).multiplyScalar(0.55).getHexString()}`
    const mesh = new Mesh(
      unitGeo().plane,
      toonMat(dim, { gradient: theme.gradient }),
    )
    mesh.rotation.x = Math.PI / 2
    mesh.scale.set(width, depth, 1)
    mesh.position.set(x, height, z)
    return mesh
  }

  function accentLight(
    x: number,
    y: number,
    z: number,
    color: string,
    intensity: number,
    distance: number,
  ): PointLight {
    const light = new PointLight(color, intensity, distance, 1.7)
    light.position.set(x, y, z)
    accentLights.push(light)
    return light
  }

  function buildRoomShell(index: number): Group {
    const group = new Group()
    const def = rooms[index]
    const room = layout.rooms[index]
    if (!def || !room) {
      return group
    }
    const theme = THEMES[def.id]
    group.add(
      wallsMesh(
        wallBoxes.filter(
          (box) => box.source.kind === 'room' && box.source.index === index,
        ),
        theme,
      ),
    )
    group.add(
      floorMesh(room.x, room.z, room.width, room.depth, theme, {
        x: room.width / 2,
        y: room.depth / 2,
      }),
      ceilingMesh(room.x, room.z, room.width, room.depth, room.height, theme),
    )
    if (state.tier === 'full') {
      group.add(
        accentLight(
          room.x,
          room.height - 0.35,
          room.z,
          theme.lightColor,
          14,
          room.width * 2.2,
        ),
      )
    }
    // portal al FUTURO en el muro de salida (si hay sala siguiente): pegado
    // al muro trasero, mirando hacia adentro de la sala (-Z), con el acento
    // del rubro que viene. Su vortice se anima via roomPortals (world.update).
    const next = rooms[index + 1]
    if (next) {
      const portal = futurePortal(THEMES[next.id].accent)
      portal.group.position.set(room.x, 0, room.z + room.depth / 2 - 0.05)
      portal.group.rotation.y = Math.PI
      group.add(portal.group)
      roomPortals.set(index, portal.update)
    }
    return group
  }

  /** El pasillo entre salas ya no renderiza nada: los muros estan sellados y
   *  el portal al futuro vive en el muro de salida de la sala
   *  (buildRoomShell). Shell vacio para no tocar el set de zonas/tour. */
  function buildCorridorShell(): Group {
    return new Group()
  }

  function buildPastShell(index: number): Group {
    const group = new Group()
    const past = pastRooms[index]
    if (!past) {
      return group
    }
    const theme = THEMES.past
    group.add(
      wallsMesh(
        pastWallBoxes.filter((box) => box.source.index === index),
        theme,
      ),
    )
    group.add(
      floorMesh(past.x, past.z, past.width, past.depth, theme, {
        x: past.width / 2,
        y: past.depth / 2,
      }),
      ceilingMesh(past.x, past.z, past.width, past.depth, past.height, theme),
      accentLight(past.x, past.height - 0.3, past.z, theme.lightColor, 5, 9),
    )
    return group
  }

  function getShell(key: ShellKey): Group {
    const cached = shells.get(key)
    if (cached) {
      return cached
    }
    const [kind, rawIndex] = key.split('-')
    const index = Number(rawIndex)
    let group: Group
    if (kind === 'room') {
      group = buildRoomShell(index)
    } else if (kind === 'corridor') {
      group = buildCorridorShell()
    } else {
      group = buildPastShell(index)
    }
    shells.set(key, group)
    return group
  }

  function syncShells(wanted: ReadonlySet<ShellKey>): void {
    for (const key of mountedShells) {
      if (!wanted.has(key)) {
        const group = shells.get(key)
        if (group) {
          scene.remove(group)
        }
        mountedShells.delete(key)
      }
    }
    for (const key of wanted) {
      if (!mountedShells.has(key)) {
        scene.add(getShell(key))
        mountedShells.add(key)
      }
    }
  }

  // -------------------------------------------------------------------------
  // Contents (la parte que se paga: 1 sala viva)
  // -------------------------------------------------------------------------

  function mountBuild(index: number, build: RoomBuild): void {
    contents.set(index, build)
    scene.add(build.group)
    for (const item of build.interactables) {
      registerInteractable(state, item)
    }
    if (build.colliders) {
      state.obstacleSources.set(`room-${index}`, build.colliders)
    }
    // calienta shaders con la sala ya montada (pool toon = casi noop)
    renderer.compile(scene, camera)
  }

  function unmountBuild(index: number): void {
    const build = contents.get(index)
    if (!build) {
      return
    }
    scene.remove(build.group)
    for (const item of build.interactables) {
      unregisterInteractable(state, item.id)
    }
    state.obstacleSources.delete(`room-${index}`)
    build.dispose()
    contents.delete(index)
  }

  function preload(index: number): Promise<void> {
    if (disposed || contents.has(index)) {
      return Promise.resolve()
    }
    const inFlight = pending.get(index)
    if (inFlight) {
      return inFlight
    }
    const def = rooms[index]
    const room = layout.rooms[index]
    if (!def || !room) {
      return Promise.resolve()
    }
    const promise = WORLD[def.id]
      .load()
      .then(({ default: factory }) => {
        pending.delete(index)
        if (disposed || !wantedContent.has(index)) {
          return
        }
        const build = factory({
          def,
          room,
          theme: THEMES[def.id],
          locale: state.locale,
          state,
          actions,
        })
        mountBuild(index, build)
      })
      .catch((error: unknown) => {
        pending.delete(index)
        console.error('[journey] preload de sala fallo', error)
      })
    pending.set(index, promise)
    return promise
  }

  function disposeContentsExcept(keep: number): void {
    for (const index of [...contents.keys()]) {
      if (index !== keep) {
        unmountBuild(index)
      }
    }
  }

  /** Content de la sala listo; con fade solo si hay que construirlo ya. */
  async function ensureContent(index: number, useFade: boolean): Promise<void> {
    if (contents.has(index)) {
      return
    }
    if (useFade) {
      await deps.fade(true)
    }
    await preload(index)
    if (useFade) {
      await deps.fade(false)
    }
  }

  // -------------------------------------------------------------------------
  // Zonas + theme
  // -------------------------------------------------------------------------

  function applyTheme(id: ThemeZoneId): void {
    const theme = THEMES[id]
    targetSky.set(theme.sky)
    targetFog.set(theme.fog)
  }

  function themeIdForZone(zone: Zone): ThemeZoneId {
    if (zone.kind === 'corridor') {
      return 'corridor'
    }
    return rooms[zone.index]?.id ?? 'corridor'
  }

  interface ShadowArea {
    x: number
    z: number
    width: number
    depth: number
    height: number
  }

  /** Luz de sombra CENITAL sobre el centro del area (coherente con la
   *  lampara central de cada sala: la sombra cae bajo el personaje, no en
   *  una diagonal arbitraria) + frustum ceñido (solo full). */
  function aimShadow(area: ShadowArea): void {
    const light = deps.shadowLight
    if (!light) {
      return
    }
    const half = Math.max(area.width, area.depth) / 2 + 1.5
    light.position.set(area.x + 0.8, area.height + 6, area.z + 0.8)
    light.target.position.set(area.x, 0, area.z)
    light.target.updateMatrixWorld()
    const shadowCam = light.shadow.camera
    shadowCam.left = -half
    shadowCam.right = half
    shadowCam.top = half
    shadowCam.bottom = -half
    shadowCam.updateProjectionMatrix()
  }

  function focusShadow(zone: Zone): void {
    const area =
      zone.kind === 'room'
        ? layout.rooms[zone.index]
        : layout.corridors[zone.index]
    if (area) {
      aimShadow(area)
    }
  }

  function applyZone(zone: Zone, manageFade: boolean): Promise<void> {
    const wanted = new Set<ShellKey>()
    let result: Promise<void> = Promise.resolve()
    if (zone.kind === 'room') {
      wanted.add(`room-${zone.index}`)
      if (layout.corridors[zone.index - 1]) {
        wanted.add(`corridor-${zone.index - 1}`)
      }
      if (layout.corridors[zone.index]) {
        wanted.add(`corridor-${zone.index}`)
      }
      wantedContent.clear()
      wantedContent.add(zone.index)
      disposeContentsExcept(zone.index)
      result = ensureContent(zone.index, manageFade)
    } else {
      wanted.add(`corridor-${zone.index}`)
      wanted.add(`room-${zone.index}`)
      if (layout.rooms[zone.index + 1]) {
        wanted.add(`room-${zone.index + 1}`)
      }
      // esclusa: libera la sala anterior y precarga la siguiente
      wantedContent.clear()
      wantedContent.add(zone.index + 1)
      unmountBuild(zone.index)
      disposeContentsExcept(zone.index + 1)
      result = preload(zone.index + 1)
    }
    syncShells(wanted)
    applyTheme(themeIdForZone(zone))
    focusShadow(zone)
    return result
  }

  // -------------------------------------------------------------------------
  // API
  // -------------------------------------------------------------------------

  /** Interactable del portal al futuro, sobre el muro de SALIDA de la sala
   *  `index` (se cruza a `index + 1`). Se re-registra tras cada cruce
   *  (crossPortal cierra el ciclo). El prompt lleva el año de la sala
   *  DESTINO. Id `gate-` (no `portal-`, reservado al portal al pasado). */
  function registerGateInteractable(index: number): void {
    const room = layout.rooms[index]
    const next = rooms[index + 1]
    if (!room || !next) {
      return
    }
    registerInteractable(state, {
      id: `gate-${index}`,
      x: room.x,
      z: room.z + room.depth / 2, // muro de salida
      radius: 2.4,
      label: {
        es: `Cruzar el portal a ${next.year}`,
        en: `Cross the portal to ${next.year}`,
      },
      onActivate: () => {
        void world.crossPortal(index)
      },
    })
  }

  const world: World = {
    async init() {
      for (let i = 0; i < rooms.length - 1; i += 1) {
        registerGateInteractable(i)
      }
      state.zone = { kind: 'room', index: 0 }
      await applyZone(state.zone, false)
    },

    setZone(zone) {
      state.zone = zone
      if (state.past !== null) {
        return
      }
      void applyZone(zone, true)
    },

    async crossPortal(index) {
      if (crossing.has(index)) {
        return // ya hay un cruce en curso
      }
      const target = layout.rooms[index + 1]
      if (!target) {
        return
      }
      crossing.add(index)
      unregisterInteractable(state, `gate-${index}`)
      sfx.play('whoosh')
      await deps.fade(true, 'warp')
      deps.teleportPlayer(0, target.z - target.depth / 2 + 1.5)
      state.zone = { kind: 'room', index: index + 1 }
      await applyZone(state.zone, false) // misma esclusa que teleportToRoom
      deps.onZoneApplied?.()
      await deps.fade(false, 'warp')
      crossing.delete(index)
      registerGateInteractable(index) // vuelve a ser interactuable
    },

    async teleportToRoom(index) {
      const target = layout.rooms[index]
      if (!target) {
        return
      }
      await deps.fade(true)
      if (state.past !== null && pastBuild) {
        scene.remove(pastBuild.group)
        for (const item of pastBuild.interactables) {
          unregisterInteractable(state, item.id)
        }
        state.obstacleSources.delete('past')
        pastBuild.dispose()
        pastBuild = null
        state.past = null
        deps.setPastMode(false)
      }
      deps.teleportPlayer(0, target.z - target.depth / 2 + 1.5)
      state.zone = { kind: 'room', index }
      await applyZone(state.zone, false)
      deps.onZoneApplied?.()
      await deps.fade(false)
    },

    async enterPast(roomIndex, spawn) {
      const def = rooms[roomIndex]
      const pastRoom = pastRooms[roomIndex]
      const presentRoom = layout.rooms[roomIndex]
      if (!def || !pastRoom || !presentRoom || state.past !== null) {
        return
      }
      // transicion "de sueño": whoosh + white-out (tapa la carga)
      sfx.play('whoosh')
      await deps.fade(true, 'dream')
      state.past = roomIndex
      deps.setPastMode(true)
      // el content presente sigue construido pero fuera de escena
      const present = contents.get(roomIndex)
      if (present) {
        scene.remove(present.group)
      }
      const { default: factory } = await loadPast()
      if (disposed) {
        return
      }
      const build = factory({
        def,
        pastRoom,
        theme: THEMES.past,
        locale: state.locale,
        state,
        returnTo: {
          x: 0,
          z: presentRoom.z - presentRoom.depth / 2 + 1.5,
        },
        actions: {
          exitPast: (returnTo) => {
            void world.exitPast(returnTo)
          },
          openStory: deps.ui.openStory,
          openDialog: deps.ui.openDialog,
        },
      })
      pastBuild = build
      scene.add(build.group)
      for (const item of build.interactables) {
        registerInteractable(state, item)
      }
      if (build.colliders) {
        state.obstacleSources.set('past', build.colliders)
      }
      syncShells(new Set<ShellKey>([`past-${roomIndex}`]))
      applyTheme('past')
      aimShadow(pastRoom)
      deps.teleportPlayer(spawn.x, spawn.z)
      renderer.compile(scene, camera)
      deps.onZoneApplied?.()
      await deps.fade(false, 'dream')
    },

    async exitPast(returnTo) {
      const roomIndex = state.past
      if (roomIndex === null) {
        return
      }
      sfx.play('whoosh')
      await deps.fade(true, 'dream')
      if (pastBuild) {
        scene.remove(pastBuild.group)
        for (const item of pastBuild.interactables) {
          unregisterInteractable(state, item.id)
        }
        state.obstacleSources.delete('past')
        pastBuild.dispose()
        pastBuild = null
      }
      state.past = null
      deps.setPastMode(false)
      const present = contents.get(roomIndex)
      if (present) {
        scene.add(present.group)
      }
      deps.teleportPlayer(returnTo.x, returnTo.z)
      state.zone = { kind: 'room', index: roomIndex }
      await applyZone(state.zone, false)
      deps.onZoneApplied?.()
      await deps.fade(false, 'dream')
    },

    setAccentsEnabled(on) {
      for (const light of accentLights) {
        light.visible = on
      }
    },

    update(t, dt) {
      // portales al futuro: energia + vortice girando (shells cacheados)
      for (const portal of roomPortals.values()) {
        portal(t)
      }
      // theme: lerp de background/fog (~400 ms)
      const k = 1 - Math.exp(-dt * 8)
      background.lerp(targetSky, k)
      fog.color.lerp(targetFog, k)
      // animaciones del contenido vivo (NPCs, micro-interacciones)
      for (const build of contents.values()) {
        build.update?.(t, dt)
      }
      pastBuild?.update?.(t, dt)
    },

    dispose() {
      disposed = true
      wantedContent.clear()
      for (const index of [...contents.keys()]) {
        unmountBuild(index)
      }
      state.obstacleSources.clear()
      if (pastBuild) {
        scene.remove(pastBuild.group)
        pastBuild.dispose()
        pastBuild = null
      }
      for (const key of mountedShells) {
        const group = shells.get(key)
        if (group) {
          scene.remove(group)
        }
      }
      mountedShells.clear()
      for (const group of shells.values()) {
        disposeDeep(group)
      }
      shells.clear()
      roomPortals.clear()
      crossing.clear()
      accentLights.length = 0
    },
  }

  return world
}
