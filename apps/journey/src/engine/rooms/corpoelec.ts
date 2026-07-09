/**
 * @module rooms/corpoelec (engine)
 * @description Sala 1 — CORPOELEC (central electrica estatal, VE, 2013),
 *   refactorizada al CANON de sala (plan journey-salas-estandar, informe
 *   08): `officeLayout` con laptops de la epoca (2 encendidas por los
 *   devs, 2 togglables con E), 5 NPCs conversables con los 2 enfoques
 *   (`npcCoworkers`: Yorman y Genesis devs, Wilmer almacenista, Dubraska
 *   administrativa, Ing. Betancourt jefe), cuadros de rubro (`wallArt`:
 *   lineas 765/400/230 kV y transformador 40 MVA inspeccionables, Guri y
 *   mapa de 3 sedes decorativos) y el `softwareShowcase` junto a la
 *   puerta con 3 demos del sistema real (grid DataTables, buscador
 *   "quien lo tomo", reporte de incidencias — estetica intranet 2013 +
 *   badge OFFLINE). Props firma: fila de transformadores TX-001,
 *   estanteria de inventario con equipos 2013 en cajas etiquetadas
 *   (walkie-talkies, radios base, telefonos, PC, laptops, tablets),
 *   bobinas, aisladores y lineas amarillas de seguridad en el piso.
 *   Micros heredados: tablero rojo <-> verde (energiza el monitor
 *   OFFLINE -> ONLINE) y buscar el equipo 0042 (papel lento vs sistema
 *   inmediato). Kit informativo ESTANDAR (`infoKit`) en las posiciones
 *   canonicas. Paredes blanco hueso; el rubro vive en piso/props/luz.
 */
import { Group, Mesh, PointLight } from 'three'
import type { Box2 } from '../../lib/collision'
import type { Locale } from '../../lib/rooms'
import { sfx } from '../audio'
import type { NpcHandle } from '../character'
import { CORPOELEC_PRESENTE_DIALOGS } from '../dialogs/corpoelec-presente'
import type { Interactable } from '../state'
import {
  boxMesh,
  disposeDeep,
  label,
  mergedBoxes,
  outlinedMergedBoxes,
  outlineGroup,
  toonMat,
  toonMatOwn,
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
  paperStack,
  type ShowcaseDemo,
  softwareShowcase,
  switchableMonitor,
  wallArt,
} from './props'

const BOARD_LABEL_ON = {
  es: 'Energizar el tablero de control',
  en: 'Power up the control board',
} as const

const BOARD_LABEL_OFF = {
  es: 'Cortar el tablero de control',
  en: 'Power down the control board',
} as const

const SEARCH_LABEL = {
  es: 'Buscar el equipo 0042',
  en: 'Look up asset 0042',
} as const

const LAPTOP_LABELS = {
  on: { es: 'Encender la laptop libre', en: 'Power on the spare laptop' },
  off: { es: 'Apagar la laptop libre', en: 'Power off the spare laptop' },
} as const

/** Pantallas era-2013 de las laptops del officeLayout, por puesto. */
const LAPTOP_SCREENS = [
  {
    title: 'equipos.php — PHP',
    lines: [
      '$rs = mysql_query(',
      "  'SELECT * FROM equipos');",
      'while ($eq = fetch($rs))',
      '  guardarOffline($eq);',
    ],
  },
  {
    title: 'guia_sede.pdf',
    lines: [
      'GUIA RAPIDA — SEDE',
      '1. registrar el equipo',
      '2. asignar responsable',
      '3. sin red: seguir igual',
    ],
  },
  {
    title: 'respaldo.sql — sync',
    lines: [
      'pendientes en cola: 14',
      'yaracuy  -> base comun',
      'carabobo -> base comun',
      'lara: sin red (cola OK)',
    ],
  },
  {
    title: 'inventario.js — jQuery',
    lines: [
      "$('#tabla').on('click',",
      "  'tr', mostrarEquipo)",
      "$.get('/api/equipos',",
      '  pintarTabla) // 2013',
    ],
  },
] as const

/** Transformador: caja gris + aletas + 3 bujes ceramicos (primitivas). */
function transformer(position: readonly [number, number, number]): Group {
  const group = new Group()
  group.position.set(position[0], position[1], position[2])
  const body = boxMesh(1.3, 1.4, 0.9, toonMat('#5c6168'))
  body.position.y = 0.7
  body.castShadow = true
  group.add(body)
  const units = unitGeo()
  for (const x of [-0.5, 0, 0.5]) {
    const bushing = new Mesh(units.cylinder, toonMat('#b8b4a8'))
    bushing.scale.set(0.17, 0.35, 0.17)
    bushing.position.set(x, 1.55, 0)
    group.add(bushing)
  }
  for (const x of [-0.72, 0.72]) {
    const fin = boxMesh(0.12, 1.2, 0.7, toonMat('#4c5057'))
    fin.position.set(x, 0.7, 0)
    group.add(fin)
  }
  return group
}

// --- laminas de los cuadros (wallArt): tinta plana sobre papel claro ---

const ART_PAPER = '#f4efe2'
const ART_INK = '#1c1f26'
const ART_ORANGE = '#e2572b'
const ART_YELLOW = '#f2b705'

function artBase(ctx: CanvasRenderingContext2D, size: number): void {
  ctx.fillStyle = ART_PAPER
  ctx.fillRect(0, 0, size, size)
  ctx.strokeStyle = ART_INK
  ctx.globalAlpha = 0.35
  ctx.lineWidth = 3
  ctx.strokeRect(10, 10, size - 20, size - 20)
  ctx.globalAlpha = 1
}

