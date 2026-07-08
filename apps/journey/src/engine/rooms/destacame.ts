/**
 * @module rooms/destacame (engine)
 * @description Sala 6 — Destacame UNIFICADA (fintech de inclusion
 *   financiera, CL+MX, 2021-hoy), construida al CANON de sala (plan
 *   journey-salas-estandar, informe 13). Reescribe la vieja CIMA: la
 *   sala junta las 2 experiencias (destacame-frontend +
 *   destacame-architect) en 2 AREAS reales — (A) PagaloAqui, pagar
 *   deudas con la banca (cards co-branded Santander / Santander
 *   Consumer / Scotiabank + WebPay), y (B) el producto Destacame (el
 *   gauge de score 459-760, la SuperApp, la expansion a Mexico). La
 *   arquitectura NO es una tercera area: son guiños intrinsecos
 *   (wallArt de microfrontends / microservicios Django / admin de
 *   campañas + pizarra del Design System, la mesa de reunion del lead,
 *   el panel de vibe coding heredado de cima). 5 NPCs conversables
 *   (decision del usuario: los 5 del informe; la dev frontend se llama
 *   Camila Espinoza para no chocar con GoodMeal). 2 showcases (uno por
 *   area, E cicla las demos de cada uno). Micros (decision: las 3):
 *   PAGAR LA DEUDA (el kiosco procesa WebPay con -95% y confirma),
 *   MEJORAR EL SCORE (la aguja del gauge sube de coral a verde) y
 *   LANZAR CAMPAÑA (el admin procesa en minutos lo que tomaba horas).
 *   La micro Chile/Mexico de la entrada fue ELIMINADA (mandato del
 *   informe). Kit informativo ESTANDAR + CTA de contacto + puerta
 *   PROXIMAMENTE. Paredes blanco hueso; el unico acento estructural es
 *   el azul Destacame #0052cc — los rojos bancarios viven SOLO dentro
 *   de las cards del showcase A.
 */
import { Group, Mesh, MeshBasicMaterial, OctahedronGeometry } from 'three'
import type { Box2 } from '../../lib/collision'
import type { Locale } from '../../lib/rooms'
import { sfx } from '../audio'
import type { NpcHandle } from '../character'
import { DESTACAME_PRESENTE_DIALOGS } from '../dialogs/destacame-presente'
import type { Interactable } from '../state'
import {
  boxMesh,
  disposeDeep,
  label,
  makeCanvasTexture,
  mergedBoxes,
  outlinedMergedBoxes,
  outlineGroup,
  screenPanel,
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
  type ScreenSwap,
  type ShowcaseDemo,
  screenVariants,
  softwareShowcase,
  switchableMonitor,
  wallArt,
} from './props'

const DEUDA_LABEL = {
  es: 'Pagar la deuda (WebPay)',
  en: 'Pay the debt (WebPay)',
} as const

const SCORE_LABEL = {
  es: 'Mejorar el score',
  en: 'Improve the score',
} as const

const CAMPANA_LABEL = {
  es: 'Lanzar una campaña',
  en: 'Launch a campaign',
} as const

const CODE_LABEL = {
  es: 'Ver el codigo del equipo (IA / Python / TS)',
  en: 'Browse the team code (AI / Python / TS)',
} as const

const CONTACT_LABEL = {
  es: 'Contactar a Pablo',
  en: 'Contact Pablo',
} as const

const LAPTOP_LABELS = {
  on: { es: 'Encender la laptop libre', en: 'Power on the spare laptop' },
  off: { es: 'Apagar la laptop libre', en: 'Power off the spare laptop' },
} as const

/** Pantallas del rincon dev: Nuxt, el microservicio y el admin. */
const LAPTOP_SCREENS = [
  {
    title: 'DeudaCard.vue — Nuxt',
    lines: [
      '<script setup lang="ts">',
      'const { deuda } = defineProps<{',
      '  deuda: DeudaResumen',
      '}>()  // -95% aplicado',
    ],
  },
  {
    title: 'campanas/service.py',
    lines: [
      '@transaction.atomic',
      'def lanzar(campana):',
      '    targets = scoring.filtrar(',
      '        pais=campana.pais)',
    ],
  },
  {
    title: 'panel · plataforma',
    lines: [
      'campañas: 4 min (antes horas)',
      'equipos en paralelo: 3',
      'paises: CL + MX',
      'deuda tecnica ↓',
    ],
  },
] as const

// --- paleta del rubro (informe 13) ---

const DTC_BLUE = '#0052cc'
const DTC_BLUE_DARK = '#003d99'
const CARD_BLUE = '#e6f0ff'
const SANT_RED = '#ea1d25'
const SCOTIA_RED = '#ec111a'
const OK_GREEN = '#22c55e'
const MORA_CORAL = '#ef4444'
const COIN_GOLD = '#d9a92b'
const PANEL_INK = '#10182b'
// mobiliario CC0 (Kenney Furniture Kit, ver public/models/CREDITS.md)
const DESK_URL = '/models/furniture/desk.glb'
const CHAIR_URL = '/models/furniture/chairDesk.glb'
// tono claro para los pedestales de kiosco (antes navy oscuro PANEL_INK)
const KIOSK_DESK = '#aeb8cc'

// --- laminas de los cuadros (wallArt): tinta plana sobre papel claro ---

const ART_PAPER = '#f4efe2'
const ART_INK = '#1c2030'

function artBase(ctx: CanvasRenderingContext2D, size: number): void {
  ctx.fillStyle = ART_PAPER
  ctx.fillRect(0, 0, size, size)
  ctx.strokeStyle = ART_INK
  ctx.globalAlpha = 0.35
  ctx.lineWidth = 3
  ctx.strokeRect(10, 10, size - 20, size - 20)
  ctx.globalAlpha = 1
}

/** Microfrontends: el shell central y los remotes hacia los bancos. */
function drawMicrofrontends(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 15px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('MICROFRONTENDS', 20, 36)
  // shell/host central
  ctx.fillStyle = DTC_BLUE
  ctx.fillRect(96, 58, 64, 34)
  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('shell', 112, 79)
  // remotes: productos fintech colgando del shell
  const remotes: readonly (readonly [number, string])[] = [
    [34, 'deudas'],
    [104, 'score'],
    [174, 'credito'],
  ]
  ctx.strokeStyle = DTC_BLUE
  ctx.lineWidth = 3
  for (const [x, name] of remotes) {
    ctx.beginPath()
    ctx.moveTo(128, 92)
    ctx.lineTo(x + 24, 128)
    ctx.stroke()
    ctx.strokeRect(x, 128, 52, 28)
    ctx.fillStyle = ART_INK
    ctx.font = 'bold 9px "Space Mono", ui-monospace, monospace'
    ctx.fillText(name, x + 5, 146)
    ctx.fillStyle = DTC_BLUE
  }
  // flechas de fork hacia las entidades bancarias
  ctx.strokeStyle = ART_INK
  ctx.globalAlpha = 0.7
  ctx.setLineDash([4, 4])
  for (const x of [60, 130, 200]) {
    ctx.beginPath()
    ctx.moveTo(x, 156)
    ctx.lineTo(x, 186)
    ctx.stroke()
  }
  ctx.setLineDash([])
  ctx.globalAlpha = 1
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 10px "Space Mono", ui-monospace, monospace'
  ctx.fillText('santander · scotiabank · ...', 34, 202)
  ctx.globalAlpha = 0.6
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('equipos en paralelo, sin pisarse', 20, 238)
  ctx.globalAlpha = 1
}

/** Grafo de microservicios Django (la idea del viejo cima, en lamina). */
function drawMicroservicios(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 15px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('MICROSERVICIOS', 20, 36)
  const nodes: readonly (readonly [number, number, string])[] = [
    [128, 70, 'gateway'],
    [58, 130, 'scoring'],
    [128, 140, 'pagos'],
    [198, 130, 'campañas'],
    [88, 196, 'usuarios'],
    [168, 196, 'deudas'],
  ]
  const edges: readonly (readonly [number, number])[] = [
    [0, 1],
    [0, 2],
    [0, 3],
    [1, 4],
    [2, 4],
    [2, 5],
    [3, 5],
  ]
  ctx.strokeStyle = DTC_BLUE
  ctx.lineWidth = 2.5
  for (const [a, b] of edges) {
    const na = nodes[a]
    const nb = nodes[b]
    if (!na || !nb) {
      continue
    }
    ctx.beginPath()
    ctx.moveTo(na[0], na[1])
    ctx.lineTo(nb[0], nb[1])
    ctx.stroke()
  }
  for (const [x, y, name] of nodes) {
    ctx.fillStyle = ART_PAPER
    ctx.strokeStyle = ART_INK
    ctx.lineWidth = 2.5
    ctx.beginPath()
    ctx.arc(x, y, 19, 0, Math.PI * 2)
    ctx.fill()
    ctx.stroke()
    ctx.fillStyle = ART_INK
    ctx.font = 'bold 8px "Space Mono", ui-monospace, monospace'
    ctx.textAlign = 'center'
    ctx.fillText(name, x, y + 3)
    ctx.textAlign = 'left'
  }
  ctx.fillStyle = ART_INK
  ctx.globalAlpha = 0.6
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('python/django detras del frontend', 20, 238)
  ctx.globalAlpha = 1
}

