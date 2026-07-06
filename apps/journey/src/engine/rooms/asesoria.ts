/**
 * @module rooms/asesoria (engine)
 * @description Sala 5 — Asesoria / PROSALUD (nov-dic 2015), construida al
 *   CANON de sala (plan journey-salas-estandar, informe 17): la sede del
 *   instituto de salud YA con el sistema web local que Pablo desarrollo e
 *   implanto EL SOLO (PHP + MySQL sobre XAMPP) + el rincon de asesoria de
 *   la tesis que rescato en ~1 semana. Dos zonas: INSTITUTO (sala de
 *   espera con display de turnos, mostrador de admision con monitor de
 *   afiliados, estante de farmacia con monitor de inventario, cartelera
 *   de campañas) y RINCON DE ASESORIA (officeLayout de 3 puestos con
 *   Jhonny y Oriana en codigo PHP, proyector con las laminas de la
 *   defensa, sobre de pago con ficha — el primer trabajo COBRADO como
 *   consultor). 5 NPCs (2C+2P+1J), wallArt 4 laminas (2 inspeccionables:
 *   cartel PROSALUD + plan de rescate de 1 semana), softwareShowcase
 *   look NAVEGADOR 2015 (unica sala venezolana web; badge RED LOCAL ·
 *   XAMPP) con 3 demos: turnos, farmacia, afiliados. Micros: tomar un
 *   turno (el ticket vuela y el display sube), despachar un medicamento
 *   (la caja vuela, el stock baja y el minimo alerta en rojo) y ENSAYAR
 *   LA DEFENSA (E cicla las laminas del proyector; al completar el
 *   ciclo, los tesistas celebran) + laptop libre togglable. Paredes
 *   blanco hueso; el rubro vive en piso/props/luz (verde salud + morado
 *   eco del aula).
 */
import { Group, Mesh, MeshBasicMaterial, PlaneGeometry } from 'three'
import type { Box2 } from '../../lib/collision'
import type { Locale } from '../../lib/rooms'
import { sfx } from '../audio'
import type { NpcHandle } from '../character'
import { ASESORIA_PRESENTE_DIALOGS } from '../dialogs/asesoria-presente'
import type { Interactable } from '../state'
import {
  boxMesh,
  disposeDeep,
  label,
  makeCanvasTexture,
  mergedBoxes,
  outlinedMergedBoxes,
  outlineGroup,
  toonMat,
} from '../toon'
import type { RoomBuild, RoomCtx } from '../world'
import {
  desk,
  footprint,
  infoKit,
  monitor,
  npcCoworkers,
  type OfficeLayout,
  officeLayout,
  type PropHandle,
  type ScreenSwap,
  type ShowcaseDemo,
  screenVariants,
  softwareShowcase,
  switchableMonitor,
  wallArt,
} from './props'

const TURNO_LABEL = {
  es: 'Tomar un turno',
  en: 'Take a ticket',
} as const

const DESPACHO_LABEL = {
  es: 'Despachar un medicamento',
  en: 'Dispatch a medicine',
} as const

const ENSAYO_LABEL = {
  es: 'Ensayar la defensa',
  en: 'Rehearse the defence',
} as const

const SOBRE_LABEL = {
  es: 'Mirar el sobre de pago',
  en: 'Look at the payment envelope',
} as const

const LAPTOP_LABELS = {
  on: { es: 'Encender la laptop libre', en: 'Power on the spare laptop' },
  off: { es: 'Apagar la laptop libre', en: 'Power off the spare laptop' },
} as const

/** Pantallas era-2015 (web local PHP + MySQL) de las laptops, por puesto. */
const LAPTOP_SCREENS = [
  {
    title: 'citas.php — PHP 5',
    lines: [
      '<?php require "conexion.php";',
      '$sql = "SELECT * FROM turnos',
      '  WHERE fecha = CURDATE()";',
      '$r = mysqli_query($cn, $sql);',
    ],
  },
  {
    title: 'farmacia.php — inventario',
    lines: [
      'if ($stock <= $minimo) {',
      '  echo "<tr class=rojo>";',
      '}  // la alerta de Coromoto',
      'mysqli_commit($cn);',
    ],
  },
  {
    title: 'checklist_defensa.txt',
    lines: [
      'lamina titulo....... OK',
      'lamina problema..... OK',
      'demo en vivo........ OK',
      'ensayo general: HOY',
    ],
  },
] as const

/** Ficha del sobre de pago: el primer trabajo cobrado como consultor. */
const SOBRE_STORY: Record<Locale, { title: string; paragraphs: string[] }> = {
  es: {
    title: 'El primer trabajo cobrado',
    paragraphs: [
      'Este sobre es el guiño mas importante de la sala: en noviembre ' +
        'de 2015, a Pablo le PAGARON por primera vez como consultor ' +
        'independiente — por desarrollar la solucion de PROSALUD y por ' +
        'capacitar al equipo de tesis para defenderla.',
      'No fue solo programar: fue diagnosticar un proyecto heredado, ' +
        'proponer un plan de una semana, cumplirlo en solitario e ' +
        'implantar el sistema en la red del instituto. Alcance, entrega ' +
        'y cobro: la primera consultoria completa.',
      'Aqui nace el hilo del Pablo freelance y lider que reaparece en ' +
        'el resto del recorrido: quien cobra por resolver, aprende a ' +
        'responder por lo que entrega.',
    ],
  },
  en: {
    title: 'The first paid job',
    paragraphs: [
      'This envelope is the room’s most important nod: in November ' +
        '2015 Pablo got PAID for the first time as an independent ' +
        'consultant — for building the PROSALUD solution and for ' +
        'coaching the thesis team to defend it.',
      'It was not just coding: it was diagnosing an inherited project, ' +
        'proposing a one-week plan, delivering it single-handedly and ' +
        'deploying the system on the institute network. Scope, delivery ' +
        'and payment: the first complete consulting job.',
      'The freelance-and-leader thread that reappears across the rest ' +
        'of the journey starts here: whoever charges to solve, learns ' +
        'to answer for what they deliver.',
    ],
  },
}

// --- laminas de los cuadros (wallArt): tinta plana sobre papel claro ---

const ART_PAPER = '#f2f4ee'
const ART_INK = '#1a2820'
const ART_GREEN = '#2e8b57'
const ART_PURPLE = '#7a4fc0'
const ART_RED = '#c0392b'

function artBase(ctx: CanvasRenderingContext2D, size: number): void {
  ctx.fillStyle = ART_PAPER
  ctx.fillRect(0, 0, size, size)
  ctx.strokeStyle = ART_INK
  ctx.globalAlpha = 0.35
  ctx.lineWidth = 3
  ctx.strokeRect(10, 10, size - 20, size - 20)
  ctx.globalAlpha = 1
}

/** Cartel institucional PROSALUD: cruz + silueta de comunidad. */
function drawCartelProsalud(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_GREEN
  ctx.font = 'bold 20px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('PROSALUD', 24, 42)
  ctx.fillStyle = ART_INK
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('Instituto Autonomo de la Salud', 24, 60)
  ctx.fillText('del Estado Yaracuy', 24, 74)
  // cruz de salud
  ctx.fillStyle = ART_GREEN
  ctx.fillRect(112, 96, 32, 88)
  ctx.fillRect(84, 124, 88, 32)
  // silueta de comunidad al pie: cabezas + hombros
  ctx.strokeStyle = ART_INK
  ctx.lineWidth = 3
  ctx.lineCap = 'round'
  for (const [x, r] of [
    [52, 11],
    [88, 13],
    [128, 15],
    [168, 13],
    [204, 11],
  ] as const) {
    ctx.beginPath()
    ctx.arc(x, 202, r, 0, Math.PI * 2)
    ctx.stroke()
    ctx.beginPath()
    ctx.moveTo(x - r - 5, 232)
    ctx.quadraticCurveTo(x, 210 + r / 2, x + r + 5, 232)
    ctx.stroke()
  }
  ctx.fillStyle = ART_INK
  ctx.globalAlpha = 0.6
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('14 municipios · San Felipe', 24, 246)
  ctx.globalAlpha = 1
}

