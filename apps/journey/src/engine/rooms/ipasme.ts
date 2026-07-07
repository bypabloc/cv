/**
 * @module rooms/ipasme (engine)
 * @description Sala 2 — IPASME (servicio de salud docente, VE, 2014),
 *   construida al CANON de sala (plan journey-salas-estandar, informe 09):
 *   `officeLayout` en el rincon de desarrollo (Daniela sentada en su
 *   laptop Java, 2 libres togglables con E), 5 NPCs conversables con los
 *   2 enfoques (`npcCoworkers`: Daniela y Jose Miguel devs, Yuleima
 *   enfermera, Argenis archivista, Dr. Villasmil medico/jefe), cuadros de
 *   rubro (`wallArt`: lamina de anatomia y carnet de afiliado
 *   inspeccionables, flujo de atencion y cartel escolar decorativos) y el
 *   `softwareShowcase` junto a la puerta con 3 demos del sistema real
 *   (ficha de paciente, buscador de historia, control de acceso —
 *   estetica app de escritorio Windows 2014, NUNCA navegador). Props
 *   firma: camilla con rollo de papel, escritorio medico con tensiometro,
 *   negatoscopio con radiografia, bascula, sala de espera con sillas en
 *   hilera + dispensador de turnos, mostrador de admision con cruz roja y
 *   monitor de historias, farmacia y el archivador semivacio (el papel
 *   migrado). Micros: buscar una historia al instante (eje minutos ->
 *   inmediato) y tomar un turno. Kit informativo ESTANDAR (`infoKit`) en
 *   las posiciones canonicas. Paredes blanco hueso; el rubro vive en
 *   piso/props/luz (azul institucional + verde menta).
 */
import { Group, Mesh, MeshBasicMaterial, PlaneGeometry } from 'three'
import type { Box2 } from '../../lib/collision'
import type { Locale } from '../../lib/rooms'
import { sfx } from '../audio'
import type { NpcHandle } from '../character'
import { IPASME_PRESENTE_DIALOGS } from '../dialogs/ipasme-presente'
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

const SEARCH_LABEL = {
  es: 'Buscar una historia',
  en: 'Look up a record',
} as const

const TURNO_LABEL = {
  es: 'Tomar un turno',
  en: 'Take a ticket',
} as const

const LAPTOP_LABELS = {
  on: { es: 'Encender la laptop libre', en: 'Power on the spare laptop' },
  off: { es: 'Apagar la laptop libre', en: 'Power off the spare laptop' },
} as const

/** Pantallas era-2014 (Java de escritorio) de las laptops, por puesto. */
const LAPTOP_SCREENS = [
  {
    title: 'Paciente.java — POO',
    lines: [
      'public class Paciente {',
      '  String cedula;',
      '  List<Consulta> citas;',
      '}  // el modelo primero',
    ],
  },
  {
    title: 'HistoriaDAO.java — CRUD',
    lines: [
      'crear(p);  leer(cedula);',
      'actualizar(p); borrar(id);',
      'SELECT * FROM historias',
      ' WHERE cedula = ? // 0,2 s',
    ],
  },
  {
    title: 'checklist_qa.txt',
    lines: [
      'ficha paciente..... OK',
      'buscador cedula.... OK',
      'acceso por rol..... OK',
      'PC admision: reinstalar',
    ],
  },
] as const

// --- laminas de los cuadros (wallArt): tinta plana sobre papel claro ---

const ART_PAPER = '#f4efe2'
const ART_INK = '#1c2a30'
const ART_BLUE = '#2f7fb0'
const ART_MINT = '#63c2a8'
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

/** Lamina de anatomia: torso con costillas + columna (cartel clinico). */
function drawAnatomia(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 17px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('ANATOMIA HUMANA', 24, 38)
  ctx.strokeStyle = ART_INK
  ctx.lineWidth = 3
  ctx.lineCap = 'round'
  // cabeza + columna
  ctx.beginPath()
  ctx.arc(128, 76, 18, 0, Math.PI * 2)
  ctx.stroke()
  ctx.beginPath()
  ctx.moveTo(128, 94)
  ctx.lineTo(128, 196)
  ctx.stroke()
  // costillas (arcos simetricos)
  ctx.lineWidth = 2
  for (const y of [112, 128, 144, 160]) {
    ctx.beginPath()
    ctx.moveTo(128, y)
    ctx.quadraticCurveTo(94, y + 6, 88, y + 18)
    ctx.moveTo(128, y)
    ctx.quadraticCurveTo(162, y + 6, 168, y + 18)
    ctx.stroke()
  }
  // pelvis
  ctx.beginPath()
  ctx.moveTo(106, 196)
  ctx.quadraticCurveTo(128, 214, 150, 196)
  ctx.stroke()
  // rotulos de cartel clinico
  ctx.fillStyle = ART_BLUE
  ctx.font = 'bold 12px "Space Mono", ui-monospace, monospace'
  ctx.fillText('torax', 178, 130)
  ctx.fillText('columna', 34, 150)
  ctx.strokeStyle = ART_BLUE
  ctx.lineWidth = 1.5
  ctx.beginPath()
  ctx.moveTo(174, 126)
  ctx.lineTo(158, 126)
  ctx.moveTo(66, 146)
  ctx.lineTo(124, 146)
  ctx.stroke()
  ctx.fillStyle = ART_INK
  ctx.globalAlpha = 0.6
  ctx.font = '12px "Space Mono", ui-monospace, monospace'
  ctx.fillText('consultorio 3 · medicina gral', 24, 234)
  ctx.globalAlpha = 1
}

