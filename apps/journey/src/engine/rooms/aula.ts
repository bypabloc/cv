/**
 * @module rooms/aula (engine)
 * @description Sala 0 — Aula/Universidad (iai + projects-degrees, 2015).
 *   Salon CLASICO en paleta blanca/beige/azul con guiños morados: pupitres
 *   azules en filas mirando al frente (+Z), escritorio del profesor,
 *   pizarras de RETOS y APRENDIZAJES en las paredes laterales, grieta al
 *   pasado a la IZQUIERDA y pilar-atril con la reseña a la DERECHA.
 *   2 estudiantes SENTADOS tecleando con sus pantallas encendidas (codigo
 *   cliente-servidor del proyecto de grado); las 2 PCs libres — la tuya y
 *   una del laboratorio — se ENCIENDEN y APAGAN con E (toggle ilimitado).
 *   Los 3 estudiantes son conversables (arboles de dialogo bilingues +
 *   burbuja de habla suelta al acercarse). Manga-ink.
 */
import { Group } from 'three'
import type { Box2 } from '../../lib/collision'
import { sfx } from '../audio'
import { makeNpc, type NpcHandle } from '../character'
import { npcTalk } from '../dialog'
import { AULA_PRESENTE_DIALOGS } from '../dialogs/aula-presente'
import type { Interactable } from '../state'
import {
  disposeDeep,
  outlinedMergedBoxes,
  outlineGroup,
  toonMat,
} from '../toon'
import type { RoomBuild, RoomCtx } from '../world'
import {
  fichaBoard,
  footprint,
  lecternNotebook,
  pastPortal,
  switchableMonitor,
} from './props'