/** El plan de rescate: cronograma de 7 dias con checkmarks. */
function drawPlanRescate(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 16px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('PLAN DE RESCATE · 7 DIAS', 22, 38)
  const steps = [
    'D1  diagnostico',
    'D2  arquitectura',
    'D3-5  desarrollo',
    'D6  implantacion',
    'D7  ensayo defensa',
  ] as const
  ctx.font = 'bold 12px "Space Mono", ui-monospace, monospace'
  steps.forEach((step, index) => {
    const y = 62 + index * 34
    ctx.strokeStyle = ART_INK
    ctx.lineWidth = 2
    ctx.strokeRect(24, y, 168, 24)
    ctx.fillStyle = ART_INK
    ctx.fillText(step, 32, y + 16)
    // checkmark verde al margen
    ctx.strokeStyle = ART_GREEN
    ctx.lineWidth = 4
    ctx.beginPath()
    ctx.moveTo(206, y + 14)
    ctx.lineTo(214, y + 21)
    ctx.lineTo(228, y + 4)
    ctx.stroke()
  })
  ctx.fillStyle = ART_PURPLE
  ctx.font = 'bold 12px "Space Mono", ui-monospace, monospace'
  ctx.fillText('meses varados -> 1 semana', 24, 244)
}

/** Diagrama del sistema: navegador -> XAMPP/PHP -> MySQL en red local. */
function drawDiagramaSistema(
  ctx: CanvasRenderingContext2D,
  size: number,
): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 16px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('ARQUITECTURA WEB LOCAL', 22, 38)
  const boxes = [
    ['NAVEGADOR', 'cada PC del instituto'],
    ['XAMPP · PHP', 'servidor local'],
    ['MySQL', 'una sola base'],
  ] as const
  boxes.forEach(([title, sub], index) => {
    const y = 60 + index * 60
    ctx.strokeStyle = index === 1 ? ART_GREEN : ART_INK
    ctx.lineWidth = index === 1 ? 3 : 2
    ctx.strokeRect(52, y, 152, 38)
    ctx.fillStyle = index === 1 ? ART_GREEN : ART_INK
    ctx.font = 'bold 13px "Space Mono", ui-monospace, monospace'
    ctx.fillText(title, 62, y + 17)
    ctx.globalAlpha = 0.65
    ctx.font = '10px "Space Mono", ui-monospace, monospace'
    ctx.fillText(sub, 62, y + 31)
    ctx.globalAlpha = 1
    if (index < boxes.length - 1) {
      ctx.strokeStyle = ART_INK
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.moveTo(128, y + 38)
      ctx.lineTo(128, y + 60)
      ctx.moveTo(123, y + 55)
      ctx.lineTo(128, y + 60)
      ctx.lineTo(133, y + 55)
      ctx.stroke()
    }
  })
  ctx.fillStyle = ART_INK
  ctx.globalAlpha = 0.6
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('sin instalar nada en los puestos', 24, 244)
  ctx.globalAlpha = 1
}

/** Afiche de la defensa: birrete + fecha (ata el hilo academico). */
function drawAficheDefensa(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_PURPLE
  ctx.font = 'bold 15px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('DEFENSA DE PROYECTO', 30, 40)
  ctx.fillText('DE GRADO', 30, 60)
  // birrete: base + tapa romboide + borla
  ctx.strokeStyle = ART_INK
  ctx.lineWidth = 3
  ctx.beginPath()
  ctx.moveTo(78, 128)
  ctx.lineTo(128, 104)
  ctx.lineTo(178, 128)
  ctx.lineTo(128, 152)
  ctx.closePath()
  ctx.stroke()
  ctx.strokeRect(106, 142, 44, 26)
  ctx.beginPath()
  ctx.moveTo(178, 128)
  ctx.lineTo(184, 168)
  ctx.stroke()
  ctx.fillStyle = ART_PURPLE
  ctx.beginPath()
  ctx.arc(184, 174, 6, 0, Math.PI * 2)
  ctx.fill()
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 14px "Space Mono", ui-monospace, monospace'
  ctx.fillText('15 DIC 2015', 88, 206)
  ctx.globalAlpha = 0.6
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('sistema web para PROSALUD', 30, 240)
  ctx.globalAlpha = 1
}

/** Cartelera de campañas de salud: vacunacion + dengue (decorativa). */
function drawCartelera(ctx: CanvasRenderingContext2D, size: number): void {
  // corcho
  ctx.fillStyle = '#c8a878'
  ctx.fillRect(0, 0, size, size)
  ctx.strokeStyle = '#8a6a48'
  ctx.lineWidth = 8
  ctx.strokeRect(4, 4, size - 8, size - 8)
  // afiche 1: vacunacion (jeringa)
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(22, 26, 100, 130)
  ctx.fillStyle = ART_GREEN
  ctx.font = 'bold 12px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('VACUNATE', 32, 46)
  ctx.strokeStyle = ART_INK
  ctx.lineWidth = 3
  ctx.strokeRect(48, 62, 14, 52)
  ctx.beginPath()
  ctx.moveTo(55, 114)
  ctx.lineTo(55, 134)
  ctx.stroke()
  ctx.fillStyle = ART_INK
  ctx.font = '9px "Space Mono", ui-monospace, monospace'
  ctx.fillText('jornada', 34, 148)
  // afiche 2: dengue (gota tachada)
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(134, 26, 100, 130)
  ctx.fillStyle = ART_RED
  ctx.font = 'bold 12px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('SIN DENGUE', 142, 46)
  ctx.strokeStyle = ART_INK
  ctx.lineWidth = 3
  ctx.beginPath()
  ctx.arc(184, 96, 22, 0, Math.PI * 2)
  ctx.moveTo(184, 58)
  ctx.quadraticCurveTo(196, 78, 184, 74)
  ctx.stroke()
  ctx.strokeStyle = ART_RED
  ctx.beginPath()
  ctx.moveTo(166, 114)
  ctx.lineTo(202, 78)
  ctx.stroke()
  ctx.fillStyle = ART_INK
  ctx.font = '9px "Space Mono", ui-monospace, monospace'
  ctx.fillText('sin agua quieta', 140, 148)
  // pie comun
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(22, 172, 212, 60)
  ctx.fillStyle = ART_GREEN
  ctx.font = 'bold 11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('PROSALUD · red de atencion', 34, 196)
  ctx.fillText('primaria del estado Yaracuy', 34, 212)
}

const ART_FICHA_PROSALUD = {
  title: {
    es: 'PROSALUD: la salud de todo un estado',
    en: 'PROSALUD: a whole state’s healthcare',
  },
  paragraphs: {
    es: [
      'PROSALUD es el Instituto Autonomo de la Salud del Estado ' +
        'Yaracuy, con sede en San Felipe: el ente rector de la red de ' +
        'atencion primaria del estado — ambulatorios y programas de ' +
        'salud para unos 610 mil habitantes en 14 municipios.',
      'En 2015 su dia a dia administrativo vivia en papel: papelitos ' +
        'de turno numerados a mano, un cuaderno de farmacia con ' +
        'tachones y un archivador de afiliados en carpetas manila. Un ' +
        'instituto que coordina la salud de un estado no podia seguir ' +
        'dependiendo de un pincho de papelitos.',
      'El sistema web local que Pablo desarrollo e implanto — citas y ' +
        'turnos, farmacia e inventario, admision y afiliados — corre ' +
        'desde la red del propio instituto: cada PC entra por el ' +
        'navegador, sin instalar nada.',
    ],
    en: [
      'PROSALUD is the Autonomous Health Institute of Yaracuy State, ' +
        'based in San Felipe: the governing body of the state’s ' +
        'primary-care network — outpatient centres and health ' +
        'programmes for some 610 thousand people across 14 municipios.',
      'In 2015 its administrative day-to-day lived on paper: ' +
        'hand-numbered queue slips, a pharmacy notebook full of ' +
        'scribbles and a member archive in manila folders. An institute ' +
        'coordinating a whole state’s healthcare could not keep ' +
        'depending on a spike of paper slips.',
      'The local web system Pablo built and deployed — appointments ' +
        'and queues, pharmacy and inventory, admissions and members — ' +
        'runs from the institute’s own network: every PC reaches it ' +
        'through the browser, nothing installed.',
    ],
  },
} as const

