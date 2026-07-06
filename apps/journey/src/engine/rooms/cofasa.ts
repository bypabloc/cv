/**
 * @module rooms/cofasa (engine)
 * @description Sala 3 — Laboratorio Cofasa (farmaceutica, VE, 2017-18),
 *   construida al CANON de sala (plan journey-salas-estandar, informe
 *   10): `officeLayout` en el rincon de desarrollo (Yorman y Douglas
 *   sentados en sus laptops Laravel/jQuery, 1 libre togglable con E), 5
 *   NPCs conversables con los 2 enfoques (`npcCoworkers`: Yorman y
 *   Douglas devs, Nelida supervisora en ronda, Rafael operario con
 *   cofia en la llenadora, Carmen jefa de produccion), cuadros de rubro
 *   (`wallArt`: envasado de inyectables, Pareto de causas y
 *   disponibilidad inspeccionables — decision del usuario: 3 fichas —,
 *   poster cGMP decorativo) y el `softwareShowcase` junto a la puerta
 *   con 3 demos del sistema real (registrar parada, paradas por causa,
 *   disponibilidad — panel admin jQuery/Bootstrap 2017, NUNCA SPA).
 *   Props firma: tanque de mezcla inox, llenadora de ampollas con banda
 *   de vidrio ambar (Miovit corriendo), linea de blisteres, cajas de
 *   producto Miovit, mesa QC, estanteria de registros de lote y la
 *   TORRE ANDON (unico lugar con rojo/verde junto al dashboard). Micro:
 *   simular una parada — el andon pasa a rojo y el monitor registra la
 *   causa al toque (ciclando el catalogo real). Guiño: etiqueta de la
 *   planta en Urb. Industrial Lebrun, Petare. Kit informativo ESTANDAR
 *   (`infoKit`) en las posiciones canonicas. Paredes blanco hueso; el
 *   rubro vive en piso/props/luz (azul Cofasa + acero + ambar).
 */
import { Group, Mesh } from 'three'
import type { Box2 } from '../../lib/collision'
import type { Locale } from '../../lib/rooms'
import { sfx } from '../audio'
import type { NpcHandle } from '../character'
import { COFASA_PRESENTE_DIALOGS } from '../dialogs/cofasa-presente'
import type { Interactable } from '../state'
import {
  basicMat,
  boxMesh,
  disposeDeep,
  label,
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
  softwareShowcase,
  switchableMonitor,
  wallArt,
} from './props'

const ANDON_LABEL = {
  es: 'Simular una parada',
  en: 'Simulate a stoppage',
} as const

const LAPTOP_LABELS = {
  on: { es: 'Encender la laptop libre', en: 'Power on the spare laptop' },
  off: { es: 'Apagar la laptop libre', en: 'Power off the spare laptop' },
} as const

/** Pantallas era-2017 (Laravel + jQuery) de las laptops, por puesto. */
const LAPTOP_SCREENS = [
  {
    title: 'ParadaController.php',
    lines: [
      'public function store($r) {',
      '  Parada::create(',
      '    $r->validated());',
      '}  // Laravel 5, LAN',
    ],
  },
  {
    title: 'paradas.js — jQuery',
    lines: [
      "$('#btn-registrar')",
      "  .on('click', () =>",
      "    $.post('/paradas',",
      '      datos));  // 2017',
    ],
  },
  {
    title: 'pendientes.txt',
    lines: [
      'causa nueva: calibracion',
      'reporte turno: imprimir',
      'selector: frecuentes 1o',
      'backup BD: viernes',
    ],
  },
] as const

// --- paleta del rubro (informe 10) ---

const COFASA_BLUE = '#1560bd'
const STEEL = '#9aa0a6'
const STEEL_DARK = '#7a8088'
const AMBER = '#c9862e'
const ANDON_RED = '#e23b34'
const ANDON_GREEN = '#3aa856'

// --- laminas de los cuadros (wallArt): tinta plana sobre papel claro ---

const ART_PAPER = '#f4efe2'
const ART_INK = '#182430'

function artBase(ctx: CanvasRenderingContext2D, size: number): void {
  ctx.fillStyle = ART_PAPER
  ctx.fillRect(0, 0, size, size)
  ctx.strokeStyle = ART_INK
  ctx.globalAlpha = 0.35
  ctx.lineWidth = 3
  ctx.strokeRect(10, 10, size - 20, size - 20)
  ctx.globalAlpha = 1
}

/** Flujo de envasado: mezcla -> llenado -> ... -> Kit Miovit. */
function drawEnvasado(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 15px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('ENVASADO DE INYECTABLES', 20, 36)
  const steps = [
    'MEZCLA',
    'LLENADO',
    'SELLADO',
    'INSPECCION',
    'BLISTEADO',
    'KIT MIOVIT',
  ] as const
  ctx.font = 'bold 10px "Space Mono", ui-monospace, monospace'
  steps.forEach((step, index) => {
    const y = 52 + index * 30
    const active = index === 1
    ctx.strokeStyle = active ? COFASA_BLUE : ART_INK
    ctx.lineWidth = active ? 3 : 2
    ctx.strokeRect(58, y, 110, 20)
    ctx.fillStyle = active ? COFASA_BLUE : ART_INK
    ctx.fillText(step, 66, y + 14)
    if (index < steps.length - 1) {
      ctx.strokeStyle = ART_INK
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.moveTo(113, y + 20)
      ctx.lineTo(113, y + 30)
      ctx.moveTo(109, y + 26)
      ctx.lineTo(113, y + 30)
      ctx.lineTo(117, y + 26)
      ctx.stroke()
    }
  })
  // ampolla ambar al margen: cuerpo + cuello sellado
  ctx.strokeStyle = AMBER
  ctx.lineWidth = 3
  ctx.strokeRect(196, 96, 22, 48)
  ctx.beginPath()
  ctx.moveTo(201, 96)
  ctx.lineTo(207, 78)
  ctx.moveTo(213, 96)
  ctx.lineTo(207, 78)
  ctx.stroke()
  ctx.fillStyle = AMBER
  ctx.font = 'bold 9px "Space Mono", ui-monospace, monospace'
  ctx.fillText('ambar', 192, 158)
  ctx.fillStyle = ART_INK
  ctx.globalAlpha = 0.6
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('la linea que el sistema vigila', 20, 238)
  ctx.globalAlpha = 1
}