/** Carnet de afiliado IPASME ampliado: foto, numero y cruz azul. */
function drawCarnet(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 17px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('CARNET DE AFILIADO', 24, 38)
  // tarjeta
  ctx.strokeStyle = ART_INK
  ctx.lineWidth = 3
  ctx.strokeRect(36, 60, 184, 116)
  ctx.fillStyle = ART_BLUE
  ctx.fillRect(36, 60, 184, 22)
  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 13px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('IPASME', 44, 76)
  // cruz medica en la esquina de la banda
  ctx.fillRect(196, 63, 6, 16)
  ctx.fillRect(191, 68, 16, 6)
  // foto + lineas de datos
  ctx.strokeStyle = ART_INK
  ctx.lineWidth = 2
  ctx.strokeRect(46, 92, 44, 54)
  ctx.beginPath()
  ctx.arc(68, 110, 9, 0, Math.PI * 2)
  ctx.moveTo(54, 140)
  ctx.quadraticCurveTo(68, 122, 82, 140)
  ctx.stroke()
  ctx.fillStyle = ART_INK
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('DOCENTE · MPPE', 102, 102)
  ctx.fillText('afiliado 0913', 102, 120)
  ctx.fillText('cedula V-9.318.442', 102, 138)
  ctx.fillStyle = ART_MINT
  ctx.fillText('familiares: 3', 102, 156)
  ctx.fillStyle = ART_INK
  ctx.globalAlpha = 0.6
  ctx.font = '12px "Space Mono", ui-monospace, monospace'
  ctx.fillText('un afiliado = un expediente', 24, 226)
  ctx.globalAlpha = 1
}

/** Flujo de atencion: recepcion -> admision -> consulta -> farmacia. */
function drawFlujo(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 17px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('FLUJO DE ATENCION', 24, 38)
  const steps = ['RECEPCION', 'ADMISION', 'CONSULTA', 'FARMACIA'] as const
  ctx.font = 'bold 11px "Space Mono", ui-monospace, monospace'
  steps.forEach((step, index) => {
    const y = 64 + index * 42
    ctx.strokeStyle = index === 1 ? ART_BLUE : ART_INK
    ctx.lineWidth = index === 1 ? 3 : 2
    ctx.strokeRect(70, y, 116, 26)
    ctx.fillStyle = index === 1 ? ART_BLUE : ART_INK
    ctx.fillText(step, 82, y + 17)
    if (index < steps.length - 1) {
      ctx.strokeStyle = ART_INK
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.moveTo(128, y + 26)
      ctx.lineTo(128, y + 42)
      ctx.moveTo(123, y + 37)
      ctx.lineTo(128, y + 42)
      ctx.lineTo(133, y + 37)
      ctx.stroke()
    }
  })
  // la historia medica alimenta la admision (el cuello de botella)
  ctx.fillStyle = ART_MINT
  ctx.font = 'bold 10px "Space Mono", ui-monospace, monospace'
  ctx.fillText('historia', 196, 116)
  ctx.fillText('medica', 196, 128)
  ctx.strokeStyle = ART_MINT
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.moveTo(206, 132)
  ctx.lineTo(190, 119)
  ctx.stroke()
  ctx.fillStyle = ART_INK
  ctx.globalAlpha = 0.6
  ctx.font = '12px "Space Mono", ui-monospace, monospace'
  ctx.fillText('sin historia no hay consulta', 24, 234)
  ctx.globalAlpha = 1
}

/** Cartel "IPASME va a la Escuela": escuelita + cruz de salud. */
function drawEscuela(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_BLUE
  ctx.font = 'bold 16px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('IPASME VA A LA ESCUELA', 20, 40)
  // escuelita: cuerpo + techo + puerta
  ctx.strokeStyle = ART_INK
  ctx.lineWidth = 3
  ctx.strokeRect(74, 120, 108, 70)
  ctx.beginPath()
  ctx.moveTo(64, 120)
  ctx.lineTo(128, 78)
  ctx.lineTo(192, 120)
  ctx.closePath()
  ctx.stroke()
  ctx.strokeRect(116, 152, 24, 38)
  // cruz de salud sobre la puerta
  ctx.fillStyle = ART_RED
  ctx.fillRect(124, 128, 8, 20)
  ctx.fillRect(118, 134, 20, 8)
  // camino
  ctx.strokeStyle = ART_MINT
  ctx.lineWidth = 3
  ctx.beginPath()
  ctx.moveTo(128, 190)
  ctx.quadraticCurveTo(96, 214, 48, 222)
  ctx.stroke()
  ctx.fillStyle = ART_INK
  ctx.globalAlpha = 0.6
  ctx.font = '12px "Space Mono", ui-monospace, monospace'
  ctx.fillText('salud para el docente y su familia', 20, 236)
  ctx.globalAlpha = 1
}

/** Radiografia del negatoscopio: torax en azul claro sobre fondo negro. */
function drawRadiografia(ctx: CanvasRenderingContext2D, size: number): void {
  ctx.fillStyle = '#0a0e14'
  ctx.fillRect(0, 0, size, size)
  ctx.strokeStyle = '#bcd8e8'
  ctx.lineWidth = 3
  ctx.lineCap = 'round'
  ctx.globalAlpha = 0.9
  ctx.beginPath()
  ctx.moveTo(128, 40)
  ctx.lineTo(128, 210)
  ctx.stroke()
  ctx.lineWidth = 2
  for (const y of [70, 92, 114, 136, 158]) {
    ctx.beginPath()
    ctx.moveTo(128, y)
    ctx.quadraticCurveTo(78, y + 10, 66, y + 28)
    ctx.moveTo(128, y)
    ctx.quadraticCurveTo(178, y + 10, 190, y + 28)
    ctx.stroke()
  }
  ctx.globalAlpha = 0.5
  ctx.font = '12px "Space Mono", ui-monospace, monospace'
  ctx.fillStyle = '#bcd8e8'
  ctx.fillText('RX-2014-0913', 14, 240)
  ctx.globalAlpha = 1
}