const ART_FICHA_PLAN = {
  title: {
    es: 'De meses varados a una semana',
    en: 'From stalled months to one week',
  },
  paragraphs: {
    es: [
      'La tesis que sostenia este sistema llevaba MESES bloqueada: ' +
        'codigo heredado que nadie entendia, tres planes tachados y la ' +
        'fecha de defensa rodeada en rojo. En noviembre de 2015 ' +
        'contrataron a Pablo para rescatarla.',
      'El diagnostico tomo una tarde: leer todo lo heredado y listar ' +
        'los puntos exactos de falla. De ahi salio este cronograma de ' +
        'siete dias — diagnostico, arquitectura, desarrollo en ' +
        'solitario, implantacion en el instituto y ensayo de la ' +
        'defensa — que se cumplio dia por dia.',
      'La leccion que Pablo repite desde entonces: un diagnostico ' +
        'preciso mas un plan claro convierten meses de bloqueo en dias ' +
        'de trabajo. Este cuadro colgaba antes en el aula; hoy vive ' +
        'donde ocurrio la historia.',
    ],
    en: [
      'The thesis behind this system had been stuck for MONTHS: ' +
        'inherited code nobody understood, three crossed-out plans and ' +
        'the defence date circled in red. In November 2015 Pablo was ' +
        'hired to rescue it.',
      'The diagnosis took one afternoon: reading everything inherited ' +
        'and listing the exact failure points. Out of it came this ' +
        'seven-day timeline — diagnosis, architecture, solo ' +
        'development, deployment at the institute and defence ' +
        'rehearsal — met day by day.',
      'The lesson Pablo has repeated ever since: a precise diagnosis ' +
        'plus a clear plan turn months of blockage into days of work. ' +
        'This chart used to hang in the classroom; now it lives where ' +
        'the story happened.',
    ],
  },
} as const

// --- demos del showcase: navegador 2015 + UI Bootstrap 2-3 verde ---

const WEB_BG = '#f7f7f5'
const WEB_INK = '#1c2a22'
const WEB_GREEN = '#2e8b57'
const WEB_STRIPE = '#e8f0ea'
const WEB_RED = '#c0392b'

/** Chrome de navegador 2015: pestaña + barra de direcciones + navbar. */
function browserChrome(
  ctx: CanvasRenderingContext2D,
  size: number,
  page: string,
): void {
  ctx.fillStyle = WEB_BG
  ctx.fillRect(0, 0, size, size)
  // barra de pestañas
  ctx.fillStyle = '#d8d8d2'
  ctx.fillRect(0, 0, size, 18)
  ctx.fillStyle = '#f0f0ea'
  ctx.fillRect(6, 3, 108, 15)
  ctx.fillStyle = WEB_INK
  ctx.font = '9px Tahoma, "Space Grotesk", sans-serif'
  ctx.textAlign = 'left'
  ctx.textBaseline = 'alphabetic'
  ctx.fillText('PROSALUD - Sistema', 12, 14)
  // barra de direcciones
  ctx.fillStyle = '#eceee8'
  ctx.fillRect(0, 18, size, 20)
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(28, 21, size - 40, 14)
  ctx.strokeStyle = '#b8b8b0'
  ctx.lineWidth = 1
  ctx.strokeRect(28, 21, size - 40, 14)
  ctx.fillStyle = WEB_INK
  ctx.font = '9px "Space Mono", ui-monospace, monospace'
  ctx.fillText(`http://192.168.1.10/prosalud/${page}`, 33, 31)
  // navbar verde Bootstrap-2015
  ctx.fillStyle = WEB_GREEN
  ctx.fillRect(0, 38, size, 22)
  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 11px Tahoma, "Space Grotesk", sans-serif'
  ctx.fillText('PROSALUD', 8, 53)
  ctx.font = '9px Tahoma, "Space Grotesk", sans-serif'
  ctx.fillText('Turnos   Farmacia   Afiliados', 84, 53)
}

/** Boton 2015 con degradado suave (look Bootstrap 2). */
function webButton(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  text: string,
): void {
  const grad = ctx.createLinearGradient(0, y, 0, y + 18)
  grad.addColorStop(0, '#3aa66a')
  grad.addColorStop(1, WEB_GREEN)
  ctx.fillStyle = grad
  ctx.fillRect(x, y, w, 18)
  ctx.strokeStyle = '#1f6b42'
  ctx.lineWidth = 1
  ctx.strokeRect(x, y, w, 18)
  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 10px Tahoma, "Space Grotesk", sans-serif'
  ctx.fillText(text, x + 8, y + 13)
}

/** Demo 1: turnos — la cola del dia con el numero subiendo. */
function drawDemoTurnos(
  ctx: CanvasRenderingContext2D,
  size: number,
  t: number,
): void {
  browserChrome(ctx, size, 'turnos.php')
  const turno = 42 + (Math.floor(t * 0.5) % 3)
  ctx.fillStyle = WEB_GREEN
  ctx.font = 'bold 22px "Space Mono", ui-monospace, monospace'
  ctx.fillText(`TURNO 0${turno}`, 12, 88)
  ctx.fillStyle = WEB_INK
  ctx.font = '10px Tahoma, "Space Grotesk", sans-serif'
  ctx.fillText('atendiendo · vent. 2', 148, 84)
  const rows = [
    ['043', 'M. Peroza', 'citas'],
    ['044', 'J. Sivira', 'farmacia'],
    ['045', 'C. Oropeza', 'admision'],
    ['046', 'R. Camacaro', 'citas'],
  ] as const
  rows.forEach((row, index) => {
    const y = 100 + index * 22
    if (index % 2 === 0) {
      ctx.fillStyle = WEB_STRIPE
      ctx.fillRect(10, y, size - 20, 20)
    }
    ctx.fillStyle = WEB_INK
    ctx.font = '10px "Space Mono", ui-monospace, monospace'
    ctx.fillText(row[0], 16, y + 14)
    ctx.fillText(row[1], 52, y + 14)
    ctx.fillText(row[2], 150, y + 14)
    ctx.fillStyle = WEB_GREEN
    ctx.fillText('en cola', 202, y + 14)
  })
  webButton(ctx, 10, 194, 96, 'Asignar turno')
}

/** Demo 2: farmacia — stock con la fila roja del minimo. */
function drawDemoFarmacia(
  ctx: CanvasRenderingContext2D,
  size: number,
  t: number,
): void {
  browserChrome(ctx, size, 'farmacia.php')
  ctx.fillStyle = WEB_INK
  ctx.font = 'bold 12px Tahoma, "Space Grotesk", sans-serif'
  ctx.fillText('Inventario de insumos', 10, 78)
  const blink = Math.floor(t * 2) % 2 === 0
  const rows = [
    ['ibuprofeno 400', '86', false],
    ['amoxicilina 500', '54', false],
    ['acetaminofen 650', '12', true],
    ['sales rehidratacion', '61', false],
  ] as const
  rows.forEach(([nombre, stock, low], index) => {
    const y = 88 + index * 22
    if (low) {
      ctx.fillStyle = blink ? '#f6d5d0' : '#f0c4bd'
      ctx.fillRect(10, y, size - 20, 20)
    } else if (index % 2 === 0) {
      ctx.fillStyle = WEB_STRIPE
      ctx.fillRect(10, y, size - 20, 20)
    }
    ctx.fillStyle = low ? WEB_RED : WEB_INK
    ctx.font = '10px "Space Mono", ui-monospace, monospace'
    ctx.fillText(nombre, 16, y + 14)
    ctx.fillText(stock, 176, y + 14)
    ctx.fillText(low ? 'MINIMO' : 'ok', 204, y + 14)
  })
  ctx.fillStyle = WEB_RED
  ctx.font = 'bold 10px "Space Mono", ui-monospace, monospace'
  ctx.fillText('alerta: pedir acetaminofen', 10, 188)
  webButton(ctx, 10, 196, 84, 'Despachar')
}

