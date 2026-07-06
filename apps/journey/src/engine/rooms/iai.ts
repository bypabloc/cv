/**
 * @module rooms/iai (engine)
 * @description Sala 3 — IAI (Instituto Autonomo de Infraestructura del
 *   Estado Yaracuy, VE, 2015), construida al CANON de sala (plan
 *   journey-salas-estandar, informe 16): `officeLayout` en el rincon del
 *   equipo de tesis (Keiber y Marielys sentados en sus laptops Java, 1
 *   libre togglable con E), 5 NPCs conversables con los 2 enfoques
 *   (`npcCoworkers`: Keiber y Marielys tesistas/dev, Ing. Gregorio
 *   inspector en ronda, Belkis analista de presupuestos, Ing. Maritza
 *   presidenta del instituto), cuadros de rubro (`wallArt`: valla
 *   institucional, diagrama de red cliente-servidor y lamina del APU
 *   inspeccionables; plano de via agricola decorativo) y el
 *   `softwareShowcase` junto a la puerta con 3 demos del sistema real
 *   (presupuesto COVENIN con recalculo, hoja de APU, valuaciones con
 *   curva S — estetica app de escritorio Java/Windows 2015 con badge RED
 *   LOCAL, NUNCA navegador). Props firma: meson de planos con rollos y
 *   plano desplegado, planoteca, valla de obra de la calle 19, cascos y
 *   conos, estante tecnico COVENIN, corcho con tabulador y sellos, la
 *   PC-SERVIDOR ("NO APAGAR", LED parpadeante y cable a los puestos),
 *   ventilador de pie (calor de San Felipe) y termo de cafe. Micros:
 *   recalcular el presupuesto (indices BCV -> total al instante, tag
 *   "antes: 40 APU a mano") y conformar una valuacion (el sello CONFORME
 *   baja y golpea + el avance sube). Kit informativo ESTANDAR (`infoKit`)
 *   en las posiciones canonicas. Paredes blanco hueso; el rubro vive en
 *   piso/props/luz (ambar obra + gris concreto).
 */
import { Group, Mesh, MeshBasicMaterial, PlaneGeometry } from 'three'
import type { Box2 } from '../../lib/collision'
import type { Locale } from '../../lib/rooms'
import { sfx } from '../audio'
import type { NpcHandle } from '../character'
import { IAI_PRESENTE_DIALOGS } from '../dialogs/iai-presente'
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
  unitGeo,
} from '../toon'
import type { RoomBuild, RoomCtx } from '../world'
import {
  desk,
  footprint,
  infoKit,
  npcCoworkers,
  type OfficeLayout,
  officeLayout,
  type PropHandle,
  type ShowcaseDemo,
  screenVariants,
  softwareShowcase,
  switchableMonitor,
  wallArt,
} from './props'

const RECALC_LABEL = {
  es: 'Recalcular el presupuesto',
  en: 'Recalculate the budget',
} as const

const SELLO_LABEL = {
  es: 'Conformar una valuacion',
  en: 'Sign off a valuation',
} as const

const LAPTOP_LABELS = {
  on: { es: 'Encender la laptop libre', en: 'Power on the spare laptop' },
  off: { es: 'Apagar la laptop libre', en: 'Power off the spare laptop' },
} as const

/** Pantallas era-2015 (Java de escritorio + red local) de las laptops. */
const LAPTOP_SCREENS = [
  {
    title: 'Obra.java — modelo',
    lines: [
      'public class Obra {',
      '  String codigo;',
      '  List<Partida> partidas;',
      '}  // COVENIN primero',
    ],
  },
  {
    title: 'PresupuestoDAO.java',
    lines: [
      'SELECT * FROM partidas',
      ' WHERE obra_id = ?',
      'recalcular(indicesBCV);',
      '// total al instante',
    ],
  },
  {
    title: 'plan_hitos.txt',
    lines: [
      'modulo partidas.... OK',
      'modulo APU......... OK',
      'valuaciones..... en QA',
      'defensa: documentar!',
    ],
  },
] as const

// --- laminas de los cuadros (wallArt): tinta plana sobre papel claro ---

const ART_PAPER = '#f4efe2'
const ART_INK = '#232620'
const ART_AMBER = '#d9a013'
const ART_CONCRETE = '#8f959e'
const ART_RED = '#b03a2e'

function artBase(ctx: CanvasRenderingContext2D, size: number): void {
  ctx.fillStyle = ART_PAPER
  ctx.fillRect(0, 0, size, size)
  ctx.strokeStyle = ART_INK
  ctx.globalAlpha = 0.35
  ctx.lineWidth = 3
  ctx.strokeRect(10, 10, size - 20, size - 20)
  ctx.globalAlpha = 1
}

/** Escudo simplificado del Yaracuy: blason + franjas + estrella. */
function drawEscudo(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  s: number,
): void {
  ctx.save()
  ctx.translate(x, y)
  ctx.strokeStyle = ART_INK
  ctx.lineWidth = 2.5
  ctx.beginPath()
  ctx.moveTo(-s / 2, -s / 2)
  ctx.lineTo(s / 2, -s / 2)
  ctx.lineTo(s / 2, s / 6)
  ctx.quadraticCurveTo(s / 2, s / 2, 0, s * 0.62)
  ctx.quadraticCurveTo(-s / 2, s / 2, -s / 2, s / 6)
  ctx.closePath()
  ctx.stroke()
  // franjas del blason
  ctx.fillStyle = ART_AMBER
  ctx.fillRect(-s / 2 + 3, -s / 2 + 3, s - 6, s / 4)
  ctx.fillStyle = ART_RED
  ctx.fillRect(-s / 2 + 3, -s / 4 + 3, s - 6, s / 5)
  // estrella
  ctx.fillStyle = ART_INK
  ctx.font = `bold ${Math.round(s / 3)}px "Space Grotesk", sans-serif`
  ctx.textAlign = 'center'
  ctx.fillText('★', 0, s * 0.38)
  ctx.textAlign = 'left'
  ctx.restore()
}

/** Lamina institucional: escudo Yaracuy + nombre completo del IAI. */
function drawVallaLamina(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  drawEscudo(ctx, 128, 74, 56)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 15px "Space Grotesk", system-ui, sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('INSTITUTO AUTONOMO DE', 128, 138)
  ctx.fillText('INFRAESTRUCTURA DEL', 128, 158)
  ctx.fillText('ESTADO YARACUY', 128, 178)
  ctx.fillStyle = ART_AMBER
  ctx.font = 'bold 26px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('IAI', 128, 210)
  ctx.textAlign = 'left'
  ctx.fillStyle = ART_INK
  ctx.globalAlpha = 0.6
  ctx.font = '12px "Space Mono", ui-monospace, monospace'
  ctx.fillText('San Felipe · obra publica', 24, 236)
  ctx.globalAlpha = 1
}

/** Diagrama de red: la PC-servidor central y los clientes cableados. */
function drawRedDiagrama(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 16px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('RED CLIENTE-SERVIDOR', 24, 38)
  // servidor central
  ctx.strokeStyle = ART_AMBER
  ctx.lineWidth = 3
  ctx.strokeRect(104, 58, 48, 62)
  ctx.fillStyle = ART_AMBER
  ctx.fillRect(112, 66, 32, 8)
  ctx.fillRect(112, 80, 32, 8)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('SERVIDOR', 100, 134)
  // clientes + cables
  const clients: readonly (readonly [number, number])[] = [
    [40, 180],
    [110, 196],
    [180, 180],
  ]
  ctx.lineWidth = 2
  for (const [cx, cy] of clients) {
    ctx.strokeStyle = ART_CONCRETE
    ctx.beginPath()
    ctx.moveTo(128, 120)
    ctx.lineTo(cx + 18, cy)
    ctx.stroke()
    ctx.strokeStyle = ART_INK
    ctx.strokeRect(cx, cy, 36, 24)
    ctx.strokeRect(cx + 10, cy + 24, 16, 6)
  }
  ctx.fillStyle = ART_INK
  ctx.globalAlpha = 0.6
  ctx.font = '12px "Space Mono", ui-monospace, monospace'
  ctx.fillText('una base, una verdad', 24, 236)
  ctx.globalAlpha = 1
}

