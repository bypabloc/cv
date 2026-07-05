/**
 * @module rooms/aula (engine)
 * @description Sala 0 — Aula/Universidad (iai + projects-degrees, 2015).
 *   Salon CLASICO en paleta blanca/beige/azul con guiños morados: pupitres
 *   azules en filas mirando al frente (+Z), escritorio del profesor con
 *   tesis impresas, y el KIT INFORMATIVO ESTANDAR (`infoKit`): RETOS /
 *   APRENDIZAJES en los muros laterales, grieta al pasado a la mano
 *   izquierda y cuaderno-reseña flotante a la derecha — el canon que
 *   replican todas las salas. 2 estudiantes SENTADOS tecleando con sus
 *   pantallas encendidas (codigo cliente-servidor del proyecto de grado);
 *   las 2 PCs libres — la tuya y una del laboratorio — se ENCIENDEN y
 *   APAGAN con E (toggle ilimitado). 6 NPCs conversables (arboles de
 *   dialogo bilingues + burbuja): los 3 estudiantes originales + el
 *   PROFESOR sentado en su escritorio que habla bien de Pablo, un
 *   compañero del proyecto de grado y un estudiante capacitado (AC-9,
 *   canon journey-salas-estandar). Cuadros de rubro via `wallArt`:
 *   diagrama cliente-servidor (inspeccionable), plan de rescate de 1
 *   semana y la red local. Manga-ink.
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
  footprint,
  infoKit,
  npcCoworkers,
  paperStack,
  switchableMonitor,
  wallArt,
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

// --- laminas de los cuadros (wallArt): tinta plana sobre papel claro ---

const ART_PAPER = '#f4efe2'
const ART_INK = '#232840'
const ART_BLUE = '#2f6fd0'
const ART_PURPLE = '#7a4fc0'

function artBase(ctx: CanvasRenderingContext2D, size: number): void {
  ctx.fillStyle = ART_PAPER
  ctx.fillRect(0, 0, size, size)
  ctx.strokeStyle = ART_INK
  ctx.globalAlpha = 0.35
  ctx.lineWidth = 3
  ctx.strokeRect(10, 10, size - 20, size - 20)
  ctx.globalAlpha = 1
}

function artBox(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  text: string,
  color: string,
): void {
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(x, y, w, h)
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

/** El plan de rescate: 1 semana, 2 tesis listas para defensa. */
function drawPlanRescate(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 18px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('PLAN · 1 SEMANA', 24, 40)
  ctx.strokeStyle = ART_PURPLE
  ctx.lineWidth = 4
  ctx.beginPath()
  ctx.moveTo(24, 50)
  ctx.lineTo(180, 50)
  ctx.stroke()
  const days = ['L', 'M', 'M', 'J', 'V', 'S', 'D']
  days.forEach((day, i) => {
    const x = 24 + i * 30
    artBox(ctx, x, 74, 26, 26, day, ART_INK)
    ctx.strokeStyle = ART_BLUE
    ctx.lineWidth = 3
    ctx.beginPath()
    ctx.moveTo(x + 6, 88)
    ctx.lineTo(x + 11, 94)
    ctx.lineTo(x + 20, 80)
    ctx.stroke()
  })
  ctx.fillStyle = ART_INK
  ctx.font = '14px "Space Mono", ui-monospace, monospace'
  ctx.fillText('dia 1-2: diagnostico', 24, 136)
  ctx.fillText('dia 3-5: plan + codigo', 24, 160)
  ctx.fillText('dia 6-7: defensa lista', 24, 184)
  ctx.fillStyle = ART_BLUE
  ctx.font = 'bold 16px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('2 tesis: de meses a dias', 24, 222)
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
    es: 'La red cliente-servidor (2015)',
    en: 'The client-server network (2015)',
  },
  paragraphs: {
    es: [
      'El proyecto academico corria sobre una red local con una PC como ' +
        'servidor central: todos los clientes compartian los mismos datos ' +
        'y desaparecieron las copias desincronizadas.',
      'Ese diseño — diagnosticar, centralizar, documentar cada decision — ' +
        'fue la base de la arquitectura de software que Pablo siguio ' +
        'construyendo el resto de su carrera.',
      'El plan enmarcado al lado cuenta la otra historia del aula: dos ' +
        'proyectos de grado bloqueados durante meses, reencaminados y ' +
        'listos para defensa en mas o menos una semana.',
    ],
    en: [
      'The academic project ran on a local network with one PC as the ' +
        'central server: every client shared the same data and the ' +
        'out-of-sync copies disappeared.',
      'That design — diagnose, centralize, document every decision — ' +
        'became the foundation of the software architecture Pablo kept ' +
        'building for the rest of his career.',
      'The framed plan next to it tells the other story of this room: ' +
        'two final projects blocked for months, put back on track and ' +
        'ready for defense in roughly one week.',
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
  // silla de un puesto: asiento + respaldo + 2 patas (dir=-1 la del profe)
  const chairParts = (x: number, cz: number, dir: 1 | -1) => [
    { w: 0.42, h: 0.05, d: 0.42, x, y: 0.44, z: cz },
    { w: 0.42, h: 0.5, d: 0.05, x, y: 0.72, z: cz - 0.2 * dir },
    { w: 0.05, h: 0.44, d: 0.05, x: x - 0.17, y: 0.22, z: cz - 0.1 * dir },
    { w: 0.05, h: 0.44, d: 0.05, x: x + 0.17, y: 0.22, z: cz - 0.1 * dir },
  ]
  // profesor + 8 pupitres + 9 sillas fusionados: 2 draw calls (AC-10).
  // Mobiliario AZUL (tema del aula: blanco + beige + azul, guiños morados)
  const seatSpots = [...deskSpots, ...emptySpots]
  const allDesks: readonly (readonly [number, number])[] = [
    [-2, room.z + 3.6],
    ...seatSpots,
  ]
  group.add(
    outlinedMergedBoxes(
      [
        ...allDesks.flatMap(([x, z]) => [
          { w: 1.1, h: 0.05, d: 0.6, x, y: 0.72, z },
          { w: 0.06, h: 0.72, d: 0.55, x: x - 0.5, y: 0.36, z },
          { w: 0.06, h: 0.72, d: 0.55, x: x + 0.5, y: 0.36, z },
        ]),
        ...seatSpots.flatMap(([x, z]) => chairParts(x, z - 0.55, 1)),
        ...chairParts(-2, room.z + 4.15, -1),
      ],
      toonMat('#33517e'),
      { inflate: 0.035, castShadow: true },
    ),
  )
  staticColliders.push(
    footprint(-2, room.z + 3.6, 1.2, 0.8),
    // sillas vacias (tu PC, la del lab y la del profesor)
    footprint(2, room.z + 0.65, 0.5, 0.5),
    footprint(-2, room.z - 1.75, 0.5, 0.5),
    footprint(-2, room.z + 4.15, 0.5, 0.5),
  )
  for (const [x, z] of emptySpots) {
    staticColliders.push(
      footprint(x, z, 1.3, 0.8),
      footprint(x, z - 0.55, 0.5, 0.5),
    )
  }
  // tesis impresas sobre el escritorio del profesor (guiño: los proyectos
  // de grado que Pablo rescato viven en papel sobre esa mesa)
  group.add(paperStack({ position: [-2.3, 0.745, room.z + 3.6], count: 6 }))

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
  const tesistaUno = makeNpc({
    skin: '#e8b48c',
    hair: { style: 'ponytail', color: '#5a3a22' },
    top: '#4a6a52',
    bottom: '#3a4048',
    faceSeed: 11,
    position: [-2, 0, room.z + 0.65],
    rotationY: 0,
    pose: 'sit',
  })
  const tesistaDos = makeNpc({
    skin: '#d9a684',
    hair: { style: 'spiky', color: '#1c1410' },
    top: '#7a5c3a',
    bottom: '#2e3238',
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
  // AC-7) + plan de rescate en el muro del fondo; red local en la entrada
  const art = wallArt({
    roomIndex: room.index,
    theme,
    locale: state.locale,
    onFicha: actions.openStory,
    frames: [
      {
        key: 'cliente-servidor',
        position: [-3.6, 2, room.z + room.depth / 2 - 0.08],
        rotationY: Math.PI,
        draw: drawClienteServidor,
        ficha: ART_FICHA,
      },
      {
        key: 'plan-rescate',
        position: [3.6, 2, room.z + room.depth / 2 - 0.08],
        rotationY: Math.PI,
        draw: drawPlanRescate,
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
