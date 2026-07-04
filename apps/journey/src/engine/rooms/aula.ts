/**
 * @module rooms/aula (engine)
 * @description Sala 0 — Aula/Universidad (iai + projects-degrees, 2015).
 *   Salon CLASICO: pupitres en filas mirando a la pizarra principal
 *   (CLIENTE<->SERVIDOR), escritorio del profesor al frente, pizarras de
 *   RETOS y APRENDIZAJES tituladas en las paredes laterales y micro-
 *   interaccion narrativa: encender la PC del laboratorio -> los monitores
 *   bootean en cascada mostrando el codigo cliente-servidor del proyecto
 *   de grado. 3 NPCs estudiantes. Manga-ink: toon + outline.
 */
import { Group } from 'three'
import type { Box2 } from '../../lib/collision'
import { makeNpc, type NpcHandle } from '../character'
import type { Interactable } from '../state'
import { unregisterInteractable } from '../state'
import { disposeDeep, outlineGroup, screenPanel } from '../toon'
import type { RoomBuild, RoomCtx } from '../world'
import {
  desk,
  fichaBoard,
  footprint,
  pastPortal,
  type ScreenSwap,
  switchableMonitor,
} from './props'

const MICRO_LABEL = {
  es: 'Encender la PC del laboratorio',
  en: 'Power on the lab PC',
} as const

/** Codigo era-2015 del proyecto: red local + cliente-servidor en C. */
const CODE_SCREENS = [
  {
    title: 'servidor.c',
    lines: [
      'sock = socket(AF_INET)',
      'bind(:8080)  listen(4)',
      'cliente 10.0.1.12 OK',
      'recv "ping" -> send "pong"',
    ],
  },
  {
    title: 'cliente.c',
    lines: [
      'connect(10.0.1.1:8080)',
      'send("ping")',
      'recv: "pong"  2ms',
      'estado: EN RED',
    ],
  },
] as const

const PLAYER_PC_SCREEN = {
  title: '> ping servidor',
  lines: [
    '64 bytes: t=2ms',
    'conectado: OK',
    'red del laboratorio: VIVA',
    '2 tesis: EN MARCHA',
  ],
} as const