/** Hoja de APU: secciones materiales/mano de obra/equipos + %. */
function drawApuLamina(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 16px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('A.P.U. — PARTIDA E-411', 24, 38)
  const sections: readonly (readonly [string, number])[] = [
    ['MATERIALES', 56],
    ['MANO DE OBRA (tab. + FCAS)', 104],
    ['EQUIPOS', 152],
  ] as const
  ctx.font = 'bold 11px "Space Mono", ui-monospace, monospace'
  for (const [title, y] of sections) {
    ctx.fillStyle = ART_AMBER
    ctx.fillText(title, 24, y)
    ctx.strokeStyle = ART_CONCRETE
    ctx.lineWidth = 1.5
    for (const dy of [10, 22] as const) {
      ctx.beginPath()
      ctx.moveTo(24, y + dy)
      ctx.lineTo(200, y + dy)
      ctx.stroke()
      ctx.beginPath()
      ctx.moveTo(206, y + dy)
      ctx.lineTo(232, y + dy)
      ctx.stroke()
    }
  }
  ctx.fillStyle = ART_INK
  ctx.fillText('% admin · utilidad · financ.', 24, 196)
  ctx.strokeStyle = ART_INK
  ctx.lineWidth = 2
  ctx.strokeRect(24, 206, 208, 22)
  ctx.fillStyle = ART_AMBER
  ctx.font = 'bold 12px "Space Mono", ui-monospace, monospace'
  ctx.fillText('PRECIO UNITARIO  Bs 812,40', 32, 221)
}

/** Plano de via agricola: eje de la via + curvas de nivel + cotas. */
function drawPlanoVia(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 15px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('VIA AGRICOLA — PERFIL', 24, 38)
  // curvas de nivel
  ctx.strokeStyle = ART_CONCRETE
  ctx.lineWidth = 1.5
  for (const off of [0, 18, 36, 54] as const) {
    ctx.beginPath()
    ctx.moveTo(20, 90 + off)
    ctx.quadraticCurveTo(90, 60 + off, 140, 96 + off)
    ctx.quadraticCurveTo(190, 128 + off, 236, 104 + off)
    ctx.stroke()
  }
  // eje de la via
  ctx.strokeStyle = ART_AMBER
  ctx.lineWidth = 4
  ctx.setLineDash([12, 7])
  ctx.beginPath()
  ctx.moveTo(20, 178)
  ctx.quadraticCurveTo(110, 148, 236, 172)
  ctx.stroke()
  ctx.setLineDash([])
  // cotas
  ctx.fillStyle = ART_INK
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('prog. 0+000', 22, 200)
  ctx.fillText('0+850', 196, 196)
  ctx.globalAlpha = 0.6
  ctx.font = '12px "Space Mono", ui-monospace, monospace'
  ctx.fillText('esc. 1:1000 · Yaracuy 2015', 24, 236)
  ctx.globalAlpha = 1
}

const ART_FICHA_VALLA = {
  title: {
    es: 'La obra publica del Yaracuy',
    en: 'Public works in Yaracuy',
  },
  paragraphs: {
    es: [
      'El IAI era el instituto autonomo de infraestructura de la ' +
        'gobernacion del estado Yaracuy, con sede en San Felipe: ' +
        'asfaltado de calles, vialidad agricola, edificaciones y ' +
        'drenajes. Su rastro quedo en registros oficiales — hasta una ' +
        'sentencia del TSJ cita sus contratos de obra.',
      'En 2015 Pablo implanto ahi su proyecto de grado: el sistema de ' +
        'gestion de obras, presupuestos y valuaciones que reemplazo el ' +
        'Excel y el papel de la oficina tecnica.',
      'A fines de ese año el instituto se reorganizo bajo otro nombre — ' +
        'pero el sistema alcanzo a demostrar que un equipo de ' +
        'estudiantes podia digitalizar un ente publico.',
    ],
    en: [
      'The IAI was the autonomous infrastructure institute of the ' +
        'Yaracuy state government, based in San Felipe: street ' +
        'asphalting, rural roads, buildings and drainage. Its trace ' +
        'lives in official records — even a Supreme Court ruling cites ' +
        'its works contracts.',
      'In 2015 Pablo deployed his degree project there: the works, ' +
        'budgets and valuations management system that replaced the ' +
        'technical office’s Excel and paper.',
      'Late that year the institute was reorganised under another name ' +
        '— but the system lived long enough to prove a student team ' +
        'could digitise a public body.',
    ],
  },
} as const

const ART_FICHA_RED = {
  title: {
    es: 'Una PC como servidor central',
    en: 'A PC as the central server',
  },
  paragraphs: {
    es: [
      'El achievement tecnico de la etapa: una arquitectura ' +
        'cliente-servidor sobre red local, con una PC comun haciendo de ' +
        'servidor central de la base de datos y los puestos de la ' +
        'oficina conectados como clientes.',
      'Antes, cada quien tenia su copia del presupuesto y ninguna ' +
        'cuadraba con las demas. Centralizar los datos elimino las ' +
        'copias desincronizadas: un solo dato, una sola verdad.',
      'Montado en 2015 por un estudiante, con el hardware que habia. ' +
        'La etiqueta de la torre lo dice todo: SERVIDOR — NO APAGAR.',
    ],
    en: [
      'The technical achievement of this stage: a client-server ' +
        'architecture over a local network, with an ordinary PC acting ' +
        'as the central database server and the office desks connected ' +
        'as clients.',
      'Before, everyone kept their own copy of the budget and none of ' +
        'them matched. Centralising the data killed the desynchronised ' +
        'copies: one piece of data, one truth.',
      'Set up in 2015 by a student, with the hardware at hand. The ' +
        'tower label says it all: SERVER — DO NOT TURN OFF.',
    ],
  },
} as const

const ART_FICHA_APU = {
  title: {
    es: 'Como se arma una partida',
    en: 'How a line item is built',
  },
  paragraphs: {
    es: [
      'El presupuesto de obra publica venezolano se compone de partidas ' +
        'codificadas por las normas COVENIN: codigo, descripcion, ' +
        'unidad (m3, m2, kg), cantidad del computo metrico y precio ' +
        'unitario.',
      'Ese precio sale del APU — Analisis de Precios Unitarios: los ' +
        'materiales con sus rendimientos, la mano de obra segun el ' +
        'tabulador de la construccion con su factor de costos asociados ' +
        '(FCAS), los equipos, y encima los porcentajes de ' +
        'administracion, utilidad y financiamiento.',
      'Belkis, la analista del instituto, le enseño el oficio a Pablo ' +
        'partida por partida — el levantamiento de requerimientos que ' +
        'convirtio esa hoja en el motor de calculo del sistema.',
    ],
    en: [
      'A Venezuelan public-works budget is made of line items coded by ' +
        'the COVENIN standards: code, description, unit (m3, m2, kg), ' +
        'takeoff quantity and unit price.',
      'That price comes from the unit-price analysis (APU): materials ' +
        'with their yields, labour per the construction wage table with ' +
        'its associated-costs factor, equipment, plus the percentages ' +
        'for administration, profit and financing.',
      'Belkis, the institute’s analyst, taught Pablo the trade line ' +
        'item by line item — the requirements work that turned that ' +
        'sheet into the system’s calculation engine.',
    ],
  },
} as const