/** Torres de celosia con las 3 lineas troncales rotuladas (765/400/230). */
function drawLineasTransmision(
  ctx: CanvasRenderingContext2D,
  size: number,
): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 17px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('LINEAS DE TRANSMISION', 24, 38)
  ctx.strokeStyle = ART_INK
  ctx.lineWidth = 4
  ctx.lineCap = 'round'
  for (const cx of [70, 186]) {
    ctx.beginPath()
    ctx.moveTo(cx - 24, 216)
    ctx.lineTo(cx, 70)
    ctx.lineTo(cx + 24, 216)
    ctx.moveTo(cx - 26, 118)
    ctx.lineTo(cx + 26, 118)
    ctx.moveTo(cx - 20, 92)
    ctx.lineTo(cx + 20, 92)
    ctx.stroke()
  }
  ctx.lineWidth = 2
  for (const [y, labelKv] of [
    [92, '765 kV'],
    [118, '400 kV'],
    [146, '230 kV'],
  ] as const) {
    ctx.beginPath()
    ctx.moveTo(70, y)
    ctx.quadraticCurveTo(128, y + 26, 186, y)
    ctx.stroke()
    ctx.fillStyle = ART_ORANGE
    ctx.font = 'bold 13px "Space Mono", ui-monospace, monospace'
    ctx.fillText(labelKv, 108, y + 20)
    ctx.fillStyle = ART_INK
  }
  ctx.globalAlpha = 0.6
  ctx.font = '12px "Space Mono", ui-monospace, monospace'
  ctx.fillText('sistema troncal nacional', 24, 234)
  ctx.globalAlpha = 1
}

/** Corte de transformador de potencia 40 MVA + triangulo de riesgo. */
function drawTransformador(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 17px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('TRANSFORMADOR', 24, 38)
  ctx.strokeStyle = ART_INK
  ctx.lineWidth = 3
  ctx.strokeRect(78, 110, 100, 84)
  for (const x of [64, 192]) {
    ctx.beginPath()
    ctx.moveTo(x, 122)
    ctx.lineTo(x, 182)
    ctx.stroke()
    ctx.beginPath()
    ctx.moveTo(x === 64 ? 78 : 178, 136)
    ctx.lineTo(x, 136)
    ctx.moveTo(x === 64 ? 78 : 178, 168)
    ctx.lineTo(x, 168)
    ctx.stroke()
  }
  for (const x of [98, 128, 158]) {
    ctx.beginPath()
    ctx.moveTo(x, 110)
    ctx.lineTo(x, 76)
    ctx.stroke()
    ctx.beginPath()
    ctx.arc(x, 70, 6, 0, Math.PI * 2)
    ctx.stroke()
  }
  ctx.fillStyle = ART_ORANGE
  ctx.font = 'bold 15px "Space Mono", ui-monospace, monospace'
  ctx.fillText('40 MVA', 104, 152)
  ctx.fillStyle = ART_INK
  ctx.font = '12px "Space Mono", ui-monospace, monospace'
  ctx.globalAlpha = 0.6
  ctx.fillText('activo TX-001 · deposito B-3', 24, 226)
  ctx.globalAlpha = 1
  // triangulo de riesgo electrico (señaletica del rubro)
  ctx.strokeStyle = ART_YELLOW
  ctx.fillStyle = ART_YELLOW
  ctx.lineWidth = 4
  ctx.beginPath()
  ctx.moveTo(206, 206)
  ctx.lineTo(230, 206)
  ctx.lineTo(218, 184)
  ctx.closePath()
  ctx.stroke()
  ctx.strokeStyle = ART_INK
  ctx.lineWidth = 3
  ctx.beginPath()
  ctx.moveTo(219, 190)
  ctx.lineTo(215, 199)
  ctx.lineTo(219, 199)
  ctx.lineTo(215, 206)
  ctx.stroke()
}

/** Silueta de la represa del Guri (Central Simon Bolivar) + turbina. */
function drawGuri(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 17px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('CENTRAL SIMON BOLIVAR', 24, 38)
  ctx.strokeStyle = ART_INK
  ctx.lineWidth = 4
  ctx.beginPath()
  ctx.moveTo(30, 190)
  ctx.quadraticCurveTo(128, 92, 226, 190)
  ctx.stroke()
  ctx.lineWidth = 2
  for (const x of [70, 100, 130, 160, 190]) {
    ctx.beginPath()
    ctx.moveTo(x, 190)
    ctx.lineTo(x, 148 - Math.abs(128 - x) * 0.3)
    ctx.stroke()
  }
  ctx.strokeStyle = ART_ORANGE
  ctx.beginPath()
  ctx.arc(128, 214, 14, 0, Math.PI * 2)
  ctx.stroke()
  ctx.beginPath()
  for (let i = 0; i < 4; i += 1) {
    const a = (i / 4) * Math.PI * 2
    ctx.moveTo(128, 214)
    ctx.lineTo(128 + Math.cos(a) * 12, 214 + Math.sin(a) * 12)
  }
  ctx.stroke()
  ctx.fillStyle = ART_INK
  ctx.globalAlpha = 0.6
  ctx.font = '12px "Space Mono", ui-monospace, monospace'
  ctx.fillText('represa del Guri', 92, 116)
  ctx.globalAlpha = 1
}