/** El admin de campañas: la barra de horas contra la de minutos. */
function drawCampanas(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 15px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('CAMPAÑAS:', 20, 36)
  ctx.fillText('HORAS → MINUTOS', 20, 56)
  // antes: barra larga coral (a mano)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 10px "Space Mono", ui-monospace, monospace'
  ctx.fillText('antes (a mano)', 24, 92)
  ctx.fillStyle = MORA_CORAL
  ctx.fillRect(24, 100, 200, 22)
  ctx.fillStyle = '#ffffff'
  ctx.fillText('~4 horas', 84, 115)
  // despues: barra corta azul (el admin de Pablo)
  ctx.fillStyle = ART_INK
  ctx.fillText('despues (admin)', 24, 152)
  ctx.fillStyle = DTC_BLUE
  ctx.fillRect(24, 160, 34, 22)
  ctx.fillStyle = ART_INK
  ctx.fillText('4 min', 66, 175)
  ctx.globalAlpha = 0.6
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('automatizar un proceso manual', 20, 222)
  ctx.fillText('tambien es producto', 20, 238)
  ctx.globalAlpha = 1
}

/** Pizarra del Design System: tokens y componentes (decorativa). */
function drawDesignSystem(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 15px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('DESIGN SYSTEM', 20, 36)
  // paleta de tokens
  const tokens: readonly string[] = [
    DTC_BLUE,
    DTC_BLUE_DARK,
    OK_GREEN,
    MORA_CORAL,
  ]
  tokens.forEach((color, index) => {
    ctx.fillStyle = color
    ctx.fillRect(24 + index * 34, 56, 26, 26)
  })
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 9px "Space Mono", ui-monospace, monospace'
  ctx.fillText('--color-primary · --ok · --mora', 24, 100)
  // componentes: boton, input, card
  ctx.fillStyle = DTC_BLUE
  ctx.fillRect(24, 118, 84, 24)
  ctx.fillStyle = '#ffffff'
  ctx.fillText('Boton', 48, 134)
  ctx.strokeStyle = ART_INK
  ctx.lineWidth = 2
  ctx.strokeRect(120, 118, 110, 24)
  ctx.strokeRect(24, 154, 206, 52)
  ctx.fillStyle = ART_INK
  ctx.fillText('Input', 128, 134)
  ctx.fillText('Card de deuda', 32, 172)
  ctx.fillStyle = CARD_BLUE
  ctx.fillRect(32, 180, 190, 18)
  ctx.fillStyle = ART_INK
  ctx.globalAlpha = 0.6
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('un solo lenguaje entre equipos', 20, 238)
  ctx.globalAlpha = 1
}

const ART_FICHA_MFE = {
  title: {
    es: 'Microfrontends: equipos en paralelo',
    en: 'Microfrontends: teams in parallel',
  },
  paragraphs: {
    es: [
      'Cuando Pablo paso de senior a arquitecto (2022), el frontend ' +
        'de Destacame crecia mas rapido que su estructura: cada ' +
        'producto fintech reescribia lo mismo y los equipos se ' +
        'pisaban. Su respuesta fue una arquitectura de ' +
        'MICROFRONTENDS: un shell comun y productos que se enchufan ' +
        'como remotes, con estandares y patrones definidos ENTRE ' +
        'equipos.',
      'El efecto fue estructural: los equipos desarrollan en ' +
        'paralelo con menos acoplamiento, una feature nueva arranca ' +
        'sobre base conocida, y la misma plataforma sostiene los ' +
        'productos de Chile y Mexico.',
      'Este diagrama es el mapa de esa decision: el shell al ' +
        'centro, los productos como remotes y las flechas punteadas ' +
        'hacia los portales co-branded de cada banco.',
    ],
    en: [
      'When Pablo moved from senior to architect (2022), the ' +
        'Destacame frontend was growing faster than its structure: ' +
        'every fintech product rewrote the same things and teams ' +
        'stepped on each other. His answer was a MICROFRONTENDS ' +
        'architecture: a common shell with products plugged in as ' +
        'remotes, with standards and patterns defined ACROSS teams.',
      'The effect was structural: teams build in parallel with ' +
        'less coupling, a new feature starts on known ground, and ' +
        'the same platform carries the products of Chile and ' +
        'Mexico.',
      'This diagram maps that decision: the shell at the centre, ' +
        'the products as remotes and the dotted arrows towards each ' +
        'bank’s co-branded portal.',
    ],
  },
} as const

const ART_FICHA_MSVC = {
  title: {
    es: 'Microservicios Python/Django',
    en: 'Python/Django microservices',
  },
  paragraphs: {
    es: [
      'Pablo llego a Destacame como frontend puro — Vue y Nuxt — y ' +
        'en unos ocho meses ya construia backend: aprendio Python y ' +
        'Django desde cero, deliberadamente, para crecer a full ' +
        'stack.',
      'Ese salto termino en microservicios Python/Django integrados ' +
        'con el frontend: scoring, pagos, campañas, usuarios, ' +
        'deudas — cada dominio como servicio propio, hablando con ' +
        'las interfaces Vue/Nuxt que el mismo conocia de memoria.',
      'Conocer ambos lados es lo que hace confiable una plataforma ' +
        'que mueve deudas y creditos reales en dos paises: quien ' +
        'diseña la pantalla sabe exactamente que hay detras del ' +
        'endpoint.',
    ],
    en: [
      'Pablo joined Destacame as pure frontend — Vue and Nuxt — ' +
        'and within about eight months he was building backend: he ' +
        'learned Python and Django from scratch, deliberately, to ' +
        'grow full stack.',
      'That leap ended in Python/Django microservices wired into ' +
        'the frontend: scoring, payments, campaigns, users, debts — ' +
        'each domain as its own service, talking to the Vue/Nuxt ' +
        'interfaces he knew by heart.',
      'Knowing both sides is what makes a platform that moves real ' +
        'debt and credit across two countries trustworthy: whoever ' +
        'designs the screen knows exactly what sits behind the ' +
        'endpoint.',
    ],
  },
} as const

const ART_FICHA_CAMPANAS = {
  title: {
    es: 'El admin de campañas: de horas a minutos',
    en: 'The campaign admin: hours to minutes',
  },
  paragraphs: {
    es: [
      'Lanzar una campaña — elegir el segmento, la oferta, el canal ' +
        '— se hacia A MANO sobre planillas y tomaba horas de un ' +
        'operador, cada vez, con errores que llegaban a clientes ' +
        'reales.',
      'Pablo construyo un admin interno que automatizo el proceso ' +
        'completo: configurar, validar y lanzar. Lo que tomaba ' +
        'horas hoy toma MINUTOS, y el equipo de campañas dejo de ' +
        'vivir dentro de las planillas.',
      'Es el logro menos visible y mas querido de la sala: una ' +
        'herramienta interna no la ve ningun cliente, pero devuelve ' +
        'horas de trabajo humano cada semana. Cruza la grieta y ' +
        'conoce a Nicolas, el operador que vivia ese proceso a mano.',
    ],
    en: [
      'Launching a campaign — picking the segment, the offer, the ' +
        'channel — was done BY HAND over spreadsheets and took an ' +
        'operator hours, every time, with errors reaching real ' +
        'customers.',
      'Pablo built an internal admin that automated the whole ' +
        'process: configure, validate, launch. What took hours now ' +
        'takes MINUTES, and the campaigns team no longer lives ' +
        'inside spreadsheets.',
      'It is the least visible, best loved achievement in the ' +
        'room: no customer ever sees an internal tool, yet it gives ' +
        'back hours of human work every week. Cross the rift and ' +
        'meet Nicolas, the operator who lived that manual process.',
    ],
  },
} as const

// --- demos del showcase A: PagaloAqui, cards co-branded por banco ---