// --- demos del showcase: app de escritorio Java/Windows 2015 ---

const WIN_BG = '#f0f0f0'
const WIN_CHROME = '#dce6f2'
const WIN_INK = '#1c1f26'
const WIN_SELECT = '#316AC5'
const WIN_NET = '#3f9d63'

/** Ventana Java/Win7 2015: barra de titulo + menu de obras + badge RED. */
function winChrome(
  ctx: CanvasRenderingContext2D,
  size: number,
  title: string,
): void {
  ctx.fillStyle = WIN_BG
  ctx.fillRect(0, 0, size, size)
  ctx.fillStyle = WIN_CHROME
  ctx.fillRect(0, 0, size, 24)
  ctx.fillStyle = WIN_INK
  ctx.font = 'bold 13px Tahoma, "Space Grotesk", sans-serif'
  ctx.textAlign = 'left'
  ctx.textBaseline = 'alphabetic'
  ctx.fillText(title, 8, 17)
  ctx.strokeStyle = WIN_INK
  ctx.lineWidth = 1.5
  ctx.strokeRect(size - 21, 5, 15, 14)
  ctx.beginPath()
  ctx.moveTo(size - 17, 9)
  ctx.lineTo(size - 10, 15)
  ctx.moveTo(size - 10, 9)
  ctx.lineTo(size - 17, 15)
  ctx.stroke()
  // menu del sistema de obras + badge de la red local
  ctx.fillStyle = WIN_INK
  ctx.font = '10px Tahoma, "Space Grotesk", sans-serif'
  ctx.fillText('Archivo  Obras  Presupuestos  Valuaciones', 8, 38)
  ctx.fillStyle = WIN_NET
  ctx.fillRect(size - 62, 28, 54, 13)
  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 9px "Space Mono", ui-monospace, monospace'
  ctx.fillText('RED LOCAL', size - 58, 38)
  ctx.strokeStyle = '#b8bcc4'
  ctx.beginPath()
  ctx.moveTo(0, 44)
  ctx.lineTo(size, 44)
  ctx.stroke()
}

/** Demo 1: presupuesto de la obra — partidas COVENIN + recalculo BCV. */
function drawDemoPresupuesto(
  ctx: CanvasRenderingContext2D,
  size: number,
  t: number,
): void {
  winChrome(ctx, size, 'SGO · Presupuesto de obra')
  ctx.fillStyle = WIN_INK
  ctx.font = 'bold 11px Tahoma, "Space Grotesk", sans-serif'
  ctx.fillText('Obra: Asfaltado calle 19 · San Felipe', 10, 58)
  const rows = [
    'E-411 asfalto  m3  120  812',
    'E-421 base     m3  340  356',
    'E-131 demolic. m2  210  184',
  ] as const
  const flash = t % 6 < 1.1
  rows.forEach((row, index) => {
    const y = 72 + index * 22
    if (flash) {
      ctx.fillStyle = '#fdf2cf'
      ctx.fillRect(8, y - 12, size - 16, 18)
    }
    ctx.fillStyle = WIN_INK
    ctx.font = '11px "Space Mono", ui-monospace, monospace'
    ctx.fillText(row, 12, y)
    ctx.strokeStyle = '#c8ccd4'
    ctx.beginPath()
    ctx.moveTo(8, y + 5)
    ctx.lineTo(size - 8, y + 5)
    ctx.stroke()
  })
  // boton Recalcular + total
  ctx.fillStyle = flash ? WIN_SELECT : WIN_CHROME
  ctx.fillRect(10, 148, 92, 20)
  ctx.strokeStyle = '#8a90a0'
  ctx.strokeRect(10, 148, 92, 20)
  ctx.fillStyle = flash ? '#ffffff' : WIN_INK
  ctx.font = 'bold 11px Tahoma, "Space Grotesk", sans-serif'
  ctx.fillText('Recalcular', 22, 162)
  ctx.fillStyle = WIN_INK
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  ctx.fillText(`indices BCV: ${flash ? 'AGO *' : 'JUL'}`, 116, 162)
  ctx.fillStyle = ART_AMBER
  ctx.font = 'bold 14px "Space Mono", ui-monospace, monospace'
  ctx.fillText(flash ? 'TOTAL Bs 21.560.900' : 'TOTAL Bs 18.240.500', 10, 196)
  ctx.fillStyle = WIN_INK
  ctx.globalAlpha = 0.6
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('antes: 40 APU a mano, una semana', 10, 216)
  ctx.globalAlpha = 1
}

/** Demo 2: el APU de una partida — la hoja completa hasta el PU. */
function drawDemoApu(
  ctx: CanvasRenderingContext2D,
  size: number,
  t: number,
): void {
  winChrome(ctx, size, 'SGO · APU partida E-411')
  const sections = [
    ['MATERIALES', 'Bs 388,20'],
    ['MANO DE OBRA (FCAS)', 'Bs 214,90'],
    ['EQUIPOS', 'Bs 102,10'],
    ['% adm · util · financ', 'Bs 107,20'],
  ] as const
  const active = Math.floor(t * 0.6) % sections.length
  sections.forEach(([name, amount], index) => {
    const y = 62 + index * 30
    if (index === active) {
      ctx.fillStyle = WIN_SELECT
      ctx.fillRect(8, y - 13, size - 16, 22)
    }
    ctx.fillStyle = index === active ? '#ffffff' : WIN_INK
    ctx.font = 'bold 10px "Space Mono", ui-monospace, monospace'
    ctx.fillText(name, 12, y)
    ctx.font = '11px "Space Mono", ui-monospace, monospace'
    ctx.textAlign = 'right'
    ctx.fillText(amount, size - 14, y)
    ctx.textAlign = 'left'
  })
  ctx.strokeStyle = WIN_INK
  ctx.lineWidth = 2
  ctx.strokeRect(8, 182, size - 16, 26)
  ctx.fillStyle = ART_AMBER
  ctx.font = 'bold 13px "Space Mono", ui-monospace, monospace'
  ctx.fillText('PRECIO UNITARIO  Bs 812,40', 16, 200)
  ctx.fillStyle = WIN_INK
  ctx.globalAlpha = 0.6
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('tabulador vigente + rendimientos', 10, 224)
  ctx.globalAlpha = 1
}