const ART_FICHA_ANATOMIA = {
  title: {
    es: 'Salud integral para los docentes',
    en: 'Whole-person care for teachers',
  },
  paragraphs: {
    es: [
      'El IPASME es el instituto de prevision y asistencia social del ' +
        'personal del Ministerio de Educacion venezolano: medicina ' +
        'general y especializada, odontologia, laboratorio, rayos X y ' +
        'farmacia para los docentes y sus familias, desde 1950.',
      'Toda esa atencion gira alrededor de un documento: la historia ' +
        'medica. Sin ella no hay consulta — y durante decadas vivio en ' +
        'carpetas de papel numeradas a mano.',
      'El sistema que Pablo construyo en 2014 digitalizo justamente esa ' +
        'puerta de entrada: registro y consulta de pacientes, consultas ' +
        'y registros clinicos en una app de escritorio.',
    ],
    en: [
      'IPASME is the welfare and social-assistance institute for ' +
        'Venezuela’s Ministry of Education staff: general and ' +
        'specialised medicine, dentistry, laboratory, X-rays and a ' +
        'pharmacy for teachers and their families, since 1950.',
      'All of that care revolves around one document: the medical ' +
        'record. Without it there is no consultation — and for decades ' +
        'it lived in hand-numbered paper folders.',
      'The system Pablo built in 2014 digitised exactly that entry ' +
        'point: patient registration and lookup, consultations and ' +
        'clinical records in a desktop app.',
    ],
  },
} as const

const ART_FICHA_CARNET = {
  title: {
    es: 'El carnet de afiliado',
    en: 'The member card',
  },
  paragraphs: {
    es: [
      'El "paciente" del IPASME es el docente afiliado — y su familia. ' +
        'Cada afiliado tiene un expediente unico con su numeracion: ' +
        'multiplica eso por decadas de servicio y el archivo fisico se ' +
        'vuelve una montaña de carpetas manila.',
      'Con un volumen de atenciones enorme (cientos de miles al año ' +
        'entre medicina, odontologia y laboratorio), el papel no daba ' +
        'abasto: buscar una historia costaba varios minutos por ' +
        'paciente... si aparecia.',
      'De ahi el eje del sistema de 2014: la busqueda por cedula o ' +
        'numero de historia paso de minutos en el archivo a una ' +
        'consulta inmediata en pantalla.',
    ],
    en: [
      'IPASME’s "patient" is the affiliated teacher — and their ' +
        'family. Every member has a unique numbered file: multiply that ' +
        'by decades of service and the physical archive becomes a ' +
        'mountain of manila folders.',
      'With a huge volume of visits (hundreds of thousands a year ' +
        'across medicine, dentistry and the lab), paper could not keep ' +
        'up: finding a record cost several minutes per patient... when ' +
        'it showed up at all.',
      'Hence the core of the 2014 system: searching by ID or record ' +
        'number went from minutes at the archive to an instant lookup ' +
        'on screen.',
    ],
  },
} as const

// --- demos del showcase: app de escritorio Windows 2014 (Swing-like) ---

const WIN_BG = '#ece9d8'
const WIN_CHROME = '#d4d0c8'
const WIN_INK = '#1c1f26'
const WIN_SELECT = '#316AC5'

/** Ventana clasica: barra de titulo gris + menu + marco hundido. */
function winChrome(
  ctx: CanvasRenderingContext2D,
  size: number,
  title: string,
): void {
  ctx.fillStyle = WIN_BG
  ctx.fillRect(0, 0, size, size)
  // barra de titulo gris con boton de cerrar
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
  // menu clasico
  ctx.fillStyle = WIN_INK
  ctx.font = '11px Tahoma, "Space Grotesk", sans-serif'
  ctx.fillText('Archivo  Edicion  Pacientes  Consultas  Ayuda', 8, 38)
  ctx.strokeStyle = '#b8b4a8'
  ctx.beginPath()
  ctx.moveTo(0, 44)
  ctx.lineTo(size, 44)
  ctx.stroke()
}

/** Campo hundido 3D de formulario Windows. */
function winField(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  text: string,
): void {
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(x, y, w, 16)
  ctx.strokeStyle = '#7a766a'
  ctx.lineWidth = 1
  ctx.strokeRect(x, y, w, 16)
  ctx.fillStyle = WIN_INK
  ctx.font = '11px Tahoma, "Space Mono", monospace'
  ctx.fillText(text, x + 4, y + 12)
}

/** Demo 1: ficha de paciente — formulario denso + tabla de consultas. */
function drawDemoFicha(
  ctx: CanvasRenderingContext2D,
  size: number,
  t: number,
): void {
  winChrome(ctx, size, 'SHM · Ficha de paciente')
  ctx.fillStyle = WIN_INK
  ctx.font = '11px Tahoma, "Space Grotesk", sans-serif'
  ctx.fillText('N. historia:', 10, 62)
  winField(ctx, 78, 50, 60, '0913')
  ctx.fillText('Cedula:', 148, 62)
  winField(ctx, 192, 50, 56, 'V-9318442')
  ctx.fillText('Paciente:', 10, 84)
  winField(ctx, 78, 72, 170, 'Marisol Peres · 41')
  // GroupBox de consultas con la fila activa rotando
  ctx.strokeStyle = '#9a968a'
  ctx.strokeRect(10, 96, size - 20, 96)
  ctx.fillStyle = WIN_BG
  ctx.fillRect(16, 90, 74, 10)
  ctx.fillStyle = WIN_INK
  ctx.font = 'bold 10px Tahoma, "Space Grotesk", sans-serif'
  ctx.fillText('Consultas', 18, 98)
  const rows = [
    '12/03  control    Dr. V.',
    '02/06  odontologia Dra. M.',
    '19/09  laboratorio Lic. R.',
  ] as const
  const active = Math.floor(t * 0.7) % rows.length
  rows.forEach((row, index) => {
    const y = 106 + index * 24
    if (index === active) {
      ctx.fillStyle = WIN_SELECT
      ctx.fillRect(14, y - 2, size - 28, 20)
    }
    ctx.fillStyle = index === active ? '#ffffff' : WIN_INK
    ctx.font = '11px "Space Mono", ui-monospace, monospace'
    ctx.fillText(row, 18, y + 12)
    ctx.strokeStyle = '#c8c4b8'
    ctx.beginPath()
    ctx.moveTo(14, y + 18)
    ctx.lineTo(size - 14, y + 18)
    ctx.stroke()
  })
  // botones CRUD 3D
  for (const [x, text] of [
    [10, 'Nuevo'],
    [76, 'Guardar'],
    [152, 'Eliminar'],
  ] as const) {
    ctx.fillStyle = WIN_CHROME
    ctx.fillRect(x, 200, 60, 18)
    ctx.strokeStyle = '#7a766a'
    ctx.strokeRect(x, 200, 60, 18)
    ctx.fillStyle = WIN_INK
    ctx.font = '11px Tahoma, "Space Grotesk", sans-serif'
    ctx.fillText(text, x + 8, 213)
  }
}