/** Demo 3: afiliados — buscador por cedula con tipeo animado. */
function drawDemoAfiliados(
  ctx: CanvasRenderingContext2D,
  size: number,
  t: number,
): void {
  browserChrome(ctx, size, 'afiliados.php')
  const query = 'V-12.884.301'
  const typed = query.slice(
    0,
    Math.min(query.length, Math.floor((t * 2.4) % (query.length + 4))),
  )
  ctx.fillStyle = WEB_INK
  ctx.font = '10px Tahoma, "Space Grotesk", sans-serif'
  ctx.fillText('Cedula del afiliado:', 10, 80)
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(10, 86, 130, 18)
  ctx.strokeStyle = '#b8b8b0'
  ctx.lineWidth = 1
  ctx.strokeRect(10, 86, 130, 18)
  const caret = Math.floor(t * 3) % 2 === 0 ? '_' : ' '
  ctx.fillStyle = WEB_INK
  ctx.font = '10px "Space Mono", ui-monospace, monospace'
  ctx.fillText(`${typed}${caret}`, 15, 99)
  webButton(ctx, 148, 86, 60, 'Buscar')
  // ficha del afiliado
  ctx.strokeStyle = '#b8c8bc'
  ctx.strokeRect(10, 114, size - 20, 78)
  ctx.fillStyle = WEB_GREEN
  ctx.font = 'bold 11px Tahoma, "Space Grotesk", sans-serif'
  ctx.fillText('Nairelys Peroza · 34', 18, 132)
  ctx.fillStyle = WEB_INK
  ctx.font = '10px "Space Mono", ui-monospace, monospace'
  ctx.fillText('municipio: Independencia', 18, 150)
  ctx.fillText('cita: 10:30 · medicina gral', 18, 166)
  ctx.fillText('carnet: vigente', 18, 182)
  webButton(ctx, 10, 200, 108, 'Imprimir carnet')
}