/** Demo 3: valuaciones — avance fisico vs financiero + curva S. */
function drawDemoValuaciones(
  ctx: CanvasRenderingContext2D,
  size: number,
  t: number,
): void {
  winChrome(ctx, size, 'SGO · Valuaciones')
  const obras = [
    ['Calle 19', 0.68, 0.72, 'CONFORMADA'],
    ['Via agricola', 0.44, 0.4, 'EN REVISION'],
    ['Drenaje Av. 7', 0.9, 0.86, 'CONFORMADA'],
  ] as const
  obras.forEach(([name, fisico, financiero, estado], index) => {
    const y = 58 + index * 42
    ctx.fillStyle = WIN_INK
    ctx.font = 'bold 10px "Space Mono", ui-monospace, monospace'
    ctx.fillText(String(name), 10, y)
    ctx.fillStyle = estado === 'CONFORMADA' ? WIN_NET : ART_AMBER
    ctx.textAlign = 'right'
    ctx.fillText(String(estado), size - 10, y)
    ctx.textAlign = 'left'
    // barras fisico (ambar) / financiero (gris)
    ctx.fillStyle = '#dde1e8'
    ctx.fillRect(10, y + 6, 150, 7)
    ctx.fillRect(10, y + 17, 150, 7)
    ctx.fillStyle = ART_AMBER
    ctx.fillRect(10, y + 6, 150 * Number(fisico), 7)
    ctx.fillStyle = ART_CONCRETE
    ctx.fillRect(10, y + 17, 150 * Number(financiero), 7)
    ctx.fillStyle = WIN_INK
    ctx.font = '9px "Space Mono", ui-monospace, monospace'
    ctx.fillText(`F ${Math.round(Number(fisico) * 100)}%`, 166, y + 13)
    ctx.fillText(`$ ${Math.round(Number(financiero) * 100)}%`, 166, y + 24)
  })
  // curva S animada en la esquina
  ctx.strokeStyle = '#c8ccd4'
  ctx.strokeRect(size - 74, 182, 64, 40)
  ctx.strokeStyle = WIN_SELECT
  ctx.lineWidth = 2
  ctx.beginPath()
  const progress = (Math.sin(t * 0.8) + 1) / 2
  for (let i = 0; i <= 20; i += 1) {
    const p = (i / 20) * (0.4 + progress * 0.6)
    const px = size - 72 + p * 60
    const py = 220 - (1 / (1 + Math.exp(-(p * 8 - 4)))) * 34
    if (i === 0) {
      ctx.moveTo(px, py)
    } else {
      ctx.lineTo(px, py)
    }
  }
  ctx.stroke()
  ctx.fillStyle = WIN_INK
  ctx.font = '9px "Space Mono", ui-monospace, monospace'
  ctx.fillText('curva S', size - 70, 178)
  ctx.globalAlpha = 0.6
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('cuadro demostrativo: lo arma', 10, 196)
  ctx.fillText('el sistema, firma el inspector', 10, 210)
  ctx.globalAlpha = 1
}