/** Mapa low-poly de Venezuela con las 3 sedes del despliegue. */
function drawMapaSedes(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 17px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('DESPLIEGUE · 3 ESTADOS', 24, 38)
  ctx.strokeStyle = ART_INK
  ctx.lineWidth = 3
  ctx.beginPath()
  ctx.moveTo(46, 96)
  ctx.lineTo(96, 74)
  ctx.lineTo(160, 80)
  ctx.lineTo(214, 96)
  ctx.lineTo(206, 150)
  ctx.lineTo(168, 196)
  ctx.lineTo(112, 188)
  ctx.lineTo(66, 160)
  ctx.closePath()
  ctx.stroke()
  const sedes: readonly (readonly [number, number, string])[] = [
    [96, 118, 'YARACUY'],
    [130, 104, 'CARABOBO'],
    [76, 136, 'LARA'],
  ]
  ctx.font = 'bold 11px "Space Mono", ui-monospace, monospace'
  for (const [x, y, name] of sedes) {
    ctx.fillStyle = ART_ORANGE
    ctx.beginPath()
    ctx.arc(x, y, 5, 0, Math.PI * 2)
    ctx.fill()
    ctx.fillStyle = ART_INK
    ctx.fillText(name, x + 9, y + 4)
  }
  ctx.globalAlpha = 0.6
  ctx.font = '12px "Space Mono", ui-monospace, monospace'
  ctx.fillText('una base comun, modo offline', 24, 226)
  ctx.globalAlpha = 1
}

const ART_FICHA_LINEAS = {
  title: {
    es: 'El sistema troncal (765 / 400 / 230 kV)',
    en: 'The transmission backbone (765 / 400 / 230 kV)',
  },
  paragraphs: {
    es: [
      'CORPOELEC opera el Sistema Electrico Nacional de Venezuela: ' +
        'generacion, transmision y distribucion, con la Central ' +
        'Hidroelectrica Simon Bolivar (Guri) como emblema y un troncal ' +
        'de transmision en tres niveles: 765, 400 y 230 kV.',
      'La operacion diaria vive de subestaciones, transformadores y ' +
        'cuadrillas en campo. Cada repuesto importa: una falla sin ' +
        'repuesto ubicable puede dejar media region a oscuras.',
      'El sistema que Pablo construyo en 2013 rastreaba justamente eso: ' +
        'que equipo existe, donde esta y quien lo tiene, en tres estados ' +
        'a la vez.',
    ],
    en: [
      'CORPOELEC runs Venezuela’s National Electric System: ' +
        'generation, transmission and distribution, with the Simon ' +
        'Bolivar Hydroelectric Plant (Guri) as its emblem and a ' +
        'transmission backbone on three levels: 765, 400 and 230 kV.',
      'Daily operations live on substations, transformers and field ' +
        'crews. Every spare matters: a fault without a locatable spare ' +
        'can leave half a region in the dark.',
      'The system Pablo built in 2013 tracked exactly that: which ' +
        'equipment exists, where it sits and who holds it, across three ' +
        'states at once.',
    ],
  },
} as const

const ART_FICHA_TRAFO = {
  title: {
    es: 'Transformador de potencia (40 MVA)',
    en: 'Power transformer (40 MVA)',
  },
  paragraphs: {
    es: [
      'El transformador de potencia es el corazon de una subestacion: ' +
        'sube y baja la tension entre las lineas y la red local. Los de ' +
        'este tamaño se miden en decenas de MVA y se cuidan como oro.',
      'Cuidarlos exige saber QUE repuestos hay y DONDE estan: bujes, ' +
        'aceite, medidores. Antes de 2013 esa respuesta vivia en ' +
        'planillas de papel duplicadas entre sedes — localizar un ' +
        'repuesto podia costar una mañana entera.',
      'Con el inventario digital de Pablo, cada activo quedo etiquetado ' +
        '(TX-001, RAD-014...) y la busqueda paso de aproximadamente 20 ' +
        'minutos de carpetas a una consulta inmediata.',
    ],
    en: [
      'The power transformer is the heart of a substation: it steps ' +
        'voltage up and down between the lines and the local grid. Ones ' +
        'this size are measured in tens of MVA and treated like gold.',
      'Caring for them means knowing WHICH spares exist and WHERE they ' +
        'are: bushings, oil, meters. Before 2013 that answer lived in ' +
        'paper records duplicated across sites — locating a spare ' +
        'could cost an entire morning.',
      'With the digital inventory Pablo built, every asset got a tag ' +
        '(TX-001, RAD-014...) and lookups went from roughly 20 minutes ' +
        'of folders to an immediate query.',
    ],
  },
} as const

// --- demos del showcase: estetica intranet 2013 (PHP + jQuery) ---

/** Cabecera naranja CORPOELEC + badge OFFLINE de las demos del monitor. */
function demoHeader(
  ctx: CanvasRenderingContext2D,
  size: number,
  title: string,
): void {
  ctx.fillStyle = '#f0efe8'
  ctx.fillRect(0, 0, size, size)
  ctx.fillStyle = ART_ORANGE
  ctx.fillRect(0, 0, size, 34)
  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 15px "Space Grotesk", system-ui, sans-serif'
  ctx.textAlign = 'left'
  ctx.textBaseline = 'alphabetic'
  ctx.fillText(title, 10, 23)
  ctx.fillStyle = '#8a1f1f'
  ctx.fillRect(size - 74, 8, 64, 19)
  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('OFFLINE', 178 + 12, 22)
}