/** Pareto de causas de parada: barras horizontales ordenadas. */
function drawPareto(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 15px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('PARADAS POR CAUSA', 20, 36)
  const causes = [
    ['CAMBIO FORMATO', 150],
    ['LIMPIEZA', 118],
    ['ATASCO', 84],
    ['FALTA MATERIAL', 58],
    ['FALLA ELECTRICA', 38],
  ] as const
  causes.forEach(([name, width], index) => {
    const y = 58 + index * 32
    ctx.fillStyle = index < 2 ? COFASA_BLUE : ART_INK
    ctx.globalAlpha = index < 2 ? 1 : 0.75
    ctx.fillRect(20, y, width, 14)
    ctx.globalAlpha = 1
    ctx.font = 'bold 9px "Space Mono", ui-monospace, monospace'
    ctx.fillStyle = ART_INK
    ctx.fillText(name, 22, y + 26)
  })
  ctx.fillStyle = ART_INK
  ctx.globalAlpha = 0.6
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('antes nadie las media', 20, 238)
  ctx.globalAlpha = 1
}

/** Donut de disponibilidad + la formula del indicador resumen. */
function drawDisponibilidad(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 15px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('DISPONIBILIDAD DE LINEA', 20, 36)
  const cx = 128
  const cy = 118
  const start = -Math.PI / 2
  // porcion operando (azul Cofasa) + detenida (gris)
  ctx.lineWidth = 22
  ctx.strokeStyle = COFASA_BLUE
  ctx.beginPath()
  ctx.arc(cx, cy, 52, start, start + Math.PI * 2 * 0.84)
  ctx.stroke()
  ctx.strokeStyle = STEEL_DARK
  ctx.globalAlpha = 0.6
  ctx.beginPath()
  ctx.arc(cx, cy, 52, start + Math.PI * 2 * 0.84, start + Math.PI * 2)
  ctx.stroke()
  ctx.globalAlpha = 1
  ctx.fillStyle = COFASA_BLUE
  ctx.font = 'bold 22px "Space Grotesk", system-ui, sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText('84%', cx, cy + 8)
  ctx.textAlign = 'left'
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('disponibilidad =', 44, 204)
  ctx.fillText('  operando / total', 44, 220)
  ctx.globalAlpha = 0.6
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('el indicador resumen', 20, 238)
  ctx.globalAlpha = 1
}

/** Poster de buenas practicas: figura con cofia + normas de sala limpia. */
function drawCGMP(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = COFASA_BLUE
  ctx.font = 'bold 15px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('BUENAS PRACTICAS · cGMP', 20, 36)
  // operario: cofia (arco), cabeza, mascarilla y bata trapecio
  ctx.strokeStyle = ART_INK
  ctx.lineWidth = 3
  ctx.lineCap = 'round'
  ctx.beginPath()
  ctx.arc(70, 92, 20, 0, Math.PI * 2)
  ctx.stroke()
  ctx.beginPath()
  ctx.arc(70, 86, 24, Math.PI, 0)
  ctx.stroke()
  // mascarilla
  ctx.beginPath()
  ctx.moveTo(56, 98)
  ctx.lineTo(84, 98)
  ctx.moveTo(56, 104)
  ctx.lineTo(84, 104)
  ctx.stroke()
  // bata
  ctx.beginPath()
  ctx.moveTo(52, 118)
  ctx.lineTo(40, 190)
  ctx.lineTo(100, 190)
  ctx.lineTo(88, 118)
  ctx.closePath()
  ctx.stroke()
  const rules = [
    'cofia y mascarilla',
    'lavado de manos',
    'bata esteril',
    'sin joyas',
  ] as const
  ctx.font = 'bold 10px "Space Mono", ui-monospace, monospace'
  rules.forEach((rule, index) => {
    const y = 90 + index * 26
    ctx.fillStyle = COFASA_BLUE
    ctx.fillRect(122, y - 8, 8, 8)
    ctx.fillStyle = ART_INK
    ctx.fillText(rule, 138, y)
  })
  ctx.fillStyle = ART_INK
  ctx.globalAlpha = 0.6
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('sala limpia: la norma manda', 20, 238)
  ctx.globalAlpha = 1
}

const ART_FICHA_ENVASADO = {
  title: {
    es: 'Del tanque al Kit Miovit',
    en: 'From the tank to the Miovit Kit',
  },
  paragraphs: {
    es: [
      'Laboratorio Cofasa es una farmaceutica venezolana emblematica: ' +
        'empezo distribuyendo en los años cincuenta y desde 1974 fabrica ' +
        'en su planta de la Urb. Industrial Lebrun, en Petare. Produce ' +
        'medicamentos eticos, genericos y OTC: ampollas inyectables, ' +
        'tabletas, jarabes y colirios.',
      'Su producto estrella es Miovit, el complejo B inyectable que se ' +
        'vende en kit: ampollas de vidrio ambar con sus inyectadoras. La ' +
        'linea de esta sala lo esta envasando: mezcla, llenado, sellado ' +
        'a la llama, inspeccion, blisteado y estuchado.',
      'El sistema que Pablo construyo en 2017-18 monitoreaba justamente ' +
        'ese proceso: cada evento de produccion y cada parada de maquina ' +
        'de la linea, registrados en el momento.',
    ],
    en: [
      'Laboratorio Cofasa is an emblematic Venezuelan pharma company: ' +
        'it began as a distributor in the fifties and has manufactured ' +
        'since 1974 at its plant in the Lebrun industrial district of ' +
        'Petare. It makes ethical, generic and OTC medicines: injectable ' +
        'ampoules, tablets, syrups and eye drops.',
      'Its flagship product is Miovit, the injectable B-complex sold as ' +
        'a kit: amber glass ampoules with their syringes. The line in ' +
        'this room is packaging it: mixing, filling, flame sealing, ' +
        'inspection, blistering and boxing.',
      'The system Pablo built in 2017-18 monitored exactly that ' +
        'process: every production event and every machine stoppage on ' +
        'the line, logged as they happened.',
    ],
  },
} as const

