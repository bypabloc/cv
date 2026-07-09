/**
 * @module rooms/aula (engine)
 * @description Sala 0 — Aula/Universidad (sintetica: UPTYAB 2011-2016,
 *   universidad pura). Salon CLASICO en paleta blanca/beige/azul con
 *   guiños morados: pupitres azules en filas mirando al frente (+Z),
 *   escritorio del profesor con trabajos impresos, y el KIT INFORMATIVO
 *   ESTANDAR (`infoKit`): RETOS / APRENDIZAJES en los muros laterales,
 *   grieta al pasado a la mano izquierda y cuaderno-reseña flotante a la
 *   derecha — el canon que replican todas las salas. 2 estudiantes
 *   SENTADOS tecleando con sus pantallas encendidas (practica de sockets
 *   del laboratorio de redes); las 2 PCs libres — la tuya y una del
 *   laboratorio — se ENCIENDEN y APAGAN con E (toggle ilimitado). 6 NPCs
 *   conversables (arboles de dialogo bilingues + burbuja) re-enfocados a
 *   la vida universitaria: el PROFESOR anticipa las historias de 2015
 *   (foreshadowing de las salas IAI y Asesoria) sin contarlas. Cuadros
 *   de rubro via `wallArt`: diagrama cliente-servidor (inspeccionable,
 *   semilla academica) y la red del laboratorio. Manga-ink.
 */
import { Group } from 'three'
import type { Box2 } from '../../lib/collision'
import { sfx } from '../audio'
import { makeNpc, type NpcHandle } from '../character'
import { npcTalk } from '../dialog'
import { AULA_PRESENTE_DIALOGS } from '../dialogs/aula-presente'
import type { Interactable } from '../state'
import { disposeDeep, outlineGroup } from '../toon'
import type { RoomBuild, RoomCtx } from '../world'
import { placeFurniture } from './furniture'
import {
  footprint,
  infoKit,
  npcCoworkers,
  paperStack,
  schoolChair,
  seatInteractable,
  switchableMonitor,
  wallArt,
} from './props'

// escritorio CC0 (Kenney Furniture Kit) tintado de BLANCO; las sillas son
// procedurales de 4 patas (schoolChair) — universidad de bajos recursos, 2011
const DESK_URL = '/models/furniture/desk.glb'

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

/** Practica del laboratorio de redes: cliente-servidor en C. */
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
    'practica de redes: OK',
  ],
} as const

// --- pizarras del aula (wallArt): TIZA sobre pizarra verde vieja con marco
// de madera (colegio de bajos recursos, pedido del dueno 2026-07-07). Los
// nombres ART_* se conservan (los usan las draw fns); los valores son ahora
// la paleta de tiza. ---

const ART_PAPER = '#33503f' // verde pizarra (fondo del tablero)
const ART_INK = '#eef2e6' // tiza blanca (texto y trazos)
const ART_BLUE = '#a9d6ef' // tiza celeste (acento)
const ART_PURPLE = '#f2e2a6' // tiza amarilla (acento)

// escritorios BLANCOS + sillas de madera (4 patas) + monitor CRT crema (2000);
// las pizarras verdes llevan marco de madera
const WHITE_DESK = '#eeece4'
const CHAIR_WOOD = '#a9743f'
const WOOD_FRAME = '#7a5230'
const CRT_CREAM = '#e3ddcb'

function artBase(ctx: CanvasRenderingContext2D, size: number): void {
  ctx.fillStyle = ART_PAPER
  ctx.fillRect(0, 0, size, size)
  // manchas de borrador (polvo de tiza) muy sutiles
  ctx.globalAlpha = 0.06
  ctx.fillStyle = ART_INK
  const smudges: readonly (readonly [number, number, number])[] = [
    [70, 58, 58],
    [188, 150, 66],
    [120, 210, 48],
  ]
  for (const [cx, cy, r] of smudges) {
    ctx.beginPath()
    ctx.ellipse(cx, cy, r, r * 0.5, 0, 0, Math.PI * 2)
    ctx.fill()
  }
  ctx.globalAlpha = 0.4
  ctx.strokeStyle = ART_INK
  ctx.lineWidth = 3
  ctx.strokeRect(10, 10, size - 20, size - 20)
  ctx.globalAlpha = 1
}