/** Demo 1: grid de inventario estilo DataTables con fila resaltada. */
function drawDemoGrid(
  ctx: CanvasRenderingContext2D,
  size: number,
  t: number,
): void {
  demoHeader(ctx, size, 'CORPOELEC · Inventario')
  const rows = [
    'TX-001  Transformador  Yaracuy',
    'RAD-014 Radio portatil Carabobo',
    'PC-207  Computadora    Lara',
    'AIS-090 Aislador       Yaracuy',
  ] as const
  ctx.fillStyle = '#d8d4c8'
  ctx.fillRect(8, 44, size - 16, 22)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 12px "Space Mono", ui-monospace, monospace'
  ctx.fillText('CODIGO  EQUIPO         SEDE', 14, 59)
  const active = Math.floor(t * 0.7) % rows.length
  rows.forEach((row, index) => {
    const y = 70 + index * 26
    if (index === active) {
      ctx.fillStyle = '#f5c9b4'
      ctx.fillRect(8, y, size - 16, 24)
    }
    ctx.fillStyle = ART_INK
    ctx.font = '12px "Space Mono", ui-monospace, monospace'
    ctx.fillText(row, 14, y + 16)
  })
  ctx.fillStyle = ART_INK
  ctx.globalAlpha = 0.6
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('1-4 de 1.248 · pag 1/312', 14, 196)
  ctx.globalAlpha = 1
}

/** Demo 2: buscador "quien lo tomo" con tipeo animado + ficha. */
function drawDemoBuscar(
  ctx: CanvasRenderingContext2D,
  size: number,
  t: number,
): void {
  demoHeader(ctx, size, 'Buscar equipo')
  const query = 'TX-001'
  const typed = query.slice(
    0,
    Math.min(query.length, Math.floor((t * 2.4) % (query.length + 4))),
  )
  ctx.strokeStyle = ART_INK
  ctx.lineWidth = 2
  ctx.strokeRect(10, 46, size - 20, 26)
  ctx.fillStyle = ART_INK
  ctx.font = '14px "Space Mono", ui-monospace, monospace'
  const caret = Math.floor(t * 3) % 2 === 0 ? '_' : ' '
  ctx.fillText(`> ${typed}${caret}`, 16, 64)
  ctx.font = '12px "Space Mono", ui-monospace, monospace'
  const lines = [
    'TX-001 · Transformador',
    'estado: OPERATIVO',
    'sede: Yaracuy · dep. B-3',
    'responsable: J. Perez',
    'historial: 3 asignaciones',
    'consulta: 0,2 s',
  ] as const
  lines.forEach((line, index) => {
    ctx.fillStyle = index === 5 ? ART_ORANGE : ART_INK
    ctx.fillText(line, 14, 96 + index * 20)
  })
}

/** Demo 3: reporte de incidencias — barras por sede animadas. */
function drawDemoReporte(
  ctx: CanvasRenderingContext2D,
  size: number,
  t: number,
): void {
  demoHeader(ctx, size, 'Equipos por sede')
  const sedes = [
    ['YARACUY', 118],
    ['CARABOBO', 96],
    ['LARA', 74],
  ] as const
  sedes.forEach(([name, base], index) => {
    const x = 26 + index * 76
    const height = base + Math.sin(t * 1.4 + index * 2.1) * 6
    ctx.fillStyle = index === 1 ? ART_ORANGE : '#8a8f98'
    ctx.fillRect(x, 190 - height, 44, height)
    ctx.fillStyle = ART_INK
    ctx.font = 'bold 10px "Space Mono", ui-monospace, monospace'
    ctx.fillText(name, x - 2, 206)
    ctx.font = '12px "Space Mono", ui-monospace, monospace'
    ctx.fillText(String(Math.round(height * 3.4)), x + 10, 186 - height)
  })
  ctx.fillStyle = ART_INK
  ctx.globalAlpha = 0.6
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('incidencias del mes: 12', 14, 218)
  ctx.globalAlpha = 1
}