const ART_FICHA_PARETO = {
  title: {
    es: 'Las causas que nadie media',
    en: 'The causes nobody measured',
  },
  paragraphs: {
    es: [
      'Una linea farmaceutica se detiene por muchas razones: cambio de ' +
        'formato entre lotes, limpieza y sanitizacion, atascos, falta ' +
        'de material, fallas electricas, calibracion. Todas normales — ' +
        'pero nadie sabia cual se comia el tiempo.',
      'El sistema registro cada parada con su causa y su duracion, y ' +
        'este grafico existio por primera vez: las causas ordenadas de ' +
        'mayor a menor. Arriba no quedaron las fallas de maquina, sino ' +
        'el cambio de formato y la limpieza.',
      'Con esa visibilidad la planta priorizo: planificar lotes para ' +
        'cambiar menos veces y programar la sanitizacion. Decisiones ' +
        'informadas por datos que antes eran ruido.',
    ],
    en: [
      'A pharma line stops for many reasons: changeover between ' +
        'batches, cleaning and sanitisation, jams, missing material, ' +
        'power failures, calibration. All normal — but nobody knew ' +
        'which one ate the time.',
      'The system logged every stoppage with its cause and duration, ' +
        'and this chart existed for the first time: causes ranked top ' +
        'to bottom. Machine failures were not on top — changeover and ' +
        'cleaning were.',
      'With that visibility the plant prioritised: planning batches to ' +
        'switch less often and scheduling sanitisation. Decisions ' +
        'informed by data that used to be noise.',
    ],
  },
} as const

const ART_FICHA_DISPONIBILIDAD = {
  title: {
    es: 'El indicador resumen',
    en: 'The summary indicator',
  },
  paragraphs: {
    es: [
      'Disponibilidad = tiempo operando / tiempo total. Una formula ' +
        'simple que resume la salud de la linea: cuanto del turno la ' +
        'maquina realmente produjo.',
      'Antes del sistema, calcularla exigia VARIAS horas de ' +
        'consolidacion manual: juntar planillas de todos los turnos, ' +
        'sumar tiempos a calculadora y pelear con totales que no ' +
        'cuadraban. Con la captura digital paso a ser una consulta ' +
        'directa.',
      'Ese fue el corazon del sistema de Pablo: transformar datos ' +
        'crudos en indicadores accionables. Estuvo en uso productivo ' +
        'casi dos años, ajustandose con el feedback de la planta.',
    ],
    en: [
      'Availability = running time / total time. A simple formula that ' +
        'sums up the health of the line: how much of the shift the ' +
        'machine actually produced.',
      'Before the system, computing it took SEVERAL hours of manual ' +
        'consolidation: collecting every shift’s sheets, adding ' +
        'times on a calculator and fighting totals that never matched. ' +
        'With digital capture it became a direct query.',
      'That was the heart of Pablo’s system: turning raw data ' +
        'into actionable indicators. It stayed in productive use for ' +
        'almost two years, tuned with the plant’s feedback.',
    ],
  },
} as const

// --- demos del showcase: panel admin web 2017 (jQuery + Bootstrap) ---

const WEB_BG = '#f4f5f7'
const WEB_INK = '#1c2430'
const WEB_LINE = '#c8ccd2'

/** Chrome del panel admin 2017: navbar azul Cofasa + sidebar de modulos. */
function webChrome(
  ctx: CanvasRenderingContext2D,
  size: number,
  title: string,
): void {
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, size, size)
  ctx.fillStyle = COFASA_BLUE
  ctx.fillRect(0, 0, size, 26)
  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 12px "Space Grotesk", system-ui, sans-serif'
  ctx.textAlign = 'left'
  ctx.textBaseline = 'alphabetic'
  ctx.fillText(title, 8, 18)
  // sidebar de modulos, "Paradas" activo
  ctx.fillStyle = WEB_BG
  ctx.fillRect(0, 26, 58, size - 26)
  ctx.strokeStyle = WEB_LINE
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.moveTo(58, 26)
  ctx.lineTo(58, size)
  ctx.stroke()
  const modules = ['Inicio', 'Paradas', 'Report.', 'Usuar.'] as const
  ctx.font = '10px "Space Grotesk", system-ui, sans-serif'
  modules.forEach((module, index) => {
    const y = 46 + index * 20
    if (index === 1) {
      ctx.fillStyle = COFASA_BLUE
      ctx.fillRect(0, y - 12, 58, 17)
      ctx.fillStyle = '#ffffff'
    } else {
      ctx.fillStyle = WEB_INK
    }
    ctx.fillText(module, 6, y)
  })
}

/** Campo plano estilo Bootstrap 2017. */
function webField(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  text: string,
): void {
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(x, y, w, 17)
  ctx.strokeStyle = WEB_LINE
  ctx.lineWidth = 1.5
  ctx.strokeRect(x, y, w, 17)
  ctx.fillStyle = WEB_INK
  ctx.font = '10px "Space Mono", ui-monospace, monospace'
  ctx.fillText(text, x + 5, y + 12)
}

const DEMO_CAUSAS = [
  'atasco mecanico',
  'cambio de formato',
  'limpieza',
] as const

/** Demo 1: registrar parada — formulario con la causa ciclando. */
function drawDemoEvento(
  ctx: CanvasRenderingContext2D,
  size: number,
  t: number,
): void {
  webChrome(ctx, size, 'Monitoreo de Produccion')
  ctx.fillStyle = WEB_INK
  ctx.font = 'bold 12px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('Registrar parada', 66, 44)
  ctx.font = '10px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('Linea:', 66, 64)
  webField(ctx, 106, 52, 140, 'Llenadora ampollas L-2')
  ctx.fillText('Causa:', 66, 88)
  const causa = DEMO_CAUSAS[Math.floor(t * 0.5) % DEMO_CAUSAS.length]
  webField(ctx, 106, 76, 140, `${causa} ▾`)
  ctx.fillText('Inicio:', 66, 112)
  webField(ctx, 106, 100, 70, '10:42:07')
  ctx.fillStyle = WEB_INK
  ctx.globalAlpha = 0.6
  ctx.font = '9px "Space Mono", ui-monospace, monospace'
  ctx.fillText('(la pone el sistema)', 182, 112)
  ctx.globalAlpha = 1
  // boton azul + registro por empleado
  ctx.fillStyle = COFASA_BLUE
  ctx.fillRect(106, 126, 80, 20)
  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 10px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('Registrar', 122, 140)
  ctx.fillStyle = WEB_INK
  ctx.font = '10px "Space Mono", ui-monospace, monospace'
  ctx.fillText('usuario: nguerra', 66, 166)
  // ultimos eventos
  ctx.strokeStyle = WEB_LINE
  ctx.strokeRect(66, 176, size - 76, 42)
  ctx.font = '9px "Space Mono", ui-monospace, monospace'
  ctx.fillText('10:12  limpieza        18 min', 72, 190)
  ctx.fillText('08:55  cambio formato  36 min', 72, 202)
  ctx.fillText('07:41  atasco           6 min', 72, 214)
}