export default function buildAula(ctx: RoomCtx): RoomBuild {
  const { def, room, theme, state, actions } = ctx
  const group = new Group()
  const interactables: Interactable[] = []
  const updates: ((t: number, dt: number) => void)[] = []
  const npcs: NpcHandle[] = []
  const disposables: { dispose(): void }[] = []
  const staticColliders: Box2[] = []
  const half = room.width / 2
  const screenTheme = {
    screenBg: theme.screenBg,
    screenFg: theme.screenFg,
    ink: theme.ink,
  }
  const offScreen = {
    lines: [],
    theme: { screenBg: '#08080c', screenFg: '#22301c', ink: theme.ink },
    dot: '#b23a3a',
  }

  // pizarra principal del salon (el plan de rescate) en el muro del fondo
  const board = screenPanel({
    title: '[CLIENTE] <-> [SERVIDOR]',
    lines: [
      'red local del laboratorio',
      'plan de rescate: 1 semana',
      '2 tesis: bloqueado -> listo',
    ],
    theme: { screenBg: '#2e4d3a', screenFg: '#d8ecc8', ink: theme.ink },
    width: 2.6,
    height: 1.4,
  })
  board.position.set(0, 1.7, room.z + room.depth / 2 - 0.12)
  board.rotation.y = Math.PI
  group.add(board)

  // escritorio del profesor al frente, junto a la pizarra
  group.add(
    desk({ position: [-1.6, 0, room.z + 2.5], width: 1.1, color: '#5a4632' }),
  )
  staticColliders.push(footprint(-1.6, room.z + 2.5, 1.2, 0.8))

  // pupitres en filas mirando al frente (+Z); el front-right es "tu PC"
  const deskSpots: readonly (readonly [number, number])[] = [
    [-1.4, room.z + 0.8],
    [1.4, room.z + 0.8],
    [-1.4, room.z - 0.8],
    [1.4, room.z - 0.8],
  ]
  const monitors: ScreenSwap[] = []
  deskSpots.forEach(([x, z], index) => {
    group.add(desk({ position: [x, 0, z], width: 1.1, color: '#5a4632' }))
    staticColliders.push(footprint(x, z, 1.3, 0.8))
    const isPlayerPc = index === 1
    const code = isPlayerPc
      ? PLAYER_PC_SCREEN
      : (CODE_SCREENS[index % 2] ?? PLAYER_PC_SCREEN)
    const { group: monitorGroup, screen } = switchableMonitor({
      position: [x, 0.72, z + 0.05],
      rotationY: Math.PI,
      width: 0.46,
      variants: {
        off: offScreen,
        on: {
          title: code.title,
          lines: code.lines,
          theme: screenTheme,
          dot: '#3f9d63',
        },
      },
      initial: 'off',
    })
    group.add(monitorGroup)
    monitors.push(screen)
    disposables.push(screen)
  })

  // micro-interaccion narrativa: encender la PC -> boot en cascada
  const microId = `micro-aula-${room.index}`
  let bootStart = -1
  const booted = new Set<number>()
  interactables.push({
    id: microId,
    x: 1.4,
    z: room.z + 0.8,
    radius: 2,
    label: MICRO_LABEL,
    onActivate: () => {
      bootStart = -2 // el proximo update fija el inicio del cascade
      unregisterInteractable(state, microId)
    },
  })
  updates.push((t) => {
    if (bootStart === -2) {
      bootStart = t
    }
    if (bootStart < 0 || booted.size === monitors.length) {
      return
    }
    monitors.forEach((screen, index) => {
      // tu PC (index 1) bootea primero, el resto en cascada
      const delay = index === 1 ? 0 : 0.5 + index * 0.4
      if (!booted.has(index) && t - bootStart >= delay) {
        booted.add(index)
        screen.show('on')
      }
    })
  })

  // pizarras tituladas: RETOS (muro izq) / APRENDIZAJES (muro der)
  const texts = def.texts[state.locale]
  const retos = fichaBoard({
    roomIndex: room.index,
    kind: 'retos',
    position: [-half + 0.35, 0, room.z - 0.6],
    rotationY: Math.PI / 2,
    theme,
    locale: state.locale,
    preview: texts.retos,
    state,
    onOpen: actions.openFicha,
  })
  const aprendizajes = fichaBoard({
    roomIndex: room.index,
    kind: 'aprendizajes',
    position: [half - 0.35, 0, room.z - 0.6],
    rotationY: -Math.PI / 2,
    theme,
    locale: state.locale,
    preview: texts.aprendizajes,
    state,
    onOpen: actions.openFicha,
  })
  // portal al pasado (las tesis bloqueadas)
  const portal = pastPortal({
    room,
    position: [-half + 0.35, 0, room.z + 2.2],
    rotationY: Math.PI / 2,
    accent: theme.accent,
    onEnter: actions.enterPast,
  })
  for (const prop of [retos, aprendizajes, portal]) {
    group.add(prop.group)
    if (prop.interactable) {
      interactables.push(prop.interactable)
    }
    if (prop.update) {
      updates.push(prop.update)
    }
  }

  // NPCs estudiantes: 2 en sus pupitres mirando al frente + 1 en ronda
  npcs.push(
    makeNpc({
      skin: '#e8b48c',
      hair: { style: 'ponytail', color: '#5a3a22' },
      top: '#4a6a52',
      bottom: '#3a4048',
      faceSeed: 11,
      position: [-1.4, 0, room.z + 0.25],
      rotationY: 0,
    }),
    makeNpc({
      skin: '#d9a684',
      hair: { style: 'spiky', color: '#1c1410' },
      top: '#7a5c3a',
      bottom: '#2e3238',
      faceSeed: 23,
      position: [1.4, 0, room.z - 1.35],
      rotationY: 0,
    }),
    makeNpc({
      skin: '#c98f6a',
      hair: { style: 'bun', color: '#2a1c12' },
      top: '#3f5a8a',
      bottom: '#3a4048',
      faceSeed: 37,
      position: [2.6, 0, room.z + 2.3],
      path: [
        [2.6, room.z + 2.3],
        [-2.6, room.z + 2.3],
        [-2.6, room.z - 2.3],
        [2.6, room.z - 2.3],
      ],
      speed: 0.7,
    }),
  )
  for (const npc of npcs) {
    group.add(npc.group)
    updates.push((t, dt) => npc.update(t, dt))
  }

  // contorno de tinta en todos los props (screens/labels/caras se excluyen)
  outlineGroup(group, 1.03)

  return {
    group,
    interactables,
    colliders: () => [...staticColliders, ...npcs.map((npc) => npc.collider())],
    update: (t, dt) => {
      for (const fn of updates) {
        fn(t, dt)
      }
    },
    dispose: () => {
      for (const npc of npcs) {
        npc.dispose()
      }
      for (const item of disposables) {
        item.dispose()
      }
      disposeDeep(group)
    },
  }
}