interface BankDemoData {
  bank: string
  brand: string
  titulo: string
  concepto: string
  monto: string
  boton: string
}

/** Chrome co-branded: barra del banco sobre fondo blanco. */
function bankChrome(
  ctx: CanvasRenderingContext2D,
  size: number,
  data: BankDemoData,
): void {
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, size, size)
  ctx.fillStyle = data.brand
  ctx.fillRect(0, 0, size, 26)
  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 11px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText(`${data.bank} · PagaloAqui`, 8, 17)
}

/** Card de deuda co-branded con el ciclo pagar -> WebPay -> pagado. */
function drawBankDemo(
  data: BankDemoData,
): (ctx: CanvasRenderingContext2D, size: number, t: number) => void {
  return (ctx, size, t) => {
    bankChrome(ctx, size, data)
    ctx.fillStyle = PANEL_INK
    ctx.font = 'bold 12px "Space Grotesk", system-ui, sans-serif'
    ctx.fillText(data.titulo, 12, 48)
    // la card de la deuda
    ctx.strokeStyle = data.brand
    ctx.lineWidth = 2
    ctx.strokeRect(12, 60, size - 24, 74)
    ctx.fillStyle = PANEL_INK
    ctx.font = '10px "Space Mono", ui-monospace, monospace'
    ctx.fillText(data.concepto, 20, 80)
    ctx.font = 'bold 20px "Space Mono", ui-monospace, monospace'
    ctx.fillText(data.monto, 20, 106)
    ctx.fillStyle = OK_GREEN
    ctx.font = 'bold 10px "Space Mono", ui-monospace, monospace'
    ctx.fillText('descuento aplicado ✓', 20, 126)
    // ciclo del boton: pagar (pulsa) -> WebPay procesando -> pagado
    const cycle = (t * 0.5) % 6
    if (cycle < 2.4) {
      const pulse = 0.75 + Math.sin(t * 3) * 0.25
      ctx.globalAlpha = pulse
      ctx.fillStyle = data.brand
      ctx.fillRect(12, 150, size - 24, 26)
      ctx.globalAlpha = 1
      ctx.fillStyle = '#ffffff'
      ctx.font = 'bold 11px "Space Grotesk", system-ui, sans-serif'
      ctx.fillText(data.boton, 20, 167)
    } else if (cycle < 3.8) {
      ctx.fillStyle = CARD_BLUE
      ctx.fillRect(12, 150, size - 24, 26)
      const k = (cycle - 2.4) / 1.4
      ctx.fillStyle = data.brand
      ctx.fillRect(12, 150, (size - 24) * k, 26)
      ctx.fillStyle = PANEL_INK
      ctx.font = 'bold 10px "Space Mono", ui-monospace, monospace'
      ctx.fillText('WebPay · procesando...', 56, 167)
    } else {
      ctx.fillStyle = OK_GREEN
      ctx.fillRect(12, 150, size - 24, 26)
      ctx.fillStyle = '#ffffff'
      ctx.font = 'bold 11px "Space Grotesk", system-ui, sans-serif'
      ctx.fillText('Pago confirmado ✓', 66, 167)
    }
    // sello WebPay
    ctx.strokeStyle = PANEL_INK
    ctx.lineWidth = 1.5
    ctx.strokeRect(12, 190, 74, 20)
    ctx.fillStyle = PANEL_INK
    ctx.font = 'bold 9px "Space Mono", ui-monospace, monospace'
    ctx.fillText('WebPay', 28, 204)
    ctx.globalAlpha = 0.6
    ctx.fillText('100% online · sin sucursal', 96, 204)
    ctx.globalAlpha = 1
  }
}

// --- demos del showcase B: el producto Destacame (score + Buro MX) ---

/** Gauge semicircular 459-760 con la aguja animada. */
function drawGaugeArc(
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  radius: number,
  needleK: number,
): void {
  const segments: readonly (readonly [number, number, string])[] = [
    [Math.PI, Math.PI * 1.33, MORA_CORAL],
    [Math.PI * 1.33, Math.PI * 1.66, '#e8b93a'],
    [Math.PI * 1.66, Math.PI * 2, OK_GREEN],
  ]
  ctx.lineWidth = 12
  for (const [from, to, color] of segments) {
    ctx.strokeStyle = color
    ctx.beginPath()
    ctx.arc(cx, cy, radius, from, to)
    ctx.stroke()
  }
  // la aguja: needleK 0 = coral (izq), 1 = verde (der)
  const angle = Math.PI + needleK * Math.PI
  ctx.strokeStyle = PANEL_INK
  ctx.lineWidth = 4
  ctx.beginPath()
  ctx.moveTo(cx, cy)
  ctx.lineTo(
    cx + Math.cos(angle) * (radius - 14),
    cy + Math.sin(angle) * (radius - 14),
  )
  ctx.stroke()
  ctx.fillStyle = PANEL_INK
  ctx.beginPath()
  ctx.arc(cx, cy, 5, 0, Math.PI * 2)
  ctx.fill()
}

/** Demo B1: destacame.cl — el dashboard del score con el descuento. */
function drawDemoScoreCl(
  ctx: CanvasRenderingContext2D,
  size: number,
  t: number,
): void {
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, size, size)
  ctx.fillStyle = DTC_BLUE
  ctx.fillRect(0, 0, size, 26)
  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 11px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('destacame.cl · Tu Score', 8, 17)
  // el gauge respira entre 0.55 y 0.7 (score sano subiendo)
  const k = 0.55 + (Math.sin(t * 0.9) + 1) * 0.075
  drawGaugeArc(ctx, 128, 108, 62, k)
  ctx.fillStyle = PANEL_INK
  ctx.font = 'bold 22px "Space Mono", ui-monospace, monospace'
  ctx.fillText('612', 108, 104)
  ctx.font = 'bold 9px "Space Mono", ui-monospace, monospace'
  ctx.fillText('459', 52, 126)
  ctx.fillText('760', 182, 126)
  // card del descuento en deuda vencida
  ctx.fillStyle = CARD_BLUE
  ctx.fillRect(12, 140, size - 24, 40)
  ctx.fillStyle = PANEL_INK
  ctx.font = 'bold 10px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('Hasta 95% de descuento', 20, 157)
  ctx.fillText('en tu deuda vencida', 20, 171)
  ctx.fillStyle = DTC_BLUE
  ctx.fillRect(12, 190, 140, 24)
  ctx.fillStyle = '#ffffff'
  ctx.fillText('Ver mis descuentos', 22, 206)
  ctx.fillStyle = PANEL_INK
  ctx.globalAlpha = 0.6
  ctx.font = '9px "Space Mono", ui-monospace, monospace'
  ctx.fillText('gratis · CL', 176, 206)
  ctx.globalAlpha = 1
}

/** Demo B2: destacame.com.mx — el Score de Buro gratis en el movil. */
function drawDemoBuroMx(
  ctx: CanvasRenderingContext2D,
  size: number,
  t: number,
): void {
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, size, size)
  ctx.fillStyle = DTC_BLUE
  ctx.fillRect(0, 0, size, 26)
  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 11px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('destacame.com.mx · Buro', 8, 17)
  // el marco del movil
  ctx.strokeStyle = PANEL_INK
  ctx.lineWidth = 3
  ctx.strokeRect(70, 40, 116, 178)
  const k = 0.6 + (Math.sin(t * 0.7) + 1) * 0.06
  drawGaugeArc(ctx, 128, 110, 40, k)
  ctx.fillStyle = PANEL_INK
  ctx.font = 'bold 15px "Space Mono", ui-monospace, monospace'
  ctx.fillText('672', 114, 106)
  ctx.font = 'bold 9px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('Tu Score de Buro', 88, 132)
  ctx.fillText('GRATIS', 112, 145)
  // recomendaciones con check
  ctx.fillStyle = OK_GREEN
  ctx.font = 'bold 9px "Space Mono", ui-monospace, monospace'
  ctx.fillText('✓ sin afectar historial', 80, 165)
  ctx.fillText('✓ creditos a tu medida', 80, 180)
  ctx.fillStyle = DTC_BLUE
  ctx.fillRect(80, 190, 96, 18)
  ctx.fillStyle = '#ffffff'
  ctx.fillText('Consultar', 102, 203)
  ctx.fillStyle = PANEL_INK
  ctx.globalAlpha = 0.6
  ctx.fillText('alianza Buro de Credito · MX', 34, 236)
  ctx.globalAlpha = 1
}