/** Demo 2: paradas por causa — barras que crecen (Chart.js-like). */
function drawDemoPareto(
  ctx: CanvasRenderingContext2D,
  size: number,
  t: number,
): void {
  webChrome(ctx, size, 'Monitoreo de Produccion')
  ctx.fillStyle = WEB_INK
  ctx.font = 'bold 12px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('Paradas por causa · mes', 66, 44)
  const grow = Math.min(1, ((t * 0.9) % 5) / 1.1)
  const bars = [
    ['cambio formato', 150],
    ['limpieza', 116],
    ['atasco', 78],
    ['falta material', 52],
    ['electrica', 30],
  ] as const
  bars.forEach(([name, width], index) => {
    const y = 62 + index * 32
    ctx.fillStyle = WEB_INK
    ctx.font = '9px "Space Mono", ui-monospace, monospace'
    ctx.fillText(name, 66, y - 3)
    ctx.fillStyle = index < 2 ? COFASA_BLUE : STEEL_DARK
    ctx.fillRect(66, y, width * grow, 12)
  })
  ctx.fillStyle = WEB_INK
  ctx.globalAlpha = 0.6
  ctx.font = '9px "Space Mono", ui-monospace, monospace'
  ctx.fillText('horas de linea perdidas por causa', 66, 224)
  ctx.globalAlpha = 1
}

/** Demo 3: disponibilidad — donut con el semaforo del dashboard. */
function drawDemoDisponibilidad(
  ctx: CanvasRenderingContext2D,
  size: number,
  t: number,
): void {
  webChrome(ctx, size, 'Monitoreo de Produccion')
  ctx.fillStyle = WEB_INK
  ctx.font = 'bold 12px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('Disponibilidad · linea 2', 66, 44)
  const frac = 0.87 * Math.min(1, ((t * 0.9) % 5) / 1.3)
  const cx = 150
  const cy = 124
  const start = -Math.PI / 2
  ctx.lineWidth = 18
  ctx.strokeStyle = ANDON_GREEN
  ctx.beginPath()
  ctx.arc(cx, cy, 46, start, start + Math.PI * 2 * frac)
  ctx.stroke()
  ctx.strokeStyle = ANDON_RED
  ctx.globalAlpha = 0.75
  ctx.beginPath()
  ctx.arc(
    cx,
    cy,
    46,
    start + Math.PI * 2 * Math.max(frac, 0.02),
    start + Math.PI * 2,
  )
  ctx.stroke()
  ctx.globalAlpha = 1
  ctx.fillStyle = WEB_INK
  ctx.font = 'bold 20px "Space Grotesk", system-ui, sans-serif'
  ctx.textAlign = 'center'
  ctx.fillText(`${Math.round(frac * 100)}%`, cx, cy + 7)
  ctx.textAlign = 'left'
  ctx.font = '9px "Space Mono", ui-monospace, monospace'
  ctx.fillStyle = ANDON_GREEN
  ctx.fillText('■ operando', 66, 204)
  ctx.fillStyle = ANDON_RED
  ctx.fillText('■ detenida (por causa)', 66, 218)
}