/** Caja de tiza: contorno + etiqueta (sin relleno — el trazo es tiza). */
function artBox(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  text: string,
  color: string,
): void {
  ctx.strokeStyle = color
  ctx.lineWidth = 3
  ctx.strokeRect(x, y, w, h)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 15px "Space Mono", ui-monospace, monospace'
  ctx.textAlign = 'center'
  ctx.fillText(text, x + w / 2, y + h / 2 + 5)
  ctx.textAlign = 'left'
}

/** Diagrama cliente-servidor del proyecto (PC servidor + 3 clientes). */
function drawClienteServidor(
  ctx: CanvasRenderingContext2D,
  size: number,
): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 18px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('CLIENTE-SERVIDOR', 24, 40)
  artBox(ctx, 78, 60, 100, 36, 'SERVIDOR', ART_BLUE)
  ctx.strokeStyle = ART_INK
  ctx.lineWidth = 2
  const clients: readonly number[] = [40, 108, 176]
  for (const cx of clients) {
    ctx.beginPath()
    ctx.moveTo(128, 96)
    ctx.lineTo(cx + 20, 168)
    ctx.stroke()
    artBox(ctx, cx, 168, 42, 30, 'PC', ART_INK)
  }
  ctx.fillStyle = ART_BLUE
  ctx.font = '13px "Space Mono", ui-monospace, monospace'
  ctx.fillText('ping ->', 44, 130)
  ctx.fillText('<- pong 2ms', 140, 150)
  ctx.fillStyle = ART_INK
  ctx.globalAlpha = 0.6
  ctx.fillText('datos centralizados, cero copias', 24, 226)
  ctx.globalAlpha = 1
}

/** El pensum de la carrera: las materias que forman el cimiento. */
function drawPensum(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 18px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('ING. INFORMATICA', 24, 40)
  ctx.strokeStyle = ART_PURPLE
  ctx.lineWidth = 4
  ctx.beginPath()
  ctx.moveTo(24, 50)
  ctx.lineTo(180, 50)
  ctx.stroke()
  const materias = ['POO', 'BD', 'REDES', 'SO', 'ARQ']
  materias.forEach((materia, i) => {
    const x = 24 + (i % 3) * 70
    const y = 74 + Math.floor(i / 3) * 44
    artBox(ctx, x, y, 60, 30, materia, i % 2 === 0 ? ART_BLUE : ART_PURPLE)
  })
  ctx.fillStyle = ART_INK
  ctx.font = '14px "Space Mono", ui-monospace, monospace'
  ctx.fillText('2011 -> 2016 · UPTYAB', 24, 186)
  ctx.fillStyle = ART_BLUE
  ctx.font = 'bold 16px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('el cimiento de todo', 24, 222)
}

/** Topologia de la red local del laboratorio. */
function drawRedLocal(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 18px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('RED DEL LABORATORIO', 24, 40)
  artBox(ctx, 98, 108, 60, 30, 'SWITCH', ART_PURPLE)
  const nodes: readonly (readonly [number, number])[] = [
    [40, 62],
    [156, 62],
    [40, 180],
    [156, 180],
  ]
  ctx.strokeStyle = ART_INK
  ctx.lineWidth = 2
  for (const [nx, ny] of nodes) {
    ctx.beginPath()
    ctx.moveTo(128, 123)
    ctx.lineTo(nx + 30, ny + 15)
    ctx.stroke()
    artBox(ctx, nx, ny, 60, 30, '10.0.1.x', ART_INK)
  }
  ctx.fillStyle = ART_INK
  ctx.globalAlpha = 0.6
  ctx.font = '13px "Space Mono", ui-monospace, monospace'
  ctx.fillText('una PC servidor, todos conectados', 24, 232)
  ctx.globalAlpha = 1
}