/** Los 3 mockups HTML del showcase A (PagaloAqui, co-branded). */
function showcaseADemos(): ShowcaseDemo[] {
  const chrome = (brand: string, title: string): string =>
    `<div style="background:${brand};color:#fff;padding:.45rem .6rem;` +
    `font-weight:700">${title}</div>`
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
  const brandBtn = (brand: string, text: string): string =>
    `<span style="display:inline-block;background:${brand};color:#fff;` +
    `padding:.3rem .8rem;font-weight:700;margin:.3rem 0">${text}</span>`
  const credito = (es: boolean): string =>
    es
      ? '<p style="opacity:.7;margin:.5rem 0 0">PagaloAqui: pagar deudas ' +
        'con la banca 100% online via WebPay, co-branded por entidad. ' +
        'Pablo construyo estas interfaces cuidando la validacion y los ' +
        'datos sensibles de cada pago (Destacame, 2021-hoy)</p>'
      : '<p style="opacity:.7;margin:.5rem 0 0">PagaloAqui: settling ' +
        'bank debt 100% online through WebPay, co-branded per entity. ' +
        'Pablo built these interfaces guarding the validation and ' +
        'sensitive data behind every payment (Destacame, 2021-today)</p>'
  return [
    {
      key: 'santander',
      title: {
        es: 'PagaloAqui · Santander',
        en: 'PagaloAqui · Santander',
      },
      draw: drawBankDemo({
        bank: 'Santander',
        brand: SANT_RED,
        titulo: 'Tu deuda con Banco Santander',
        concepto: 'Consumo · 3 cuotas atrasadas',
        monto: '$842.500',
        boton: 'Pagar ahora',
      }),
      panel: {
        brand: SANT_RED,
        html: {
          es:
            chrome(SANT_RED, 'Santander · PagaloAqui') +
            gridTable(
              ['Concepto', 'Detalle'],
              [
                ['Deuda total', '$842.500'],
                ['Estado', 'Vencida · 3 cuotas atrasadas'],
                ['Descuento por pago', 'aplicado ✓'],
                ['Medio de pago', 'WebPay'],
              ],
            ) +
            brandBtn(SANT_RED, 'Pagar ahora') +
            '<p style="margin:.4rem 0 0"><strong style="color:#22c55e">' +
            'Pago confirmado ✓</strong> — deuda regularizada 100% ' +
            'online, sin sucursal</p>' +
            credito(true),
          en:
            chrome(SANT_RED, 'Santander · PagaloAqui') +
            gridTable(
              ['Item', 'Detail'],
              [
                ['Total debt', '$842,500'],
                ['Status', 'Overdue · 3 late instalments'],
                ['Payment discount', 'applied ✓'],
                ['Payment method', 'WebPay'],
              ],
            ) +
            brandBtn(SANT_RED, 'Pay now') +
            '<p style="margin:.4rem 0 0"><strong style="color:#22c55e">' +
            'Payment confirmed ✓</strong> — debt regularised 100% ' +
            'online, no branch visit</p>' +
            credito(false),
        },
      },
    },
    {
      key: 'consumer',
      title: {
        es: 'PagaloAqui · Santander Consumer',
        en: 'PagaloAqui · Santander Consumer',
      },
      draw: drawBankDemo({
        bank: 'Santander Consumer',
        brand: SANT_RED,
        titulo: 'Paga tu Cuota',
        concepto: 'Credito automotriz · cuota del mes',
        monto: '$126.900',
        boton: 'Pagar cuota',
      }),
      panel: {
        brand: SANT_RED,
        html: {
          es:
            chrome(SANT_RED, 'Santander Consumer · Paga tu Cuota') +
            gridTable(
              ['Concepto', 'Detalle'],
              [
                ['Cuota del mes', '$126.900'],
                ['Credito', 'Automotriz'],
                ['Vencimiento', '05 del mes'],
                ['Medio de pago', 'WebPay'],
              ],
            ) +
            brandBtn(SANT_RED, 'Pagar cuota') +
            '<p style="margin:.4rem 0 0">Saldo restante visible y sin ' +
            'letra chica — la cuota queda al dia en una sesion</p>' +
            credito(true),
          en:
            chrome(SANT_RED, 'Santander Consumer · Pay your instalment') +
            gridTable(
              ['Item', 'Detail'],
              [
                ['This month’s instalment', '$126,900'],
                ['Credit', 'Auto loan'],
                ['Due date', '5th of the month'],
                ['Payment method', 'WebPay'],
              ],
            ) +
            brandBtn(SANT_RED, 'Pay instalment') +
            '<p style="margin:.4rem 0 0">Remaining balance visible, no ' +
            'fine print — the instalment settles in one session</p>' +
            credito(false),
        },
      },
    },
    {
      key: 'scotiabank',
      title: {
        es: 'PagaloAqui · Scotiabank',
        en: 'PagaloAqui · Scotiabank',
      },
      draw: drawBankDemo({
        bank: 'Scotiabank',
        brand: SCOTIA_RED,
        titulo: 'Regulariza tu deuda vencida',
        concepto: 'Pago total o repactacion',
        monto: '$1.238.400',
        boton: 'Regularizar 100% online',
      }),
      panel: {
        brand: SCOTIA_RED,
        html: {
          es:
            chrome(SCOTIA_RED, 'Scotiabank · Soluciones') +
            gridTable(
              ['Concepto', 'Detalle'],
              [
                ['Deuda vencida', '$1.238.400'],
                ['Alternativa 1', 'Pago total con descuento'],
                ['Alternativa 2', 'Repactacion en cuotas'],
                ['Medio de pago', 'WebPay'],
              ],
            ) +
            brandBtn(SCOTIA_RED, 'Regularizar 100% online') +
            '<p style="margin:.4rem 0 0">El cliente elige la ' +
            'alternativa, ve el descuento de frente y paga seguro</p>' +
            credito(true),
          en:
            chrome(SCOTIA_RED, 'Scotiabank · Solutions') +
            gridTable(
              ['Item', 'Detail'],
              [
                ['Overdue debt', '$1,238,400'],
                ['Option 1', 'Full payment with discount'],
                ['Option 2', 'Repactation in instalments'],
                ['Payment method', 'WebPay'],
              ],
            ) +
            brandBtn(SCOTIA_RED, 'Regularise 100% online') +
            '<p style="margin:.4rem 0 0">The customer picks the ' +
            'option, sees the discount up front and pays safely</p>' +
            credito(false),
        },
      },
    },
  ]
}