/** Los 3 mockups HTML del panel operable (panel admin 2017). */
function showcaseDemos(): ShowcaseDemo[] {
  const chrome = (title: string): string =>
    '<div style="background:#1560bd;color:#fff;padding:.45rem .6rem;' +
    `font-weight:700">${title}</div>` +
    '<div style="background:#f4f5f7;color:#1c2430;padding:.2rem .6rem;' +
    'font-size:.8rem;border-bottom:1px solid #c8ccd2">Inicio&nbsp;&nbsp;' +
    '<strong>Paradas</strong>&nbsp;&nbsp;Reportes&nbsp;&nbsp;Usuarios</div>'
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
  const bar = (width: number, blue: boolean): string =>
    `<div style="background:${blue ? '#1560bd' : '#7a8088'};height:.65rem;` +
    `width:${width}%;margin:.15rem 0"></div>`
  return [
    {
      key: 'evento',
      title: {
        es: 'Registrar parada',
        en: 'Log a stoppage',
      },
      draw: drawDemoEvento,
      panel: {
        brand: COFASA_BLUE,
        html: {
          es:
            chrome('Monitoreo de Produccion · Registrar parada') +
            '<p style="margin:.6rem 0 .3rem"><strong>Linea:</strong> ' +
            'Llenadora de ampollas L-2 (lote Miovit MV-1807)</p>' +
            '<input placeholder="Causa: atasco / cambio de formato / ' +
            'limpieza / falta de material...">' +
            gridTable(
              ['Inicio', 'Fin', 'Causa', 'Registro'],
              [
                ['10:42', '—', 'atasco mecanico', 'nguerra'],
                ['10:12', '10:30', 'limpieza', 'nguerra'],
                ['08:55', '09:31', 'cambio de formato', 'rescalona'],
              ],
            ) +
            '<p style="opacity:.7;margin:.5rem 0 0">La hora la pone el ' +
            'sistema y el registro queda con nombre — antes: la libreta ' +
            'y el reloj de pulsera de la supervisora. Web en la red ' +
            'LOCAL de la planta, login por empleado (jQuery + Laravel, ' +
            '2017)</p>',
          en:
            chrome('Production Monitoring · Log a stoppage') +
            '<p style="margin:.6rem 0 .3rem"><strong>Line:</strong> ' +
            'Ampoule filler L-2 (Miovit batch MV-1807)</p>' +
            '<input placeholder="Cause: jam / changeover / cleaning / ' +
            'missing material...">' +
            gridTable(
              ['Start', 'End', 'Cause', 'Logged by'],
              [
                ['10:42', '—', 'mechanical jam', 'nguerra'],
                ['10:12', '10:30', 'cleaning', 'nguerra'],
                ['08:55', '09:31', 'changeover', 'rescalona'],
              ],
            ) +
            '<p style="opacity:.7;margin:.5rem 0 0">The system stamps ' +
            'the time and every entry has a name — before: the ' +
            'supervisor’s notebook and wristwatch. Web app on the ' +
            'plant’s LOCAL network, per-employee login (jQuery + ' +
            'Laravel, 2017)</p>',
        },
      },
    },
    {
      key: 'pareto',
      title: {
        es: 'Paradas por causa',
        en: 'Downtime by cause',
      },
      draw: drawDemoPareto,
      panel: {
        brand: COFASA_BLUE,
        html: {
          es:
            chrome('Monitoreo de Produccion · Paradas por causa') +
            '<p style="margin:.6rem 0 .3rem"><strong>Horas de linea ' +
            'perdidas por causa (mes)</strong></p>' +
            `<p style="margin:0">cambio de formato${bar(84, true)}</p>` +
            `<p style="margin:0">limpieza / sanitizacion${bar(64, true)}</p>` +
            `<p style="margin:0">atasco mecanico${bar(42, false)}</p>` +
            `<p style="margin:0">falta de material${bar(28, false)}</p>` +
            `<p style="margin:0">falla electrica${bar(16, false)}</p>` +
            '<p style="opacity:.7;margin:.5rem 0 0">La vista que dio ' +
            'visibilidad POR PRIMERA VEZ a las causas mas frecuentes: ' +
            'arriba quedaron el cambio de formato y la limpieza — no ' +
            'las fallas. Con eso produccion priorizo lotes y ' +
            'sanitizacion programada</p>',
          en:
            chrome('Production Monitoring · Downtime by cause') +
            '<p style="margin:.6rem 0 .3rem"><strong>Line hours lost ' +
            'by cause (month)</strong></p>' +
            `<p style="margin:0">changeover${bar(84, true)}</p>` +
            `<p style="margin:0">cleaning / sanitisation${bar(64, true)}</p>` +
            `<p style="margin:0">mechanical jam${bar(42, false)}</p>` +
            `<p style="margin:0">missing material${bar(28, false)}</p>` +
            `<p style="margin:0">power failure${bar(16, false)}</p>` +
            '<p style="opacity:.7;margin:.5rem 0 0">The view that gave ' +
            'visibility to the most frequent causes FOR THE FIRST ' +
            'TIME: changeover and cleaning came out on top — not ' +
            'breakdowns. Production used it to prioritise batches and ' +
            'scheduled sanitisation</p>',
        },
      },
    },
    {
      key: 'disponibilidad',
      title: {
        es: 'Disponibilidad',
        en: 'Line availability',
      },
      draw: drawDemoDisponibilidad,
      panel: {
        brand: COFASA_BLUE,
        html: {
          es:
            chrome('Monitoreo de Produccion · Disponibilidad') +
            '<p style="font-size:1.5rem;margin:.6rem 0 .2rem">' +
            '<strong>87%</strong> disponibilidad — linea 2 (demo)</p>' +
            '<p style="margin:0 0 .4rem;opacity:.85"><code>' +
            'disponibilidad = tiempo operando / tiempo total</code></p>' +
            gridTable(
              ['Indicador', 'Antes', 'Con el sistema'],
              [
                [
                  'reporte de productividad',
                  'varias horas a mano',
                  'consulta directa',
                ],
                ['causas de parada', 'nadie las media', 'contadas y ordenadas'],
                ['registro', 'planillas de papel', 'digital, centralizado'],
              ],
            ) +
            '<p style="opacity:.7;margin:.5rem 0 0">El semaforo ' +
            'verde/rojo del dashboard habla el mismo idioma que la ' +
            'torre andon de la linea. En uso productivo casi 2 años ' +
            '(2017-18)</p>',
          en:
            chrome('Production Monitoring · Availability') +
            '<p style="font-size:1.5rem;margin:.6rem 0 .2rem">' +
            '<strong>87%</strong> availability — line 2 (demo)</p>' +
            '<p style="margin:0 0 .4rem;opacity:.85"><code>' +
            'availability = running time / total time</code></p>' +
            gridTable(
              ['Indicator', 'Before', 'With the system'],
              [
                ['productivity report', 'hours by hand', 'direct query'],
                ['stoppage causes', 'nobody measured', 'counted and ranked'],
                ['logging', 'paper sheets', 'digital, centralised'],
              ],
            ) +
            '<p style="opacity:.7;margin:.5rem 0 0">The dashboard’s ' +
            'green/red traffic light speaks the same language as the ' +
            'line’s andon tower. In productive use for almost 2 ' +
            'years (2017-18)</p>',
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
      id: `micro-cofasa-${roomIndex}-laptop${toggle.spot}`,
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

export default function buildCofasa(ctx: RoomCtx): RoomBuild {
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

  // rincon de desarrollo del canon: 3 puestos con laptops de la epoca;
  // Yorman y Douglas trabajan en las suyas, la tercera se enciende con E
  const deskSpots: readonly (readonly [number, number])[] = [
    [-1.7, room.z - 3.7],
    [0.7, room.z - 4.2],
    [-0.5, room.z - 2.3],
  ]
  const office = officeLayout({
    spots: deskSpots,
    color: '#3d4f66',
    poweredSpots: new Set([0, 1]),
    screenTheme,
    screenFor: (index) => LAPTOP_SCREENS[index] ?? LAPTOP_SCREENS[0],
  })
  group.add(office.group)
  staticColliders.push(...office.colliders)
  disposables.push(office)
  interactables.push(...laptopToggles(office, deskSpots, room.index))

  // tanque de mezcla inox (-X, esquina fondo): cilindro + valvulas +
  // tuberia hacia la llenadora
  const units = unitGeo()
  const tank = new Mesh(units.cylinder, toonMat('#b8bcc0'))
  tank.scale.set(1.1, 1.7, 1.1)
  tank.position.set(-half + 1.2, 0.85, room.z - 5.3)
  tank.castShadow = true
  group.add(
    tank,
    outlinedMergedBoxes(
      [
        // valvulas + patas del tanque
        { w: 0.14, h: 0.14, d: 0.3, x: -half + 1.2, y: 0.5, z: room.z - 4.72 },
        { w: 0.3, h: 0.14, d: 0.14, x: -half + 1.76, y: 1.1, z: room.z - 5.3 },
        // tuberia: baja del tanque y corre hacia la llenadora
        { w: 0.1, h: 0.6, d: 0.1, x: -half + 1.2, y: 2.0, z: room.z - 5.3 },
        { w: 0.1, h: 0.1, d: 1.2, x: -half + 1.2, y: 2.3, z: room.z - 4.7 },
        { w: 0.1, h: 0.9, d: 0.1, x: -half + 1.2, y: 1.9, z: room.z - 4.15 },
        // banda de ampollas: tablero (fusionado aqui — mismo material,
        // C15: un batch STEEL_DARK menos = -2 draw calls)
        { w: 0.8, h: 0.08, d: 2.6, x: -half + 1.6, y: 0.72, z: room.z - 1.7 },
      ],
      toonMat(STEEL_DARK),
      { castShadow: true },
    ),
  )
  staticColliders.push(footprint(-half + 1.2, room.z - 5.3, 1.3, 1.3))
  const tankLabel = label(locale === 'es' ? 'MEZCLA' : 'MIXING', {
    size: 0.14,
    color: theme.accent,
  })
  tankLabel.position.set(-half + 1.2, 2.2, room.z - 4.55)
  tankLabel.rotation.y = Math.PI / 2
  group.add(tankLabel)

  // llenadora de ampollas (-X, fondo-medio): cuerpo inox + tolva +
  // cabezal sobre la banda — la maquina que corre Miovit
  group.add(
    outlinedMergedBoxes(
      [
        { w: 1.1, h: 1.5, d: 0.9, x: -half + 1.6, y: 0.75, z: room.z - 3.9 },
        { w: 0.5, h: 0.4, d: 0.5, x: -half + 1.6, y: 1.7, z: room.z - 3.9 },
        // cabezal de llenado que cuelga sobre la banda
        { w: 0.3, h: 0.24, d: 0.3, x: -half + 1.6, y: 1.28, z: room.z - 3.25 },
        {
          w: 0.08,
          h: 0.34,
          d: 0.08,
          x: -half + 1.6,
          y: 1.05,
          z: room.z - 3.25,
        },
        // panel de control lateral
        {
          w: 0.34,
          h: 0.26,
          d: 0.06,
          x: -half + 2.18,
          y: 1.15,
          z: room.z - 3.9,
        },
        // linea de blisteres: mesa corta (fusionada aqui — mismo
        // material, C15: un batch STEEL menos = -2 draw calls)
        { w: 0.8, h: 0.76, d: 1.1, x: -half + 1.6, y: 0.38, z: room.z + 0.3 },
      ],
      toonMat(STEEL),
      { castShadow: true },
    ),
  )
  staticColliders.push(footprint(-half + 1.6, room.z - 3.9, 1.3, 1.1))

  // banda de ampollas: patas + fila de ampollas ambar saliendo de la
  // llenadora (el tablero viaja en el batch STEEL_DARK del tanque)
  group.add(
    mergedBoxes(
      [
        // patas de la banda
        { w: 0.08, h: 0.7, d: 0.08, x: -half + 1.3, y: 0.35, z: room.z - 2.8 },
        { w: 0.08, h: 0.7, d: 0.08, x: -half + 1.9, y: 0.35, z: room.z - 2.8 },
        { w: 0.08, h: 0.7, d: 0.08, x: -half + 1.3, y: 0.35, z: room.z - 0.6 },
        { w: 0.08, h: 0.7, d: 0.08, x: -half + 1.9, y: 0.35, z: room.z - 0.6 },
      ],
      toonMat(STEEL_DARK),
    ),
    // ampollas de vidrio ambar en fila sobre la banda
    mergedBoxes(
      Array.from({ length: 9 }, (_, i) => ({
        w: 0.07,
        h: 0.16,
        d: 0.07,
        x: -half + 1.45 + (i % 2) * 0.3,
        y: 0.84,
        z: room.z - 2.75 + i * 0.26,
      })),
      toonMat(AMBER),
    ),
  )
  staticColliders.push(footprint(-half + 1.6, room.z - 1.7, 1.0, 2.8))

  // linea de blisteres: los blisteres de aluminio saliendo (la mesa
  // corta viaja en el batch STEEL de la llenadora)
  group.add(
    mergedBoxes(
      Array.from({ length: 6 }, (_, i) => ({
        w: 0.2,
        h: 0.025,
        d: 0.13,
        x: -half + 1.38 + (i % 2) * 0.42,
        y: 0.79,
        z: room.z + 0.02 + Math.floor(i / 2) * 0.24,
        rotY: (i % 2) * 0.2,
      })),
      toonMat('#cfd3d6'),
    ),
  )
  staticColliders.push(footprint(-half + 1.6, room.z + 0.3, 1.0, 1.3))

  // cajas de producto Miovit apiladas al final de la linea (-X, frente)
  group.add(
    outlinedMergedBoxes(
      [
        { w: 0.5, h: 0.3, d: 0.34, x: -half + 1.3, y: 0.15, z: room.z + 1.7 },
        { w: 0.5, h: 0.3, d: 0.34, x: -half + 1.86, y: 0.15, z: room.z + 1.66 },
        { w: 0.5, h: 0.3, d: 0.34, x: -half + 1.56, y: 0.45, z: room.z + 1.72 },
        { w: 0.5, h: 0.3, d: 0.34, x: -half + 1.4, y: 0.75, z: room.z + 1.68 },
      ],
      toonMat(COFASA_BLUE),
      { inflate: 0.03, castShadow: true },
    ),
  )
  staticColliders.push(footprint(-half + 1.6, room.z + 1.7, 1.2, 0.7))
  const miovitLabel = label('MIOVIT', { size: 0.16, color: theme.accent })
  miovitLabel.position.set(-half + 1.5, 1.25, room.z + 1.7)
  miovitLabel.rotation.y = Math.PI / 2
  group.add(miovitLabel)

  // TORRE ANDON junto a la linea: el UNICO lugar con rojo/verde de la
  // sala (ademas del dashboard). E simula una parada: rojo + registro.
  const andonMats = {
    red: basicMat('#4a201c'),
    amber: basicMat('#6a5a1a'),
    green: basicMat(ANDON_GREEN),
  }
  const andonPole = outlinedMergedBoxes(
    [
      { w: 0.3, h: 0.06, d: 0.3, x: -3.3, y: 0.03, z: room.z - 2.4 },
      { w: 0.08, h: 1.1, d: 0.08, x: -3.3, y: 0.6, z: room.z - 2.4 },
    ],
    toonMat('#5a5f66'),
    { castShadow: true },
  )
  const andonGreen = boxMesh(0.2, 0.16, 0.2, andonMats.green)
  andonGreen.position.set(-3.3, 1.24, room.z - 2.4)
  andonGreen.userData.noOutline = true
  const andonAmber = boxMesh(0.2, 0.16, 0.2, andonMats.amber)
  andonAmber.position.set(-3.3, 1.42, room.z - 2.4)
  andonAmber.userData.noOutline = true
  const andonRed = boxMesh(0.2, 0.16, 0.2, andonMats.red)
  andonRed.position.set(-3.3, 1.6, room.z - 2.4)
  andonRed.userData.noOutline = true
  group.add(andonPole, andonGreen, andonAmber, andonRed)
  staticColliders.push(footprint(-3.3, room.z - 2.4, 0.4, 0.4))

  // monitor de linea junto al andon: registra la parada simulada con la
  // causa ciclando el catalogo real (mismo lenguaje verde/rojo)
  const causas =
    locale === 'es'
      ? (['atasco mecanico', 'cambio de formato', 'limpieza'] as const)
      : (['mechanical jam', 'changeover', 'cleaning'] as const)
  group.add(
    desk({
      position: [-2.2, 0, room.z - 2.45],
      width: 1.0,
      color: '#4a5560',
    }),
  )
  staticColliders.push(footprint(-2.2, room.z - 2.45, 1.1, 0.7))
  const lineaVariants: Record<
    string,
    { title: string; lines: string[]; theme: typeof screenTheme; dot: string }
  > = {
    run: {
      title: locale === 'es' ? 'linea 2 · Miovit' : 'line 2 · Miovit',
      lines:
        locale === 'es'
          ? [
              'estado: OPERANDO',
              'lote: MV-1807',
              'turno: mañana',
              'paradas hoy: 2',
            ]
          : [
              'status: RUNNING',
              'batch: MV-1807',
              'shift: morning',
              'stops today: 2',
            ],
      theme: screenTheme,
      dot: ANDON_GREEN,
    },
  }
  causas.forEach((causa, index) => {
    lineaVariants[`parada-${index}`] = {
      title: locale === 'es' ? 'PARADA · linea 2' : 'STOPPED · line 2',
      lines:
        locale === 'es'
          ? [
              `causa: ${causa}`,
              'inicio: 10:42:07',
              'registro: nguerra',
              'andon: ROJO',
            ]
          : [
              `cause: ${causa}`,
              'start: 10:42:07',
              'logged by: nguerra',
              'andon: RED',
            ],
      theme: screenTheme,
      dot: ANDON_RED,
    }
  })
  const linea = switchableMonitor({
    position: [-2.2, 0.72, room.z - 2.5],
    rotationY: 0,
    width: 0.58,
    variants: lineaVariants,
    initial: 'run',
  })
  group.add(linea.group)
  disposables.push(linea.screen)
  let causaIndex = 0
  let andonUntil = -1
  // la luz ambar queda tenue fija (solo verde<->rojo cambian de estado)
  const setAndon = (stopped: boolean): void => {
    andonMats.red.color.set(stopped ? ANDON_RED : '#4a201c')
    andonMats.green.color.set(stopped ? '#1c3a24' : ANDON_GREEN)
  }
  interactables.push({
    id: `micro-cofasa-andon-${room.index}`,
    x: -3.3,
    z: room.z - 2.4,
    radius: 2.0,
    label: ANDON_LABEL,
    onActivate: () => {
      linea.screen.show(`parada-${causaIndex}`)
      causaIndex = (causaIndex + 1) % causas.length
      setAndon(true)
      sfx.play('blip')
      andonUntil = -2 // pendiente: el proximo update fija el fin
    },
  })
  updates.push((t) => {
    if (andonUntil === -2) {
      andonUntil = t + 4
    }
    if (andonUntil > 0 && t > andonUntil) {
      andonUntil = -1
      setAndon(false)
      linea.screen.show('run')
    }
  })

  // mesa QC (+X, fondo): frascos, ampollas de muestra e instrumental
  group.add(
    desk({
      position: [half - 1.5, 0, room.z - 4.6],
      rotationY: Math.PI / 2,
      width: 1.5,
      color: '#4a5560',
    }),
    outlinedMergedBoxes(
      [
        // lupa de inspeccion: base + brazo + aro
        { w: 0.12, h: 0.05, d: 0.12, x: half - 1.4, y: 0.77, z: room.z - 4.9 },
        { w: 0.04, h: 0.3, d: 0.04, x: half - 1.4, y: 0.94, z: room.z - 4.9 },
        { w: 0.2, h: 0.2, d: 0.03, x: half - 1.4, y: 1.14, z: room.z - 4.86 },
        // frascos de reactivos
        { w: 0.1, h: 0.2, d: 0.1, x: half - 1.7, y: 0.85, z: room.z - 4.35 },
        {
          w: 0.08,
          h: 0.16,
          d: 0.08,
          x: half - 1.55,
          y: 0.83,
          z: room.z - 4.28,
        },
      ],
      toonMat('#c8ccd2'),
      { castShadow: true },
    ),
    // gradilla con ampollas de muestra
    mergedBoxes(
      Array.from({ length: 5 }, (_, i) => ({
        w: 0.06,
        h: 0.14,
        d: 0.06,
        x: half - 1.32,
        y: 0.83,
        z: room.z - 4.6 + (i - 2) * 0.1,
      })),
      toonMat(AMBER),
    ),
  )
  staticColliders.push(footprint(half - 1.5, room.z - 4.6, 0.9, 1.6))
  const qcLabel = label(
    locale === 'es' ? 'CONTROL DE CALIDAD' : 'QUALITY CONTROL',
    { size: 0.13, color: theme.accent },
  )
  qcLabel.position.set(half - 0.15, 1.95, room.z - 4.6)
  qcLabel.rotation.y = -Math.PI / 2
  group.add(qcLabel)

  // estanteria de registros de lote (+X, medio): carpetas blancas con
  // lomo azul — la documentacion cGMP de cada lote
  const shelfX = half - 0.55
  group.add(
    outlinedMergedBoxes(
      [
        { w: 0.5, h: 0.04, d: 1.7, x: shelfX, y: 0.6, z: room.z - 2.0 },
        { w: 0.5, h: 0.04, d: 1.7, x: shelfX, y: 1.15, z: room.z - 2.0 },
        { w: 0.5, h: 0.04, d: 1.7, x: shelfX, y: 1.7, z: room.z - 2.0 },
        { w: 0.5, h: 1.72, d: 0.05, x: shelfX, y: 0.86, z: room.z - 2.87 },
        { w: 0.5, h: 1.72, d: 0.05, x: shelfX, y: 0.86, z: room.z - 1.13 },
      ],
      toonMat('#c8ccd2'),
      { castShadow: true },
    ),
    mergedBoxes(
      Array.from({ length: 10 }, (_, i) => ({
        w: 0.3,
        h: 0.3,
        d: 0.09,
        x: shelfX,
        y: (i < 5 ? 0.62 : 1.17) + 0.15,
        z: room.z - 2.72 + (i % 5) * 0.34,
      })),
      toonMat('#e8e6e0'),
    ),
  )
  staticColliders.push(footprint(shelfX, room.z - 2.0, 0.7, 1.9))
  const lotesLabel = label(
    locale === 'es' ? 'REGISTROS DE LOTE' : 'BATCH RECORDS',
    { size: 0.13, color: theme.accent },
  )
  lotesLabel.position.set(shelfX - 0.1, 2.05, room.z - 2.0)
  lotesLabel.rotation.y = -Math.PI / 2
  group.add(lotesLabel)

  // guiño fino (decision del usuario): la planta real de la Urb.
  // Industrial Lebrun, Petare — etiqueta discreta sobre la puerta
  const plantaLabel = label('PLANTA LEBRUN · PETARE · CARACAS', {
    size: 0.11,
    color: theme.ink,
  })
  plantaLabel.position.set(0, 2.7, frontZ - 0.08)
  plantaLabel.rotation.y = Math.PI
  group.add(plantaLabel)

  // cuadros de rubro (wallArt): envasado, Pareto de causas y
  // disponibilidad inspeccionables (3 fichas — decision del usuario);
  // poster cGMP decorativo junto a la puerta
  const art = wallArt({
    roomIndex: room.index,
    theme,
    locale,
    onFicha: actions.openStory,
    frames: [
      {
        key: 'envasado-inyectables',
        position: [-3.6, 2, backZ + 0.08],
        rotationY: 0,
        draw: drawEnvasado,
        ficha: ART_FICHA_ENVASADO,
      },
      {
        key: 'paradas-por-causa',
        position: [3.6, 2, backZ + 0.08],
        rotationY: 0,
        draw: drawPareto,
        ficha: ART_FICHA_PARETO,
      },
      {
        key: 'disponibilidad',
        position: [-3.6, 2, frontZ - 0.08],
        rotationY: Math.PI,
        draw: drawDisponibilidad,
        ficha: ART_FICHA_DISPONIBILIDAD,
      },
      {
        key: 'cgmp',
        position: [3.6, 2, frontZ - 0.08],
        rotationY: Math.PI,
        draw: drawCGMP,
      },
    ],
  })
  staticColliders.push(...art.colliders)
  const sink = { group, interactables, updates }
  addProps(sink, art.props)

  // showcase del software junto a la puerta al pasillo (canon AC-6):
  // panel admin web 2017 — E cicla las 3 demos
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

  // NPCs del canon (2 enfoques, informe 10): Yorman y Douglas (devs,
  // sentados en sus laptops), Nelida (supervisora en ronda entre la
  // linea y el frente), Rafael (operario con cofia en la llenadora) y
  // Carmen (jefa de produccion supervisando QC).
  const coworkers = npcCoworkers({
    roomIndex: room.index,
    openDialog: actions.openDialog,
    npcs: [
      {
        key: 'yorman',
        role: 'coworker',
        spec: {
          skin: '#c98f6a',
          hair: { style: 'short', color: '#1a140e' },
          top: '#3f5a73',
          bottom: '#2e3238',
          accessory: 'badge',
          faceSeed: 21,
        },
        position: [-1.7, 0, room.z - 5.05],
        rotationY: 0,
        pose: 'sit',
        dialog: COFASA_PRESENTE_DIALOGS.yorman,
      },
      {
        key: 'douglas',
        role: 'coworker',
        spec: {
          skin: '#8a5a3c',
          hair: { style: 'spiky', color: '#10100c' },
          top: '#4a5a72',
          bottom: '#3a4048',
          accessory: 'glasses',
          faceSeed: 64,
        },
        position: [0.7, 0, room.z - 5.05],
        rotationY: 0,
        pose: 'sit',
        dialog: COFASA_PRESENTE_DIALOGS.douglas,
      },
      {
        key: 'nelida',
        role: 'staff',
        spec: {
          skin: '#d9a684',
          hair: { style: 'bun', color: '#2a1a12' },
          top: '#eef0ec',
          bottom: '#5a6a78',
          accessory: 'badge',
          faceSeed: 42,
        },
        position: [-2.6, 0, room.z - 0.8],
        path: [
          [-2.6, room.z - 0.8],
          [1.6, room.z + 1.6],
          [-1.0, room.z + 3.4],
        ],
        speed: 0.55,
        dialog: COFASA_PRESENTE_DIALOGS.nelida,
      },
      {
        key: 'rafael',
        role: 'staff',
        spec: {
          skin: '#b5825f',
          // el "bun" blanco lee como la cofia de sala limpia
          hair: { style: 'bun', color: '#f0f2f4' },
          top: '#f0eee8',
          bottom: '#c8ccd2',
          accessory: 'badge',
          faceSeed: 77,
        },
        position: [-3.7, 0, room.z - 3.9],
        rotationY: -Math.PI / 2,
        dialog: COFASA_PRESENTE_DIALOGS.rafael,
      },
      {
        key: 'carmen',
        role: 'boss',
        spec: {
          skin: '#e8b48c',
          hair: { style: 'ponytail', color: '#2c1e14' },
          top: '#f0eee8',
          bottom: '#3a4048',
          accessory: 'tie',
          faceSeed: 96,
        },
        position: [half - 2.4, 0, room.z - 3.6],
        rotationY: -1.2,
        dialog: COFASA_PRESENTE_DIALOGS.carmen,
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