const ART_FICHA = {
  title: {
    es: 'La red cliente-servidor del laboratorio',
    en: 'The lab client-server network',
  },
  paragraphs: {
    es: [
      'En el laboratorio de redes se montaba una red local con una PC ' +
        'como servidor central: todos los clientes compartian los mismos ' +
        'datos y el ping-pong entre maquinas era el latido del aula.',
      'Ese diseño — diagnosticar, centralizar, documentar cada decision — ' +
        'fue la base de la arquitectura de software que Pablo siguio ' +
        'construyendo el resto de su carrera.',
      'Lo que esa semilla germino en 2015 — un instituto de obras ' +
        'publicas y una tesis rescatada — se cuenta unas salas mas ' +
        'adelante en el recorrido.',
    ],
    en: [
      'In the networks lab we built a local network with one PC as the ' +
        'central server: every client shared the same data and the ' +
        'ping-pong between machines was the heartbeat of the room.',
      'That design — diagnose, centralize, document every decision — ' +
        'became the foundation of the software architecture Pablo kept ' +
        'building for the rest of his career.',
      'What that seed grew into during 2015 — a public-works institute ' +
        'and a rescued thesis — is told a few rooms ahead in the ' +
        'journey.',
    ],
  },
} as const

export default function buildAula(ctx: RoomCtx): RoomBuild {
  const { def, room, theme, state, actions } = ctx
  const group = new Group()
  const interactables: Interactable[] = []
  const updates: ((t: number, dt: number) => void)[] = []
  const npcs: NpcHandle[] = []
  const disposables: { dispose(): void }[] = []
  const staticColliders: Box2[] = []
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

  // pupitres en filas mirando al frente (+Z); el front-right es "tu PC".
  // Con la sala uniforme (13.2 m) hay 2 columnas con PC + 2 columnas de
  // pupitres libres a los costados (sin monitor: laminas del mismo merge).
  const deskSpots: readonly (readonly [number, number])[] = [
    [-2, room.z + 1.2],
    [2, room.z + 1.2],
    [-2, room.z - 1.2],
    [2, room.z - 1.2],
  ]
  const emptySpots: readonly (readonly [number, number])[] = [
    [-5, room.z + 1.2],
    [5, room.z + 1.2],
    [-5, room.z - 1.2],
    [5, room.z - 1.2],
  ]
  const seatSpots = [...deskSpots, ...emptySpots]
  const allDesks: readonly (readonly [number, number])[] = [
    [-2, room.z + 3.6],
    ...seatSpots,
  ]
  // mobiliario CC0 Kenney (T4): escritorios + sillas GLB en las MISMAS
  // posiciones del pupitre viejo. Los colliders (footprint, abajo) siguen
  // siendo la fuente de verdad de la navegacion. El alumno se sienta en
  // z-0.55 mirando al frente (+Z); el profesor mira a la clase (-Z).
  for (const [x, z] of allDesks) {
    group.add(
      placeFurniture({
        url: DESK_URL,
        x,
        z,
        targetWidth: 1.15,
        color: WHITE_DESK,
      }),
    )
  }
  // sillas de 4 patas (procedurales) detras de cada escritorio, mirando +Z
  for (const [x, z] of seatSpots) {
    group.add(schoolChair({ position: [x, 0, z - 0.55], color: CHAIR_WOOD }))
  }
  // silla del profesor: mira a la clase (-Z)
  group.add(
    schoolChair({
      position: [-2, 0, room.z + 4.15],
      rotationY: Math.PI,
      color: CHAIR_WOOD,
    }),
  )
  // COLISIONES (fuente de verdad de la navegacion, desacopladas de la
  // geometria): UN footprint por escritorio + UNO por silla VACIA, en una
  // sola pasada consistente. Las sillas con NPC sentado (deskSpots 0 y 3, y
  // la del profesor) las cubre el collider del propio NPC -> se saltan aca.
  const NPC_PCS: ReadonlySet<number> = new Set([0, 3])
  staticColliders.push(footprint(-2, room.z + 3.6, 1.2, 0.7)) // escritorio profe
  deskSpots.forEach(([x, z], i) => {
    staticColliders.push(footprint(x, z, 1.2, 0.7))
    if (!NPC_PCS.has(i)) {
      staticColliders.push(footprint(x, z - 0.55, 0.46, 0.46))
    }
  })
  for (const [x, z] of emptySpots) {
    staticColliders.push(
      footprint(x, z, 1.2, 0.7),
      footprint(x, z - 0.55, 0.46, 0.46),
    )
  }
  // trabajos de catedra impresos sobre el escritorio del profesor
  group.add(paperStack({ position: [-2.3, 0.745, room.z + 3.6], count: 6 }))

  // monitores: los de los NPCs ya estan ENCENDIDOS (estan trabajando);
  // las 2 PCs libres se encienden INDIVIDUALMENTE con E (NPC_PCS definido arriba)
  deskSpots.forEach(([x, z], index) => {
    const isPlayerPc = index === 1
    const code = isPlayerPc
      ? PLAYER_PC_SCREEN
      : (CODE_SCREENS[index % 2] ?? PLAYER_PC_SCREEN)
    const { group: monitorGroup, screen } = switchableMonitor({
      position: [x, 0.72, z + 0.05],
      rotationY: Math.PI,
      width: 0.46,
      // PC blanca vieja (CRT abultado crema, estilo 2000)
      crt: true,
      bodyColor: CRT_CREAM,
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

  // sillas vacias sentables (AC-4): tu PC, la del laboratorio y los 4
  // pupitres decorativos. La silla del profesor (room.z+4.15, dir=-1)
  // queda EXCLUIDA: la ocupa el NPC profesor.
  const sittableSpots = [deskSpots[1], deskSpots[2], ...emptySpots]
  sittableSpots.forEach((spot, index) => {
    if (!spot) {
      return
    }
    const [x, z] = spot
    interactables.push(
      seatInteractable(`silla-aula-${room.index}-${index}`, x, z - 0.55, state),
    )
  })

  // kit informativo estandar (RETOS / APRENDIZAJES / grieta / cuaderno):
  // misma posicion y tamaño en TODAS las salas — el aula es el canon
  const texts = def.texts[state.locale]
  const kit = infoKit({
    room,
    year: def.year,
    theme,
    locale: state.locale,
    texts,
    withLight: state.tier === 'full',
    // salon de clases: RETOS/APRENDIZAJES en pizarra verde con tiza
    boardStyle: 'chalk',
    onFicha: actions.openFicha,
    onEnterPast: actions.enterPast,
    onStory: actions.openStory,
  })
  staticColliders.push(...kit.colliders)
  for (const prop of kit.props) {
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
  const companeraLab = makeNpc({
    skin: '#e8b48c',
    hair: { style: 'ponytail', color: '#5a3a22' },
    top: '#4a6a52',
    bottom: '#3a4048',
    model: 'michelle',
    faceSeed: 11,
    position: [-2, 0, room.z + 0.65],
    rotationY: 0,
    pose: 'sit',
  })
  const estudianteSockets = makeNpc({
    skin: '#d9a684',
    hair: { style: 'spiky', color: '#1c1410' },
    top: '#7a5c3a',
    bottom: '#2e3238',
    model: 'josh',
    faceSeed: 23,
    position: [2, 0, room.z - 1.75],
    rotationY: 0,
    pose: 'sit',
  })
  const estudianteRonda = makeNpc({
    skin: '#c98f6a',
    hair: { style: 'bun', color: '#2a1c12' },
    top: '#3f5a8a',
    bottom: '#3a4048',
    model: 'sophie',
    faceSeed: 37,
    position: [3.6, 0, room.z + 2.6],
    path: [
      [3.6, room.z + 2.6],
      [-3.6, room.z + 2.6],
      [-3.6, room.z - 3.6],
      [3.6, room.z - 3.6],
    ],
    speed: 0.7,
  })
  npcs.push(companeraLab, estudianteSockets, estudianteRonda)
  for (const npc of npcs) {
    group.add(npc.group)
    updates.push((t, dt) => npc.update(t, dt))
  }
  const talks = [
    npcTalk({
      id: `talk-aula-${room.index}-companera-lab`,
      npc: companeraLab,
      dialog: AULA_PRESENTE_DIALOGS['companera-lab'],
      openDialog: actions.openDialog,
    }),
    npcTalk({
      id: `talk-aula-${room.index}-estudiante-sockets`,
      npc: estudianteSockets,
      dialog: AULA_PRESENTE_DIALOGS['estudiante-sockets'],
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

  // CANON (AC-9): profesor sentado en su escritorio que habla bien de
  // Pablo + compañero del proyecto de grado + estudiante capacitado
  const coworkers = npcCoworkers({
    roomIndex: room.index,
    validateMix: false, // el aula esta exenta del mix 2+2 (AC-5)
    openDialog: actions.openDialog,
    npcs: [
      {
        key: 'profesor',
        role: 'boss',
        spec: {
          skin: '#d9a684',
          hair: { style: 'short', color: '#8a8a92' },
          top: '#5a4632',
          bottom: '#3a4048',
          accessory: 'glasses',
          model: 'martha',
          faceSeed: 67,
        },
        position: [-2, 0, room.z + 4.15],
        rotationY: Math.PI,
        pose: 'sit',
        dialog: AULA_PRESENTE_DIALOGS.profesor,
      },
      {
        key: 'companero-proyecto',
        role: 'coworker',
        spec: {
          skin: '#e8b48c',
          hair: { style: 'spiky', color: '#3a2a1a' },
          top: '#6a4a7a',
          bottom: '#3a4048',
          model: 'bryce',
          faceSeed: 71,
        },
        position: [-5, 0, room.z + 0.65],
        rotationY: 0,
        pose: 'sit',
        dialog: AULA_PRESENTE_DIALOGS['companero-proyecto'],
      },
      {
        key: 'companero-ayudado',
        role: 'staff',
        spec: {
          skin: '#c98f6a',
          hair: { style: 'ponytail', color: '#2a1c12' },
          top: '#4a6a8a',
          bottom: '#4a4438',
          model: 'leonard',
          faceSeed: 79,
        },
        position: [5, 0, room.z + 0.65],
        rotationY: 0,
        pose: 'sit',
        dialog: AULA_PRESENTE_DIALOGS['companero-ayudado'],
      },
    ],
  })
  npcs.push(...coworkers.npcs)
  for (const npc of coworkers.npcs) {
    group.add(npc.group)
    updates.push((t, dt) => npc.update(t, dt))
  }
  for (const talk of coworkers.talks) {
    interactables.push(talk.interactable)
    updates.push(talk.update)
  }

  // cuadros de rubro (wallArt): diagrama cliente-servidor (inspeccionable,
  // AC-7) + pensum de la carrera en el muro del fondo; red local en la
  // entrada. (La lamina del plan de rescate se mudo a la sala asesoria.)
  const art = wallArt({
    roomIndex: room.index,
    theme,
    locale: state.locale,
    onFicha: actions.openStory,
    // marco de madera: las 3 laminas son pizarras verdes del aula
    frameColor: WOOD_FRAME,
    frames: [
      {
        key: 'cliente-servidor',
        position: [-3.6, 2, room.z + room.depth / 2 - 0.08],
        rotationY: Math.PI,
        draw: drawClienteServidor,
        ficha: ART_FICHA,
      },
      {
        key: 'pensum',
        position: [3.6, 2, room.z + room.depth / 2 - 0.08],
        rotationY: Math.PI,
        draw: drawPensum,
      },
      {
        key: 'red-local',
        position: [-3.6, 2, room.z - room.depth / 2 + 0.08],
        rotationY: 0,
        draw: drawRedLocal,
      },
    ],
  })
  staticColliders.push(...art.colliders)
  for (const prop of art.props) {
    group.add(prop.group)
    if (prop.interactable) {
      interactables.push(prop.interactable)
    }
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