/** Los 2 mockups HTML del showcase B (producto Destacame, CL + MX). */
function showcaseBDemos(): ShowcaseDemo[] {
  const chrome = (title: string): string =>
    `<div style="background:${DTC_BLUE};color:#fff;padding:.45rem .6rem;` +
    `font-weight:700">${title}</div>`
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
  const blueBtn = (text: string): string =>
    `<span style="display:inline-block;background:${DTC_BLUE};color:#fff;` +
    `padding:.3rem .8rem;font-weight:700;margin:.3rem 0">${text}</span>`
  return [
    {
      key: 'score-cl',
      title: {
        es: 'destacame.cl · Tu Score',
        en: 'destacame.cl · Your Score',
      },
      draw: drawDemoScoreCl,
      panel: {
        brand: DTC_BLUE,
        html: {
          es:
            chrome('destacame.cl · Tu salud financiera') +
            gridTable(
              ['Indicador', 'Valor'],
              [
                ['Tu score', '612 (de 459 a 760)'],
                ['Tendencia', 'subiendo ↑'],
                ['Deuda vencida', 'hasta 95% de descuento'],
                ['Creditos', 'preaprobados segun score'],
              ],
            ) +
            blueBtn('Ver mis descuentos') +
            '<p style="margin:.4rem 0 0">Consultar y mejorar el score ' +
            'es gratis: la app muestra que lo baja y que lo sube</p>' +
            '<p style="opacity:.7;margin:.5rem 0 0">La SuperApp de ' +
            'salud financiera: millones de usuarios en Chile. Pablo ' +
            'construyo sus interfaces Vue/Nuxt y luego la arquitectura ' +
            'que las sostiene (2021-hoy)</p>',
          en:
            chrome('destacame.cl · Your financial health') +
            gridTable(
              ['Indicator', 'Value'],
              [
                ['Your score', '612 (from 459 to 760)'],
                ['Trend', 'rising ↑'],
                ['Overdue debt', 'up to 95% off'],
                ['Credit', 'pre-approved by score'],
              ],
            ) +
            blueBtn('See my discounts') +
            '<p style="margin:.4rem 0 0">Checking and improving the ' +
            'score is free: the app shows what drags it and what ' +
            'lifts it</p>' +
            '<p style="opacity:.7;margin:.5rem 0 0">The financial ' +
            'health SuperApp: millions of users in Chile. Pablo built ' +
            'its Vue/Nuxt interfaces and then the architecture that ' +
            'carries them (2021-today)</p>',
        },
      },
    },
    {
      key: 'buro-mx',
      title: {
        es: 'destacame.com.mx · Score de Buro',
        en: 'destacame.com.mx · Buro Score',
      },
      draw: drawDemoBuroMx,
      panel: {
        brand: DTC_BLUE,
        html: {
          es:
            chrome('destacame.com.mx · Tu Score de Buro GRATIS') +
            gridTable(
              ['Indicador', 'Valor'],
              [
                ['Score de Buro', '672 · gratis'],
                ['Historial', 'sin afectarlo ✓'],
                ['Alianza', 'Buro de Credito'],
                ['Recomendaciones', 'creditos y tarjetas a tu medida'],
              ],
            ) +
            blueBtn('Consultar gratis') +
            '<p style="margin:.4rem 0 0">Contacto por WhatsApp y ' +
            'creditos por niveles segun tu score</p>' +
            '<p style="opacity:.7;margin:.5rem 0 0">La expansion a ' +
            'Mexico: la misma plataforma orquestada para dos paises — ' +
            'la arquitectura de microfrontends y microservicios que ' +
            'Pablo lidero lo hizo posible (2022-hoy)</p>',
          en:
            chrome('destacame.com.mx · Your FREE Buro Score') +
            gridTable(
              ['Indicator', 'Value'],
              [
                ['Buro score', '672 · free'],
                ['Credit history', 'unaffected ✓'],
                ['Alliance', 'Buro de Credito'],
                ['Recommendations', 'credit and cards for your tier'],
              ],
            ) +
            blueBtn('Check for free') +
            '<p style="margin:.4rem 0 0">WhatsApp support and tiered ' +
            'credit based on your score</p>' +
            '<p style="opacity:.7;margin:.5rem 0 0">The Mexico ' +
            'expansion: one platform orchestrated for two countries — ' +
            'made possible by the microfrontend and microservice ' +
            'architecture Pablo led (2022-today)</p>',
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

type MonitorVariant = {
  title: string
  lines: string[]
  theme: { screenBg: string; screenFg: string; ink: string }
  dot?: string
}

/** Variantes del kiosco de pago: la card de cada banco + el ciclo. */
function deudaVariantsFor(
  locale: Locale,
  theme: MonitorVariant['theme'],
): Record<string, MonitorVariant> {
  const es = locale === 'es'
  return {
    'bank-0': {
      title: 'Santander · PagaloAqui',
      lines: es
        ? ['Tu deuda: $842.500', 'estado: VENCIDA', 'descuento -95% ✓', '']
        : ['Your debt: $842,500', 'status: OVERDUE', 'discount -95% ✓', ''],
      theme,
      dot: SANT_RED,
    },
    'bank-1': {
      title: 'Consumer · Paga tu Cuota',
      lines: es
        ? [
            'cuota del mes: $126.900',
            'credito automotriz',
            'al dia tras pagar',
            '',
          ]
        : ['instalment: $126,900', 'auto loan', 'current after paying', ''],
      theme,
      dot: SANT_RED,
    },
    'bank-2': {
      title: 'Scotiabank · Soluciones',
      lines: es
        ? [
            'deuda vencida: $1.238.400',
            'pago total o repactar',
            'descuento de frente',
            '',
          ]
        : [
            'overdue: $1,238,400',
            'full pay or repactate',
            'discount up front',
            '',
          ],
      theme,
      dot: SCOTIA_RED,
    },
    run: {
      title: 'WebPay',
      lines: es
        ? ['procesando pago...', 'transaccion segura 🔒', '', '']
        : ['processing payment...', 'secure transaction 🔒', '', ''],
      theme,
      dot: '#d99a2b',
    },
    ok: {
      title: es ? 'Pago confirmado ✓' : 'Payment confirmed ✓',
      lines: es
        ? ['deuda regularizada', '100% online', 'sin sucursal, sin fila', '']
        : ['debt regularised', '100% online', 'no branch, no queue', ''],
      theme,
      dot: OK_GREEN,
    },
  }
}

/** Variantes del admin de campañas: configurada -> corriendo -> lanzada. */
function campanaVariantsFor(
  locale: Locale,
  theme: MonitorVariant['theme'],
): Record<string, MonitorVariant> {
  const es = locale === 'es'
  return {
    idle: {
      title: es ? 'admin de campañas' : 'campaign admin',
      lines: es
        ? [
            'segmento: mora 30-90d CL',
            'oferta: -40% · canal: email',
            'antes: HORAS a mano',
            '[E] lanzar',
          ]
        : [
            'segment: 30-90d arrears CL',
            'offer: -40% · channel: email',
            'before: HOURS by hand',
            '[E] launch',
          ],
      theme,
    },
    run: {
      title: es ? 'lanzando...' : 'launching...',
      lines: es
        ? [
            'validando segmento ✓',
            'cruzando descuentos ✓',
            'encolando envios...',
            '',
          ]
        : [
            'validating segment ✓',
            'crossing discounts ✓',
            'queueing sends...',
            '',
          ],
      theme,
      dot: '#d99a2b',
    },
    ok: {
      title: es ? 'campaña lanzada ✓' : 'campaign launched ✓',
      lines: es
        ? [
            'tiempo total: 4 min',
            '(antes: ~4 horas)',
            '12.480 clientes',
            '0 errores',
          ]
        : [
            'total time: 4 min',
            '(before: ~4 hours)',
            '12,480 customers',
            '0 errors',
          ],
      theme,
      dot: OK_GREEN,
    },
  }
}

/** Micro de PagaloAqui: el kiosco procesa WebPay y confirma; cada
 *  disparo cicla al siguiente banco co-branded (maquina de estados). */
function deudaMicro(opts: {
  roomIndex: number
  position: readonly [number, number]
  screen: ScreenSwap
  banksCount: number
}): { interactable: Interactable; update(t: number): void } {
  const { screen } = opts
  let startT = -1
  let bank = 0
  return {
    interactable: {
      id: `micro-destacame-deuda-${opts.roomIndex}`,
      x: opts.position[0],
      z: opts.position[1],
      radius: 2.2,
      label: DEUDA_LABEL,
      onActivate: () => {
        if (startT === -1) {
          startT = -2 // pendiente: el proximo update fija el inicio
          screen.show('run')
          sfx.play('blip')
        }
      },
    },
    update: (t: number) => {
      if (startT === -2) {
        startT = t
      }
      if (startT < 0) {
        return
      }
      const elapsed = t - startT
      if (elapsed < 1.8) {
        // WebPay procesando (la pantalla ya esta en 'run')
      } else if (elapsed < 5.2) {
        screen.show('ok')
      } else {
        bank = (bank + 1) % opts.banksCount
        screen.show(`bank-${bank}`)
        startT = -1
      }
    },
  }
}

/** Micro del score: la aguja del gauge sube de coral a verde, el
 *  numero celebra el salto y vuelve a descansar en el punto real. */
function scoreMicro(opts: {
  roomIndex: number
  position: readonly [number, number]
  pivot: Group
  lowLabel: Mesh
  highLabel: Mesh
}): { interactable: Interactable; update(t: number): void } {
  const { pivot, lowLabel, highLabel } = opts
  const LOW = 0.85
  const HIGH = -0.85
  let startT = -1
  return {
    interactable: {
      id: `micro-destacame-score-${opts.roomIndex}`,
      x: opts.position[0],
      z: opts.position[1],
      radius: 2.2,
      label: SCORE_LABEL,
      onActivate: () => {
        if (startT === -1) {
          startT = -2
          sfx.play('boot')
        }
      },
    },
    update: (t: number) => {
      if (startT === -2) {
        startT = t
      }
      if (startT < 0) {
        return
      }
      const elapsed = t - startT
      if (elapsed < 1.6) {
        // la aguja barre de coral a verde con easing
        const k = elapsed / 1.6
        const eased = k * k * (3 - 2 * k)
        pivot.rotation.z = LOW + (HIGH - LOW) * eased
      } else if (elapsed < 5.0) {
        pivot.rotation.z = HIGH
        lowLabel.visible = false
        highLabel.visible = true
      } else {
        pivot.rotation.z = LOW
        lowLabel.visible = true
        highLabel.visible = false
        startT = -1
      }
    },
  }
}

/** Micro del admin: lanzar la campaña — corre y reporta los 4 min. */
function campanaMicro(opts: {
  roomIndex: number
  position: readonly [number, number]
  screen: ScreenSwap
}): { interactable: Interactable; update(t: number): void } {
  const { screen } = opts
  let startT = -1
  return {
    interactable: {
      id: `micro-destacame-campana-${opts.roomIndex}`,
      x: opts.position[0],
      z: opts.position[1],
      radius: 2.0,
      label: CAMPANA_LABEL,
      onActivate: () => {
        if (startT === -1) {
          startT = -2
          screen.show('run')
          sfx.play('blip')
        }
      },
    },
    update: (t: number) => {
      if (startT === -2) {
        startT = t
      }
      if (startT < 0) {
        return
      }
      const elapsed = t - startT
      if (elapsed < 1.6) {
        // corriendo (la pantalla ya esta en 'run')
      } else if (elapsed < 5.4) {
        screen.show('ok')
      } else {
        screen.show('idle')
        startT = -1
      }
    },
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
      id: `micro-destacame-${roomIndex}-laptop${toggle.spot}`,
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

/** Textura de la cara del gauge gigante del Area B (fondo + arco). */
function gaugeFaceTexture() {
  return makeCanvasTexture(256, (ctx, size) => {
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, size, size)
    ctx.fillStyle = DTC_BLUE
    ctx.fillRect(0, 0, size, 34)
    ctx.fillStyle = '#ffffff'
    ctx.font = 'bold 16px "Space Grotesk", system-ui, sans-serif'
    ctx.fillText('TU SCORE', 88, 23)
    drawGaugeArc(ctx, 128, 168, 92, 0.5)
    // la aguja del canvas queda tapada por la aguja 3D animada; los
    // extremos del rango son fijos
    ctx.fillStyle = PANEL_INK
    ctx.font = 'bold 14px "Space Mono", ui-monospace, monospace'
    ctx.fillText('459', 16, 196)
    ctx.fillText('760', 212, 196)
  })
}

export default function buildDestacame(ctx: RoomCtx): RoomBuild {
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
  const units = unitGeo()
  const screenTheme = {
    screenBg: theme.screenBg,
    screenFg: theme.screenFg,
    ink: theme.ink,
  }

  // rincon dev del canon (fondo, centro): 3 puestos — Camila y Diego
  // trabajan en las suyas, la tercera se enciende con E y muestra el
  // panel de plataforma (campañas en 4 min, equipos en paralelo)
  const deskSpots: readonly (readonly [number, number])[] = [
    [-2.9, room.z - 3.4],
    [-1.4, room.z - 3.5],
    [1.8, room.z - 3.4],
  ]
  const office = officeLayout({
    roomIndex: room.index,
    state,
    spots: deskSpots,
    color: PANEL_INK,
    furniture: { deskUrl: DESK_URL, chairUrl: CHAIR_URL },
    poweredSpots: new Set([0, 1]),
    screenTheme,
    screenFor: (index) => LAPTOP_SCREENS[index] ?? LAPTOP_SCREENS[0],
  })
  group.add(office.group)
  staticColliders.push(...office.colliders)
  disposables.push(office)
  interactables.push(...laptopToggles(office, deskSpots, room.index))
  interactables.push(...office.seats)
  const devLabel = label(
    locale === 'es' ? 'EQUIPO PLATAFORMA' : 'PLATFORM TEAM',
    { size: 0.13, color: theme.accent },
  )
  devLabel.position.set(0, 1.85, room.z - 4.5)
  group.add(devLabel)

  // AREA A — PagaloAqui (muro -X, mitad del fondo): el kiosco de pago
  // co-branded con WebPay — la micro de pagar la deuda vive aqui
  group.add(
    desk({
      position: [-half + 1.1, 0, room.z - 3.0],
      rotationY: Math.PI / 2,
      width: 1.8,
      color: KIOSK_DESK,
    }),
  )
  const kiosco = switchableMonitor({
    position: [-half + 1.05, 0.75, room.z - 3.0],
    rotationY: Math.PI / 2,
    width: 1.0,
    variants: deudaVariantsFor(locale, screenTheme),
    initial: 'bank-0',
  })
  group.add(kiosco.group)
  disposables.push(kiosco.screen)
  staticColliders.push(footprint(-half + 1.1, room.z - 3.0, 1.0, 2.0))
  const pagar = deudaMicro({
    roomIndex: room.index,
    position: [-half + 1.1, room.z - 3.0],
    screen: kiosco.screen,
    banksCount: 3,
  })
  interactables.push(pagar.interactable)
  updates.push(pagar.update)
  const areaALabel = label('PAGALOAQUI', {
    size: 0.14,
    color: theme.accent,
  })
  areaALabel.position.set(-half + 1.1, 2.15, room.z - 3.0)
  areaALabel.rotation.y = Math.PI / 2
  group.add(areaALabel)

  // props firma del Area A: la tarjeta bancaria sobre el kiosco, el
  // sello WebPay y la pila de monedas del pago que por fin sale
  const tarjeta = boxMesh(0.6, 0.05, 0.4, toonMat('#1a2e5a'))
  tarjeta.position.set(-half + 1.3, 0.81, room.z - 1.9)
  tarjeta.rotation.y = 0.45
  // C15: tarjeta plana y oscura — el hull no aporta trazo visible
  tarjeta.userData.noOutline = true
  group.add(tarjeta)
  // sello WebPay: PANEL_INK casi negro — sin hull (C15, trazo invisible)
  const selloWebpay = mergedBoxes(
    [
      // sello WebPay de pie junto al kiosco
      { w: 0.55, h: 0.34, d: 0.06, x: -half + 0.5, y: 1.55, z: room.z - 1.6 },
      { w: 0.1, h: 0.5, d: 0.1, x: -half + 0.5, y: 1.1, z: room.z - 1.6 },
    ],
    toonMat(PANEL_INK),
  )
  selloWebpay.castShadow = true
  selloWebpay.userData.noOutline = true
  group.add(
    selloWebpay,
    // monedas apiladas (el pago recuperado)
    mergedBoxes(
      [
        { w: 0.22, h: 0.05, d: 0.22, x: -half + 0.6, y: 0.03, z: room.z - 4.3 },
        { w: 0.22, h: 0.05, d: 0.22, x: -half + 0.6, y: 0.08, z: room.z - 4.3 },
        {
          w: 0.22,
          h: 0.05,
          d: 0.22,
          x: -half + 0.62,
          y: 0.13,
          z: room.z - 4.28,
        },
        { w: 0.22, h: 0.05, d: 0.22, x: -half + 0.9, y: 0.03, z: room.z - 4.1 },
        { w: 0.22, h: 0.05, d: 0.22, x: -half + 0.9, y: 0.08, z: room.z - 4.1 },
      ],
      toonMat(COIN_GOLD),
    ),
  )
  const webpayLabel = label('WebPay', { size: 0.1, color: '#e8eef8' })
  webpayLabel.position.set(-half + 0.5, 1.55, room.z - 1.53)
  webpayLabel.rotation.y = Math.PI / 2
  group.add(webpayLabel)

  // tag flotante del descuento: el -95% que rebancariza
  const tag = new Group()
  const tagChip = boxMesh(0.72, 0.3, 0.06, toonMat(OK_GREEN))
  tagChip.userData.noOutline = true
  const tagLabel = label('deuda -95%', { size: 0.11, color: '#0c2a18' })
  tagLabel.position.z = 0.05
  tag.add(tagChip, tagLabel)
  tag.position.set(-half + 1.6, 2.0, room.z - 3.9)
  tag.rotation.y = Math.PI / 2
  group.add(tag)
  updates.push((t) => {
    tag.position.y = 2.0 + Math.sin(t * 1.8) * 0.08
  })

  // AREA B — producto Destacame (muro +X): el GAUGE del score 459-760
  // con la aguja 3D — la micro de mejorar el score vive aqui
  const gauge = new Group()
  gauge.position.set(half - 1.5, 0, room.z - 2.4)
  gauge.rotation.y = -Math.PI / 2
  gauge.add(
    outlinedMergedBoxes(
      [
        { w: 1.0, h: 0.1, d: 0.7, x: 0, y: 0.05, z: 0 },
        { w: 0.14, h: 0.7, d: 0.14, x: 0, y: 0.45, z: 0 },
        { w: 1.62, h: 1.24, d: 0.08, x: 0, y: 1.5, z: -0.03 },
      ],
      toonMat(PANEL_INK),
      { inflate: 0.03, castShadow: true },
    ),
  )
  const gaugeFace = new Mesh(
    units.plane,
    new MeshBasicMaterial({ map: gaugeFaceTexture() }),
  )
  gaugeFace.scale.set(1.5, 1.12, 1)
  gaugeFace.position.set(0, 1.5, 0.02)
  gaugeFace.userData.noOutline = true
  gauge.add(gaugeFace)
  // la aguja 3D pivotea sobre el centro del arco del canvas
  const needlePivot = new Group()
  needlePivot.position.set(0, 1.26, 0.05)
  const needle = boxMesh(0.035, 0.44, 0.02, toonMat(PANEL_INK))
  needle.position.y = 0.22
  needle.userData.noOutline = true
  needlePivot.add(needle)
  needlePivot.rotation.z = 0.85 // arranca en la zona coral (score bajo)
  gauge.add(needlePivot)
  const scoreLow = label('487', { size: 0.16, color: MORA_CORAL })
  scoreLow.position.set(0, 0.86, 0.06)
  const scoreHigh = label('712', { size: 0.16, color: OK_GREEN })
  scoreHigh.position.set(0, 0.86, 0.06)
  scoreHigh.visible = false
  gauge.add(scoreLow, scoreHigh)
  group.add(gauge)
  staticColliders.push(footprint(half - 1.5, room.z - 2.4, 1.1, 0.9))
  const subir = scoreMicro({
    roomIndex: room.index,
    position: [half - 1.5, room.z - 2.4],
    pivot: needlePivot,
    lowLabel: scoreLow,
    highLabel: scoreHigh,
  })
  interactables.push(subir.interactable)
  updates.push(subir.update)
  const areaBLabel = label(
    locale === 'es' ? 'TU SCORE · DESTACAME' : 'YOUR SCORE · DESTACAME',
    { size: 0.13, color: theme.accent },
  )
  areaBLabel.position.set(half - 1.5, 2.4, room.z - 2.4)
  areaBLabel.rotation.y = -Math.PI / 2
  group.add(areaBLabel)

  // la SuperApp en su pedestal + la tarjeta prepago azul + el KPI de
  // la pared: el producto que rebancariza en dos paises
  group.add(
    outlinedMergedBoxes(
      [
        { w: 0.7, h: 0.1, d: 0.55, x: half - 2.3, y: 0.05, z: room.z + 0.9 },
        { w: 0.12, h: 0.42, d: 0.12, x: half - 2.3, y: 0.31, z: room.z + 0.9 },
        { w: 0.78, h: 1.45, d: 0.12, x: half - 2.3, y: 1.24, z: room.z + 0.9 },
      ],
      toonMat('#15151a'),
      { inflate: 0.03, castShadow: true },
    ),
  )
  staticColliders.push(footprint(half - 2.3, room.z + 0.9, 0.9, 0.7))
  const phonePanel = screenPanel({
    title: locale === 'es' ? 'SuperApp · hoy' : 'SuperApp · today',
    lines:
      locale === 'es'
        ? [
            'score: 612 ↑',
            'deuda vencida: -95%',
            'credito preaprobado',
            'CL + MX',
          ]
        : [
            'score: 612 ↑',
            'overdue debt: -95%',
            'pre-approved credit',
            'CL + MX',
          ],
    theme: screenTheme,
    width: 0.64,
    height: 1.2,
  })
  phonePanel.position.set(half - 2.3 - 0.07, 1.3, room.z + 0.9)
  phonePanel.rotation.y = -Math.PI / 2
  group.add(phonePanel)
  const prepago = boxMesh(0.5, 0.32, 0.04, toonMat(DTC_BLUE))
  prepago.position.set(half - 2.3, 0.36, room.z + 1.7)
  prepago.rotation.y = -Math.PI / 2 + 0.3
  // C15: tarjeta chica a ras del pedestal — sin hull
  prepago.userData.noOutline = true
  group.add(prepago)
  const kpiPanel = screenPanel({
    title: locale === 'es' ? 'DESTACAME · KPIs' : 'DESTACAME · KPIs',
    lines:
      locale === 'es'
        ? [
            '+2M usuarios CL + MX',
            'score gratis: siempre',
            'deudas resueltas ↑',
          ]
        : ['+2M users CL + MX', 'free score: always', 'debts resolved ↑'],
    theme: screenTheme,
    width: 1.5,
    height: 0.9,
  })
  kpiPanel.position.set(half - 0.12, 2.2, room.z + 1.9)
  kpiPanel.rotation.y = -Math.PI / 2
  group.add(kpiPanel)

  // GUIÑO liderazgo: la mesa de reunion del lead (equipos de 4-6) —
  // Ana Sofia preside; el admin de campañas esta a un paso
  const meeting = new Group()
  meeting.position.set(-1.7, 0, room.z + 1.6)
  meeting.add(
    outlinedMergedBoxes(
      [
        { w: 3.4, h: 0.07, d: 1.5, x: 0, y: 0.74, z: 0 },
        { w: 0.12, h: 0.74, d: 1.3, x: -1.5, y: 0.37, z: 0 },
        { w: 0.12, h: 0.74, d: 1.3, x: 1.5, y: 0.37, z: 0 },
      ],
      toonMat('#1b2433'),
      { castShadow: true },
    ),
  )
  const chairSpots: readonly (readonly [number, number])[] = [
    [-1.1, -0.9],
    [0, -0.9],
    [1.1, -0.9],
    [-1.1, 0.9],
    [0, 0.9],
    [1.1, 0.9],
  ]
  meeting.add(
    outlinedMergedBoxes(
      chairSpots.flatMap(([x, dz]) => [
        { w: 0.44, h: 0.06, d: 0.44, x, y: 0.45, z: dz },
        {
          w: 0.44,
          h: 0.55,
          d: 0.05,
          x,
          y: 0.75,
          z: dz + (dz > 0 ? 0.2 : -0.2),
        },
      ]),
      toonMat('#26303f'),
      { inflate: 0.035 },
    ),
  )
  group.add(meeting)
  staticColliders.push(footprint(-1.7, room.z + 1.6, 3.7, 3.2))

  // GUIÑO horas -> minutos operable: el admin de campañas junto a la
  // mesa del lead — la micro de lanzar campaña vive aqui
  group.add(
    desk({
      position: [-half + 1.0, 0, room.z + 2.6],
      rotationY: Math.PI / 2,
      width: 1.2,
      color: KIOSK_DESK,
    }),
  )
  const campanaAdmin = switchableMonitor({
    position: [-half + 0.95, 0.75, room.z + 2.6],
    rotationY: Math.PI / 2,
    width: 0.8,
    variants: campanaVariantsFor(locale, screenTheme),
    initial: 'idle',
  })
  group.add(campanaAdmin.group)
  disposables.push(campanaAdmin.screen)
  staticColliders.push(footprint(-half + 1.0, room.z + 2.6, 0.9, 1.4))
  const lanzar = campanaMicro({
    roomIndex: room.index,
    position: [-half + 1.0, room.z + 2.6],
    screen: campanaAdmin.screen,
  })
  interactables.push(lanzar.interactable)
  updates.push(lanzar.update)

  // GUIÑO vibe coding (heredado de cima): E cicla vibe -> Python -> TS
  const vibe = screenVariants({
    width: 2.0,
    height: 1.2,
    variants: {
      vibe: {
        title: 'vibe coding',
        lines: [
          '> claude "refactor module"',
          'tests: 128 passed',
          'review: aprobado',
        ],
        theme: screenTheme,
      },
      python: {
        title: 'campanas/service.py — Django',
        lines: [
          '@transaction.atomic',
          'def lanzar(campana):',
          '    targets = scoring.filtrar(',
          '        pais=campana.pais)',
          '    return dispatch(targets)',
        ],
        theme: screenTheme,
        dot: '#4dcc7a',
      },
      ts: {
        title: 'usePagos.ts — frontend',
        lines: [
          'const { data } = useQuery(',
          "  ['deudas', rut],",
          '  fetchDeudas,',
          ')',
          'if (data) renderPlan(data)',
        ],
        theme: screenTheme,
        dot: '#4dcc7a',
      },
    },
    initial: 'vibe',
  })
  vibe.mesh.position.set(4.6, 1.9, frontZ - 0.12)
  vibe.mesh.rotation.y = Math.PI
  group.add(vibe.mesh)
  disposables.push(vibe)
  const VIBE_SEQ = ['vibe', 'python', 'ts'] as const
  let vibeIndex = 0
  interactables.push({
    id: `micro-destacame-code-${room.index}`,
    x: 4.6,
    z: frontZ - 0.9,
    radius: 1.9,
    label: CODE_LABEL,
    onActivate: () => {
      vibeIndex = (vibeIndex + 1) % VIBE_SEQ.length
      vibe.show(VIBE_SEQ[vibeIndex] ?? 'vibe')
      sfx.play('blip')
    },
  })

  // puerta PROXIMAMENTE en el muro +X (heredada de cima): lo que viene
  const coming = new Group()
  coming.position.set(half - 0.35, 0, room.z - 3.8)
  coming.rotation.y = -Math.PI / 2
  const comingFrame = boxMesh(1.2, 2.1, 0.09, toonMat('#10151f'))
  comingFrame.position.set(0, 1.05, 0)
  const comingPanel = boxMesh(
    1.05,
    1.9,
    0.02,
    toonMat('#141c2b', { emissive: theme.accent, emissiveIntensity: 0.12 }),
  )
  comingPanel.position.set(0, 1.05, 0.05)
  // C15: panel emisivo DENTRO del marco (el marco ya da el trazo)
  comingPanel.userData.noOutline = true
  const comingTitle = label(locale === 'es' ? 'PROXIMAMENTE' : 'COMING SOON', {
    size: 0.16,
    color: '#9db8ff',
  })
  comingTitle.position.set(0, 1.35, 0.09)
  const comingSub = label(locale === 'es' ? 'ideas futuras' : 'future ideas', {
    size: 0.1,
    color: '#5f77a8',
  })
  comingSub.position.set(0, 1.1, 0.09)
  coming.add(comingFrame, comingPanel, comingTitle, comingSub)
  group.add(coming)

  // CTA de contacto (heredado de cima): el holograma azul que corona
  // la cima de la carrera, al centro del muro del fondo
  const beacon = new Group()
  beacon.position.set(0, 0, room.z + 4.9)
  const pedestal = new Mesh(units.cylinder, toonMat('#141a26'))
  pedestal.scale.set(0.62, 1, 0.62)
  pedestal.position.y = 0.5
  // C15: cilindro casi negro — el holo encima es el foco, sin hull
  pedestal.userData.noOutline = true
  const holoMat = toonMatOwn(DTC_BLUE, {
    emissive: '#5aa2ff',
    emissiveIntensity: 0.9,
    transparent: true,
    opacity: 0.92,
  })
  const holo = new Mesh(new OctahedronGeometry(0.24, 0), holoMat)
  holo.position.y = 1.35
  holo.rotation.y = 0.6
  beacon.add(pedestal, holo)
  group.add(beacon)
  staticColliders.push(footprint(0, room.z + 4.9, 0.8, 0.8))
  interactables.push({
    id: `contact-${room.index}`,
    x: 0,
    z: room.z + 4.9,
    radius: 2.2,
    label: CONTACT_LABEL,
    onActivate: () => actions.openContact(),
  })
  updates.push((t, dt) => {
    holoMat.emissiveIntensity = 0.9 + Math.sin(t * 2.4) * 0.35
    holo.rotation.y += dt * 0.8
    sfx.feed(`holo-${room.index}`, 'holo', 0, room.z + 4.9)
  })

  // cuadros de rubro (wallArt): microfrontends, microservicios Django
  // y campañas horas->minutos inspeccionables (3 fichas — decision del
  // usuario); la pizarra del Design System queda decorativa
  const art = wallArt({
    roomIndex: room.index,
    theme,
    locale,
    onFicha: actions.openStory,
    frames: [
      {
        key: 'microfrontends',
        position: [-3.6, 2, backZ + 0.08],
        rotationY: 0,
        draw: drawMicrofrontends,
        ficha: ART_FICHA_MFE,
      },
      {
        key: 'microservicios',
        position: [3.6, 2, backZ + 0.08],
        rotationY: 0,
        draw: drawMicroservicios,
        ficha: ART_FICHA_MSVC,
      },
      {
        key: 'campanas',
        position: [0, 2.15, backZ + 0.08],
        rotationY: 0,
        draw: drawCampanas,
        ficha: ART_FICHA_CAMPANAS,
      },
      {
        key: 'design-system',
        position: [-4.6, 2, frontZ - 0.08],
        rotationY: Math.PI,
        draw: drawDesignSystem,
      },
    ],
  })
  staticColliders.push(...art.colliders)
  const sink = { group, interactables, updates }
  addProps(sink, art.props)

  // showcase A junto a la puerta (canon AC-6): PagaloAqui — E cicla
  // las 3 cards co-branded (Santander, Consumer, Scotiabank)
  const showcaseA = softwareShowcase({
    roomIndex: room.index,
    key: 'pagaloaqui',
    position: [-2.4, 0, frontZ - 0.9],
    rotationY: Math.PI,
    theme,
    locale,
    demos: showcaseADemos(),
    openShowcase: actions.openShowcase,
  })
  addProps(sink, [showcaseA])
  staticColliders.push(footprint(-2.4, frontZ - 0.9, 0.9, 0.7))

  // showcase B junto a la puerta: el producto Destacame — E cicla
  // destacame.cl <-> destacame.com.mx
  const showcaseB = softwareShowcase({
    roomIndex: room.index,
    key: 'producto',
    position: [2.4, 0, frontZ - 0.9],
    rotationY: Math.PI,
    theme,
    locale,
    demos: showcaseBDemos(),
    openShowcase: actions.openShowcase,
  })
  addProps(sink, [showcaseB])
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

  // NPCs del canon (2 enfoques, informe 13): Camila y Diego (devs,
  // sentados en sus laptops), Rodrigo (representante de banco frente
  // al kiosco de PagaloAqui), Valentina (PM en ronda) y Ana Sofia
  // (lead MX presidiendo la mesa de reunion)
  const coworkers = npcCoworkers({
    roomIndex: room.index,
    openDialog: actions.openDialog,
    npcs: [
      {
        key: 'camila',
        role: 'coworker',
        spec: {
          skin: '#e0aa86',
          hair: { style: 'ponytail', color: '#241a10' },
          top: DTC_BLUE_DARK,
          bottom: '#2e3238',
          accessory: 'badge',
          model: 'female-office',
          faceSeed: 23,
        },
        position: [-0.9, 0, room.z - 5.35],
        rotationY: 0,
        pose: 'sit',
        dialog: DESTACAME_PRESENTE_DIALOGS.camila,
      },
      {
        key: 'diego',
        role: 'coworker',
        spec: {
          skin: '#c08a60',
          hair: { style: 'spiky', color: '#141008' },
          top: '#2e4258',
          bottom: '#22262e',
          accessory: 'glasses',
          model: 'male-casual',
          faceSeed: 47,
        },
        position: [0.9, 0, room.z - 5.35],
        rotationY: 0,
        pose: 'sit',
        dialog: DESTACAME_PRESENTE_DIALOGS.diego,
      },
      {
        key: 'rodrigo',
        role: 'staff',
        spec: {
          skin: '#d9a684',
          hair: { style: 'short', color: '#3a3430' },
          top: '#3c3f4a',
          bottom: '#23262e',
          accessory: 'tie',
          model: 'male-suit',
          faceSeed: 61,
        },
        position: [-3.3, 0, room.z - 2.7],
        rotationY: -Math.PI / 2,
        dialog: DESTACAME_PRESENTE_DIALOGS.rodrigo,
      },
      {
        key: 'valentina',
        role: 'staff',
        spec: {
          skin: '#e8c49c',
          hair: { style: 'bun', color: '#4a2c14' },
          top: '#7a4fc0',
          bottom: '#2e3238',
          accessory: 'badge',
          model: 'female-casual',
          faceSeed: 78,
        },
        position: [0.4, 0, room.z - 1.4],
        path: [
          [0.4, room.z - 1.4],
          [2.6, room.z + 0.4],
          [-1.2, room.z - 0.4],
        ],
        speed: 0.5,
        dialog: DESTACAME_PRESENTE_DIALOGS.valentina,
      },
      {
        key: 'anasofia',
        role: 'boss',
        spec: {
          skin: '#c98f6a',
          hair: { style: 'bun', color: '#1a1410' },
          top: '#0e3a80',
          bottom: '#1c2430',
          accessory: 'tie',
          model: 'female-office',
          faceSeed: 92,
        },
        position: [-3.9, 0, room.z + 1.6],
        rotationY: Math.PI / 2,
        dialog: DESTACAME_PRESENTE_DIALOGS.anasofia,
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