const PC_LABELS = {
  mine: {
    on: { es: 'Encender tu PC', en: 'Power on your PC' },
    off: { es: 'Apagar tu PC', en: 'Power off your PC' },
  },
  lab: {
    on: {
      es: 'Encender la PC del laboratorio',
      en: 'Power on the lab PC',
    },
    off: {
      es: 'Apagar la PC del laboratorio',
      en: 'Power off the lab PC',
    },
  },
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

  // el muro del fondo queda libre: ahi vive la puerta al pasillo con su
  // marquesina SIGUE LA TRAYECTORIA (la monta world en el shell)

  // pupitres en filas mirando al frente (+Z); el front-right es "tu PC"
  const deskSpots: readonly (readonly [number, number])[] = [
    [-1.4, room.z + 0.8],
    [1.4, room.z + 0.8],
    [-1.4, room.z - 0.8],
    [1.4, room.z - 0.8],
  ]
  // silla de un puesto: asiento + respaldo + 2 patas (dir=-1 la del profe)
  const chairParts = (x: number, cz: number, dir: 1 | -1) => [
    { w: 0.42, h: 0.05, d: 0.42, x, y: 0.44, z: cz },
    { w: 0.42, h: 0.5, d: 0.05, x, y: 0.72, z: cz - 0.2 * dir },
    { w: 0.05, h: 0.44, d: 0.05, x: x - 0.17, y: 0.22, z: cz - 0.1 * dir },
    { w: 0.05, h: 0.44, d: 0.05, x: x + 0.17, y: 0.22, z: cz - 0.1 * dir },
  ]
  // profesor + 4 pupitres + 5 sillas fusionados: 2 draw calls (AC-10).
  // Mobiliario AZUL (tema del aula: blanco + beige + azul, guiños morados)
  const allDesks: readonly (readonly [number, number])[] = [
    [-1.6, room.z + 2.5],
    ...deskSpots,
  ]
  group.add(
    outlinedMergedBoxes(
      [
        ...allDesks.flatMap(([x, z]) => [
          { w: 1.1, h: 0.05, d: 0.6, x, y: 0.72, z },
          { w: 0.06, h: 0.72, d: 0.55, x: x - 0.5, y: 0.36, z },
          { w: 0.06, h: 0.72, d: 0.55, x: x + 0.5, y: 0.36, z },
        ]),
        ...deskSpots.flatMap(([x, z]) => chairParts(x, z - 0.55, 1)),
        ...chairParts(-1.6, room.z + 3.05, -1),
      ],
      toonMat('#33517e'),
      { inflate: 0.035, castShadow: true },
    ),
  )
  staticColliders.push(
    footprint(-1.6, room.z + 2.5, 1.2, 0.8),
    // sillas vacias (tu PC, la del lab y la del profesor)
    footprint(1.4, room.z + 0.25, 0.5, 0.5),
    footprint(-1.4, room.z - 1.35, 0.5, 0.5),
    footprint(-1.6, room.z + 3.05, 0.5, 0.5),
  )

  // monitores: los de los NPCs ya estan ENCENDIDOS (estan trabajando);
  // las 2 PCs libres se encienden INDIVIDUALMENTE con E
  const NPC_PCS: ReadonlySet<number> = new Set([0, 3])
  deskSpots.forEach(([x, z], index) => {
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
      initial: NPC_PCS.has(index) ? 'on' : 'off',
    })
    group.add(monitorGroup)
    disposables.push(screen)
    if (!NPC_PCS.has(index)) {
      // toggle ilimitado: encender/apagar cambia pantalla, sfx y label
      const labels = isPlayerPc ? PC_LABELS.mine : PC_LABELS.lab
      let powered = false
      const item: Interactable = {
        id: `micro-aula-${room.index}-pc${index}`,
        x,
        z,
        radius: 1.8,
        label: { ...labels.on },
        onActivate: () => {
          powered = !powered
          screen.show(powered ? 'on' : 'off')
          sfx.play(powered ? 'boot' : 'shutdown')
          item.label = powered ? labels.off : labels.on
        },
      }
      interactables.push(item)
    }
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
    onOpen: actions.openFicha,
  })
  // grieta al pasado, pegada al muro IZQUIERDO (el pasado a la izquierda)
  const portal = pastPortal({
    room,
    position: [-half + 0.1, 0, room.z + 2.2],
    rotationY: Math.PI / 2,
    accent: theme.accent,
    year: def.year,
    locale: state.locale,
    onEnter: actions.enterPast,
  })
  // pilar-atril con la reseña de la etapa, a la DERECHA (espejo del portal)
  const nota = lecternNotebook({
    roomIndex: room.index,
    position: [half - 0.9, 0, room.z + 2.4],
    rotationY: -Math.PI / 2,
    theme,
    notebook: { title: texts.title, lines: texts.notebook },
    story: { title: texts.title, paragraphs: texts.resena },
    onOpen: actions.openStory,
  })
  staticColliders.push(footprint(half - 0.9, room.z + 2.4, 0.7, 0.7))
  for (const prop of [retos, aprendizajes, portal, nota]) {
    group.add(prop.group)
    if (prop.interactable) {
      interactables.push(prop.interactable)
    }
    if (prop.update) {
      updates.push(prop.update)
    }
  }

  // NPCs estudiantes: 2 SENTADOS tecleando en sus PCs + 1 en ronda.
  // Todos conversables con E (arbol de dialogo + burbuja de habla suelta).
  const tesistaUno = makeNpc({
    skin: '#e8b48c',
    hair: { style: 'ponytail', color: '#5a3a22' },
    top: '#4a6a52',
    bottom: '#3a4048',
    faceSeed: 11,
    position: [-1.4, 0, room.z + 0.25],
    rotationY: 0,
    pose: 'sit',
  })
  const tesistaDos = makeNpc({
    skin: '#d9a684',
    hair: { style: 'spiky', color: '#1c1410' },
    top: '#7a5c3a',
    bottom: '#2e3238',
    faceSeed: 23,
    position: [1.4, 0, room.z - 1.35],
    rotationY: 0,
    pose: 'sit',
  })
  const estudianteRonda = makeNpc({
    skin: '#c98f6a',
    hair: { style: 'bun', color: '#2a1c12' },
    top: '#3f5a8a',
    bottom: '#3a4048',
    faceSeed: 37,
    position: [2.6, 0, room.z + 1.7],
    path: [
      [2.6, room.z + 1.7],
      [-2.6, room.z + 1.7],
      [-2.6, room.z - 2.3],
      [2.6, room.z - 2.3],
    ],
    speed: 0.7,
  })
  npcs.push(tesistaUno, tesistaDos, estudianteRonda)
  for (const npc of npcs) {
    group.add(npc.group)
    updates.push((t, dt) => npc.update(t, dt))
  }
  const talks = [
    npcTalk({
      id: `talk-aula-${room.index}-tesista-uno`,
      npc: tesistaUno,
      dialog: AULA_PRESENTE_DIALOGS['tesista-uno'],
      openDialog: actions.openDialog,
    }),
    npcTalk({
      id: `talk-aula-${room.index}-tesista-dos`,
      npc: tesistaDos,
      dialog: AULA_PRESENTE_DIALOGS['tesista-dos'],
      openDialog: actions.openDialog,
    }),
    npcTalk({
      id: `talk-aula-${room.index}-estudiante-ronda`,
      npc: estudianteRonda,
      dialog: AULA_PRESENTE_DIALOGS['estudiante-ronda'],
      openDialog: actions.openDialog,
    }),
  ]
  for (const talk of talks) {
    interactables.push(talk.interactable)
    updates.push(talk.update)
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