/** Los 3 mockups HTML del panel operable (branding intranet 2013). */
function showcaseDemos(): ShowcaseDemo[] {
  const header = (title: string): string =>
    '<div style="background:#e2572b;color:#fff;padding:.5rem .7rem;' +
    'font-weight:700">' +
    `${title}<span style="float:right;background:#8a1f1f;` +
    'padding:0 .45rem;border-radius:3px;font-size:.75rem;' +
    'line-height:1.5rem">OFFLINE</span></div>'
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
      key: 'grid',
      title: {
        es: 'Inventario de equipos',
        en: 'Equipment inventory',
      },
      draw: drawDemoGrid,
      panel: {
        brand: '#e2572b',
        html: {
          es:
            header('CORPOELEC · Inventario de equipos') +
            gridTable(
              ['Codigo', 'Equipo', 'Estado', 'Sede', 'Asignado a'],
              [
                ['TX-001', 'Transformador', 'Operativo', 'Yaracuy', 'J. Perez'],
                [
                  'RAD-014',
                  'Radio portatil',
                  'Asignado',
                  'Carabobo',
                  'Cuadrilla 3',
                ],
                ['PC-207', 'Computadora', 'Operativo', 'Lara', 'Admin. Lara'],
                ['LAP-033', 'Laptop', 'En reparacion', 'Carabobo', 'Taller'],
                ['AIS-090', 'Aislador 230 kV', 'En deposito', 'Yaracuy', '—'],
              ],
            ) +
            '<p style="opacity:.7;margin:.5rem 0 0">Mostrando 1–5 de 1.248 ' +
            'equipos · pagina 1 de 250 · ultima sync: hace 2 h (sin red — ' +
            'cola local)</p>',
          en:
            header('CORPOELEC · Equipment inventory') +
            gridTable(
              ['Code', 'Equipment', 'Status', 'Site', 'Assigned to'],
              [
                ['TX-001', 'Transformer', 'Operational', 'Yaracuy', 'J. Perez'],
                ['RAD-014', 'Handheld radio', 'Assigned', 'Carabobo', 'Crew 3'],
                ['PC-207', 'Desktop PC', 'Operational', 'Lara', 'Lara admin'],
                ['LAP-033', 'Laptop', 'Under repair', 'Carabobo', 'Workshop'],
                ['AIS-090', '230 kV insulator', 'In depot', 'Yaracuy', '—'],
              ],
            ) +
            '<p style="opacity:.7;margin:.5rem 0 0">Showing 1–5 of 1,248 ' +
            'assets · page 1 of 250 · last sync: 2 h ago (no network — ' +
            'local queue)</p>',
        },
      },
    },
    {
      key: 'buscador',
      title: {
        es: 'Buscador "quien lo tomo"',
        en: '"Who took it" search',
      },
      draw: drawDemoBuscar,
      panel: {
        brand: '#e2572b',
        html: {
          es:
            header('Buscador de equipos') +
            '<input placeholder="Codigo o nombre del equipo (ej. TX-001)">' +
            '<div style="border:1px solid #c8c4b8;padding:.6rem;' +
            'margin-top:.6rem"><strong>TX-001 · Transformador de potencia' +
            '</strong><br>Estado: Operativo · Sede: Yaracuy · Deposito B-3' +
            '<br>Responsable actual: J. Perez (desde 03/2013)' +
            '<p style="margin:.45rem 0 0;opacity:.8">Historial: Cuadrilla 2 ' +
            '(01/2013) → Taller, revision (02/2013) → J. Perez (03/2013)</p>' +
            '<p style="margin:.35rem 0 0">Consulta: <strong>0,2 s</strong> ' +
            '— antes: 20+ min en planillas de papel</p></div>',
          en:
            header('Equipment search') +
            '<input placeholder="Asset code or name (e.g. TX-001)">' +
            '<div style="border:1px solid #c8c4b8;padding:.6rem;' +
            'margin-top:.6rem"><strong>TX-001 · Power transformer' +
            '</strong><br>Status: Operational · Site: Yaracuy · Depot B-3' +
            '<br>Current holder: J. Perez (since 03/2013)' +
            '<p style="margin:.45rem 0 0;opacity:.8">History: Crew 2 ' +
            '(01/2013) → Workshop, service (02/2013) → J. Perez (03/2013)' +
            '</p><p style="margin:.35rem 0 0">Lookup: <strong>0.2 s' +
            '</strong> — before: 20+ min in paper records</p></div>',
        },
      },
    },
    {
      key: 'reporte',
      title: {
        es: 'Incidencias por equipo',
        en: 'Incidents per unit',
      },
      draw: drawDemoReporte,
      panel: {
        brand: '#e2572b',
        html: {
          es:
            header('Reporte de incidencias') +
            gridTable(
              ['Sede', 'Equipos', 'Operativos', 'Dañados'],
              [
                ['Yaracuy', '412', '399', '13'],
                ['Carabobo', '486', '470', '16'],
                ['Lara', '350', '341', '9'],
              ],
            ) +
            '<p style="margin:.6rem 0 .2rem"><strong>RAD-014 · Radio ' +
            'portatil</strong> — linea de tiempo:</p>' +
            '<p style="opacity:.8;margin:0">02/2013 asignado a Cuadrilla 3 ' +
            '· 05/2013 reporte de daño (antena) · 05/2013 enviado a taller ' +
            '· 06/2013 operativo de nuevo</p>',
          en:
            header('Incident report') +
            gridTable(
              ['Site', 'Assets', 'Operational', 'Damaged'],
              [
                ['Yaracuy', '412', '399', '13'],
                ['Carabobo', '486', '470', '16'],
                ['Lara', '350', '341', '9'],
              ],
            ) +
            '<p style="margin:.6rem 0 .2rem"><strong>RAD-014 · Handheld ' +
            'radio</strong> — timeline:</p>' +
            '<p style="opacity:.8;margin:0">02/2013 assigned to Crew 3 · ' +
            '05/2013 damage report (antenna) · 05/2013 sent to workshop · ' +
            '06/2013 operational again</p>',
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

/** E enciende/apaga las laptops libres del officeLayout (patron aula). */
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
      id: `micro-corpoelec-${roomIndex}-laptop${toggle.spot}`,
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

/** Tablero de medidores rojo <-> verde; dueño del estado "energizado". */
function controlBoard(opts: {
  position: readonly [number, number]
  withLight: boolean
  onToggle(energized: boolean): void
}): { group: Group; item: Interactable; energized(): boolean } {
  const group = new Group()
  group.position.set(opts.position[0], 0, opts.position[1])
  group.rotation.y = -Math.PI / 2
  const panel = boxMesh(1.6, 1.1, 0.08, toonMat('#2e3238'))
  panel.position.set(0, 1.5, 0)
  group.add(panel)
  const lampMat = toonMatOwn('#cc3b3b', {
    emissive: '#cc3b3b',
    emissiveIntensity: 1.2,
  })
  const gaugeMat = toonMatOwn('#d8d4c8', {
    emissive: '#cc3b3b',
    emissiveIntensity: 0.35,
  })
  const units = unitGeo()
  for (const x of [-0.5, 0, 0.5]) {
    const gauge = new Mesh(units.cylinder, gaugeMat)
    gauge.scale.set(0.22, 0.03, 0.22)
    gauge.rotation.x = Math.PI / 2
    gauge.position.set(x, 1.72, 0.06)
    const lamp = new Mesh(units.sphere, lampMat)
    lamp.scale.setScalar(0.1)
    lamp.position.set(x, 1.28, 0.06)
    group.add(gauge, lamp)
  }
  const statusLight = opts.withLight ? new PointLight('#cc3b3b', 1.6, 4) : null
  if (statusLight) {
    statusLight.position.set(0, 1.5, 0.5)
    group.add(statusLight)
  }
  let energized = false
  const item: Interactable = {
    id: 'micro-corpoelec-board',
    x: opts.position[0],
    z: opts.position[1],
    radius: 2,
    label: { ...BOARD_LABEL_ON },
    onActivate: () => {
      energized = !energized
      const color = energized ? '#4dcc7a' : '#cc3b3b'
      lampMat.color.set(color)
      lampMat.emissive.set(color)
      gaugeMat.emissive.set(color)
      statusLight?.color.set(color)
      sfx.play(energized ? 'boot' : 'shutdown')
      item.label = energized ? BOARD_LABEL_OFF : BOARD_LABEL_ON
      opts.onToggle(energized)
    },
  }
  return { group, item, energized: () => energized }
}

export default function buildCorpoelec(ctx: RoomCtx): RoomBuild {
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

  // filas de oficina del canon: 4 puestos con laptops de la epoca; los
  // devs (Yorman y Genesis) trabajan en 2 encendidas, las otras 2 se
  // encienden/apagan con E (mismo patron del aula)
  const deskSpots: readonly (readonly [number, number])[] = [
    [-2, room.z + 0.6],
    [2, room.z + 0.6],
    [-2, room.z - 1.8],
    [2, room.z - 1.8],
  ]
  const office = officeLayout({
    roomIndex: room.index,
    state,
    spots: deskSpots,
    color: '#3d4a5c',
    poweredSpots: new Set([0, 3]),
    screenTheme,
    screenFor: (index) => LAPTOP_SCREENS[index] ?? LAPTOP_SCREENS[0],
  })
  group.add(office.group)
  staticColliders.push(...office.colliders)
  disposables.push(office)
  interactables.push(...laptopToggles(office, deskSpots, room.index))
  interactables.push(...office.seats)

  // fila de transformadores (subestacion) en el muro -X + etiqueta de
  // activo TX-001 (todo equipo del inventario tiene su codigo)
  group.add(
    transformer([-half + 1.5, 0, room.z - 4.9]),
    transformer([-half + 1.5, 0, room.z - 3]),
  )
  staticColliders.push(
    footprint(-half + 1.5, room.z - 4.9, 1.8, 1.1),
    footprint(-half + 1.5, room.z - 3, 1.8, 1.1),
  )
  const assetTag = label('TX-001', { size: 0.14, color: theme.trim })
  assetTag.position.set(-half + 2.35, 1.15, room.z - 4.9)
  assetTag.rotation.y = Math.PI / 2
  group.add(assetTag)

  // seccion de inventario (+X, frente): estanteria metalica con cajas
  // etiquetadas y los equipos 2013 que el sistema rastreaba — 3 lotes
  // fusionados (metal / kraft / equipos oscuros) = 6 draw calls
  const shelfX = half - 0.55
  group.add(
    // lote metal: estanteria (3 repisas + laterales) + radios base +
    // telefonos fijos + PC torre en el piso
    outlinedMergedBoxes(
      [
        { w: 0.5, h: 0.04, d: 1.9, x: shelfX, y: 0.5, z: room.z - 4.1 },
        { w: 0.5, h: 0.04, d: 1.9, x: shelfX, y: 1.0, z: room.z - 4.1 },
        { w: 0.5, h: 0.04, d: 1.9, x: shelfX, y: 1.5, z: room.z - 4.1 },
        { w: 0.5, h: 1.62, d: 0.05, x: shelfX, y: 0.81, z: room.z - 5.07 },
        { w: 0.5, h: 1.62, d: 0.05, x: shelfX, y: 0.81, z: room.z - 3.13 },
        // radio base con perilla (repisa media)
        { w: 0.3, h: 0.12, d: 0.22, x: shelfX, y: 1.08, z: room.z - 4.7 },
        // telefono fijo de escritorio
        { w: 0.22, h: 0.08, d: 0.2, x: shelfX, y: 1.06, z: room.z - 3.6 },
        {
          w: 0.06,
          h: 0.05,
          d: 0.18,
          x: shelfX - 0.08,
          y: 1.12,
          z: room.z - 3.6,
        },
        // PC torre 2013 en el piso junto a la estanteria
        { w: 0.2, h: 0.52, d: 0.46, x: shelfX - 0.5, y: 0.26, z: room.z - 2.7 },
      ],
      toonMat('#6a7078'),
      { castShadow: true },
    ),
    // lote kraft: cajas etiquetadas + bobinas de cable + aisladores
    outlinedMergedBoxes(
      [
        { w: 0.55, h: 0.4, d: 0.55, x: shelfX, y: 0.72, z: room.z - 4.1 },
        { w: 0.5, h: 0.36, d: 0.5, x: shelfX, y: 0.22, z: room.z - 4.55 },
        { w: 0.5, h: 0.36, d: 0.5, x: shelfX, y: 0.22, z: room.z - 3.65 },
        { w: 0.45, h: 0.34, d: 0.45, x: shelfX, y: 1.7, z: room.z - 4.55 },
        // bobinas de cable (carrete: 2 flanges + nucleo) en el rincon
        { w: 0.1, h: 0.62, d: 0.62, x: half - 1.35, y: 0.31, z: room.z - 5.15 },
        { w: 0.1, h: 0.62, d: 0.62, x: half - 1.75, y: 0.31, z: room.z - 5.15 },
        { w: 0.32, h: 0.3, d: 0.3, x: half - 1.55, y: 0.31, z: room.z - 5.15 },
        // aisladores ceramicos apilados (repisa alta)
        { w: 0.14, h: 0.3, d: 0.14, x: shelfX, y: 1.67, z: room.z - 3.5 },
        { w: 0.14, h: 0.3, d: 0.14, x: shelfX, y: 1.67, z: room.z - 3.72 },
      ],
      toonMat('#8a6f4d'),
      { castShadow: true },
    ),
    // lote oscuro: walkie-talkies con antena, laptops gruesas y tablets
    outlinedMergedBoxes(
      [
        {
          w: 0.09,
          h: 0.24,
          d: 0.06,
          x: shelfX - 0.12,
          y: 1.14,
          z: room.z - 4.4,
        },
        {
          w: 0.02,
          h: 0.14,
          d: 0.02,
          x: shelfX - 0.14,
          y: 1.32,
          z: room.z - 4.4,
        },
        {
          w: 0.09,
          h: 0.24,
          d: 0.06,
          x: shelfX + 0.1,
          y: 1.14,
          z: room.z - 4.3,
        },
        {
          w: 0.02,
          h: 0.14,
          d: 0.02,
          x: shelfX + 0.08,
          y: 1.32,
          z: room.z - 4.3,
        },
        // laptop gruesa 2013 (base + tapa abierta) en la repisa baja
        { w: 0.32, h: 0.05, d: 0.24, x: shelfX, y: 0.55, z: room.z - 3.4 },
        { w: 0.32, h: 0.24, d: 0.04, x: shelfX, y: 0.68, z: room.z - 3.28 },
        // tablets de bisel grueso apiladas
        { w: 0.17, h: 0.03, d: 0.24, x: shelfX, y: 1.53, z: room.z - 4.0 },
        {
          w: 0.17,
          h: 0.03,
          d: 0.24,
          x: shelfX + 0.02,
          y: 1.56,
          z: room.z - 3.95,
        },
        // monitor CRT panzon sobre la repisa media (sede vieja)
        { w: 0.34, h: 0.3, d: 0.36, x: shelfX, y: 1.19, z: room.z - 5.0 },
      ],
      toonMat('#2e3238'),
      { castShadow: true },
    ),
  )
  staticColliders.push(
    footprint(shelfX, room.z - 4.1, 0.7, 2.1),
    footprint(half - 1.55, room.z - 5.15, 0.9, 0.8),
    footprint(shelfX - 0.5, room.z - 2.7, 0.4, 0.6),
  )
  const inventoryLabel = label(locale === 'es' ? 'INVENTARIO' : 'INVENTORY', {
    size: 0.16,
    color: '#f2b705',
  })
  inventoryLabel.position.set(shelfX - 0.1, 1.95, room.z - 4.1)
  inventoryLabel.rotation.y = -Math.PI / 2
  group.add(inventoryLabel)
  // lineas amarillas de seguridad demarcando la seccion (piso, sin
  // contorno: 1 draw call)
  group.add(
    mergedBoxes(
      [
        { w: 0.06, h: 0.02, d: 3.4, x: half - 1.55, y: 0.011, z: room.z - 4.0 },
        { w: 1.5, h: 0.02, d: 0.06, x: half - 0.8, y: 0.011, z: room.z - 2.3 },
      ],
      toonMat('#f2b705'),
    ),
  )

  // escritorio del monitor de inventario: arranca OFFLINE, el tablero lo
  // pone ONLINE; al lado, las planillas que el sistema jubilo + el casco
  group.add(
    desk({ position: [1.8, 0, room.z + 3.0], width: 1.4, color: '#3a3e44' }),
  )
  staticColliders.push(footprint(1.8, room.z + 3.0, 1.5, 0.8))
  group.add(
    paperStack({ position: [1.3, 0.745, room.z + 3.1], count: 5 }),
    paperStack({ position: [2.75, 0, room.z + 2.7], count: 11 }),
  )
  const inventory = switchableMonitor({
    position: [1.8, 0.72, room.z + 2.9],
    rotationY: Math.PI,
    width: 0.72,
    variants: {
      offline: {
        title: '[OFFLINE] inventario',
        lines: [
          'ID    EQUIPO       SEDE',
          '0041  transformador yaracuy',
          '0042  aislador      carabobo',
          '0043  medidor       lara',
          'busqueda: en papel...',
        ],
        theme: screenTheme,
        dot: '#cc3b3b',
      },
      online: {
        title: '[ONLINE] inventario',
        lines: [
          'ID    EQUIPO       SEDE',
          '0041  transformador yaracuy',
          '0042  aislador      carabobo',
          '0043  medidor       lara',
          'sync 3 sedes: OK   2ms',
        ],
        theme: screenTheme,
        dot: '#4dcc7a',
      },
      'search-offline': {
        title: '[OFFLINE] buscando 0042...',
        lines: [
          'sistema sin energia',
          'revisando planillas a mano',
          'carpeta 7 de 38...',
          'tiempo estimado: 20+ min',
        ],
        theme: screenTheme,
        dot: '#cc3b3b',
      },
      'search-online': {
        title: '[ONLINE] buscar: 0042',
        lines: [
          '> buscar "0042"',
          '0042  aislador  carabobo',
          'ubicacion: deposito B-3',
          'tiempo: 0.2 s',
        ],
        theme: screenTheme,
        dot: '#4dcc7a',
      },
    },
    initial: 'offline',
  })
  group.add(inventory.group)
  disposables.push(inventory.screen)
  const helmet = new Group()
  helmet.position.set(2.35, 0.85, room.z + 2.9)
  const units = unitGeo()
  const dome = new Mesh(units.sphere, toonMat('#f2b705'))
  dome.scale.set(0.32, 0.22, 0.32)
  dome.position.y = 0.02
  const brim = new Mesh(units.cylinder, toonMat('#f2b705'))
  brim.scale.set(0.44, 0.02, 0.44)
  helmet.add(dome, brim)
  group.add(helmet)

  // micro-interaccion: tablero de medidores rojo -> verde + luz de estado
  const board = controlBoard({
    position: [half - 0.42, room.z + 2.6],
    withLight: state.tier === 'full',
    onToggle: (energized) =>
      inventory.screen.show(energized ? 'online' : 'offline'),
  })
  group.add(board.group)
  interactables.push(board.item)

  // micro "buscar un equipo": papel lento vs sistema inmediato, segun
  // este energizado el tablero; la pantalla vuelve sola a los ~3 s
  let searchUntil = -1
  interactables.push({
    id: `micro-corpoelec-search-${room.index}`,
    x: 1.8,
    z: room.z + 3.0,
    radius: 1.9,
    label: SEARCH_LABEL,
    onActivate: () => {
      inventory.screen.show(
        board.energized() ? 'search-online' : 'search-offline',
      )
      sfx.play('blip')
      searchUntil = -2 // pendiente: el proximo update fija el fin
    },
  })
  updates.push((t) => {
    if (searchUntil === -2) {
      searchUntil = t + 3
    }
    if (searchUntil > 0 && t > searchUntil) {
      searchUntil = -1
      inventory.screen.show(board.energized() ? 'online' : 'offline')
    }
  })

  // cuadros de rubro (wallArt): lineas de transmision y transformador
  // 40 MVA inspeccionables (muro -Z); Guri y mapa de sedes decorativos
  // flanqueando la puerta al pasillo (muro +Z)
  const art = wallArt({
    roomIndex: room.index,
    theme,
    locale,
    onFicha: actions.openStory,
    frames: [
      {
        key: 'lineas-transmision',
        position: [-3.6, 2, backZ + 0.08],
        rotationY: 0,
        draw: drawLineasTransmision,
        ficha: ART_FICHA_LINEAS,
      },
      {
        key: 'transformador-40mva',
        position: [3.6, 2, backZ + 0.08],
        rotationY: 0,
        draw: drawTransformador,
        ficha: ART_FICHA_TRAFO,
      },
      {
        key: 'guri',
        position: [-3.6, 2, frontZ - 0.08],
        rotationY: Math.PI,
        draw: drawGuri,
      },
      {
        key: 'mapa-sedes',
        position: [3.6, 2, frontZ - 0.08],
        rotationY: Math.PI,
        draw: drawMapaSedes,
      },
    ],
  })
  staticColliders.push(...art.colliders)
  const sink = { group, interactables, updates }
  addProps(sink, art.props)

  // showcase del software junto a la puerta al pasillo (canon AC-6):
  // monitor Canvas en loop + panel HTML operable; E cicla las 3 demos
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

  // NPCs del canon (2 enfoques, informe 08): Yorman y Genesis (devs,
  // sentados en sus laptops), Wilmer (almacenista junto a la estanteria),
  // Dubraska (administrativa en ronda de inventario) y el Ing. Betancourt
  // (jefe, supervisando la subestacion). Todos con casco.
  const coworkers = npcCoworkers({
    roomIndex: room.index,
    openDialog: actions.openDialog,
    npcs: [
      {
        key: 'yorman',
        role: 'coworker',
        spec: {
          skin: '#c98f6a',
          hair: { style: 'spiky', color: '#14100c' },
          top: '#3f5a73',
          bottom: '#2e3238',
          accessory: 'helmet',
          model: 'james',
          faceSeed: 83,
        },
        position: [-2, 0, room.z + 0.05],
        rotationY: 0,
        pose: 'sit',
        dialog: CORPOELEC_PRESENTE_DIALOGS.yorman,
      },
      {
        key: 'genesis',
        role: 'coworker',
        spec: {
          skin: '#e8b48c',
          hair: { style: 'bun', color: '#3a2a1a' },
          top: '#5a4a72',
          bottom: '#3a4048',
          accessory: 'helmet',
          model: 'louise',
          faceSeed: 29,
        },
        position: [2, 0, room.z - 2.35],
        rotationY: 0,
        pose: 'sit',
        dialog: CORPOELEC_PRESENTE_DIALOGS.genesis,
      },
      {
        key: 'wilmer',
        role: 'staff',
        spec: {
          skin: '#b5825f',
          hair: { style: 'short', color: '#8a8a92' },
          top: '#5a6a48',
          bottom: '#4a4438',
          accessory: 'helmet',
          model: 'pete',
          faceSeed: 51,
        },
        position: [half - 2.1, 0, room.z - 3.8],
        rotationY: -1.1,
        dialog: CORPOELEC_PRESENTE_DIALOGS.wilmer,
      },
      {
        key: 'dubraska',
        role: 'staff',
        spec: {
          skin: '#d9a684',
          hair: { style: 'ponytail', color: '#1c1410' },
          top: '#7a4652',
          bottom: '#3a4048',
          accessory: 'helmet',
          model: 'kate',
          faceSeed: 67,
        },
        position: [0.6, 0, room.z + 2.4],
        path: [
          [0.6, room.z + 2.4],
          [half - 2.6, room.z - 2.6],
          [-2.8, room.z + 3.2],
        ],
        speed: 0.55,
        dialog: CORPOELEC_PRESENTE_DIALOGS.dubraska,
      },
      {
        key: 'rafael',
        role: 'boss',
        spec: {
          skin: '#d9a684',
          hair: { style: 'short', color: '#4a3a2e' },
          top: '#3a4a62',
          bottom: '#2e3238',
          accessory: 'helmet',
          model: 'joe',
          faceSeed: 91,
        },
        position: [-half + 3.1, 0, room.z - 1.6],
        rotationY: 0.9,
        dialog: CORPOELEC_PRESENTE_DIALOGS.rafael,
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
