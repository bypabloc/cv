/**
 * @module rooms/aula (engine)
 * @description Sala 0 — Aula/Universidad (iai + projects-degrees, 2015).
 *   Pupitres con PCs en red, pizarra de RETOS, cuaderno de APRENDIZAJES,
 *   guiño cliente-servidor y micro-interaccion "pasar los proyectos de
 *   bloqueado a listo". 3 NPCs estudiantes. Manga-ink: toon + outline.
 */
import { Group } from 'three'
import { makeNpc, type NpcHandle } from '../character'
import type { Interactable } from '../state'
import { unregisterInteractable } from '../state'
import {
  disposeDeep,
  label,
  mergedBoxes,
  outlineGroup,
  screenPanel,
  toonMatOwn,
} from '../toon'
import type { RoomBuild, RoomCtx } from '../world'
import { desk, fichaProp, monitor, pastPortal } from './props'

const MICRO_LABEL = {
  es: 'Reencaminar los proyectos',
  en: 'Rescue the projects',
} as const

export default function buildAula(ctx: RoomCtx): RoomBuild {
  const { def, room, theme, state, actions } = ctx
  const group = new Group()
  const interactables: Interactable[] = []
  const updates: ((t: number, dt: number) => void)[] = []
  const npcs: NpcHandle[] = []
  const half = room.width / 2

  // pupitres con PCs en red local
  const desks: readonly (readonly [number, number])[] = [
    [-1.4, -1.2],
    [1.4, -1.2],
    [-1.4, 0.6],
    [1.4, 0.6],
  ]
  for (const [x, dz] of desks) {
    group.add(
      desk({ position: [x, 0, room.z + dz], width: 1.1, color: '#5a4632' }),
      monitor({
        position: [x, 0.75, room.z + dz - 0.1],
        lines: ['> ping servidor', 'conectado: OK'],
        theme: {
          screenBg: theme.screenBg,
          screenFg: theme.screenFg,
          ink: theme.ink,
        },
        width: 0.42,
      }),
    )
  }

  // guiño: pizarra cliente-servidor con el plan de rescate
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

  // RETOS: pizarra en el muro izquierdo
  const retos = fichaProp({
    roomIndex: room.index,
    kind: 'retos',
    style: 'pizarra',
    position: [-half + 0.45, 0, room.z - 1],
    rotationY: Math.PI / 2,
    accent: theme.accent,
    state,
    onOpen: actions.openFicha,
  })
  // APRENDIZAJES: cuaderno sobre podio
  const aprendizajes = fichaProp({
    roomIndex: room.index,
    kind: 'aprendizajes',
    style: 'cuaderno',
    position: [half - 1.2, 0, room.z + 1.6],
    accent: theme.accent,
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

  // micro-interaccion: dos proyectos pasan de BLOQUEADO (rojo) a LISTO
  const microId = `micro-aula-${room.index}`
  const micro = new Group()
  micro.position.set(half - 0.4, 0, room.z - 1)
  micro.rotation.y = -Math.PI / 2
  const boardMat = toonMatOwn('#b23a3a', {
    emissive: '#b23a3a',
    emissiveIntensity: 0.35,
  })
  const captions = { es: ['BLOQUEADO', 'LISTO'], en: ['BLOCKED', 'DONE'] }
  const [blockedText, doneText] = captions[state.locale]
  // las 2 tarjetas fusionadas (1 draw call, mismo material animable)
  const cards = mergedBoxes(
    [-0.55, 0.55].map((x) => ({
      w: 0.85,
      h: 0.55,
      d: 0.05,
      x,
      y: 1.5,
      z: 0,
    })),
    boardMat,
  )
  micro.add(cards)
  // al activar se alterna la visibilidad: BLOQUEADO off, LISTO on
  const toggleLabels: { visible: boolean }[] = []
  for (const x of [-0.55, 0.55]) {
    const blocked = label(blockedText ?? 'BLOQUEADO', { size: 0.12 })
    blocked.position.set(x, 1.5, 0.04)
    const done = label(doneText ?? 'LISTO', { size: 0.12 })
    done.position.set(x, 1.5, 0.04)
    done.visible = false
    micro.add(blocked, done)
    toggleLabels.push(blocked, done)
  }
  group.add(micro)
  interactables.push({
    id: microId,
    x: half - 0.4,
    z: room.z - 1,
    radius: 2,
    label: MICRO_LABEL,
    onActivate: () => {
      boardMat.color.set('#3f9d63')
      boardMat.emissive.set('#3f9d63')
      for (const mesh of toggleLabels) {
        mesh.visible = !mesh.visible
      }
      unregisterInteractable(state, microId)
    },
  })

  // NPCs estudiantes (reparto del plan: ponytail/spiky/bun, distinguibles)
  npcs.push(
    makeNpc({
      skin: '#e8b48c',
      hair: { style: 'ponytail', color: '#5a3a22' },
      top: '#4a6a52',
      bottom: '#3a4048',
      faceSeed: 11,
      position: [-1.4, 0, room.z - 0.6],
      rotationY: Math.PI,
    }),
    makeNpc({
      skin: '#d9a684',
      hair: { style: 'spiky', color: '#1c1410' },
      top: '#7a5c3a',
      bottom: '#2e3238',
      faceSeed: 23,
      position: [1.4, 0, room.z + 1.2],
      rotationY: 0.4,
    }),
    makeNpc({
      skin: '#c98f6a',
      hair: { style: 'bun', color: '#2a1c12' },
      top: '#3f5a8a',
      bottom: '#3a4048',
      faceSeed: 37,
      position: [0, 0, room.z + 2.6],
      path: [
        [0, room.z + 2.6],
        [2.2, room.z + 2.6],
        [2.2, room.z - 2.2],
        [-2.4, room.z - 2.2],
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
  void def

  return {
    group,
    interactables,
    update: (t, dt) => {
      for (const fn of updates) {
        fn(t, dt)
      }
    },
    dispose: () => {
      for (const npc of npcs) {
        npc.dispose()
      }
      disposeDeep(group)
    },
  }
}