/** Demo 2: buscador de historia — tipeo animado + resultado 0,2 s. */
function drawDemoBuscar(
  ctx: CanvasRenderingContext2D,
  size: number,
  t: number,
): void {
  winChrome(ctx, size, 'SHM · Buscar historia')
  const query = 'V-9318442'
  const typed = query.slice(
    0,
    Math.min(query.length, Math.floor((t * 2.4) % (query.length + 4))),
  )
  ctx.fillStyle = WIN_INK
  ctx.font = '11px Tahoma, "Space Grotesk", sans-serif'
  ctx.fillText('Cedula o N. de historia:', 10, 62)
  const caret = Math.floor(t * 3) % 2 === 0 ? '_' : ' '
  winField(ctx, 10, 68, 150, `${typed}${caret}`)
  ctx.fillStyle = WIN_CHROME
  ctx.fillRect(168, 68, 52, 16)
  ctx.strokeStyle = '#7a766a'
  ctx.strokeRect(168, 68, 52, 16)
  ctx.fillStyle = WIN_INK
  ctx.fillText('Buscar', 176, 80)
  // resultado inmediato
  ctx.strokeStyle = '#9a968a'
  ctx.strokeRect(10, 96, size - 20, 100)
  const lines = [
    'historia 0913 · M. Peres',
    'afiliado docente MPPE',
    'antecedentes: al dia',
    'ultima consulta: 19/09',
  ] as const
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  lines.forEach((line, index) => {
    ctx.fillStyle = WIN_INK
    ctx.fillText(line, 18, 114 + index * 18)
  })
  ctx.fillStyle = ART_BLUE
  ctx.font = 'bold 12px "Space Mono", ui-monospace, monospace'
  ctx.fillText('consulta: 0,2 s', 18, 190)
  ctx.fillStyle = WIN_INK
  ctx.globalAlpha = 0.6
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('antes: varios minutos en archivo', 10, 216)
  ctx.globalAlpha = 1
}

/** Demo 3: control de acceso — login por rol + datos de salud con llave. */
function drawDemoAcceso(
  ctx: CanvasRenderingContext2D,
  size: number,
  t: number,
): void {
  winChrome(ctx, size, 'SHM · Control de acceso')
  ctx.fillStyle = WIN_INK
  ctx.font = '11px Tahoma, "Space Grotesk", sans-serif'
  ctx.fillText('Usuario:', 10, 62)
  winField(ctx, 64, 50, 100, 'yrondon')
  ctx.fillText('Clave:', 10, 84)
  winField(ctx, 64, 72, 100, '********')
  // roles: el activo rota
  const roles = ['MEDICO', 'ADMISION', 'ENFERMERIA'] as const
  const active = Math.floor(t * 0.5) % roles.length
  roles.forEach((role, index) => {
    const y = 108 + index * 20
    ctx.strokeStyle = WIN_INK
    ctx.lineWidth = 1.5
    ctx.beginPath()
    ctx.arc(18, y, 5, 0, Math.PI * 2)
    ctx.stroke()
    if (index === active) {
      ctx.fillStyle = WIN_SELECT
      ctx.beginPath()
      ctx.arc(18, y, 2.6, 0, Math.PI * 2)
      ctx.fill()
    }
    ctx.fillStyle = WIN_INK
    ctx.font = '11px "Space Mono", ui-monospace, monospace'
    ctx.fillText(role, 32, y + 4)
  })
  // seccion "datos de salud" con candado si el rol no es medico
  const locked = roles[active] !== 'MEDICO'
  ctx.strokeStyle = locked ? ART_RED : '#3f9d63'
  ctx.lineWidth = 2
  ctx.strokeRect(118, 100, 128, 72)
  ctx.fillStyle = locked ? ART_RED : '#3f9d63'
  ctx.font = 'bold 10px "Space Mono", ui-monospace, monospace'
  ctx.fillText('DATOS DE SALUD', 128, 116)
  // candado: cuerpo + arco
  ctx.strokeRect(172, 128, 20, 16)
  ctx.beginPath()
  ctx.arc(182, 128, 7, Math.PI, 0)
  ctx.stroke()
  ctx.font = 'bold 11px "Space Mono", ui-monospace, monospace'
  ctx.fillText(locked ? 'BLOQUEADO' : 'PERMITIDO', 128, 162)
  ctx.fillStyle = WIN_INK
  ctx.globalAlpha = 0.6
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('cada rol ve solo lo suyo', 10, 200)
  ctx.fillText('validacion en cada campo', 10, 216)
  ctx.globalAlpha = 1
}

