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
import {
  desk,
  deskKeyboard,
  deskMouse,
  footprint,
  infoKit,
  npcCoworkers,
  seatInteractable,
  switchableMonitor,
  wallArt,
} from './props'
import { placeProp } from './props-catalog'

// mobiliario escolar CC0: pupitre `wooden_desk` (escritorio real de patas,
// blanco) + silla `school_chair` (respaldo de travesaños) — universidad de
// bajos recursos, 2011. NO se usa `school_desk`/`desk_office` del pack: ese
// modelo es en realidad un BAUL/cofre macizo, no un escritorio (se veia como
// una caja blanca solida). `wooden_desk` si tiene superficie + patas.

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

type ScreenTheme = { screenBg: string; screenFg: string; ink: string }
type OffScreen = { lines: readonly string[]; theme: ScreenTheme; dot: string }

/**
 * Un CRT crema con Linux para un pupitre del aula (helper para bajar la
 * complejidad de buildAula). El de la profesora (isProf) mira a la clase (-Z);
 * los alumnos miran +Z. Encendido si es la profesora o el puesto tiene NPC;
 * los puestos vacios devuelven un interactable para encender/apagar con E.
 */
function aulaCrt(o: {
  x: number
  z: number
  index: number
  isProf: boolean
  hasNpc: boolean
  deskTop: number
  crtBody: string
  screenTheme: ScreenTheme
  offScreen: OffScreen
}): {
  group: Group
  screen: ReturnType<typeof switchableMonitor>['screen']
  interactable?: Interactable
} {
  const isPlayerPc = o.index === 0 // el 1er pupitre de alumno es "tu PC"
  const code = isPlayerPc
    ? PLAYER_PC_SCREEN
    : (CODE_SCREENS[o.index % 2] ?? PLAYER_PC_SCREEN)
  const powered = o.isProf || o.hasNpc
  // El CRT de la profesora mira hacia SU silla (+Z, "al reves" respecto a los
  // alumnos; pedido de Pablo — la profesora se sienta detras y lo ve de frente)
  // y se corre a +X (lado de la profe, lejos del tacho a -X). Los CRT de los
  // alumnos miran a la clase (-Z), del lado del alumno.
  const mx = o.isProf ? o.x + 0.5 : o.x
  // el CRT del alumno se corre al FONDO del escritorio (+Z, lejos del alumno
  // que se sienta en -Z) para que su pecho no lo toque; el teclado va al frente
  // (ver abajo). El de la profesora queda hacia su silla (+Z).
  const mz = o.isProf ? o.z - 0.05 : o.z + 0.2
  const { group, screen } = switchableMonitor({
    position: [mx, o.deskTop, mz],
    rotationY: o.isProf ? 0 : Math.PI,
    width: 0.46,
    crt: true,
    bodyColor: o.crtBody,
    variants: {
      off: o.offScreen,
      on: {
        title: code.title,
        lines: code.lines,
        theme: o.screenTheme,
        dot: '#3f9d63',
        kind: 'linux',
      },
    },
    initial: powered ? 'on' : 'off',
  })
  // teclado bajo las manos del que teclea (hijo del group; z local positivo =
  // hacia el alumno/profe). Alumno: CRT al fondo (mz=z+0.2); sus manos de la
  // pose typing caen en mundo z~+0.1 respecto al centro del escritorio (medido
  // con tmp/aula-measure.py leyendo los bones mixamorig_*Hand), asi que el
  // teclado va a z local 0.3 = mundo z+0.2-0.3 = z-0.1, justo bajo las manos.
  group.add(deskKeyboard({ position: [0, 0, 0.3], width: 0.36 }))
  // mouse al costado derecho del teclado (x local +0.3, fuera del teclado de
  // ancho 0.36 -> borde en +0.18), misma z. En coords LOCALES del group del
  // CRT (rotado hacia el que teclea), asi que queda a la derecha del alumno.
  group.add(deskMouse({ position: [0.3, 0, 0.3] }))
  if (o.isProf || o.hasNpc) {
    return { group, screen }
  }
  // pupitre vacio: toggle ilimitado encender/apagar la PC con E
  const labels = isPlayerPc ? PC_LABELS.mine : PC_LABELS.lab
  let on = false
  const interactable: Interactable = {
    id: `micro-aula-pc${o.index}`,
    x: o.x,
    z: o.z,
    radius: 1.8,
    label: { ...labels.on },
    onActivate: () => {
      on = !on
      screen.show(on ? 'on' : 'off')
      sfx.play(on ? 'boot' : 'shutdown')
      interactable.label = on ? labels.off : labels.on
    },
  }
  return { group, screen, interactable }
}

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

  // LAYOUT 4+4 (pedido de Pablo 2026-07-09): 4 pupitres a la IZQUIERDA + 4 a
  // la DERECHA, dejando el PASILLO CENTRAL (x=0) LIBRE para el pilar del
  // cuaderno (infoKit, en x=0/z=room.z). Cada lado = 2 columnas x 2 filas,
  // todos mirando al frente (+Z, hacia la profesora). El alumno se sienta en
  // seatZ(z) mirando +Z; los footprints (abajo) siguen siendo la fuente de
  // verdad de la navegacion. TODOS los pupitres tienen su CRT con Linux.
  // filas mas separadas entre si (gap ~3.2 vs 2.6 antes) para que no se vean
  // pegadas (captura de Pablo 2026-07-09): fila delantera mas al frente, trasera
  // mas atras.
  const FRONT_Z = room.z - 1.8
  const BACK_Z = room.z + 1.4
  // 2 columnas por lado, mas separadas del pasillo central y entre si:
  // izquierda x=-5.0/-2.6, derecha x=2.6/5.0 (gap columna ~2.4, antes 2.0)
  const LEFT_COLS = [-5.0, -2.6] as const
  const RIGHT_COLS = [2.6, 5.0] as const
  const ROWS = [BACK_Z, FRONT_Z] as const
  // 8 spots: bloque izquierdo primero (4) luego derecho (4), fila trasera y
  // delantera por columna. El orden define que puesto tiene NPC vs es sentable.
  const studentSpots: readonly (readonly [number, number])[] = [
    ...LEFT_COLS.flatMap((x) => ROWS.map((z) => [x, z] as const)),
    ...RIGHT_COLS.flatMap((x) => ROWS.map((z) => [x, z] as const)),
  ]
  const PROF_DESK: readonly [number, number] = [-1.2, room.z + 3.6]
  // dimensiones del pupitre (para cuadrar geometria, asiento y colision).
  // Pupitre = escritorio-tablon PROCEDURAL desk() (superficie + 2 patas, SIN
  // gavetas — es de universidad; pedido de Pablo). Es SIMETRICO, no puede
  // quedar "al reves" como el GLB wooden_desk (que tenia cajones hacia el
  // alumno). Superficie a y=0.72; el asiento va 0.55m detras (en -Z).
  const DESK_W = 1.3
  const DESK_D = 0.62 // footprint de profundidad del tablon desk() (d=0.6) + margen
  const DESK_TOP = 0.72 // altura de la superficie del desk() procedural
  // el asiento (y el NPC) va bien detras del escritorio para que el pecho NO
  // toque el monitor (captura de Pablo 2026-07-09: estaban muy pegados al CRT).
  // 0.55 -> 0.7. El monitor ademas se corre al FONDO del escritorio (+Z) y el
  // teclado al FRENTE (hacia el alumno) para que las manos de typing lo
  // alcancen — ver aulaCrt.
  const SEAT_OFFSET = 0.7 // cuanto detras del escritorio va el asiento
  const SEAT_FP = 0.46 // footprint de la silla escolar
  const seatZ = (z: number): number => z - SEAT_OFFSET
  // los 5 primeros spots tienen un alumno NPC sentado; los 3 restantes quedan
  // como sillas vacias SENTABLES (E). La profesora ya NO se sienta (esta de
  // pie explicando), asi que su silla desaparece.
  const NPC_STUDENTS: ReadonlySet<number> = new Set([0, 1, 2, 3, 4])
  // el escritorio de la profesora es mas ANCHO que los pupitres (pedido de
  // Pablo): mesa de docente. Se puede sentar y "usar" su PC (seatInteractable
  // abajo). El resto usa DESK_W.
  const PROF_DESK_W = 2.0
  // silla de la profesora: alineada en X con SU CRT (que se corre +0.5 respecto
  // al mueble — ver aulaCrt) para que quede DE FRENTE a la PC, y mas separada
  // del escritorio (SEAT_OFFSET 0.7 -> PROF_SEAT_OFFSET 1.05) porque estaba muy
  // pegada al monitor (pedido de Pablo). El CRT de la profe mira +Z, la silla
  // queda en +Z mirando -Z hacia el.
  const PROF_SEAT_OFFSET = 1.05
  const PROF_SEAT: readonly [number, number] = [
    PROF_DESK[0] + 0.5,
    PROF_DESK[1] + PROF_SEAT_OFFSET,
  ]
  // pupitres de alumno (tablon procedural sin gavetas, blancos) en cada spot.
  for (const [x, z] of studentSpots) {
    group.add(desk({ position: [x, 0, z], width: DESK_W, color: WHITE_DESK }))
  }
  // escritorio de la profesora, mas ancho.
  group.add(
    desk({
      position: [PROF_DESK[0], 0, PROF_DESK[1]],
      width: PROF_DESK_W,
      color: WHITE_DESK,
    }),
  )
  // sillas escolares (GLB) EN el asiento (seatZ) de cada pupitre de alumno,
  // mirando +Z hacia el pupitre.
  for (const [x, z] of studentSpots) {
    group.add(
      placeProp('school_chair', {
        x,
        z: seatZ(z),
        width: 0.5,
        color: CHAIR_WOOD,
      }),
    )
  }
  // silla del escritorio de la profesora: DETRAS del escritorio (en +Z, del
  // lado del muro del fondo), mirando a la clase (-Z). La profesora esta de
  // pie explicando, pero su silla sigue en su puesto (pedido de Pablo).
  group.add(
    placeProp('school_chair', {
      x: PROF_SEAT[0],
      z: PROF_SEAT[1],
      rotationY: Math.PI,
      width: 0.5,
      color: CHAIR_WOOD,
    }),
  )
  // COLISIONES (fuente de verdad de la navegacion): UN footprint por escritorio
  // + UNO por silla VACIA. Las sillas con NPC sentado (los 5 de NPC_STUDENTS)
  // las cubre el collider del propio NPC -> se saltan aca. La profesora esta de
  // pie: su collider de NPC cubre su posicion; su escritorio si lleva footprint.
  staticColliders.push(
    footprint(PROF_DESK[0], PROF_DESK[1], PROF_DESK_W, DESK_D),
  )
  // colision de la silla de la profesora: le faltaba (esta libre, la profe esta
  // de pie, asi que ningun NPC la cubre). Pedido de Pablo. Footprint al pie de
  // la silla, mismo tamaño que las sillas escolares de alumno.
  staticColliders.push(footprint(PROF_SEAT[0], PROF_SEAT[1], SEAT_FP, SEAT_FP))
  studentSpots.forEach(([x, z], i) => {
    staticColliders.push(footprint(x, z, DESK_W, DESK_D))
    if (!NPC_STUDENTS.has(i)) {
      staticColliders.push(footprint(x, seatZ(z), SEAT_FP, SEAT_FP))
    }
  })
  // props decorativos: la planta va a la esquina DERECHA-en-mundo trasera
  // (-X, pedido de Pablo: esquina contraria) y la papelera al costado
  // IZQUIERDO-en-mundo del escritorio de la profesora (+X respecto al mueble,
  // lado contrario al anterior). Ya NO hay pila de papeles sobre el escritorio
  // de la profesora (tapaba el monitor). El monitor se corre al otro extremo.
  const halfW = room.width / 2
  const PLANT_POS: readonly [number, number] = [-halfW + 0.6, room.z + 4.2]
  const TRASH_POS: readonly [number, number] = [
    PROF_DESK[0] - PROF_DESK_W / 2 - 0.4,
    PROF_DESK[1],
  ]
  group.add(
    placeProp('potted_plant', { x: PLANT_POS[0], z: PLANT_POS[1], width: 0.5 }),
    placeProp('trash_can', { x: TRASH_POS[0], z: TRASH_POS[1], width: 0.36 }),
  )
  // colisionadores de la planta y el tacho (pedido de Pablo): el jugador no
  // los atraviesa. Footprints al pie de cada prop, ajustados a su ancho.
  staticColliders.push(footprint(PLANT_POS[0], PLANT_POS[1], 0.5, 0.5))
  staticColliders.push(footprint(TRASH_POS[0], TRASH_POS[1], 0.36, 0.36))

  // COMPUTADORAS: TODOS los pupitres de alumno + el de la profesora llevan un
  // CRT blanco viejo (crema, estilo 2000) con Linux (pedido de Pablo). Los de
  // los 5 alumnos NPC arrancan ENCENDIDOS (estan tecleando); los 3 vacios se
  // encienden con E. El de la profesora arranca encendido (esta explicando).
  // El helper aulaCrt encapsula el monitor + su interactable (baja complejidad).
  const monitorSpots: readonly (readonly [number, number])[] = [
    ...studentSpots,
    PROF_DESK,
  ]
  // screen del CRT de cada spot de ALUMNO (por indice en studentSpots) + el de
  // la PROFESORA, para que el asiento de cada pupitre encienda su PC al
  // sentarse el jugador.
  type CrtScreen = ReturnType<typeof aulaCrt>['screen']
  const spotScreens = new Map<number, CrtScreen>()
  let profScreen: CrtScreen | null = null
  monitorSpots.forEach(([x, z], index) => {
    const isProf = index === studentSpots.length
    const isSittable = index < studentSpots.length && !NPC_STUDENTS.has(index)
    const crt = aulaCrt({
      x,
      z,
      index,
      isProf,
      hasNpc: NPC_STUDENTS.has(index),
      deskTop: DESK_TOP,
      crtBody: CRT_CREAM,
      screenTheme,
      offScreen,
    })
    group.add(crt.group)
    disposables.push(crt.screen)
    if (isProf) {
      profScreen = crt.screen
    } else {
      spotScreens.set(index, crt.screen)
    }
    // el toggle manual de la PC (E) SOLO en spots NO sentables (los sentables
    // encienden/apagan la PC al sentarse/levantarse — abajo). Evita el doble
    // control desincronizado.
    if (crt.interactable && !isSittable) {
      interactables.push(crt.interactable)
    }
  })

  // proyector sobre el escritorio de la profesora, en el extremo -X de la
  // superficie (el CRT esta a +X mirando a la profe; el proyector apunta a la
  // clase en -Z, hacia la pantalla de proyeccion / los alumnos).
  group.add(
    placeProp('projector', {
      x: PROF_DESK[0] - 0.35,
      z: PROF_DESK[1] - 0.05,
      y: DESK_TOP,
      width: 0.3,
      rotationY: Math.PI, // apunta a la clase (-Z)
    }),
  )

  // sillas vacias sentables (AC-4): los pupitres de alumno SIN NPC. El jugador
  // se sienta con E, la PC de ese puesto se ENCIENDE sola y el jugador TECLEA
  // (pose 'typing'); al levantarse la PC se apaga (pedido de Pablo). El asiento
  // esta en seatZ (mismo offset que los NPCs) mirando +Z hacia el pupitre.
  studentSpots.forEach(([x, z], i) => {
    if (NPC_STUDENTS.has(i)) {
      return
    }
    const screen = spotScreens.get(i)
    interactables.push(
      seatInteractable(`silla-aula-${room.index}-${i}`, x, seatZ(z), state, {
        rotationY: 0, // mira +Z hacia el pupitre/monitor
        pose: 'typing', // teclea al sentarse
        onSeatChange: (seated) => {
          screen?.show(seated ? 'on' : 'off')
          sfx.play(seated ? 'boot' : 'shutdown')
        },
      }),
    )
  })

  // silla de la PROFESORA: sentable tambien (pedido de Pablo). El jugador se
  // sienta en su escritorio ancho y "usa" su PC (teclea). La profe esta de pie
  // explicando, asi que su silla esta libre. Mira -Z (hacia el CRT que apunta
  // +Z). Su PC ya arranca encendida (esta explicando); no se apaga al
  // levantarse (la profe la sigue usando).
  interactables.push(
    seatInteractable(
      `silla-aula-${room.index}-prof`,
      PROF_SEAT[0],
      PROF_SEAT[1],
      state,
      {
        rotationY: Math.PI, // mira -Z hacia su CRT
        pose: 'typing',
        onSeatChange: (seated) => {
          if (seated) {
            profScreen?.show('on')
            sfx.play('boot')
          }
        },
      },
    ),
  )

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
    // pilar del cuaderno = cilindro procedural DELGADO del lecternNotebook (mas
    // chico y moderno que el pedestal.glb, que se veia un podio de museo
    // grande; pedido de Pablo 2026-07-09). hidePillar:false -> lo monta el kit.
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

  // NPCs estudiantes: los 3 SENTADOS en sus pupitres tecleando (pedido de
  // Pablo: NADIE camina; la unica de pie es la profesora). Cada uno se sienta
  // en seatZ() de su spot mirando +Z. Conversables con E (arbol + burbuja).
  const seatOf = (i: number): [number, number, number] => {
    const spot = studentSpots[i] ?? [0, room.z]
    return [spot[0], 0, seatZ(spot[1])]
  }
  const companeraLab = makeNpc({
    skin: '#e8b48c',
    hair: { style: 'ponytail', color: '#5a3a22' },
    top: '#4a6a52',
    bottom: '#3a4048',
    // estudiante universitaria JOVEN (kate, casual)
    model: 'kate',
    faceSeed: 11,
    // sentada en el pupitre trasero izquierdo (studentSpots[0])
    position: seatOf(0),
    rotationY: 0,
    pose: 'typing',
    standToTalk: true, // se levanta a conversar (pedido de Pablo)
  })
  const estudianteSockets = makeNpc({
    skin: '#d9a684',
    hair: { style: 'spiky', color: '#1c1410' },
    top: '#7a5c3a',
    bottom: '#2e3238',
    model: 'josh',
    faceSeed: 23,
    // sentado en el pupitre trasero derecho del bloque izquierdo (studentSpots[2])
    position: seatOf(2),
    rotationY: 0,
    pose: 'typing',
    standToTalk: true,
  })
  const estudianteRonda = makeNpc({
    skin: '#c98f6a',
    hair: { style: 'bun', color: '#2a1c12' },
    top: '#3f5a8a',
    bottom: '#3a4048',
    model: 'sophie',
    faceSeed: 37,
    // antes caminaba en ronda; ahora SENTADA en el pupitre trasero del bloque
    // derecho (studentSpots[4]) — nadie camina en el aula (pedido de Pablo).
    position: seatOf(4),
    rotationY: 0,
    pose: 'typing',
    standToTalk: true,
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

  // profesora DE PIE explicando junto a su escritorio (pedido de Pablo: la
  // UNICA de pie). Va por makeNpc directo (no npcCoworkers, que solo admite
  // poses sentadas): pose 'point' = gesticula explicando, mirando a la clase.
  const profesora = makeNpc({
    skin: '#d9a684',
    hair: { style: 'short', color: '#8a8a92' },
    top: '#5a4632',
    bottom: '#3a4048',
    accessory: 'glasses',
    model: 'martha',
    faceSeed: 67,
    // junto a su escritorio, al lado DERECHO-en-mundo de este (+X, lado
    // contrario al anterior; pedido de Pablo), un paso al frente, mirando a
    // los alumnos (-Z). El tacho quedo al otro extremo del escritorio.
    position: [PROF_DESK[0] + 1.4, 0, PROF_DESK[1] - 0.7],
    rotationY: Math.PI,
    pose: 'point',
  })
  npcs.push(profesora)
  group.add(profesora.group)
  updates.push((t, dt) => profesora.update(t, dt))
  const profesoraTalk = npcTalk({
    id: `talk-aula-${room.index}-profesor`,
    npc: profesora,
    dialog: AULA_PRESENTE_DIALOGS.profesor,
    openDialog: actions.openDialog,
  })
  interactables.push(profesoraTalk.interactable)
  updates.push(profesoraTalk.update)

  // CANON (AC-9): compañero del proyecto de grado + estudiante capacitado,
  // ambos SENTADOS en pupitres del bloque (nadie mas de pie que la profesora).
  const coworkers = npcCoworkers({
    roomIndex: room.index,
    validateMix: false, // el aula esta exenta del mix 2+2 (AC-5)
    openDialog: actions.openDialog,
    npcs: [
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
        // sentado en el pupitre delantero izquierdo (studentSpots[1])
        position: seatOf(1),
        rotationY: 0,
        pose: 'typing',
        standToTalk: true,
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
        // sentado en el pupitre delantero del bloque izquierdo (studentSpots[3])
        position: seatOf(3),
        rotationY: 0,
        pose: 'typing',
        standToTalk: true,
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