/** Los 3 mockups HTML del panel operable (look Java/Windows 2015). */
function showcaseDemos(): ShowcaseDemo[] {
  const chrome = (title: string): string =>
    '<div style="background:#dce6f2;color:#1c1f26;padding:.4rem .6rem;' +
    'font-weight:700;border-bottom:1px solid #8a90a0">' +
    `${title}<span style="float:right;border:1px solid #8a90a0;` +
    'padding:0 .4rem;font-size:.75rem;line-height:1.3rem">X</span></div>' +
    '<div style="background:#f0f0f0;color:#1c1f26;padding:.15rem .6rem;' +
    'font-size:.8rem;border-bottom:1px solid #b8bcc4">Archivo&nbsp;&nbsp;' +
    'Obras&nbsp;&nbsp;Presupuestos&nbsp;&nbsp;Valuaciones&nbsp;&nbsp;' +
    'Reportes<span style="float:right;background:#3f9d63;color:#fff;' +
    'font-size:.7rem;font-weight:700;padding:0 .35rem;border-radius:2px">' +
    'RED LOCAL</span></div>'
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
      key: 'presupuesto',
      title: {
        es: 'Presupuesto de obra',
        en: 'Works budget',
      },
      draw: drawDemoPresupuesto,
      panel: {
        brand: '#d9a013',
        html: {
          es:
            chrome('Sistema de Gestion de Obras · Presupuesto') +
            '<p style="margin:.6rem 0 .3rem"><strong>Asfaltado calle 19 · ' +
            'San Felipe</strong> — 42 partidas COVENIN · indices BCV: ' +
            'JUL 2015</p>' +
            gridTable(
              ['Codigo', 'Descripcion', 'Un', 'Cant', 'PU', 'Total'],
              [
                ['E-411', 'Asfalto en caliente', 'm3', '120', '812', '97.488'],
                ['E-421', 'Base granular', 'm3', '340', '356', '121.040'],
                ['E-131', 'Demolicion pav.', 'm2', '210', '184', '38.640'],
              ],
            ) +
            '<p style="margin:.5rem 0 0"><strong>Recalcular</strong>: al ' +
            'publicar el BCV indices nuevos, el sistema rehace los APU y ' +
            'el total de la obra <strong>al instante</strong>.</p>' +
            '<p style="opacity:.7;margin:.4rem 0 0">Antes: 40 APU a mano, ' +
            'una semana de calculadora — app de escritorio Java, 2015</p>',
          en:
            chrome('Works Management System · Budget') +
            '<p style="margin:.6rem 0 .3rem"><strong>Street 19 asphalt · ' +
            'San Felipe</strong> — 42 COVENIN line items · BCV indexes: ' +
            'JUL 2015</p>' +
            gridTable(
              ['Code', 'Description', 'Un', 'Qty', 'UP', 'Total'],
              [
                ['E-411', 'Hot-mix asphalt', 'm3', '120', '812', '97,488'],
                ['E-421', 'Granular base', 'm3', '340', '356', '121,040'],
                ['E-131', 'Pavement demolition', 'm2', '210', '184', '38,640'],
              ],
            ) +
            '<p style="margin:.5rem 0 0"><strong>Recalculate</strong>: ' +
            'when the BCV publishes new indexes, the system redoes the ' +
            'analyses and the job total <strong>instantly</strong>.</p>' +
            '<p style="opacity:.7;margin:.4rem 0 0">Before: 40 analyses ' +
            'by hand, a calculator week — Java desktop app, 2015</p>',
        },
      },
    },
    {
      key: 'apu',
      title: {
        es: 'APU de una partida',
        en: 'Unit-price analysis',
      },
      draw: drawDemoApu,
      panel: {
        brand: '#d9a013',
        html: {
          es:
            chrome('Sistema de Gestion de Obras · APU') +
            '<p style="margin:.6rem 0 .3rem"><strong>Partida E-411 · ' +
            'Asfalto en caliente (m3)</strong></p>' +
            gridTable(
              ['Componente', 'Detalle', 'Monto'],
              [
                ['Materiales', 'mezcla + rendimientos', 'Bs 388,20'],
                ['Mano de obra', 'tabulador + FCAS', 'Bs 214,90'],
                ['Equipos', 'finisher + compactadora', 'Bs 102,10'],
                ['%', 'admin + utilidad + financ.', 'Bs 107,20'],
              ],
            ) +
            '<p style="margin:.5rem 0 0"><strong>Precio unitario: ' +
            'Bs 812,40</strong> — el sistema arma la hoja completa y la ' +
            'guarda con su version de indices.</p>' +
            '<p style="opacity:.7;margin:.4rem 0 0">El oficio de Belkis ' +
            'convertido en motor de calculo — levantamiento real</p>',
          en:
            chrome('Works Management System · Unit-price analysis') +
            '<p style="margin:.6rem 0 .3rem"><strong>Item E-411 · ' +
            'Hot-mix asphalt (m3)</strong></p>' +
            gridTable(
              ['Component', 'Detail', 'Amount'],
              [
                ['Materials', 'mix + yields', 'Bs 388.20'],
                ['Labour', 'wage table + factor', 'Bs 214.90'],
                ['Equipment', 'paver + compactor', 'Bs 102.10'],
                ['%', 'admin + profit + financing', 'Bs 107.20'],
              ],
            ) +
            '<p style="margin:.5rem 0 0"><strong>Unit price: ' +
            'Bs 812.40</strong> — the system builds the full sheet and ' +
            'stores it with its index version.</p>' +
            '<p style="opacity:.7;margin:.4rem 0 0">Belkis’s trade turned ' +
            'into a calculation engine — real requirements work</p>',
        },
      },
    },
    {
      key: 'valuaciones',
      title: {
        es: 'Valuaciones y avance',
        en: 'Valuations & progress',
      },
      draw: drawDemoValuaciones,
      panel: {
        brand: '#d9a013',
        html: {
          es:
            chrome('Sistema de Gestion de Obras · Valuaciones') +
            gridTable(
              ['Obra', 'Fisico', 'Financiero', 'Estado'],
              [
                ['Asfaltado calle 19', '68%', '72%', 'CONFORMADA'],
                ['Via agricola', '44%', '40%', 'EN REVISION'],
                ['Drenaje Av. 7', '90%', '86%', 'CONFORMADA'],
              ],
            ) +
            '<p style="margin:.6rem 0 .2rem"><strong>El cuadro ' +
            'demostrativo lo arma el sistema</strong>: el inspector carga ' +
            'las mediciones, revisa la curva S y conforma con su firma.</p>' +
            '<p style="opacity:.8;margin:0">El consolidado de todas las ' +
            'obras — que antes tardaba jornadas — sale al momento para ' +
            'la presidencia.</p>',
          en:
            chrome('Works Management System · Valuations') +
            gridTable(
              ['Job', 'Physical', 'Financial', 'Status'],
              [
                ['Street 19 asphalt', '68%', '72%', 'SIGNED OFF'],
                ['Rural road', '44%', '40%', 'IN REVIEW'],
                ['Ave. 7 drainage', '90%', '86%', 'SIGNED OFF'],
              ],
            ) +
            '<p style="margin:.6rem 0 .2rem"><strong>The progress sheet ' +
            'is built by the system</strong>: the inspector loads the ' +
            'measurements, checks the S-curve and signs off.</p>' +
            '<p style="opacity:.8;margin:0">The all-works consolidated ' +
            'report — which used to take whole days — comes out on the ' +
            'spot for the presidency.</p>',
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
      id: `micro-iai-${roomIndex}-laptop${toggle.spot}`,
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

interface MicroHandle {
  group: Group
  interactable: Interactable
  update(t: number, dt: number): void
  dispose?(): void
}

/**
 * Micro "recalcular el presupuesto": el monitor del escritorio de Belkis
 * muestra el presupuesto; E dispara los indices BCV nuevos — los PU
 * parpadean en la variante `recalc` y el TOTAL sale actualizado en
 * `done`, con el tag "antes: 40 APU a mano" flotando unos segundos.
 */
function recalcMicro(opts: {
  roomIndex: number
  position: readonly [number, number, number]
  rotationY: number
  locale: Locale
  screenTheme: { screenBg: string; screenFg: string; ink: string }
}): MicroHandle {
  const group = new Group()
  const monitor = switchableMonitor({
    position: opts.position,
    rotationY: opts.rotationY,
    width: 0.58,
    variants: {
      idle: {
        title: 'presupuesto · calle 19',
        lines: [
          'partidas: 42',
          'total: Bs 18.240.500',
          'indices BCV: JUL',
          opts.locale === 'es' ? '[E] recalcular' : '[E] recalculate',
        ],
        theme: opts.screenTheme,
        dot: '#4dcc7a',
      },
      recalc: {
        title: 'indices BCV: AGO *',
        lines: [
          'E-411  Bs 812 -> ****',
          'E-421  Bs 356 -> ****',
          'E-131  Bs 184 -> ****',
          'APU x40 en proceso...',
        ],
        theme: opts.screenTheme,
        dot: '#f2b705',
      },
      done: {
        title: 'presupuesto actualizado',
        lines: [
          'indices BCV: AGO',
          'total: Bs 21.560.900',
          'APU rehechos: 40',
          opts.locale === 'es' ? 'tiempo: 0,4 s' : 'time: 0.4 s',
        ],
        theme: opts.screenTheme,
        dot: '#4dcc7a',
      },
    },
    initial: 'idle',
  })
  group.add(monitor.group)
  const tag = label(
    opts.locale === 'es' ? 'antes: 40 APU a mano' : 'before: 40 by hand',
    { size: 0.11, color: '#d9a013' },
  )
  tag.position.set(opts.position[0], opts.position[1] + 0.85, opts.position[2])
  tag.rotation.y = opts.rotationY
  tag.visible = false
  group.add(tag)
  let phase = -1
  const interactable: Interactable = {
    id: `micro-iai-recalc-${opts.roomIndex}`,
    x: opts.position[0],
    z: opts.position[2],
    radius: 2,
    label: RECALC_LABEL,
    onActivate: () => {
      if (phase === -1) {
        phase = -2 // pendiente: el proximo update fija el inicio
        monitor.screen.show('recalc')
        sfx.play('blip')
      }
    },
  }
  let start = 0
  return {
    group,
    interactable,
    update: (t) => {
      if (phase === -2) {
        phase = 0
        start = t
      }
      if (phase === 0 && t - start > 1.4) {
        phase = 1
        monitor.screen.show('done')
        tag.visible = true
      }
      if (phase === 1 && t - start > 5) {
        phase = -1
        monitor.screen.show('idle')
        tag.visible = false
      }
    },
    dispose: () => monitor.screen.dispose(),
  }
}

/**
 * Micro "conformar una valuacion": el sello CONFORME baja, golpea la
 * caratula (la marca queda visible unos segundos) y el avance fisico de
 * la mini-pantalla sube un tramo con cada conformacion.
 */
function selloMicro(opts: {
  roomIndex: number
  position: readonly [number, number, number]
  locale: Locale
  screenTheme: { screenBg: string; screenFg: string; ink: string }
}): MicroHandle {
  const [x, , z] = opts.position
  const group = new Group()
  // caratula de la valuacion sobre el escritorio + marca del sello
  const caratula = mergedBoxes(
    [{ w: 0.34, h: 0.012, d: 0.46, x, y: 0.752, z }],
    toonMat('#f2ecd9'),
  )
  caratula.userData.noOutline = true
  const marca = label('CONFORME', { size: 0.07, color: '#b03a2e' })
  marca.position.set(x, 0.765, z)
  marca.rotation.x = -Math.PI / 2
  marca.visible = false
  // sello: mango + base, flotando listo para bajar
  const sello = new Group()
  sello.add(
    outlinedMergedBoxes(
      [
        { w: 0.05, h: 0.12, d: 0.05, x: 0, y: 0.12, z: 0 },
        { w: 0.13, h: 0.05, d: 0.09, x: 0, y: 0.035, z: 0 },
      ],
      toonMat('#6a3a32'),
      { inflate: 0.02 },
    ),
  )
  const selloBaseY = 0.95
  sello.position.set(x, selloBaseY, z)
  // mini-pantalla del avance junto a la caratula
  const avanceFor = (fisico: number, financiero: number) => ({
    title: opts.locale === 'es' ? 'valuacion 04' : 'valuation 04',
    lines: [
      `${opts.locale === 'es' ? 'fisico' : 'physical'}: ${fisico}%`,
      `${opts.locale === 'es' ? 'financiero' : 'financial'}: ${financiero}%`,
    ],
    theme: opts.screenTheme,
  })
  const avance = screenVariants({
    width: 0.4,
    height: 0.26,
    variants: {
      a0: avanceFor(68, 72),
      a1: avanceFor(74, 76),
      a2: avanceFor(80, 81),
      a3: avanceFor(86, 88),
    },
    initial: 'a0',
  })
  avance.mesh.position.set(x - 0.28, 0.98, z - 0.1)
  avance.mesh.rotation.y = -Math.PI / 2
  group.add(caratula, marca, sello, avance.mesh)
  let step = 0
  let stampT = -1
  const interactable: Interactable = {
    id: `micro-iai-sello-${opts.roomIndex}`,
    x,
    z,
    radius: 1.9,
    label: SELLO_LABEL,
    onActivate: () => {
      if (stampT === -1) {
        stampT = -2 // pendiente: el proximo update fija el inicio
        sfx.play('blip')
      }
    },
  }
  return {
    group,
    interactable,
    update: (t) => {
      if (stampT === -2) {
        stampT = t
      }
      if (stampT < 0) {
        return
      }
      const elapsed = t - stampT
      if (elapsed >= 4) {
        marca.visible = false
        stampT = -1
        return
      }
      sello.position.y = selloYAt(elapsed, selloBaseY)
      if (elapsed >= 0.35 && !marca.visible) {
        marca.visible = true
        step = (step + 1) % 4
        avance.show(`a${step}`)
      }
    },
    dispose: () => avance.dispose(),
  }
}

/** Altura del sello segun la fase: baja acelerando, golpea y vuelve. */
function selloYAt(elapsed: number, baseY: number): number {
  if (elapsed < 0.35) {
    const k = elapsed / 0.35
    return baseY - (baseY - 0.76) * k * k
  }
  if (elapsed < 0.5) {
    return 0.76
  }
  if (elapsed < 1.4) {
    const k = (elapsed - 0.5) / 0.9
    return 0.76 + (baseY - 0.76) * k
  }
  return baseY
}

export default function buildIai(ctx: RoomCtx): RoomBuild {
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

  // rincon del equipo de tesis (canon): 3 puestos con laptops de la
  // epoca; Keiber y Marielys trabajan en las encendidas, 1 libre con E
  const deskSpots: readonly (readonly [number, number])[] = [
    [-1.7, room.z - 3.3],
    [0.7, room.z - 3.8],
    [-2.4, room.z - 1.7],
  ]
  const office = officeLayout({
    roomIndex: room.index,
    state,
    spots: deskSpots,
    color: '#6a6252',
    poweredSpots: new Set([0, 1]),
    screenTheme,
    screenFor: (index) => LAPTOP_SCREENS[index] ?? LAPTOP_SCREENS[0],
  })
  group.add(office.group)
  staticColliders.push(...office.colliders)
  disposables.push(office)
  interactables.push(...laptopToggles(office, deskSpots, room.index))

  // la PC-SERVIDOR (muro -X, medio): torre beige en su mesita propia,
  // etiqueta "NO APAGAR", LED parpadeante y cable de red al rincon dev
  const servX = -half + 0.9
  const servZ = room.z - 1.5
  group.add(
    outlinedMergedBoxes(
      [
        // mesita + torre beige
        { w: 0.6, h: 0.05, d: 0.5, x: servX, y: 0.5, z: servZ },
        { w: 0.06, h: 0.5, d: 0.45, x: servX - 0.25, y: 0.25, z: servZ },
        { w: 0.06, h: 0.5, d: 0.45, x: servX + 0.25, y: 0.25, z: servZ },
        { w: 0.24, h: 0.52, d: 0.46, x: servX, y: 0.79, z: servZ },
      ],
      toonMat('#d9d2bc'),
      { castShadow: true },
    ),
    // cable de red por el piso hacia los puestos del equipo
    mergedBoxes(
      [
        { w: 0.05, h: 0.012, d: 2.2, x: servX + 0.4, y: 0.006, z: servZ - 1 },
        {
          w: 3.6,
          h: 0.012,
          d: 0.05,
          x: servX + 2.2,
          y: 0.006,
          z: servZ - 2.1,
        },
      ],
      toonMat('#3a4048'),
    ),
  )
  staticColliders.push(footprint(servX, servZ, 0.75, 0.65))
  const servidorLabel = label(
    locale === 'es' ? 'SERVIDOR — NO APAGAR' : 'SERVER — DO NOT TURN OFF',
    { size: 0.09, color: theme.accent },
  )
  servidorLabel.position.set(servX, 1.24, servZ)
  servidorLabel.rotation.y = Math.PI / 2
  group.add(servidorLabel)
  const led = boxMesh(0.03, 0.03, 0.03, toonMat('#4dcc7a'))
  led.position.set(servX + 0.09, 0.95, servZ + 0.24)
  led.userData.noOutline = true
  group.add(led)
  updates.push((t) => {
    led.visible = Math.sin(t * 6) > -0.2
  })

  // meson de planos (centro-frente izquierda): rollos + plano desplegado
  // con pesas — donde el Ing. Gregorio revisa antes de salir a obra
  const mesonX = -3.6
  const mesonZ = room.z + 1.2
  group.add(
    outlinedMergedBoxes(
      [
        { w: 2.2, h: 0.06, d: 1.2, x: mesonX, y: 0.86, z: mesonZ },
        { w: 0.08, h: 0.86, d: 1.1, x: mesonX - 1, y: 0.43, z: mesonZ },
        { w: 0.08, h: 0.86, d: 1.1, x: mesonX + 1, y: 0.43, z: mesonZ },
      ],
      toonMat('#7a6a52'),
      { castShadow: true },
    ),
  )
  staticColliders.push(footprint(mesonX, mesonZ, 2.4, 1.4))
  const units = unitGeo()
  // rollos de planos (cilindros acostados) + pesas sobre el desplegado
  for (const [dx, dz, rot] of [
    [-0.6, -0.35, 0.2],
    [-0.75, -0.1, -0.15],
    [0.8, -0.4, 0.35],
  ] as const) {
    const rollo = new Mesh(units.cylinder, toonMat('#e8dfc8'))
    rollo.scale.set(0.05, 0.9, 0.05)
    rollo.rotation.z = Math.PI / 2
    rollo.rotation.y = rot
    rollo.position.set(mesonX + dx, 0.94, mesonZ + dz)
    group.add(rollo)
  }
  const desplegado = new Mesh(
    new PlaneGeometry(1.1, 0.78),
    new MeshBasicMaterial({ map: makeCanvasTexture(256, drawPlanoVia) }),
  )
  desplegado.rotation.x = -Math.PI / 2
  desplegado.rotation.z = 0.12
  desplegado.position.set(mesonX + 0.1, 0.9, mesonZ + 0.15)
  desplegado.userData.noOutline = true
  group.add(
    desplegado,
    mergedBoxes(
      [
        {
          w: 0.09,
          h: 0.05,
          d: 0.09,
          x: mesonX - 0.35,
          y: 0.92,
          z: mesonZ + 0.4,
        },
        {
          w: 0.09,
          h: 0.05,
          d: 0.09,
          x: mesonX + 0.55,
          y: 0.92,
          z: mesonZ - 0.1,
        },
      ],
      toonMat('#8f959e'),
    ),
  )

  // planoteca (muro -X, fondo): mueble de cajones anchos para planos
  group.add(
    outlinedMergedBoxes(
      [
        { w: 0.7, h: 0.95, d: 1.5, x: -half + 0.55, y: 0.475, z: room.z - 3.6 },
        ...[0.18, 0.42, 0.66].map((y) => ({
          w: 0.06,
          h: 0.14,
          d: 1.3,
          x: -half + 0.88,
          y,
          z: room.z - 3.6,
        })),
      ],
      toonMat('#8a8270'),
      { castShadow: true },
    ),
  )
  staticColliders.push(footprint(-half + 0.55, room.z - 3.6, 0.9, 1.7))

  // estante tecnico (muro -Z, derecha): Guia de Costos CIV, normas
  // COVENIN y carpetas manila por obra (lote fusionado + lomos calidos)
  const shelfX = 3.4
  group.add(
    outlinedMergedBoxes(
      [
        { w: 1.7, h: 0.04, d: 0.34, x: shelfX, y: 0.55, z: backZ + 0.35 },
        { w: 1.7, h: 0.04, d: 0.34, x: shelfX, y: 1.1, z: backZ + 0.35 },
        { w: 1.7, h: 0.04, d: 0.34, x: shelfX, y: 1.65, z: backZ + 0.35 },
        {
          w: 0.05,
          h: 1.75,
          d: 0.34,
          x: shelfX - 0.85,
          y: 0.87,
          z: backZ + 0.35,
        },
        {
          w: 0.05,
          h: 1.75,
          d: 0.34,
          x: shelfX + 0.85,
          y: 0.87,
          z: backZ + 0.35,
        },
      ],
      toonMat('#8a9098'),
      { castShadow: true },
    ),
    // lomos gruesos (Guia CIV + COVENIN) y carpetas manila
    mergedBoxes(
      [
        { w: 0.14, h: 0.4, d: 0.26, x: shelfX - 0.6, y: 0.79, z: backZ + 0.35 },
        {
          w: 0.12,
          h: 0.38,
          d: 0.26,
          x: shelfX - 0.44,
          y: 0.78,
          z: backZ + 0.35,
        },
        { w: 0.1, h: 0.36, d: 0.26, x: shelfX - 0.3, y: 0.77, z: backZ + 0.35 },
        { w: 0.5, h: 0.32, d: 0.26, x: shelfX + 0.3, y: 0.75, z: backZ + 0.35 },
        { w: 0.7, h: 0.34, d: 0.26, x: shelfX - 0.3, y: 1.31, z: backZ + 0.35 },
        { w: 0.5, h: 0.3, d: 0.26, x: shelfX + 0.45, y: 1.29, z: backZ + 0.35 },
        { w: 0.9, h: 0.3, d: 0.26, x: shelfX, y: 1.84, z: backZ + 0.35 },
      ],
      toonMat('#b09a6e'),
    ),
  )
  staticColliders.push(footprint(shelfX, backZ + 0.4, 1.9, 0.6))

  // escritorio administrativo de Belkis (muro +X, medio): corcho con el
  // tabulador pinchado, sellos humedos, termo de cafe y las dos micros
  const belkisDeskX = half - 1.0
  const belkisDeskZ = room.z - 2.3
  group.add(
    desk({
      position: [belkisDeskX, 0, belkisDeskZ],
      rotationY: Math.PI / 2,
      width: 1.6,
      color: '#7a6a52',
    }),
    // sellos humedos + almohadilla + termo de cafe
    outlinedMergedBoxes(
      [
        {
          w: 0.12,
          h: 0.04,
          d: 0.08,
          x: belkisDeskX - 0.1,
          y: 0.76,
          z: belkisDeskZ + 0.55,
        },
        {
          w: 0.05,
          h: 0.1,
          d: 0.05,
          x: belkisDeskX + 0.08,
          y: 0.79,
          z: belkisDeskZ + 0.62,
        },
        {
          w: 0.1,
          h: 0.16,
          d: 0.1,
          x: belkisDeskX + 0.15,
          y: 0.82,
          z: belkisDeskZ - 0.62,
        },
      ],
      toonMat('#6a3a32'),
      { inflate: 0.02 },
    ),
  )
  staticColliders.push(footprint(belkisDeskX, belkisDeskZ, 0.8, 1.7))
  // corcho en la pared +X con el tabulador y recortes pinchados
  const corcho = boxMesh(0.05, 0.8, 1.2, toonMat('#b09a6e'))
  corcho.position.set(half - 0.06, 1.7, belkisDeskZ)
  group.add(
    corcho,
    mergedBoxes(
      [
        {
          w: 0.02,
          h: 0.3,
          d: 0.4,
          x: half - 0.1,
          y: 1.8,
          z: belkisDeskZ - 0.3,
        },
        {
          w: 0.02,
          h: 0.36,
          d: 0.3,
          x: half - 0.1,
          y: 1.72,
          z: belkisDeskZ + 0.15,
        },
        {
          w: 0.02,
          h: 0.22,
          d: 0.26,
          x: half - 0.1,
          y: 1.56,
          z: belkisDeskZ + 0.42,
        },
      ],
      toonMat('#f2ecd9'),
    ),
  )
  const tabuladorLabel = label(
    locale === 'es' ? 'TABULADOR 2015' : 'WAGE TABLE 2015',
    { size: 0.08, color: theme.trim ?? theme.accent },
  )
  tabuladorLabel.position.set(half - 0.14, 2.2, belkisDeskZ)
  tabuladorLabel.rotation.y = -Math.PI / 2
  group.add(tabuladorLabel)

  // micro 1: recalcular el presupuesto (monitor del escritorio de Belkis)
  const recalc = recalcMicro({
    roomIndex: room.index,
    position: [belkisDeskX - 0.02, 0.75, belkisDeskZ - 0.35],
    rotationY: -Math.PI / 2,
    locale,
    screenTheme,
  })
  addProps({ group, interactables, updates }, [recalc])
  if (recalc.dispose) {
    disposables.push({ dispose: recalc.dispose })
  }

  // micro 2: conformar una valuacion (el sello CONFORME + el avance)
  const sello = selloMicro({
    roomIndex: room.index,
    position: [belkisDeskX - 0.02, 0, belkisDeskZ + 0.3],
    locale,
    screenTheme,
  })
  addProps({ group, interactables, updates }, [sello])
  if (sello.dispose) {
    disposables.push({ dispose: sello.dispose })
  }

  // valla de obra apoyada en el muro +X (frente): la calle 19 con el
  // escudo — la iconografia real del instituto
  const vallaTexture = makeCanvasTexture(256, (vctx, size) => {
    vctx.fillStyle = '#f4efe2'
    vctx.fillRect(0, 0, size, size)
    vctx.strokeStyle = ART_INK
    vctx.lineWidth = 5
    vctx.strokeRect(6, 6, size - 12, size - 12)
    drawEscudo(vctx, 52, 58, 44)
    vctx.fillStyle = ART_INK
    vctx.font = 'bold 14px "Space Grotesk", system-ui, sans-serif'
    vctx.fillText('GOBIERNO BOLIVARIANO', 92, 44)
    vctx.fillText('DE YARACUY · IAI', 92, 64)
    vctx.strokeStyle = ART_AMBER
    vctx.lineWidth = 4
    vctx.beginPath()
    vctx.moveTo(20, 96)
    vctx.lineTo(size - 20, 96)
    vctx.stroke()
    vctx.font = 'bold 20px "Space Grotesk", system-ui, sans-serif'
    vctx.fillText('OBRA: ASFALTADO', 24, 136)
    vctx.fillText('CALLE 19 · SAN FELIPE', 24, 164)
    vctx.fillStyle = ART_AMBER
    vctx.font = 'bold 14px "Space Mono", ui-monospace, monospace'
    vctx.fillText('EJECUTA: IAI · 2015', 24, 204)
    // franjas de peligro
    vctx.fillStyle = ART_AMBER
    for (let i = 0; i < 6; i += 1) {
      vctx.save()
      vctx.translate(28 + i * 40, 236)
      vctx.rotate(-0.5)
      vctx.fillRect(-6, -10, 14, 22)
      vctx.restore()
    }
  })
  const valla = new Group()
  const vallaBoard = new Mesh(
    new PlaneGeometry(1.5, 1.1),
    new MeshBasicMaterial({ map: vallaTexture }),
  )
  vallaBoard.userData.noOutline = true
  vallaBoard.position.set(half - 0.22, 1.15, room.z + 2.2)
  vallaBoard.rotation.y = -Math.PI / 2
  vallaBoard.rotation.z = 0.05
  const vallaLegs = mergedBoxes(
    [
      { w: 0.06, h: 1.2, d: 0.06, x: half - 0.14, y: 0.6, z: room.z + 1.65 },
      { w: 0.06, h: 1.2, d: 0.06, x: half - 0.14, y: 0.6, z: room.z + 2.75 },
    ],
    toonMat('#8f959e'),
  )
  valla.add(vallaBoard, vallaLegs)
  group.add(valla)
  staticColliders.push(footprint(half - 0.3, room.z + 2.2, 0.5, 1.4))

  // cascos en perchero + conos apilados: la seguridad de obra en la
  // esquina del frente (los toques ambar/naranja de la sala)
  const perchX = 4.6
  const perchZ = frontZ - 0.5
  group.add(
    outlinedMergedBoxes(
      [
        { w: 0.28, h: 0.05, d: 0.28, x: perchX, y: 0.025, z: perchZ },
        { w: 0.07, h: 1.7, d: 0.07, x: perchX, y: 0.85, z: perchZ },
        { w: 0.5, h: 0.05, d: 0.05, x: perchX, y: 1.62, z: perchZ },
      ],
      toonMat('#8f959e'),
      { castShadow: true },
    ),
  )
  for (const dx of [-0.2, 0.2] as const) {
    const casco = new Mesh(units.sphere, toonMat('#f2b705'))
    casco.scale.set(0.14, 0.1, 0.16)
    casco.position.set(perchX + dx, 1.56, perchZ + 0.06)
    group.add(casco)
  }
  staticColliders.push(footprint(perchX, perchZ, 0.4, 0.4))
  group.add(
    outlinedMergedBoxes(
      [-half + 0.8, -half + 1.25].flatMap((cx, i) => [
        {
          w: 0.34,
          h: 0.05,
          d: 0.34,
          x: cx,
          y: 0.025,
          z: frontZ - 0.8 + i * 0.15,
        },
        { w: 0.2, h: 0.2, d: 0.2, x: cx, y: 0.15, z: frontZ - 0.8 + i * 0.15 },
        { w: 0.1, h: 0.18, d: 0.1, x: cx, y: 0.34, z: frontZ - 0.8 + i * 0.15 },
      ]),
      toonMat('#e2732b'),
      { castShadow: true },
    ),
  )
  staticColliders.push(footprint(-half + 1, frontZ - 0.75, 0.9, 0.6))

  // ventilador de pie (calor de San Felipe): la cabeza oscila
  const fan = new Group()
  fan.position.set(-2.9, 0, room.z - 0.6)
  fan.add(
    outlinedMergedBoxes(
      [
        { w: 0.34, h: 0.05, d: 0.34, x: 0, y: 0.025, z: 0 },
        { w: 0.06, h: 1.25, d: 0.06, x: 0, y: 0.65, z: 0 },
      ],
      toonMat('#8f959e'),
    ),
  )
  const fanHead = new Group()
  const cage = new Mesh(units.cylinder, toonMat('#c8ccd2'))
  cage.scale.set(0.24, 0.1, 0.24)
  cage.rotation.x = Math.PI / 2
  fanHead.add(cage)
  const blades = new Mesh(units.box, toonMat('#5a6068'))
  blades.scale.set(0.34, 0.05, 0.02)
  blades.position.z = 0.02
  fanHead.add(blades)
  fanHead.position.set(0, 1.32, 0.05)
  fan.add(fanHead)
  group.add(fan)
  staticColliders.push(footprint(-2.9, room.z - 0.6, 0.45, 0.45))
  updates.push((t, dt) => {
    fanHead.rotation.y = Math.sin(t * 0.7) * 0.6
    blades.rotation.z += dt * 14
  })

  // cuadros de rubro (wallArt): valla institucional y diagrama de red
  // inspeccionables al fondo; APU inspeccionable y plano decorativo
  // flanqueando la puerta al pasillo
  const art = wallArt({
    roomIndex: room.index,
    theme,
    locale,
    onFicha: actions.openStory,
    frames: [
      {
        key: 'valla-iai',
        position: [-3.6, 2, backZ + 0.08],
        rotationY: 0,
        draw: drawVallaLamina,
        ficha: ART_FICHA_VALLA,
      },
      {
        key: 'red-local',
        position: [0.6, 2, backZ + 0.08],
        rotationY: 0,
        draw: drawRedDiagrama,
        ficha: ART_FICHA_RED,
      },
      {
        key: 'apu',
        position: [-3.6, 2, frontZ - 0.08],
        rotationY: Math.PI,
        draw: drawApuLamina,
        ficha: ART_FICHA_APU,
      },
      {
        key: 'plano-via',
        position: [3.6, 2, frontZ - 0.08],
        rotationY: Math.PI,
        draw: drawPlanoVia,
      },
    ],
  })
  staticColliders.push(...art.colliders)
  const sink = { group, interactables, updates }
  addProps(sink, art.props)

  // showcase del software junto a la puerta al pasillo (canon AC-6):
  // app de escritorio Java 2015 con badge RED LOCAL — E cicla 3 demos
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

  // kit informativo estandar (RETOS / APRENDIZAJES / grieta / cuaderno)
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

  // NPCs del canon (2 enfoques, informe 16): Keiber y Marielys (tesistas
  // sentados en el rincon dev), Belkis (analista en su escritorio de
  // sellos), el Ing. Gregorio (inspector de ronda entre el meson y el
  // showcase) y la Ing. Maritza (presidenta junto a la valla de obra).
  const coworkers = npcCoworkers({
    roomIndex: room.index,
    openDialog: actions.openDialog,
    npcs: [
      {
        key: 'keiber',
        role: 'coworker',
        spec: {
          skin: '#b5825f',
          hair: { style: 'spiky', color: '#14100c' },
          top: '#4a6a8a',
          bottom: '#2e3238',
          accessory: 'badge',
          faceSeed: 41,
        },
        position: [-1.7, 0, room.z - 4.85],
        rotationY: 0,
        pose: 'sit',
        dialog: IAI_PRESENTE_DIALOGS.keiber,
      },
      {
        key: 'marielys',
        role: 'coworker',
        spec: {
          skin: '#e8b48c',
          hair: { style: 'ponytail', color: '#2a1a12' },
          top: '#6a4a7a',
          bottom: '#3a4048',
          accessory: 'glasses',
          faceSeed: 84,
        },
        position: [0.7, 0, room.z - 4.85],
        rotationY: 0,
        pose: 'sit',
        dialog: IAI_PRESENTE_DIALOGS.marielys,
      },
      {
        key: 'gregorio',
        role: 'staff',
        spec: {
          skin: '#c98f6a',
          hair: { style: 'short', color: '#7a7a82' },
          top: '#e8e6da',
          bottom: '#3a4048',
          accessory: 'badge',
          faceSeed: 53,
        },
        position: [-3, 0, room.z + 1.9],
        path: [
          [-3, room.z + 1.9],
          [1.2, room.z + 2.6],
          [2, room.z + 0.6],
        ],
        speed: 0.5,
        dialog: IAI_PRESENTE_DIALOGS.gregorio,
      },
      {
        key: 'belkis',
        role: 'staff',
        spec: {
          skin: '#d9a684',
          hair: { style: 'bun', color: '#3a2418' },
          top: '#5a7a62',
          bottom: '#4a4438',
          accessory: 'glasses',
          faceSeed: 62,
        },
        position: [belkisDeskX - 0.9, 0, belkisDeskZ],
        rotationY: Math.PI / 2,
        dialog: IAI_PRESENTE_DIALOGS.belkis,
      },
      {
        key: 'maritza',
        role: 'boss',
        spec: {
          skin: '#d9a684',
          hair: { style: 'bun', color: '#2a2028' },
          top: '#8a3a42',
          bottom: '#2e3238',
          accessory: 'badge',
          faceSeed: 77,
        },
        position: [half - 1.5, 0, room.z + 2.7],
        rotationY: -1,
        dialog: IAI_PRESENTE_DIALOGS.maritza,
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