/** Los 3 mockups HTML del panel operable (look Windows classic 2014). */
function showcaseDemos(): ShowcaseDemo[] {
  const chrome = (title: string): string =>
    '<div style="background:#d4d0c8;color:#1c1f26;padding:.4rem .6rem;' +
    'font-weight:700;border-bottom:1px solid #9a968a">' +
    `${title}<span style="float:right;border:1px solid #7a766a;` +
    'padding:0 .4rem;font-size:.75rem;line-height:1.3rem">X</span></div>' +
    '<div style="background:#ece9d8;color:#1c1f26;padding:.15rem .6rem;' +
    'font-size:.8rem;border-bottom:1px solid #b8b4a8">Archivo&nbsp;&nbsp;' +
    'Edicion&nbsp;&nbsp;Pacientes&nbsp;&nbsp;Consultas&nbsp;&nbsp;' +
    'Ayuda</div>'
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
      key: 'ficha',
      title: {
        es: 'Ficha de paciente',
        en: 'Patient file',
      },
      draw: drawDemoFicha,
      panel: {
        brand: '#2f7fb0',
        html: {
          es:
            chrome('Sistema de Historias Medicas · Ficha') +
            '<p style="margin:.6rem 0 .3rem"><strong>Historia 0913 · ' +
            'Marisol Peres</strong> — docente MPPE · V-9.318.442 · 41 ' +
            'años · familiares: 3</p>' +
            gridTable(
              ['Fecha', 'Motivo', 'Diagnostico', 'Atendio'],
              [
                ['12/03/2014', 'Control', 'Saludable', 'Dr. Villasmil'],
                ['02/06/2014', 'Odontologia', 'Caries simple', 'Dra. Marin'],
                ['19/09/2014', 'Laboratorio', 'Perfil 20 OK', 'Lic. Rojas'],
              ],
            ) +
            '<p style="opacity:.7;margin:.5rem 0 0">CRUD completo: crear, ' +
            'consultar, actualizar y anular registros clinicos — POO en ' +
            'Java, app de escritorio Windows (2014, sin nube)</p>',
          en:
            chrome('Medical Records System · File') +
            '<p style="margin:.6rem 0 .3rem"><strong>Record 0913 · ' +
            'Marisol Peres</strong> — MPPE teacher · V-9.318.442 · 41 ' +
            'y/o · family members: 3</p>' +
            gridTable(
              ['Date', 'Reason', 'Diagnosis', 'Seen by'],
              [
                ['12/03/2014', 'Check-up', 'Healthy', 'Dr. Villasmil'],
                ['02/06/2014', 'Dentistry', 'Simple cavity', 'Dr. Marin'],
                ['19/09/2014', 'Laboratory', 'Panel 20 OK', 'Ms. Rojas'],
              ],
            ) +
            '<p style="opacity:.7;margin:.5rem 0 0">Full CRUD: create, ' +
            'read, update and void clinical records — OOP in Java, ' +
            'Windows desktop app (2014, no cloud)</p>',
        },
      },
    },
    {
      key: 'buscador',
      title: {
        es: 'Buscador de historia',
        en: 'Record search',
      },
      draw: drawDemoBuscar,
      panel: {
        brand: '#2f7fb0',
        html: {
          es:
            chrome('Sistema de Historias Medicas · Buscar') +
            '<input placeholder="Cedula o numero de historia ' +
            '(ej. V-9.318.442)">' +
            '<div style="border:1px solid #9a968a;padding:.6rem;' +
            'margin-top:.6rem;background:#fff"><strong>Historia 0913 · ' +
            'Marisol Peres</strong><br>Afiliada docente MPPE · ' +
            'antecedentes al dia · ultima consulta 19/09/2014' +
            '<p style="margin:.45rem 0 0">Consulta: <strong>0,2 s' +
            '</strong> — antes: varios minutos por paciente en el ' +
            'archivo fisico (y a veces una mañana entera)</p></div>' +
            '<p style="opacity:.7;margin:.5rem 0 0">La busqueda acepta ' +
            'cedula o numero — se acabaron los tres Perez equivocados</p>',
          en:
            chrome('Medical Records System · Search') +
            '<input placeholder="ID or record number ' +
            '(e.g. V-9.318.442)">' +
            '<div style="border:1px solid #9a968a;padding:.6rem;' +
            'margin-top:.6rem;background:#fff"><strong>Record 0913 · ' +
            'Marisol Peres</strong><br>MPPE affiliated teacher · history ' +
            'up to date · last visit 19/09/2014' +
            '<p style="margin:.45rem 0 0">Lookup: <strong>0.2 s' +
            '</strong> — before: several minutes per patient at the ' +
            'physical archive (sometimes a whole morning)</p></div>' +
            '<p style="opacity:.7;margin:.5rem 0 0">Search takes ID or ' +
            'number — no more three wrong Perez folders</p>',
        },
      },
    },
    {
      key: 'acceso',
      title: {
        es: 'Control de acceso',
        en: 'Access control',
      },
      draw: drawDemoAcceso,
      panel: {
        brand: '#2f7fb0',
        html: {
          es:
            chrome('Sistema de Historias Medicas · Acceso') +
            gridTable(
              ['Rol', 'Ficha', 'Signos', 'Datos de salud'],
              [
                ['Medico', 'ver/editar', 'ver', 'VER'],
                ['Enfermeria', 'ver', 'registrar', 'bloqueado'],
                ['Admision', 'registrar', 'bloqueado', 'bloqueado'],
              ],
            ) +
            '<p style="margin:.6rem 0 .2rem"><strong>Datos sensibles de ' +
            'salud</strong>: cada rol ve solo lo suyo, con clave propia ' +
            'y validacion de campos al registrar.</p>' +
            '<p style="opacity:.8;margin:0">El primer contacto de Pablo ' +
            'con datos sensibles — el mismo hilo que años despues ' +
            'reaparece en fintech.</p>',
          en:
            chrome('Medical Records System · Access') +
            gridTable(
              ['Role', 'File', 'Vitals', 'Health data'],
              [
                ['Doctor', 'view/edit', 'view', 'VIEW'],
                ['Nursing', 'view', 'record', 'locked'],
                ['Admissions', 'register', 'locked', 'locked'],
              ],
            ) +
            '<p style="margin:.6rem 0 .2rem"><strong>Sensitive health ' +
            'data</strong>: each role sees only its part, with its own ' +
            'password and field validation on entry.</p>' +
            '<p style="opacity:.8;margin:0">Pablo’s first contact ' +
            'with sensitive data — the same thread that resurfaces in ' +
            'fintech years later.</p>',
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
      id: `micro-ipasme-${roomIndex}-laptop${toggle.spot}`,
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

export default function buildIpasme(ctx: RoomCtx): RoomBuild {
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
  // Daniela trabaja en una encendida, las otras 2 se encienden con E
  const deskSpots: readonly (readonly [number, number])[] = [
    [-1.7, room.z - 3.3],
    [0.7, room.z - 3.8],
    [-2.4, room.z - 1.7],
  ]
  const office = officeLayout({
    roomIndex: room.index,
    state,
    spots: deskSpots,
    color: '#3d5a66',
    poweredSpots: new Set([0]),
    screenTheme,
    screenFor: (index) => LAPTOP_SCREENS[index] ?? LAPTOP_SCREENS[0],
  })
  group.add(office.group)
  staticColliders.push(...office.colliders)
  disposables.push(office)
  interactables.push(...laptopToggles(office, deskSpots, room.index))
  interactables.push(...office.seats)

  // consultorio (-X, fondo): camilla con rollo de papel, escritorio del
  // medico con tensiometro, negatoscopio con radiografia y la bascula —
  // lote blanco clinico fusionado (2 draw calls)
  group.add(
    outlinedMergedBoxes(
      [
        // camilla: colchoneta + cabecera inclinada + 4 patas
        { w: 0.72, h: 0.14, d: 1.8, x: -half + 1.7, y: 0.62, z: room.z - 4.6 },
        {
          w: 0.72,
          h: 0.1,
          d: 0.5,
          x: -half + 1.7,
          y: 0.78,
          z: room.z - 5.35,
        },
        {
          w: 0.06,
          h: 0.55,
          d: 0.06,
          x: -half + 1.4,
          y: 0.27,
          z: room.z - 5.32,
        },
        {
          w: 0.06,
          h: 0.55,
          d: 0.06,
          x: -half + 2.0,
          y: 0.27,
          z: room.z - 5.32,
        },
        {
          w: 0.06,
          h: 0.55,
          d: 0.06,
          x: -half + 1.4,
          y: 0.27,
          z: room.z - 3.9,
        },
        {
          w: 0.06,
          h: 0.55,
          d: 0.06,
          x: -half + 2.0,
          y: 0.27,
          z: room.z - 3.9,
        },
        // bascula de consultorio: base + columna + cabezal
        { w: 0.42, h: 0.06, d: 0.5, x: -half + 0.9, y: 0.03, z: room.z - 5.7 },
        {
          w: 0.08,
          h: 1.25,
          d: 0.08,
          x: -half + 0.9,
          y: 0.68,
          z: room.z - 5.85,
        },
        { w: 0.3, h: 0.14, d: 0.1, x: -half + 0.9, y: 1.36, z: room.z - 5.85 },
      ],
      toonMat('#f0eee8'),
      { castShadow: true },
    ),
  )
  staticColliders.push(
    footprint(-half + 1.7, room.z - 4.6, 0.9, 2.0),
    footprint(-half + 0.9, room.z - 5.75, 0.5, 0.5),
  )
  // rollo de papel en la cabecera de la camilla
  const units = unitGeo()
  const paperRoll = new Mesh(units.cylinder, toonMat('#ffffff'))
  paperRoll.scale.set(0.09, 0.72, 0.09)
  paperRoll.rotation.z = Math.PI / 2
  paperRoll.position.set(-half + 1.7, 0.9, room.z - 5.3)
  group.add(paperRoll)

  // escritorio del medico + tensiometro y estetoscopio (lote instrumental)
  group.add(
    desk({
      position: [-half + 1.5, 0, room.z - 2.6],
      rotationY: Math.PI / 2,
      width: 1.4,
      color: '#4a5a62',
    }),
    outlinedMergedBoxes(
      [
        // tensiometro: caja del manometro + brazalete enrollado
        {
          w: 0.16,
          h: 0.12,
          d: 0.12,
          x: -half + 1.4,
          y: 0.8,
          z: room.z - 2.9,
        },
        {
          w: 0.2,
          h: 0.07,
          d: 0.14,
          x: -half + 1.62,
          y: 0.77,
          z: room.z - 2.62,
        },
        // estetoscopio doblado sobre la tapa
        {
          w: 0.05,
          h: 0.03,
          d: 0.3,
          x: -half + 1.32,
          y: 0.755,
          z: room.z - 2.35,
        },
        {
          w: 0.16,
          h: 0.03,
          d: 0.05,
          x: -half + 1.38,
          y: 0.755,
          z: room.z - 2.22,
        },
      ],
      toonMat('#c8ccd2'),
      { castShadow: true },
    ),
  )
  staticColliders.push(footprint(-half + 1.5, room.z - 2.6, 0.8, 1.5))

  // negatoscopio en el muro -X: marco + radiografia iluminada
  const negatoscopio = new Group()
  const negFrame = boxMesh(0.06, 0.72, 0.94, toonMat('#8a9098'))
  negFrame.position.set(-half + 0.06, 1.8, room.z - 3.5)
  const radiografia = new Mesh(
    new PlaneGeometry(0.84, 0.62),
    new MeshBasicMaterial({ map: makeCanvasTexture(256, drawRadiografia) }),
  )
  radiografia.userData.noOutline = true
  radiografia.position.set(-half + 0.1, 1.8, room.z - 3.5)
  radiografia.rotation.y = Math.PI / 2
  negatoscopio.add(negFrame, radiografia)
  group.add(negatoscopio)

  // farmacia (+X, fondo): estanteria clinica + cajas de medicamentos
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
    // cajas de medicamentos (los unicos toques calidos de la sala)
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
      toonMat('#5b8fb8'),
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

  // archivador semivacio (+X, medio): el papel migrado — cajon abierto
  // con un par de carpetas manila y el hueco del tarjeton
  group.add(
    outlinedMergedBoxes(
      [
        { w: 0.6, h: 1.4, d: 0.5, x: half - 0.6, y: 0.7, z: room.z - 1.9 },
        // cajon superior deslizado abierto
        { w: 0.5, h: 0.24, d: 0.44, x: half - 0.6, y: 1.16, z: room.z - 1.62 },
      ],
      toonMat('#8a9098'),
      { castShadow: true },
    ),
    // dos carpetas manila solitarias dentro del cajon abierto
    mergedBoxes(
      [
        { w: 0.3, h: 0.16, d: 0.03, x: half - 0.68, y: 1.36, z: room.z - 1.6 },
        { w: 0.3, h: 0.14, d: 0.03, x: half - 0.6, y: 1.35, z: room.z - 1.55 },
        // el tarjeton que quedo de recuerdo en el hueco
        {
          w: 0.22,
          h: 0.12,
          d: 0.015,
          x: half - 0.46,
          y: 1.34,
          z: room.z - 1.68,
        },
      ],
      toonMat('#d9c39a'),
    ),
  )
  staticColliders.push(footprint(half - 0.6, room.z - 1.9, 0.7, 0.8))

  // admision (centro, frente): mostrador con ventanilla, PC bajo el
  // meson, monitor de historias, cruz roja y cartel IPASME
  group.add(
    outlinedMergedBoxes(
      [
        // frente + tapa + laterales del mostrador
        { w: 2.6, h: 1.0, d: 0.08, x: 1.7, y: 0.5, z: room.z + 3.18 },
        { w: 2.6, h: 0.06, d: 0.7, x: 1.7, y: 1.02, z: room.z + 2.9 },
        { w: 0.08, h: 1.0, d: 0.62, x: 0.44, y: 0.5, z: room.z + 2.88 },
        { w: 0.08, h: 1.0, d: 0.62, x: 2.96, y: 0.5, z: room.z + 2.88 },
      ],
      toonMat('#e8e6e0'),
      { castShadow: true },
    ),
    // PC de mostrador (torre 2014) bajo el meson — la que instala J.M.
    outlinedMergedBoxes(
      [{ w: 0.2, h: 0.5, d: 0.44, x: 2.5, y: 0.25, z: room.z + 2.8 }],
      toonMat('#2e3238'),
      { castShadow: true },
    ),
    // cruz medica roja sobre el mostrador
    mergedBoxes(
      [
        { w: 0.14, h: 0.5, d: 0.06, x: 1.7, y: 2.5, z: room.z + 3.16 },
        { w: 0.5, h: 0.14, d: 0.06, x: 1.7, y: 2.5, z: room.z + 3.16 },
      ],
      toonMat('#c0392b'),
    ),
  )
  staticColliders.push(footprint(1.7, room.z + 2.95, 2.7, 0.9))
  const admisionLabel = label('IPASME', { size: 0.22, color: theme.accent })
  admisionLabel.position.set(1.7, 2.05, room.z + 3.16)
  admisionLabel.rotation.y = Math.PI
  group.add(admisionLabel)

  // monitor de historias sobre el mostrador: micro "buscar una historia"
  // — la consulta inmediata que reemplazo los minutos de archivo
  const registro = switchableMonitor({
    position: [1.3, 1.02, room.z + 2.85],
    rotationY: Math.PI,
    width: 0.62,
    variants: {
      idle: {
        title: 'historias medicas',
        lines: [
          'paciente:  —',
          'cedula:    —',
          'turnos en cola: 2',
          'archivo papel: 3%',
        ],
        theme: screenTheme,
        dot: '#4dcc7a',
      },
      search: {
        title: 'buscar: V-9318442',
        lines: [
          '> cedula V-9318442',
          'historia 0913 · M. Peres',
          'antecedentes: al dia',
          'consulta: 0,2 s',
        ],
        theme: screenTheme,
        dot: '#4dcc7a',
      },
    },
    initial: 'idle',
  })
  group.add(registro.group)
  disposables.push(registro.screen)
  let searchUntil = -1
  interactables.push({
    id: `micro-ipasme-search-${room.index}`,
    x: 1.3,
    z: room.z + 2.85,
    radius: 1.9,
    label: SEARCH_LABEL,
    onActivate: () => {
      registro.screen.show('search')
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
      registro.screen.show('idle')
    }
  })

  // sala de espera (-X, frente): sillas en hilera mirando a admision
  const chairXs = [-4.9, -4.1, -3.3, -2.5] as const
  group.add(
    outlinedMergedBoxes(
      chairXs.flatMap((x) => [
        { w: 0.5, h: 0.06, d: 0.45, x, y: 0.46, z: room.z + 3.6 },
        { w: 0.5, h: 0.45, d: 0.06, x, y: 0.74, z: room.z + 3.82 },
        { w: 0.05, h: 0.44, d: 0.05, x: x - 0.2, y: 0.22, z: room.z + 3.7 },
        { w: 0.05, h: 0.44, d: 0.05, x: x + 0.2, y: 0.22, z: room.z + 3.7 },
      ]),
      toonMat('#5aa08c'),
      { inflate: 0.03, castShadow: true },
    ),
  )
  staticColliders.push(footprint(-3.7, room.z + 3.7, 3.0, 0.7))

  // dispensador de turnos junto a la hilera: E toma el siguiente numero
  const turnoPole = outlinedMergedBoxes(
    [
      { w: 0.3, h: 0.05, d: 0.3, x: -1.3, y: 0.025, z: room.z + 3.5 },
      { w: 0.1, h: 1.15, d: 0.1, x: -1.3, y: 0.62, z: room.z + 3.5 },
      { w: 0.36, h: 0.3, d: 0.12, x: -1.3, y: 1.34, z: room.z + 3.5 },
    ],
    toonMat(theme.accent),
    { castShadow: true },
  )
  group.add(turnoPole)
  staticColliders.push(footprint(-1.3, room.z + 3.5, 0.4, 0.4))
  const turnoVariant = (
    turno: number,
  ): { title: string; lines: string[]; theme: typeof screenTheme } => ({
    title: locale === 'es' ? 'su turno' : 'your ticket',
    lines: [`> ${turno} <`, locale === 'es' ? 'atendiendo: 51' : 'now: 51'],
    theme: screenTheme,
  })
  const turnoScreen = screenVariants({
    width: 0.32,
    height: 0.22,
    variants: {
      t0: turnoVariant(84),
      t1: turnoVariant(85),
      t2: turnoVariant(86),
    },
    initial: 't0',
  })
  turnoScreen.mesh.position.set(-1.3, 1.34, room.z + 3.57)
  turnoScreen.mesh.rotation.y = Math.PI
  group.add(turnoScreen.mesh)
  disposables.push(turnoScreen)
  let turnoIndex = 0
  interactables.push({
    id: `micro-ipasme-turno-${room.index}`,
    x: -1.3,
    z: room.z + 3.5,
    radius: 1.8,
    label: TURNO_LABEL,
    onActivate: () => {
      turnoIndex = (turnoIndex + 1) % 3
      turnoScreen.show(`t${turnoIndex}`)
      sfx.play('blip')
    },
  })

  // cuadros de rubro (wallArt): anatomia y carnet de afiliado
  // inspeccionables (muro -Z); flujo de atencion y cartel escolar
  // decorativos flanqueando la puerta al pasillo (muro +Z)
  const art = wallArt({
    roomIndex: room.index,
    theme,
    locale,
    onFicha: actions.openStory,
    frames: [
      {
        key: 'anatomia',
        position: [-3.6, 2, backZ + 0.08],
        rotationY: 0,
        draw: drawAnatomia,
        ficha: ART_FICHA_ANATOMIA,
      },
      {
        key: 'carnet-afiliado',
        position: [3.6, 2, backZ + 0.08],
        rotationY: 0,
        draw: drawCarnet,
        ficha: ART_FICHA_CARNET,
      },
      {
        key: 'flujo-atencion',
        position: [-3.6, 2, frontZ - 0.08],
        rotationY: Math.PI,
        draw: drawFlujo,
      },
      {
        key: 'ipasme-escuela',
        position: [3.6, 2, frontZ - 0.08],
        rotationY: Math.PI,
        draw: drawEscuela,
      },
    ],
  })
  staticColliders.push(...art.colliders)
  const sink = { group, interactables, updates }
  addProps(sink, art.props)

  // showcase del software junto a la puerta al pasillo (canon AC-6):
  // app de escritorio Windows 2014 — E cicla las 3 demos
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

  // NPCs del canon (2 enfoques, informe 09): Daniela (dev, sentada en su
  // laptop), Jose Miguel (dev/soporte, de rodillas instalando la PC del
  // mostrador), Yuleima (enfermera en ronda consultorio-admision),
  // Argenis (archivista junto al archivador semivacio) y el Dr.
  // Villasmil (medico/jefe supervisando el consultorio).
  const coworkers = npcCoworkers({
    roomIndex: room.index,
    openDialog: actions.openDialog,
    npcs: [
      {
        key: 'daniela',
        role: 'coworker',
        spec: {
          skin: '#e8b48c',
          hair: { style: 'bun', color: '#2a1a12' },
          top: '#4a6a8a',
          bottom: '#3a4048',
          accessory: 'glasses',
          faceSeed: 37,
        },
        position: [-1.7, 0, room.z - 4.85],
        rotationY: 0,
        pose: 'sit',
        dialog: IPASME_PRESENTE_DIALOGS.daniela,
      },
      {
        key: 'josemiguel',
        role: 'coworker',
        spec: {
          skin: '#c98f6a',
          hair: { style: 'spiky', color: '#14100c' },
          top: '#5a6a52',
          bottom: '#2e3238',
          accessory: 'badge',
          faceSeed: 73,
        },
        position: [2.5, 0, room.z + 2.2],
        rotationY: Math.PI,
        pose: 'kneel',
        dialog: IPASME_PRESENTE_DIALOGS.josemiguel,
      },
      {
        key: 'yuleima',
        role: 'staff',
        spec: {
          skin: '#d9a684',
          hair: { style: 'ponytail', color: '#1c1410' },
          top: '#eef0ec',
          bottom: '#7ecab0',
          accessory: 'badge',
          faceSeed: 45,
        },
        position: [-3.6, 0, room.z - 1.6],
        path: [
          [-3.6, room.z - 1.6],
          [0.2, room.z + 2.0],
          [-2.8, room.z + 2.6],
        ],
        speed: 0.55,
        dialog: IPASME_PRESENTE_DIALOGS.yuleima,
      },
      {
        key: 'argenis',
        role: 'staff',
        spec: {
          skin: '#b5825f',
          hair: { style: 'short', color: '#6a6a72' },
          top: '#8a8270',
          bottom: '#4a4438',
          accessory: 'badge',
          faceSeed: 58,
        },
        position: [half - 1.5, 0, room.z - 1.9],
        rotationY: Math.PI / 2,
        dialog: IPASME_PRESENTE_DIALOGS.argenis,
      },
      {
        key: 'villasmil',
        role: 'boss',
        spec: {
          skin: '#d9a684',
          hair: { style: 'short', color: '#8a8a92' },
          top: '#f0eee8',
          bottom: '#3a4048',
          accessory: 'tie',
          faceSeed: 91,
        },
        position: [-half + 2.6, 0, room.z - 3.4],
        rotationY: 0.9,
        dialog: IPASME_PRESENTE_DIALOGS.villasmil,
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