/** Los 3 mockups HTML del panel operable (look navegador 2015). */
function showcaseDemos(): ShowcaseDemo[] {
  const chrome = (page: string): string =>
    '<div style="background:#d8d8d2;color:#1c2a22;padding:.3rem .6rem;' +
    'font-size:.75rem;border-bottom:1px solid #b8b8b0">' +
    `http://192.168.1.10/prosalud/${page} · ` +
    '<strong>RED LOCAL · XAMPP</strong></div>' +
    '<div style="background:#2e8b57;color:#fff;padding:.35rem .6rem;' +
    'font-weight:700">PROSALUD <span style="font-weight:400;opacity:.85;' +
    'margin-left:.6rem">Turnos · Farmacia · Afiliados</span></div>'
  const gridTable = (
    head: readonly string[],
    rows: readonly (readonly string[])[],
  ): string =>
    '<table><thead><tr>' +
    head.map((cell) => `<th>${cell}</th>`).join('') +
    '</tr></thead><tbody>' +
    rows
      .map(
        (row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join('')}</tr>`,
      )
      .join('') +
    '</tbody></table>'
  return [
    {
      key: 'turnos',
      title: {
        es: 'Turnos y citas',
        en: 'Queue and appointments',
      },
      draw: drawDemoTurnos,
      panel: {
        brand: '#2e8b57',
        html: {
          es:
            chrome('turnos.php') +
            '<p style="margin:.6rem 0 .3rem"><strong>TURNO 042</strong> — ' +
            'atendiendo ahora · ventanilla 2</p>' +
            gridTable(
              ['Turno', 'Afiliado', 'Servicio', 'Estado'],
              [
                ['043', 'M. Peroza', 'Citas', 'en cola'],
                ['044', 'J. Sivira', 'Farmacia', 'en cola'],
                ['045', 'C. Oropeza', 'Admision', 'en cola'],
              ],
            ) +
            '<p style="opacity:.7;margin:.5rem 0 0">El sistema asigna el ' +
            'numero y el display lo canta: se acabaron los papelitos a ' +
            'mano y las peleas de la cola (2015, web local PHP + MySQL)</p>',
          en:
            chrome('turnos.php') +
            '<p style="margin:.6rem 0 .3rem"><strong>TICKET 042</strong> — ' +
            'now serving · window 2</p>' +
            gridTable(
              ['Ticket', 'Member', 'Service', 'Status'],
              [
                ['043', 'M. Peroza', 'Appointments', 'queued'],
                ['044', 'J. Sivira', 'Pharmacy', 'queued'],
                ['045', 'C. Oropeza', 'Admissions', 'queued'],
              ],
            ) +
            '<p style="opacity:.7;margin:.5rem 0 0">The system assigns ' +
            'the number and the display calls it: no more hand-numbered ' +
            'slips or queue fights (2015, local web app PHP + MySQL)</p>',
        },
      },
    },
    {
      key: 'farmacia',
      title: {
        es: 'Farmacia e inventario',
        en: 'Pharmacy and inventory',
      },
      draw: drawDemoFarmacia,
      panel: {
        brand: '#2e8b57',
        html: {
          es:
            chrome('farmacia.php') +
            gridTable(
              ['Insumo', 'Stock', 'Minimo', 'Estado'],
              [
                ['Ibuprofeno 400', '86', '20', 'ok'],
                ['Amoxicilina 500', '54', '15', 'ok'],
                ['<strong>Acetaminofen 650</strong>', '12', '15', 'MINIMO'],
              ],
            ) +
            '<p style="margin:.6rem 0 .2rem"><strong>La alerta de ' +
            'Coromoto</strong>: cada insumo tiene su minimo y la fila se ' +
            'pone roja ANTES de que falte en la ventanilla.</p>' +
            '<p style="opacity:.7;margin:0">Entradas, salidas y despacho ' +
            'descuentan stock al instante — el cuaderno con tachones se ' +
            'jubilo</p>',
          en:
            chrome('farmacia.php') +
            gridTable(
              ['Item', 'Stock', 'Minimum', 'Status'],
              [
                ['Ibuprofen 400', '86', '20', 'ok'],
                ['Amoxicillin 500', '54', '15', 'ok'],
                ['<strong>Paracetamol 650</strong>', '12', '15', 'MINIMUM'],
              ],
            ) +
            '<p style="margin:.6rem 0 .2rem"><strong>Coromoto’s ' +
            'alert</strong>: every item has a minimum and the row turns ' +
            'red BEFORE it runs out at the window.</p>' +
            '<p style="opacity:.7;margin:0">Stock in, stock out and ' +
            'dispatch update inventory instantly — the scribbled ' +
            'notebook retired</p>',
        },
      },
    },
    {
      key: 'afiliados',
      title: {
        es: 'Admision y afiliados',
        en: 'Admissions and members',
      },
      draw: drawDemoAfiliados,
      panel: {
        brand: '#2e8b57',
        html: {
          es:
            chrome('afiliados.php') +
            '<input placeholder="Cedula del afiliado (ej. V-12.884.301)">' +
            '<div style="border:1px solid #b8c8bc;padding:.6rem;' +
            'margin-top:.6rem;background:#fff"><strong>Nairelys Peroza · ' +
            '34</strong><br>municipio Independencia · cita 10:30 · ' +
            'carnet vigente' +
            '<p style="margin:.45rem 0 0">Busqueda al instante — antes: ' +
            'hojear carpetas manila en el archivador</p></div>' +
            '<p style="opacity:.7;margin:.5rem 0 0">Ficha del afiliado + ' +
            'impresion de carnet, servido a toda la red del instituto ' +
            'desde una sola PC con XAMPP</p>',
          en:
            chrome('afiliados.php') +
            '<input placeholder="Member ID (e.g. V-12.884.301)">' +
            '<div style="border:1px solid #b8c8bc;padding:.6rem;' +
            'margin-top:.6rem;background:#fff"><strong>Nairelys Peroza · ' +
            '34</strong><br>Independencia municipio · appt 10:30 · ' +
            'valid card' +
            '<p style="margin:.45rem 0 0">Instant lookup — before: ' +
            'leafing through manila folders in the cabinet</p></div>' +
            '<p style="opacity:.7;margin:.5rem 0 0">Member file + card ' +
            'printing, served to the whole institute network from a ' +
            'single PC running XAMPP</p>',
        },
      },
    },
  ]
}

/** Vuelca props (grupo + interactable + update) a los arrays de la sala. */
function addProps(
  sink: {
    group: Group
    interactables: Interactable[]
    updates: ((t: number, dt: number) => void)[]
  },
  props: readonly PropHandle[],
): void {
  for (const prop of props) {
    sink.group.add(prop.group)
    if (prop.interactable) {
      sink.interactables.push(prop.interactable)
    }
    if (prop.update) {
      sink.updates.push(prop.update)
    }
  }
}

/** E enciende/apaga las laptops libres del officeLayout (patron canon). */
function laptopToggles(
  office: OfficeLayout,
  spots: readonly (readonly [number, number])[],
  roomIndex: number,
): Interactable[] {
  const items: Interactable[] = []
  for (const toggle of office.toggles) {
    const spot = spots[toggle.spot]
    if (!spot) {
      continue
    }
    let powered = false
    const item: Interactable = {
      id: `micro-asesoria-${roomIndex}-laptop${toggle.spot}`,
      x: spot[0],
      z: spot[1],
      radius: 1.8,
      label: { ...LAPTOP_LABELS.on },
      onActivate: () => {
        powered = !powered
        toggle.screen.show(powered ? 'on' : 'off')
        sfx.play(powered ? 'boot' : 'shutdown')
        item.label = powered ? LAPTOP_LABELS.off : LAPTOP_LABELS.on
      },
    }
    items.push(item)
  }
  return items
}

/** Micro del turno: el ticket vuela del mostrador a la sala de espera
 *  y el display sube de numero con su ding (maquina de estados). */
function turnoMicro(opts: {
  roomIndex: number
  ticket: Mesh
  from: readonly [number, number, number]
  to: readonly [number, number, number]
  display: ScreenSwap
}): { interactable: Interactable; update(t: number): void } {
  const { ticket, from, to, display } = opts
  let startT = -1
  let turnoIndex = 0
  return {
    interactable: {
      id: `micro-asesoria-turno-${opts.roomIndex}`,
      x: from[0],
      z: from[2] + 0.4,
      radius: 2.0,
      label: TURNO_LABEL,
      onActivate: () => {
        if (startT === -1) {
          startT = -2 // pendiente: el proximo update fija el inicio
          turnoIndex = (turnoIndex + 1) % 3
          sfx.play('ring')
        }
      },
    },
    update: (t: number) => {
      if (startT === -2) {
        startT = t
        ticket.visible = true
        display.show(`t${turnoIndex}`)
      }
      if (startT < 0) {
        return
      }
      const elapsed = t - startT
      if (elapsed < 1.3) {
        // el ticket vuela en arco del dispensador a la primera silla
        const k = elapsed / 1.3
        ticket.visible = true
        ticket.position.set(
          from[0] + (to[0] - from[0]) * k,
          from[1] + (to[1] - from[1]) * k + Math.sin(k * Math.PI) * 0.6,
          from[2] + (to[2] - from[2]) * k,
        )
        ticket.rotation.y = k * 5
      } else if (elapsed < 4.2) {
        ticket.position.set(to[0], to[1], to[2])
      } else {
        ticket.visible = false
        startT = -1
      }
    },
  }
}

/** Micro de farmacia: la caja vuela del estante a la mesa de despacho,
 *  el stock del monitor baja y el minimo alerta en rojo. */
function despachoMicro(opts: {
  roomIndex: number
  caja: Mesh
  from: readonly [number, number, number]
  to: readonly [number, number, number]
  stock: ScreenSwap
}): { interactable: Interactable; update(t: number): void } {
  const { caja, from, to, stock } = opts
  let startT = -1
  let level = 0
  return {
    interactable: {
      id: `micro-asesoria-despacho-${opts.roomIndex}`,
      x: to[0],
      z: to[2],
      radius: 2.0,
      label: DESPACHO_LABEL,
      onActivate: () => {
        if (startT === -1) {
          startT = -2
          level = (level + 1) % 3
          sfx.play('blip')
        }
      },
    },
    update: (t: number) => {
      if (startT === -2) {
        startT = t
        caja.visible = true
      }
      if (startT < 0) {
        return
      }
      const elapsed = t - startT
      if (elapsed < 1.2) {
        // la caja vuela en arco del estante a la mesa
        const k = elapsed / 1.2
        caja.visible = true
        caja.position.set(
          from[0] + (to[0] - from[0]) * k,
          from[1] + (to[1] - from[1]) * k + Math.sin(k * Math.PI) * 0.45,
          from[2] + (to[2] - from[2]) * k,
        )
        caja.rotation.y = k * 3
      } else if (elapsed < 4.6) {
        caja.position.set(to[0], to[1], to[2])
        stock.show(`s${level}`)
      } else {
        caja.visible = false
        if (level === 2) {
          // tras la alerta de minimo, "llega el pedido": stock repuesto
          level = 0
          stock.show('s0')
        }
        startT = -1
      }
    },
  }
}

/** Micro firma: ensayar la defensa — E cicla las laminas del proyector
 *  y al completar el ciclo los tesistas celebran con un salto. */
function ensayoMicro(opts: {
  roomIndex: number
  position: readonly [number, number]
  pantalla: ScreenSwap
  laminas: number
  celebrate: Mesh
  onPerfect(): void
}): { interactable: Interactable; update(t: number): void } {
  const { pantalla, celebrate } = opts
  let lamina = 0
  let cheerUntil = -1
  celebrate.visible = false
  return {
    interactable: {
      id: `micro-asesoria-ensayo-${opts.roomIndex}`,
      x: opts.position[0],
      z: opts.position[1],
      radius: 2.2,
      label: ENSAYO_LABEL,
      onActivate: () => {
        lamina = (lamina + 1) % opts.laminas
        pantalla.show(`l${lamina}`)
        if (lamina === 0) {
          // ciclo completo: el ensayo salio redondo
          cheerUntil = -2
          sfx.play('ring')
          opts.onPerfect()
        } else {
          sfx.play('blip')
        }
      },
    },
    update: (t: number) => {
      if (cheerUntil === -2) {
        cheerUntil = t + 3
        celebrate.visible = true
      }
      if (cheerUntil > 0 && t > cheerUntil) {
        cheerUntil = -1
        celebrate.visible = false
      }
    },
  }
}

export default function buildAsesoria(ctx: RoomCtx): RoomBuild {
  const { def, room, theme, state, actions } = ctx
  const group = new Group()
  const interactables: Interactable[] = []
  const updates: ((t: number, dt: number) => void)[] = []
  const npcs: NpcHandle[] = []
  const disposables: { dispose(): void }[] = []
  const staticColliders: Box2[] = []
  const half = room.width / 2
  const backZ = room.z - room.depth / 2
  const frontZ = room.z + room.depth / 2
  const locale: Locale = state.locale
  const screenTheme = {
    screenBg: theme.screenBg,
    screenFg: theme.screenFg,
    ink: theme.ink,
  }

  // RINCON DE ASESORIA (-X, fondo): la mesa de los tesistas — 3 puestos,
  // Jhonny y Oriana en codigo PHP, la tercera laptop libre con E
  const deskSpots: readonly (readonly [number, number])[] = [
    [-3.4, room.z - 3.2],
    [-1.6, room.z - 3.7],
    [-2.5, room.z - 2.3],
  ]
  const office = officeLayout({
    roomIndex: room.index,
    state,
    spots: deskSpots,
    color: '#4a3f5e',
    poweredSpots: new Set([0, 1]),
    screenTheme,
    screenFor: (index) => LAPTOP_SCREENS[index] ?? LAPTOP_SCREENS[0],
  })
  group.add(office.group)
  staticColliders.push(...office.colliders)
  disposables.push(office)
  interactables.push(...laptopToggles(office, deskSpots, room.index))

  // proyector + pantalla en el muro -X: las laminas de la defensa que
  // E cicla (micro firma de la sala)
  const laminaVariant = (
    title: string,
    lines: string[],
  ): { title: string; lines: string[]; theme: typeof screenTheme } => ({
    title,
    lines,
    theme: screenTheme,
  })
  const laminas =
    locale === 'es'
      ? [
          laminaVariant('1/5 · TITULO', [
            'Sistema web integral',
            'para PROSALUD',
            'citas · farmacia · afiliados',
            'tesistas: Parra / Castillo',
          ]),
          laminaVariant('2/5 · PROBLEMA', [
            'turnos: papelitos a mano',
            'farmacia: cuaderno tachado',
            'afiliados: carpetas manila',
            'la cola no baja nunca',
          ]),
          laminaVariant('3/5 · ARQUITECTURA', [
            'navegador -> PHP -> MySQL',
            'XAMPP en red local',
            'cero instalacion por PC',
            'roles por modulo',
          ]),
          laminaVariant('4/5 · DEMO', [
            'asignar turno: display sube',
            'stock toca minimo: alerta',
            'cedula -> afiliado al',
            'instante',
          ]),
          laminaVariant('5/5 · CONCLUSIONES', [
            'de meses varados a 1 semana',
            'implantado en el instituto',
            'equipo listo para defender',
            'gracias — ¿preguntas?',
          ]),
        ]
      : [
          laminaVariant('1/5 · TITLE', [
            'Integral web system',
            'for PROSALUD',
            'queues · pharmacy · members',
            'students: Parra / Castillo',
          ]),
          laminaVariant('2/5 · PROBLEM', [
            'queues: hand-made slips',
            'pharmacy: scribbled notebook',
            'members: manila folders',
            'the line never shrinks',
          ]),
          laminaVariant('3/5 · ARCHITECTURE', [
            'browser -> PHP -> MySQL',
            'XAMPP on the local network',
            'zero installs per PC',
            'roles per module',
          ]),
          laminaVariant('4/5 · DEMO', [
            'assign ticket: display up',
            'stock hits minimum: alert',
            'ID -> member instantly',
            '',
          ]),
          laminaVariant('5/5 · CONCLUSIONS', [
            'stalled months -> 1 week',
            'deployed at the institute',
            'team ready to defend',
            'thank you — questions?',
          ]),
        ]
  const pantalla = screenVariants({
    width: 1.5,
    height: 1.0,
    variants: Object.fromEntries(laminas.map((v, i) => [`l${i}`, v])),
    initial: 'l0',
  })
  pantalla.mesh.position.set(-half + 0.08, 1.75, room.z - 3.1)
  pantalla.mesh.rotation.y = Math.PI / 2
  group.add(pantalla.mesh)
  disposables.push(pantalla)
  // marco de la pantalla + proyector sobre su mesita (lote fusionado)
  group.add(
    outlinedMergedBoxes(
      [
        {
          w: 0.05,
          h: 1.14,
          d: 1.66,
          x: -half + 0.05,
          y: 1.75,
          z: room.z - 3.1,
        },
        // mesita del proyector
        { w: 0.5, h: 0.05, d: 0.5, x: -half + 1.6, y: 0.62, z: room.z - 3.1 },
        {
          w: 0.06,
          h: 0.62,
          d: 0.06,
          x: -half + 1.42,
          y: 0.31,
          z: room.z - 3.28,
        },
        {
          w: 0.06,
          h: 0.62,
          d: 0.06,
          x: -half + 1.78,
          y: 0.31,
          z: room.z - 2.92,
        },
        // proyector: cuerpo + lente hacia la pantalla
        {
          w: 0.34,
          h: 0.14,
          d: 0.24,
          x: -half + 1.6,
          y: 0.72,
          z: room.z - 3.1,
        },
        {
          w: 0.08,
          h: 0.08,
          d: 0.08,
          x: -half + 1.41,
          y: 0.72,
          z: room.z - 3.1,
        },
      ],
      toonMat('#3a3f4a'),
      { castShadow: true },
    ),
  )
  staticColliders.push(footprint(-half + 1.6, room.z - 3.1, 0.6, 0.6))
  // cartel de celebracion del ensayo perfecto (visible solo al completar)
  const cheer = label(
    locale === 'es' ? '¡ensayo redondo!' : 'flawless rehearsal!',
    { size: 0.16, color: theme.accent },
  )
  cheer.position.set(-half + 1.1, 2.6, room.z - 3.1)
  cheer.rotation.y = Math.PI / 2
  group.add(cheer)

  // sobre de pago sobre la mesa de asesoria: el guiño del primer trabajo
  // cobrado (decision del usuario: con ficha inspeccionable)
  group.add(
    mergedBoxes(
      [
        {
          w: 0.26,
          h: 0.015,
          d: 0.16,
          x: -2.05,
          y: 0.755,
          z: room.z - 2.35,
          rotY: 0.4,
        },
      ],
      toonMat('#d9c39a'),
    ),
  )
  const sobreStory = SOBRE_STORY[locale]
  interactables.push({
    id: `sobre-${room.index}`,
    x: -2.05,
    z: room.z - 2.35,
    radius: 1.6,
    label: SOBRE_LABEL,
    onActivate: () =>
      actions.openStory(sobreStory.title, sobreStory.paragraphs),
  })

  // TORRE XAMPP (fondo, centro): la PC del instituto donde vive el
  // sistema + router con cables — el "SERVIDOR LOCAL"
  group.add(
    outlinedMergedBoxes(
      [
        // torre + base
        { w: 0.3, h: 0.72, d: 0.5, x: 1.2, y: 0.36, z: backZ + 0.55 },
        // router encima con antena
        { w: 0.26, h: 0.06, d: 0.2, x: 1.2, y: 0.78, z: backZ + 0.55 },
        { w: 0.02, h: 0.18, d: 0.02, x: 1.3, y: 0.9, z: backZ + 0.5 },
        // canaleta de cables hacia el muro
        { w: 0.05, h: 0.03, d: 0.5, x: 1.2, y: 0.02, z: backZ + 0.3 },
        { w: 0.05, h: 1.1, d: 0.03, x: 1.2, y: 0.55, z: backZ + 0.06 },
      ],
      toonMat('#2e3238'),
      { castShadow: true },
    ),
  )
  staticColliders.push(footprint(1.2, backZ + 0.55, 0.6, 0.7))
  const serverLabel = label(
    locale === 'es' ? 'SERVIDOR LOCAL' : 'LOCAL SERVER',
    { size: 0.11, color: theme.accent },
  )
  serverLabel.position.set(1.2, 1.15, backZ + 0.6)
  group.add(serverLabel)

  // MOSTRADOR DE ADMISION (centro-derecha, frente): frente + tapa +
  // laterales + cruz de salud verde + carnet sobre el meson
  group.add(
    outlinedMergedBoxes(
      [
        { w: 2.6, h: 1.0, d: 0.08, x: 1.7, y: 0.5, z: room.z + 3.18 },
        { w: 2.6, h: 0.06, d: 0.7, x: 1.7, y: 1.02, z: room.z + 2.9 },
        { w: 0.08, h: 1.0, d: 0.62, x: 0.44, y: 0.5, z: room.z + 2.88 },
        { w: 0.08, h: 1.0, d: 0.62, x: 2.96, y: 0.5, z: room.z + 2.88 },
      ],
      toonMat('#e8ece6'),
      { castShadow: true },
    ),
    // cruz de salud verde sobre el mostrador
    mergedBoxes(
      [
        { w: 0.14, h: 0.5, d: 0.06, x: 2.5, y: 2.5, z: room.z + 3.16 },
        { w: 0.5, h: 0.14, d: 0.06, x: 2.5, y: 2.5, z: room.z + 3.16 },
      ],
      toonMat(theme.accent),
    ),
    // carnet de afiliado sobre el meson
    mergedBoxes(
      [
        {
          w: 0.2,
          h: 0.012,
          d: 0.13,
          x: 2.4,
          y: 1.06,
          z: room.z + 2.85,
          rotY: -0.3,
        },
      ],
      toonMat('#7ecab0'),
    ),
  )
  staticColliders.push(footprint(1.7, room.z + 2.95, 2.7, 0.9))
  const admisionLabel = label('PROSALUD', { size: 0.22, color: theme.accent })
  admisionLabel.position.set(1.7, 2.05, room.z + 3.16)
  admisionLabel.rotation.y = Math.PI
  group.add(admisionLabel)

  // monitor de afiliados sobre el mostrador (la pantalla de Maigualida)
  group.add(
    monitor({
      position: [2.3, 1.02, room.z + 2.85],
      rotationY: Math.PI,
      width: 0.56,
      title: locale === 'es' ? 'afiliados' : 'members',
      lines:
        locale === 'es'
          ? [
              '> cedula V-12884301',
              'Nairelys Peroza · 34',
              'municipio Independencia',
              'cita 10:30 · carnet ok',
            ]
          : [
              '> ID V-12884301',
              'Nairelys Peroza · 34',
              'Independencia municipio',
              'appt 10:30 · card ok',
            ],
      theme: screenTheme,
    }),
  )

  // display de turnos sobre el mostrador: mastil + pantalla que canta el
  // turno (micro "tomar un turno" — el eje papelitos -> display)
  group.add(
    outlinedMergedBoxes(
      [
        { w: 0.08, h: 0.62, d: 0.08, x: 0.9, y: 1.36, z: room.z + 2.9 },
        { w: 0.62, h: 0.4, d: 0.1, x: 0.9, y: 1.86, z: room.z + 2.9 },
      ],
      toonMat(theme.accent),
      { castShadow: true },
    ),
  )
  const turnoVariant = (
    turno: number,
  ): { title: string; lines: string[]; theme: typeof screenTheme } => ({
    title: locale === 'es' ? 'turno' : 'ticket',
    lines: [`> 0${turno} <`, locale === 'es' ? 'ventanilla 2' : 'window 2'],
    theme: screenTheme,
  })
  const turnoDisplay = screenVariants({
    width: 0.56,
    height: 0.34,
    variants: {
      t0: turnoVariant(42),
      t1: turnoVariant(43),
      t2: turnoVariant(44),
    },
    initial: 't0',
  })
  turnoDisplay.mesh.position.set(0.9, 1.86, room.z + 2.96)
  group.add(turnoDisplay.mesh)
  disposables.push(turnoDisplay)

  // SALA DE ESPERA (-X, frente): hilera de sillas mirando a admision +
  // dos afiliados de fondo (siluetas fusionadas, baratas)
  const chairXs = [-4.9, -4.1, -3.3, -2.5] as const
  group.add(
    outlinedMergedBoxes(
      chairXs.flatMap((x) => [
        { w: 0.5, h: 0.06, d: 0.45, x, y: 0.46, z: room.z + 3.6 },
        { w: 0.5, h: 0.45, d: 0.06, x, y: 0.74, z: room.z + 3.82 },
        { w: 0.05, h: 0.44, d: 0.05, x: x - 0.2, y: 0.22, z: room.z + 3.7 },
        { w: 0.05, h: 0.44, d: 0.05, x: x + 0.2, y: 0.22, z: room.z + 3.7 },
      ]),
      toonMat('#5a9c82'),
      { inflate: 0.03, castShadow: true },
    ),
    // siluetas sentadas: torso + cabeza en dos de las sillas
    outlinedMergedBoxes(
      [
        { w: 0.38, h: 0.52, d: 0.3, x: -4.1, y: 0.78, z: room.z + 3.66 },
        { w: 0.24, h: 0.24, d: 0.24, x: -4.1, y: 1.18, z: room.z + 3.66 },
        { w: 0.38, h: 0.52, d: 0.3, x: -2.5, y: 0.78, z: room.z + 3.66 },
        { w: 0.24, h: 0.24, d: 0.24, x: -2.5, y: 1.18, z: room.z + 3.66 },
      ],
      toonMat('#4a5a52'),
      { castShadow: true },
    ),
  )
  staticColliders.push(footprint(-3.7, room.z + 3.7, 3.0, 0.7))

  // el ticket del turno que vuela del mostrador a la primera silla
  const ticket = boxMesh(0.16, 0.012, 0.1, toonMat('#f7f5ea'))
  ticket.visible = false
  group.add(ticket)
  const turnoAction = turnoMicro({
    roomIndex: room.index,
    ticket,
    from: [0.9, 1.12, room.z + 3.0],
    to: [-2.5, 1.02, room.z + 3.5],
    display: turnoDisplay,
  })
  interactables.push(turnoAction.interactable)
  updates.push(turnoAction.update)

  // FARMACIA (+X, fondo): estanteria con cajas + mesa de despacho con el
  // monitor de inventario (la alerta de minimos de Coromoto)
  const shelfX = half - 0.55
  group.add(
    outlinedMergedBoxes(
      [
        { w: 0.5, h: 0.04, d: 1.9, x: shelfX, y: 0.55, z: room.z - 4.2 },
        { w: 0.5, h: 0.04, d: 1.9, x: shelfX, y: 1.05, z: room.z - 4.2 },
        { w: 0.5, h: 0.04, d: 1.9, x: shelfX, y: 1.55, z: room.z - 4.2 },
        { w: 0.5, h: 1.66, d: 0.05, x: shelfX, y: 0.83, z: room.z - 5.17 },
        { w: 0.5, h: 1.66, d: 0.05, x: shelfX, y: 0.83, z: room.z - 3.23 },
      ],
      toonMat('#c8ccd2'),
      { castShadow: true },
    ),
    // cajas de medicamentos en verde salud
    outlinedMergedBoxes(
      [
        { w: 0.2, h: 0.12, d: 0.3, x: shelfX, y: 0.63, z: room.z - 4.8 },
        { w: 0.16, h: 0.1, d: 0.24, x: shelfX, y: 0.62, z: room.z - 4.3 },
        { w: 0.22, h: 0.14, d: 0.26, x: shelfX, y: 1.14, z: room.z - 4.6 },
        { w: 0.14, h: 0.1, d: 0.2, x: shelfX, y: 1.12, z: room.z - 3.9 },
        { w: 0.18, h: 0.12, d: 0.24, x: shelfX, y: 1.63, z: room.z - 4.9 },
        { w: 0.16, h: 0.1, d: 0.22, x: shelfX, y: 1.62, z: room.z - 4.15 },
        { w: 0.2, h: 0.1, d: 0.2, x: shelfX, y: 1.62, z: room.z - 3.5 },
      ],
      toonMat('#4a9c78'),
      { castShadow: true },
    ),
  )
  staticColliders.push(footprint(shelfX, room.z - 4.2, 0.7, 2.1))
  const farmaciaLabel = label(locale === 'es' ? 'FARMACIA' : 'PHARMACY', {
    size: 0.16,
    color: theme.trim ?? theme.accent,
  })
  farmaciaLabel.position.set(shelfX - 0.1, 1.95, room.z - 4.2)
  farmaciaLabel.rotation.y = -Math.PI / 2
  group.add(farmaciaLabel)

  // mesa de despacho con el monitor de inventario
  group.add(
    desk({
      position: [half - 1.5, 0, room.z - 2.7],
      rotationY: Math.PI / 2,
      width: 1.2,
      color: '#4a5a52',
    }),
  )
  staticColliders.push(footprint(half - 1.5, room.z - 2.7, 0.8, 1.3))
  const stockVariant = (
    nivel: number,
    alerta: boolean,
  ): {
    title: string
    lines: string[]
    theme: typeof screenTheme
    dot: string
  } => {
    let lines: string[]
    if (alerta) {
      lines =
        locale === 'es'
          ? [
              'ibuprofeno 400:  86',
              `acetaminofen: ${nivel} !!`,
              '>> MINIMO ALCANZADO <<',
              'pedir reposicion YA',
            ]
          : [
              'ibuprofen 400:   86',
              `paracetamol: ${nivel} !!`,
              '>> MINIMUM REACHED <<',
              'reorder NOW',
            ]
    } else {
      lines =
        locale === 'es'
          ? [
              'ibuprofeno 400:  86',
              `acetaminofen:  ${nivel}`,
              'amoxicilina:     54',
              'todo sobre minimo',
            ]
          : [
              'ibuprofen 400:   86',
              `paracetamol:   ${nivel}`,
              'amoxicillin:     54',
              'all above minimum',
            ]
    }
    return {
      title: locale === 'es' ? 'inventario' : 'inventory',
      lines,
      theme: screenTheme,
      dot: alerta ? '#b23a3a' : '#3f9d63',
    }
  }
  const stockMonitor = switchableMonitor({
    position: [half - 1.5, 0.75, room.z - 2.7],
    rotationY: -Math.PI / 2,
    width: 0.52,
    variants: {
      s0: stockVariant(24, false),
      s1: stockVariant(18, false),
      s2: stockVariant(12, true),
    },
    initial: 's0',
  })
  group.add(stockMonitor.group)
  disposables.push(stockMonitor.screen)

  // la caja que vuela del estante a la mesa de despacho
  const caja = boxMesh(0.2, 0.12, 0.26, toonMat('#4a9c78'))
  caja.visible = false
  group.add(caja)
  const despacho = despachoMicro({
    roomIndex: room.index,
    caja,
    from: [shelfX, 1.2, room.z - 4.6],
    to: [half - 1.5, 0.84, room.z - 3.1],
    stock: stockMonitor.screen,
  })
  interactables.push(despacho.interactable)
  updates.push(despacho.update)

  // cartelera de campañas de salud en el muro -X, sobre la sala de espera
  const cartelera = new Mesh(
    new PlaneGeometry(1.3, 1.3),
    new MeshBasicMaterial({ map: makeCanvasTexture(256, drawCartelera) }),
  )
  cartelera.userData.noOutline = true
  cartelera.position.set(-half + 0.06, 1.9, room.z + 2.4)
  cartelera.rotation.y = Math.PI / 2
  group.add(cartelera)

  // cuadros de rubro (wallArt): cartel PROSALUD y plan de rescate
  // inspeccionables; diagrama del sistema y afiche de la defensa
  // decorativos flanqueando la puerta al pasillo
  const art = wallArt({
    roomIndex: room.index,
    theme,
    locale,
    onFicha: actions.openStory,
    frames: [
      {
        key: 'plan-rescate',
        position: [-2.5, 2, backZ + 0.08],
        rotationY: 0,
        draw: drawPlanRescate,
        ficha: ART_FICHA_PLAN,
      },
      {
        key: 'cartel-prosalud',
        position: [3.6, 2, backZ + 0.08],
        rotationY: 0,
        draw: drawCartelProsalud,
        ficha: ART_FICHA_PROSALUD,
      },
      {
        key: 'diagrama-sistema',
        position: [-3.6, 2, frontZ - 0.08],
        rotationY: Math.PI,
        draw: drawDiagramaSistema,
      },
      {
        key: 'afiche-defensa',
        position: [3.6, 2, frontZ - 0.08],
        rotationY: Math.PI,
        draw: drawAficheDefensa,
      },
    ],
  })
  staticColliders.push(...art.colliders)
  const sink = { group, interactables, updates }
  addProps(sink, art.props)

  // showcase del software junto a la puerta al pasillo (canon AC-6):
  // navegador 2015 sobre XAMPP — E cicla las 3 demos
  const showcase = softwareShowcase({
    roomIndex: room.index,
    position: [2.4, 0, frontZ - 0.9],
    rotationY: Math.PI,
    theme,
    locale,
    demos: showcaseDemos(),
    openShowcase: actions.openShowcase,
  })
  addProps(sink, [showcase])
  staticColliders.push(footprint(2.4, frontZ - 0.9, 0.9, 0.7))

  // kit informativo estandar (RETOS / APRENDIZAJES / grieta / cuaderno):
  // mismas posiciones que el aula (el canon de todas las salas)
  const texts = def.texts[locale]
  const kit = infoKit({
    room,
    year: def.year,
    theme,
    locale,
    texts,
    withLight: state.tier === 'full',
    onFicha: actions.openFicha,
    onEnterPast: actions.enterPast,
    onStory: actions.openStory,
  })
  staticColliders.push(...kit.colliders)
  addProps(sink, kit.props)

  // NPCs del canon (2 enfoques, informe 17): Jhonny y Oriana (tesistas,
  // sentados en el rincon de asesoria), Coromoto (farmacia), Maigualida
  // (detras del mostrador de admision) y la Dra. Xiomara (directora de
  // ronda entre el mostrador y el rincon).
  const coworkers = npcCoworkers({
    roomIndex: room.index,
    openDialog: actions.openDialog,
    npcs: [
      {
        key: 'jhonny',
        role: 'coworker',
        spec: {
          skin: '#c98f6a',
          hair: { style: 'short', color: '#14100c' },
          top: '#4a6a5a',
          bottom: '#3a4048',
          accessory: 'glasses',
          faceSeed: 41,
        },
        position: [-3.4, 0, room.z - 4.75],
        rotationY: 0,
        pose: 'sit',
        dialog: ASESORIA_PRESENTE_DIALOGS.jhonny,
      },
      {
        key: 'oriana',
        role: 'coworker',
        spec: {
          skin: '#e8b48c',
          hair: { style: 'ponytail', color: '#2a1a12' },
          top: '#7a5fc0',
          bottom: '#3a4048',
          accessory: 'badge',
          faceSeed: 67,
        },
        position: [-1.6, 0, room.z - 4.75],
        rotationY: 0,
        pose: 'sit',
        dialog: ASESORIA_PRESENTE_DIALOGS.oriana,
      },
      {
        key: 'coromoto',
        role: 'staff',
        spec: {
          skin: '#d9a684',
          hair: { style: 'bun', color: '#5a4a3a' },
          top: '#eef0ec',
          bottom: '#4a9c78',
          accessory: 'badge',
          faceSeed: 53,
        },
        position: [half - 1.9, 0, room.z - 4.0],
        rotationY: -1.2,
        dialog: ASESORIA_PRESENTE_DIALOGS.coromoto,
      },
      {
        key: 'maigualida',
        role: 'staff',
        spec: {
          skin: '#b5825f',
          hair: { style: 'bun', color: '#1c1410' },
          top: '#7ecab0',
          bottom: '#3a4048',
          accessory: 'badge',
          faceSeed: 34,
        },
        position: [1.9, 0, room.z + 2.35],
        rotationY: 0,
        dialog: ASESORIA_PRESENTE_DIALOGS.maigualida,
      },
      {
        key: 'xiomara',
        role: 'boss',
        spec: {
          skin: '#d9a684',
          hair: { style: 'bun', color: '#8a8a92' },
          top: '#f0eee8',
          bottom: '#2e3238',
          accessory: 'tie',
          faceSeed: 88,
        },
        position: [0.6, 0, room.z + 1.2],
        path: [
          [0.6, room.z + 1.2],
          [-2.0, room.z - 1.0],
          [2.2, room.z - 0.4],
        ],
        speed: 0.5,
        dialog: ASESORIA_PRESENTE_DIALOGS.xiomara,
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

  // micro firma: ensayar la defensa — cicla laminas y, al completar el
  // ciclo, Jhonny y Oriana saltan de celebracion
  const jhonnyNpc = coworkers.npcs[0]
  const orianaNpc = coworkers.npcs[1]
  const ensayo = ensayoMicro({
    roomIndex: room.index,
    position: [-half + 1.6, room.z - 3.1],
    pantalla,
    laminas: laminas.length,
    celebrate: cheer,
    onPerfect: () => {
      jhonnyNpc?.jump()
      orianaNpc?.jump()
    },
  })
  interactables.push(ensayo.interactable)
  updates.push(ensayo.update)

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
