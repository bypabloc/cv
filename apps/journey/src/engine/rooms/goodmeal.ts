/**
 * @module rooms/goodmeal (engine)
 * @description Sala 5 — GoodMeal (food-tech anti-desperdicio, Chile,
 *   2021), construida al CANON de sala (plan journey-salas-estandar,
 *   informe 12): rincon dev (`officeLayout` de 3 puestos: Camila y
 *   Matias trabajan en las suyas, la tercera se enciende con E y
 *   muestra el contador "bugs recurrentes ↓"), mitad cafeteria partner
 *   (vitrina con donas/pan/pizza, estante del excedente del dia, mesa
 *   de empaque con Good Bags kraft y el contador de impacto) y el
 *   SMARTPHONE GIGANTE con la app (card de Good Bag con precio
 *   tachado, pin geo flotante). 5 NPCs conversables (`npcCoworkers`,
 *   decision del usuario: los 5 del informe — Camila, Matias, Jorge,
 *   Valentina y Daniela la PM). Cuadros de rubro (`wallArt`: "1/3 se
 *   desperdicia", "Vue 3" y "mapa de locales" inspeccionables — 3
 *   fichas, decision del usuario — tagline decorativo) y el
 *   `softwareShowcase` junto a la puerta con 3 demos de la app real
 *   (Good Bags cerca de ti, checkout del pago, migracion Vue 2 -> 3).
 *   Micros: EMPACAR una Good Bag (la dona vuela de la vitrina a la
 *   bolsa kraft y el contador de impacto sube) y COMPRAR la Good Bag
 *   (el checkout paga ciclando el medio, confirma y el pin geo late).
 *   Kit informativo ESTANDAR (`infoKit`) en las posiciones canonicas.
 *   Paredes blanco hueso; el rubro vive en piso/props/luz (teal
 *   GoodMeal + kraft; comida en colores calidos).
 */
import { Group, type Mesh } from 'three'
import type { Box2 } from '../../lib/collision'
import type { Locale } from '../../lib/rooms'
import { sfx } from '../audio'
import type { NpcHandle } from '../character'
import { GOODMEAL_PRESENTE_DIALOGS } from '../dialogs/goodmeal-presente'
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
import { placeProp } from './props-catalog'

const BAG_LABEL = {
  es: 'Empacar una Good Bag',
  en: 'Pack a Good Bag',
} as const

const PAGO_LABEL = {
  es: 'Comprar la Good Bag',
  en: 'Buy the Good Bag',
} as const

const LAPTOP_LABELS = {
  on: { es: 'Encender la laptop libre', en: 'Power on the spare laptop' },
  off: { es: 'Apagar la laptop libre', en: 'Power off the spare laptop' },
} as const

/** Pantallas del rincon dev: la migracion Vue 3 + el flujo de pagos. */
const LAPTOP_SCREENS = [
  {
    title: 'GoodBagCard.vue — Vue 3',
    lines: [
      '<script setup lang="ts">',
      'const { bag } = defineProps<{',
      '  bag: GoodBag',
      '}>()  // -64% hoy',
    ],
  },
  {
    title: 'usePayment.ts',
    lines: [
      'const pay = async () => {',
      '  const tx = await api.post(',
      "    '/checkout', order)",
      '  return confirm(tx)',
    ],
  },
  {
    title: 'panel dev · bugs',
    lines: [
      'bugs recurrentes ↓',
      'sprint 12:  8',
      'sprint 13:  3',
      'sprint 14:  1',
    ],
  },
] as const

// --- paleta del rubro (informe 12) ---

const GM_TEAL = '#17b5a2'
const GM_TEAL_DARK = '#128a7c'
const KRAFT = '#c8a86a'
const KRAFT_DARK = '#a8854e'
const LEAF = '#5a9a4a'
const DONA_PINK = '#e88aa0'
const PAN_BROWN = '#c8924e'
const PIZZA_AMBER = '#d8a03c'
const COUNTER_INK = '#2a3430'

// --- laminas de los cuadros (wallArt): tinta plana sobre papel claro ---

const ART_PAPER = '#f4efe2'
const ART_INK = '#1c241c'

function artBase(ctx: CanvasRenderingContext2D, size: number): void {
  ctx.fillStyle = ART_PAPER
  ctx.fillRect(0, 0, size, size)
  ctx.strokeStyle = ART_INK
  ctx.globalAlpha = 0.35
  ctx.lineWidth = 3
  ctx.strokeRect(10, 10, size - 20, size - 20)
  ctx.globalAlpha = 1
}

/** El plato con el tercio perdido: la tesis del rubro en una lamina. */
function drawTercio(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 15px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('1/3 SE DESPERDICIA', 20, 36)
  // el plato: circulo con el tercio resaltado en teal
  const cx = 118
  const cy = 120
  ctx.strokeStyle = ART_INK
  ctx.lineWidth = 4
  ctx.beginPath()
  ctx.arc(cx, cy, 58, 0, Math.PI * 2)
  ctx.stroke()
  ctx.fillStyle = GM_TEAL
  ctx.beginPath()
  ctx.moveTo(cx, cy)
  ctx.arc(cx, cy, 58, -Math.PI / 2, -Math.PI / 2 + (Math.PI * 2) / 3 / 2)
  ctx.closePath()
  ctx.fill()
  // cubiertos a los lados del plato
  ctx.strokeStyle = ART_INK
  ctx.lineWidth = 3
  ctx.beginPath()
  ctx.moveTo(cx - 78, cy - 40)
  ctx.lineTo(cx - 78, cy + 40)
  ctx.moveTo(cx + 78, cy - 40)
  ctx.lineTo(cx + 78, cy + 40)
  ctx.moveTo(cx + 72, cy - 40)
  ctx.lineTo(cx + 84, cy - 40)
  ctx.stroke()
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 10px "Space Mono", ui-monospace, monospace'
  ctx.fillText('> 1/3 de la comida producida', 22, 202)
  ctx.fillText('desperdicio = 10% de los GEI', 22, 216)
  ctx.globalAlpha = 0.6
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('la comida se hizo para comerse', 20, 238)
  ctx.globalAlpha = 1
}

/** El triangulo de Vue con la barra de migracion al 100%. */
function drawVueArt(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 15px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('MIGRACION V2 → V3', 20, 36)
  // logo Vue: triangulo exterior teal + interior tinta
  const cx = 128
  ctx.fillStyle = GM_TEAL
  ctx.beginPath()
  ctx.moveTo(cx - 62, 62)
  ctx.lineTo(cx + 62, 62)
  ctx.lineTo(cx, 164)
  ctx.closePath()
  ctx.fill()
  ctx.fillStyle = ART_INK
  ctx.beginPath()
  ctx.moveTo(cx - 30, 62)
  ctx.lineTo(cx + 30, 62)
  ctx.lineTo(cx, 112)
  ctx.closePath()
  ctx.fill()
  ctx.fillStyle = ART_PAPER
  ctx.beginPath()
  ctx.moveTo(cx - 14, 62)
  ctx.lineTo(cx + 14, 62)
  ctx.lineTo(cx, 86)
  ctx.closePath()
  ctx.fill()
  // barra de migracion completa
  ctx.strokeStyle = ART_INK
  ctx.lineWidth = 2
  ctx.strokeRect(36, 186, 184, 16)
  ctx.fillStyle = GM_TEAL
  ctx.fillRect(38, 188, 180, 12)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 10px "Space Mono", ui-monospace, monospace'
  ctx.fillText('migracion 100% · bugs ↓', 36, 216)
  ctx.globalAlpha = 0.6
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('liderada sin frenar el producto', 20, 238)
  ctx.globalAlpha = 1
}

/** Mapa de locales: la costa chilena, los pines y la nube de la app. */
function drawMapaArt(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 15px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('+3.000 COMERCIOS', 20, 36)
  // costa de Chile central estilizada
  ctx.strokeStyle = ART_INK
  ctx.lineWidth = 3
  ctx.beginPath()
  ctx.moveTo(96, 56)
  ctx.lineTo(84, 96)
  ctx.lineTo(92, 140)
  ctx.lineTo(80, 182)
  ctx.lineTo(90, 214)
  ctx.stroke()
  // la app: telefono chico arriba a la derecha
  ctx.strokeStyle = GM_TEAL
  ctx.lineWidth = 3
  ctx.strokeRect(178, 58, 40, 66)
  ctx.fillStyle = GM_TEAL
  ctx.fillRect(184, 66, 28, 40)
  // pines de locales conectados a la app
  const pins = [
    [126, 100],
    [148, 138],
    [118, 176],
  ] as const
  for (const [px, py] of pins) {
    ctx.strokeStyle = GM_TEAL
    ctx.globalAlpha = 0.5
    ctx.setLineDash([4, 4])
    ctx.beginPath()
    ctx.moveTo(px, py - 10)
    ctx.lineTo(198, 92)
    ctx.stroke()
    ctx.setLineDash([])
    ctx.globalAlpha = 1
    ctx.fillStyle = GM_TEAL_DARK
    ctx.beginPath()
    ctx.arc(px, py, 7, 0, Math.PI * 2)
    ctx.fill()
    ctx.fillStyle = ART_PAPER
    ctx.beginPath()
    ctx.arc(px, py, 2.6, 0, Math.PI * 2)
    ctx.fill()
  }
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 10px "Space Mono", ui-monospace, monospace'
  ctx.fillText('RM + Valparaiso', 118, 210)
  ctx.globalAlpha = 0.6
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('cada pin publica sus Good Bags', 20, 238)
  ctx.globalAlpha = 1
}

/** El tagline oficial con la Good Bag y el brote (decorativo). */
function drawTaglineArt(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 15px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('AHORRA, COME RICO', 20, 40)
  ctx.fillText('Y CUIDA EL PLANETA', 20, 60)
  // la Good Bag kraft con su tapa enrollada y el "?"
  ctx.fillStyle = KRAFT
  ctx.fillRect(84, 92, 88, 100)
  ctx.fillStyle = KRAFT_DARK
  ctx.fillRect(84, 84, 88, 14)
  ctx.fillStyle = GM_TEAL
  ctx.fillRect(112, 118, 32, 32)
  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 24px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('?', 122, 142)
  // el brote al lado de la bolsa
  ctx.strokeStyle = LEAF
  ctx.lineWidth = 3
  ctx.beginPath()
  ctx.moveTo(196, 190)
  ctx.lineTo(196, 160)
  ctx.stroke()
  ctx.fillStyle = LEAF
  ctx.beginPath()
  ctx.ellipse(188, 158, 10, 5, -0.6, 0, Math.PI * 2)
  ctx.ellipse(204, 158, 10, 5, 0.6, 0, Math.PI * 2)
  ctx.fill()
  ctx.fillStyle = ART_INK
  ctx.globalAlpha = 0.6
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('salvar el mundo es simple', 20, 238)
  ctx.globalAlpha = 1
}

const ART_FICHA_TERCIO = {
  title: {
    es: 'El tercio que nadie se come',
    en: 'The third nobody eats',
  },
  paragraphs: {
    es: [
      'Mas de UN TERCIO de la comida que se produce en el mundo se ' +
        'desperdicia — y ese desperdicio genera cerca del 10% de los ' +
        'gases de efecto invernadero. En una cafeteria eso tiene ' +
        'forma concreta: la vitrina perfecta de las diez de la noche ' +
        'volcada a la bolsa negra.',
      'GoodMeal ataca exactamente ese momento: el comercio empaca su ' +
        'excedente en una Good Bag sorpresa y la publica en la app a ' +
        'precio rebajado (50-70% menos). El cliente la reserva, paga ' +
        'y la retira antes del cierre — comida rescatada en vez de ' +
        'botada.',
      'Es el analogo chileno de Too Good To Go: mas de 3.000 ' +
        'comercios entre la RM y Valparaiso, con partners como ' +
        'Starbucks, Dunkin y Juan Valdez. Pablo trabajo en la app que ' +
        'hace posible ese rescate diario.',
    ],
    en: [
      'More than A THIRD of the food produced worldwide goes to ' +
        'waste — and that waste drives close to 10% of greenhouse gas ' +
        'emissions. In a cafe it takes concrete shape: the perfect ' +
        'ten-o-clock display case dumped into a black bag.',
      'GoodMeal attacks exactly that moment: the venue packs its ' +
        'surplus into a surprise Good Bag and lists it on the app at ' +
        'a discount (50-70% off). Customers reserve it, pay and pick ' +
        'it up before closing — food rescued instead of binned.',
      'It is the Chilean analogue of Too Good To Go: over 3,000 ' +
        'venues across Santiago and Valparaiso, with partners like ' +
        'Starbucks, Dunkin and Juan Valdez. Pablo worked on the app ' +
        'that makes that daily rescue possible.',
    ],
  },
} as const

const ART_FICHA_VUE = {
  title: {
    es: 'La migracion a Vue 3',
    en: 'The Vue 3 migration',
  },
  paragraphs: {
    es: [
      'La app de GoodMeal corria sobre un Vue viejo: builds lentos, ' +
        'pantallas que se pegaban y cambios que dolian. En 2021 Pablo ' +
        'LIDERO la migracion del frontend a Vue 3 con tooling ' +
        'moderno, reestructurando la base de codigo para ganar ' +
        'rendimiento y mantenibilidad — sin frenar un producto vivo ' +
        'con miles de locales encima.',
      'El resultado se sintio en ambas puntas: la UX de la app de ' +
        'pedidos mejoro notablemente y los bugs recurrentes dejaron ' +
        'de volver — el tiempo de resolucion cayo con un frontend ' +
        'estabilizado y estandares de codigo claros que el equipo ' +
        'adopto.',
      'Ademas trabajo full stack: integro el frontend con los ' +
        'servicios backend y reforzo el flujo de pagos de la ' +
        'plataforma, cuidando la consistencia de los datos sensibles ' +
        'de cada transaccion.',
    ],
    en: [
      'The GoodMeal app ran on an old Vue: slow builds, freezing ' +
        'screens and painful changes. In 2021 Pablo LED the frontend ' +
        'migration to Vue 3 with modern tooling, restructuring the ' +
        'codebase for performance and maintainability — without ' +
        'stopping a live product with thousands of venues on top.',
      'The result showed on both ends: the ordering app’s UX ' +
        'improved notably and recurring bugs stopped coming back — ' +
        'resolution time fell with a stabilised frontend and clear ' +
        'code standards the team adopted.',
      'He also worked full stack: wiring the frontend into the ' +
        'backend services and hardening the platform’s payment flow, ' +
        'guarding the consistency of each transaction’s sensitive ' +
        'data.',
    ],
  },
} as const

const ART_FICHA_MAPA = {
  title: {
    es: 'Mas de 3.000 comercios',
    en: 'Over 3,000 venues',
  },
  paragraphs: {
    es: [
      'La red de GoodMeal cubre la Region Metropolitana y ' +
        'Valparaiso: mas de 3.000 cafeterias, panaderias y ' +
        'restaurantes publican su excedente diario como Good Bags — ' +
        'con partners reales como Starbucks, Dunkin, Juan Valdez, ' +
        'Oxxo, San Camilo y Melt Pizzas, y el respaldo de Endeavor ' +
        'Chile.',
      'Cada pin del mapa publica sus bolsas del dia: cuantas hay, en ' +
        'que horario se retiran y a que precio rebajado. El cliente ' +
        'compra a ciegas — sabe el local y el tipo de comida, no el ' +
        'contenido exacto — y el pin de geolocalizacion lo guia al ' +
        'retiro.',
      'Para el comercio, la merma se vuelve ingreso; para el ' +
        'cliente, un ahorro del 50-70%; para el planeta, comida que ' +
        'se come en vez de emitir gases en un vertedero.',
    ],
    en: [
      'GoodMeal’s network covers Santiago and Valparaiso: over ' +
        '3,000 cafes, bakeries and restaurants list their daily ' +
        'surplus as Good Bags — with real partners like Starbucks, ' +
        'Dunkin, Juan Valdez, Oxxo, San Camilo and Melt Pizzas, and ' +
        'the backing of Endeavor Chile.',
      'Each pin on the map lists its bags for the day: how many, ' +
        'the pickup window and the discounted price. Customers buy ' +
        'blind — they know the venue and the food type, not the ' +
        'exact contents — and the geo pin guides them to pickup.',
      'For the venue, shrinkage becomes income; for the customer, a ' +
        '50-70% saving; for the planet, food that gets eaten instead ' +
        'of emitting gases in a landfill.',
    ],
  },
} as const

// --- demos del showcase: la app GoodMeal (teal + kraft, mobile 2021) ---

const APP_BG = '#f6f8f6'
const APP_INK = '#1c2420'
const APP_LINE = '#c8d4cc'

/** Chrome de la app movil: barra teal + fondo claro minimalista. */
function appChrome(
  ctx: CanvasRenderingContext2D,
  size: number,
  title: string,
): void {
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, size, size)
  ctx.fillStyle = GM_TEAL
  ctx.fillRect(0, 0, size, 26)
  ctx.fillStyle = KRAFT
  ctx.fillRect(0, 26, size, 3)
  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 12px "Space Grotesk", system-ui, sans-serif'
  ctx.textAlign = 'left'
  ctx.textBaseline = 'alphabetic'
  ctx.fillText(title, 8, 18)
}

/** Card de Good Bag: local, precio tachado -> rebajado y chip -%. */
function bagCard(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  data: {
    local: string
    antes: string
    ahora: string
    chip: string
    food: string
    active: boolean
  },
): void {
  ctx.strokeStyle = data.active ? GM_TEAL : APP_LINE
  ctx.lineWidth = data.active ? 3 : 1.5
  ctx.strokeRect(x, y, 216, 46)
  // foto de la comida: cuadrito calido
  ctx.fillStyle = data.food
  ctx.fillRect(x + 6, y + 8, 30, 30)
  ctx.fillStyle = APP_INK
  ctx.font = 'bold 10px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText(data.local, x + 44, y + 16)
  // precio de lista tachado
  ctx.globalAlpha = 0.55
  ctx.font = '9px "Space Mono", ui-monospace, monospace'
  ctx.fillText(data.antes, x + 44, y + 30)
  const w = ctx.measureText(data.antes).width
  ctx.strokeStyle = APP_INK
  ctx.lineWidth = 1.5
  ctx.beginPath()
  ctx.moveTo(x + 43, y + 27)
  ctx.lineTo(x + 45 + w, y + 27)
  ctx.stroke()
  ctx.globalAlpha = 1
  ctx.fillStyle = GM_TEAL_DARK
  ctx.font = 'bold 11px "Space Mono", ui-monospace, monospace'
  ctx.fillText(data.ahora, x + 44, y + 42)
  // chip de descuento
  ctx.fillStyle = GM_TEAL
  ctx.fillRect(x + 168, y + 6, 42, 16)
  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 9px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText(data.chip, x + 174, y + 17)
}

/** Demo 1: Good Bags cerca de ti — cards con precio tachado y pin. */
function drawDemoBags(
  ctx: CanvasRenderingContext2D,
  size: number,
  t: number,
): void {
  appChrome(ctx, size, 'GoodMeal · cerca de ti')
  const active = Math.floor(t * 0.6) % 3
  bagCard(ctx, 12, 40, {
    local: 'Dunkin — Providencia',
    antes: '$6.990',
    ahora: '$2.490',
    chip: '-64%',
    food: DONA_PINK,
    active: active === 0,
  })
  bagCard(ctx, 12, 94, {
    local: 'Juan Valdez — Centro',
    antes: '$7.500',
    ahora: '$2.990',
    chip: '-60%',
    food: PAN_BROWN,
    active: active === 1,
  })
  bagCard(ctx, 12, 148, {
    local: 'San Camilo — Ñuñoa',
    antes: '$5.400',
    ahora: '$1.990',
    chip: '-63%',
    food: PIZZA_AMBER,
    active: active === 2,
  })
  // pin geo latiendo abajo
  const pulse = 0.7 + Math.sin(t * 3) * 0.3
  ctx.globalAlpha = pulse
  ctx.fillStyle = GM_TEAL_DARK
  ctx.beginPath()
  ctx.arc(24, 210, 8, 0, Math.PI * 2)
  ctx.fill()
  ctx.beginPath()
  ctx.moveTo(16, 212)
  ctx.lineTo(24, 226)
  ctx.lineTo(32, 212)
  ctx.closePath()
  ctx.fill()
  ctx.globalAlpha = 1
  ctx.fillStyle = APP_INK
  ctx.globalAlpha = 0.6
  ctx.font = '9px "Space Mono", ui-monospace, monospace'
  ctx.fillText('retiro 19:00-19:30 · sorpresa (?)', 40, 214)
  ctx.globalAlpha = 1
}

/** Demo 2: el checkout — resumen, medio de pago y pago confirmado. */
function drawDemoPago(
  ctx: CanvasRenderingContext2D,
  size: number,
  t: number,
): void {
  appChrome(ctx, size, 'GoodMeal · Checkout')
  ctx.fillStyle = APP_INK
  ctx.font = 'bold 10px "Space Mono", ui-monospace, monospace'
  ctx.fillText('Good Bag · Dunkin', 12, 50)
  ctx.fillText('retiro 19:00-19:30', 12, 64)
  ctx.font = 'bold 12px "Space Mono", ui-monospace, monospace'
  ctx.fillText('TOTAL   $2.490', 12, 84)
  const medios = ['tarjeta ••••4242', 'Webpay', 'MACH'] as const
  const activo = Math.floor(t * 0.5) % medios.length
  medios.forEach((medio, index) => {
    const y = 98 + index * 22
    ctx.fillStyle = index === activo ? GM_TEAL : APP_BG
    ctx.fillRect(12, y, 118, 18)
    ctx.fillStyle = index === activo ? '#ffffff' : APP_INK
    ctx.font = 'bold 9px "Space Grotesk", system-ui, sans-serif'
    ctx.fillText(medio, 18, y + 12)
  })
  // candado de transaccion segura
  ctx.strokeStyle = GM_TEAL_DARK
  ctx.lineWidth = 2
  ctx.strokeRect(148, 104, 18, 14)
  ctx.beginPath()
  ctx.arc(157, 104, 6, Math.PI, 0)
  ctx.stroke()
  ctx.fillStyle = APP_INK
  ctx.globalAlpha = 0.6
  ctx.font = '9px "Space Mono", ui-monospace, monospace'
  ctx.fillText('transaccion segura', 148, 132)
  ctx.globalAlpha = 1
  // ciclo: pagar (pulsa) -> procesando -> confirmado
  const cycle = (t * 0.55) % 6
  if (cycle < 2.4) {
    const pulse = 0.75 + Math.sin(t * 3) * 0.25
    ctx.globalAlpha = pulse
    ctx.fillStyle = GM_TEAL
    ctx.fillRect(12, 172, size - 24, 26)
    ctx.globalAlpha = 1
    ctx.fillStyle = '#ffffff'
    ctx.font = 'bold 11px "Space Grotesk", system-ui, sans-serif'
    ctx.fillText('Pagar $2.490', 88, 189)
  } else if (cycle < 3.6) {
    ctx.fillStyle = APP_BG
    ctx.fillRect(12, 172, size - 24, 26)
    const k = (cycle - 2.4) / 1.2
    ctx.fillStyle = GM_TEAL
    ctx.fillRect(12, 172, (size - 24) * k, 26)
    ctx.fillStyle = APP_INK
    ctx.font = 'bold 10px "Space Mono", ui-monospace, monospace'
    ctx.fillText('procesando pago...', 76, 189)
  } else {
    ctx.fillStyle = GM_TEAL_DARK
    ctx.fillRect(12, 172, size - 24, 26)
    ctx.fillStyle = '#ffffff'
    ctx.font = 'bold 11px "Space Grotesk", system-ui, sans-serif'
    ctx.fillText('Pedido confirmado ✓', 62, 189)
  }
  ctx.fillStyle = APP_INK
  ctx.globalAlpha = 0.6
  ctx.font = '9px "Space Mono", ui-monospace, monospace'
  ctx.fillText('consistencia en cada paso', 12, 216)
  ctx.globalAlpha = 1
}

/** Demo 3: la app vieja se desvanece, la UI Vue 3 queda nitida. */
function drawDemoVue(
  ctx: CanvasRenderingContext2D,
  size: number,
  t: number,
): void {
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, size, size)
  ctx.fillStyle = APP_INK
  ctx.font = 'bold 12px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('Migracion Vue 2 → Vue 3', 8, 18)
  // mitad vieja: bloques grises que respiran hacia la transparencia
  const fade = 0.2 + (Math.sin(t * 1.2) + 1) * 0.15
  ctx.globalAlpha = fade
  ctx.fillStyle = '#8a8f8a'
  ctx.fillRect(10, 34, 108, 20)
  ctx.fillRect(10, 60, 108, 44)
  ctx.fillRect(10, 110, 108, 44)
  ctx.fillRect(10, 160, 70, 16)
  ctx.globalAlpha = 0.6
  ctx.font = 'bold 9px "Space Mono", ui-monospace, monospace'
  ctx.fillStyle = APP_INK
  ctx.fillText('Vue 2 · se pegaba', 14, 194)
  ctx.globalAlpha = 1
  // mitad nueva: cards teal nitidas
  ctx.fillStyle = GM_TEAL
  ctx.fillRect(138, 34, 108, 20)
  ctx.strokeStyle = GM_TEAL
  ctx.lineWidth = 2
  ctx.strokeRect(138, 60, 108, 44)
  ctx.strokeRect(138, 110, 108, 44)
  ctx.fillRect(138, 160, 70, 16)
  ctx.fillStyle = GM_TEAL_DARK
  ctx.font = 'bold 9px "Space Mono", ui-monospace, monospace'
  ctx.fillText('Vue 3 · fluida', 142, 194)
  // el triangulo de Vue flotando al centro
  const bob = Math.sin(t * 2) * 4
  const cx = 128
  const cy = 120 + bob
  ctx.fillStyle = '#3fb27f'
  ctx.beginPath()
  ctx.moveTo(cx - 20, cy - 16)
  ctx.lineTo(cx + 20, cy - 16)
  ctx.lineTo(cx, cy + 18)
  ctx.closePath()
  ctx.fill()
  ctx.fillStyle = '#2a6a5a'
  ctx.beginPath()
  ctx.moveTo(cx - 10, cy - 16)
  ctx.lineTo(cx + 10, cy - 16)
  ctx.lineTo(cx, cy)
  ctx.closePath()
  ctx.fill()
  // barra de migracion + bugs
  ctx.strokeStyle = APP_INK
  ctx.lineWidth = 1.5
  ctx.strokeRect(10, 204, 152, 12)
  ctx.fillStyle = GM_TEAL
  ctx.fillRect(11, 205, 150, 10)
  ctx.fillStyle = APP_INK
  ctx.font = 'bold 9px "Space Mono", ui-monospace, monospace'
  ctx.fillText('100%', 168, 214)
  ctx.fillText('bugs ↓', 204, 214)
}

/** Los 3 mockups HTML del panel operable (app teal + kraft). */
function showcaseDemos(): ShowcaseDemo[] {
  const chrome = (title: string): string =>
    '<div style="background:#17b5a2;color:#fff;padding:.45rem .6rem;' +
    `font-weight:700;border-bottom:3px solid #c8a86a">${title}</div>`
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
  const tealBtn = (text: string): string =>
    '<span style="display:inline-block;background:#17b5a2;color:#fff;' +
    `padding:.3rem .8rem;font-weight:700;margin:.3rem 0">${text}</span>`
  const tachado = (text: string): string => `<s style="opacity:.6">${text}</s>`
  return [
    {
      key: 'bags',
      title: {
        es: 'Good Bags cerca de ti',
        en: 'Good Bags near you',
      },
      draw: drawDemoBags,
      panel: {
        brand: GM_TEAL_DARK,
        html: {
          es:
            chrome('GoodMeal · Good Bags cerca de ti') +
            gridTable(
              ['Local', 'Antes', 'Ahora', 'Retiro'],
              [
                ['Dunkin — Providencia', tachado('$6.990'), '$2.490', '19:00'],
                ['Juan Valdez — Centro', tachado('$7.500'), '$2.990', '19:30'],
                ['San Camilo — Ñuñoa', tachado('$5.400'), '$1.990', '20:00'],
              ],
            ) +
            '<p style="margin:.4rem 0 0">Contenido sorpresa <strong>(?)' +
            '</strong> · el pin te guia al retiro</p>' +
            tealBtn('Reservar mi Good Bag') +
            '<p style="opacity:.7;margin:.5rem 0 0">El marketplace ' +
            'anti-desperdicio: cada local publica su excedente del dia ' +
            'rebajado 50-70% antes de botarlo. Pablo modernizo esta app ' +
            'de pedidos liderando su migracion a Vue 3 (2021)</p>',
          en:
            chrome('GoodMeal · Good Bags near you') +
            gridTable(
              ['Venue', 'Was', 'Now', 'Pickup'],
              [
                ['Dunkin — Providencia', tachado('$6,990'), '$2,490', '19:00'],
                ['Juan Valdez — Centro', tachado('$7,500'), '$2,990', '19:30'],
                ['San Camilo — Ñuñoa', tachado('$5,400'), '$1,990', '20:00'],
              ],
            ) +
            '<p style="margin:.4rem 0 0">Surprise contents <strong>(?)' +
            '</strong> · the pin guides you to pickup</p>' +
            tealBtn('Reserve my Good Bag') +
            '<p style="opacity:.7;margin:.5rem 0 0">The anti-waste ' +
            'marketplace: each venue lists its daily surplus at 50-70% ' +
            'off before binning it. Pablo modernised this ordering app ' +
            'by leading its Vue 3 migration (2021)</p>',
        },
      },
    },
    {
      key: 'pago',
      title: {
        es: 'Pagar la Good Bag',
        en: 'Pay for the Good Bag',
      },
      draw: drawDemoPago,
      panel: {
        brand: GM_TEAL_DARK,
        html: {
          es:
            chrome('GoodMeal · Checkout — transaccion segura 🔒') +
            gridTable(
              ['Concepto', 'Detalle'],
              [
                ['Good Bag', 'Dunkin — Providencia'],
                ['Retiro', '19:00 a 19:30'],
                ['Medio de pago', 'tarjeta ••••4242 · Webpay · MACH'],
                ['TOTAL', '$2.490'],
              ],
            ) +
            tealBtn('Pagar $2.490') +
            '<p style="margin:.5rem 0 0"><strong style="color:#128a7c">' +
            'Pedido confirmado ✓</strong> — retiralo entre 19:00 y ' +
            '19:30 mostrando la app</p>' +
            '<p style="opacity:.7;margin:.5rem 0 0">El aporte de Pablo: ' +
            'reforzo el flujo de pagos y transacciones de la plataforma ' +
            '— fiabilidad y consistencia de los datos sensibles en cada ' +
            'compra (plataforma fintech-adyacente, 2021)</p>',
          en:
            chrome('GoodMeal · Checkout — secure transaction 🔒') +
            gridTable(
              ['Item', 'Detail'],
              [
                ['Good Bag', 'Dunkin — Providencia'],
                ['Pickup', '19:00 to 19:30'],
                ['Payment method', 'card ••••4242 · Webpay · MACH'],
                ['TOTAL', '$2,490'],
              ],
            ) +
            tealBtn('Pay $2,490') +
            '<p style="margin:.5rem 0 0"><strong style="color:#128a7c">' +
            'Order confirmed ✓</strong> — pick it up between 19:00 and ' +
            '19:30 showing the app</p>' +
            '<p style="opacity:.7;margin:.5rem 0 0">Pablo’s ' +
            'contribution: he hardened the platform’s payment and ' +
            'transaction flow — reliability and consistency for the ' +
            'sensitive data behind every purchase (fintech-adjacent ' +
            'platform, 2021)</p>',
        },
      },
    },
    {
      key: 'vue3',
      title: {
        es: 'Migracion Vue 2 → 3',
        en: 'Vue 2 → 3 migration',
      },
      draw: drawDemoVue,
      panel: {
        brand: GM_TEAL_DARK,
        html: {
          es:
            chrome('GoodMeal · La app vieja vs. la app Vue 3') +
            gridTable(
              ['Antes (Vue 2)', 'Despues (Vue 3)'],
              [
                ['builds lentos', 'tooling moderno'],
                ['pantallas que se pegaban', 'UX fluida y notablemente mejor'],
                ['bugs recurrentes cada sprint', 'frontend estable, bugs ↓'],
                ['cada cambio dolia', 'estandares de codigo claros'],
              ],
            ) +
            '<p style="margin:.4rem 0 0"><strong>migracion 100%</strong> ' +
            '— sin frenar el producto en marcha</p>' +
            '<p style="opacity:.7;margin:.5rem 0 0">Pablo lidero esta ' +
            'migracion como Desarrollador Web Full Stack (mayo-dic ' +
            '2021): reestructuro el frontend, modernizo la base de ' +
            'codigo y redujo el tiempo de resolucion de bugs ' +
            'recurrentes estabilizando la app de pedidos</p>',
          en:
            chrome('GoodMeal · The old app vs. the Vue 3 app') +
            gridTable(
              ['Before (Vue 2)', 'After (Vue 3)'],
              [
                ['slow builds', 'modern tooling'],
                ['freezing screens', 'fluid, notably better UX'],
                ['recurring bugs every sprint', 'stable frontend, bugs ↓'],
                ['every change hurt', 'clear code standards'],
              ],
            ) +
            '<p style="margin:.4rem 0 0"><strong>migration 100%</strong> ' +
            '— without stopping the running product</p>' +
            '<p style="opacity:.7;margin:.5rem 0 0">Pablo led this ' +
            'migration as a Full Stack Web Developer (May-Dec 2021): ' +
            'he restructured the frontend, modernised the codebase and ' +
            'cut the resolution time of recurring bugs by stabilising ' +
            'the ordering app</p>',
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
  dot: string
}

/** Variantes del contador de impacto: en marcha y celebrando el +1. */
function impactVariantsFor(
  locale: Locale,
  theme: MonitorVariant['theme'],
): Record<string, MonitorVariant> {
  const es = locale === 'es'
  return {
    run: {
      title: es ? 'IMPACTO GOODMEAL' : 'GOODMEAL IMPACT',
      lines: es
        ? [
            '1.284 comidas rescatadas',
            '2,9 t de CO2 evitadas',
            '',
            'cada bolsa suma',
          ]
        : ['1,284 meals rescued', '2.9 t of CO2 avoided', '', 'every bag adds'],
      theme,
      dot: GM_TEAL,
    },
    up: {
      title: es ? 'IMPACTO +1 ✓' : 'IMPACT +1 ✓',
      lines: es
        ? [
            '1.285 comidas rescatadas',
            '+1 Good Bag publicada',
            'CO2 evitado: +2,5 kg',
            '',
          ]
        : [
            '1,285 meals rescued',
            '+1 Good Bag listed',
            'CO2 avoided: +2.5 kg',
            '',
          ],
      theme,
      dot: '#3aa856',
    },
  }
}

/** Variantes del smartphone: card, pago por medio y confirmacion. */
function phoneVariantsFor(
  locale: Locale,
  theme: MonitorVariant['theme'],
  medios: readonly string[],
): Record<string, MonitorVariant> {
  const es = locale === 'es'
  const variants: Record<string, MonitorVariant> = {
    card: {
      title: es ? 'GoodMeal · hoy' : 'GoodMeal · today',
      lines: es
        ? [
            'Good Bag · Dunkin',
            'antes  $6.990',
            'AHORA  $2.490 (-64%)',
            'retiro 19:00-19:30',
          ]
        : [
            'Good Bag · Dunkin',
            'was  $6,990',
            'NOW  $2,490 (-64%)',
            'pickup 19:00-19:30',
          ],
      theme,
      dot: GM_TEAL,
    },
    ok: {
      title: es ? 'Confirmado ✓' : 'Confirmed ✓',
      lines: es
        ? [
            'Pedido #GB-5417',
            'retira 19:00-19:30',
            'muestra la app',
            'impacto: +1 comida',
          ]
        : [
            'Order #GB-5417',
            'pickup 19:00-19:30',
            'show the app',
            'impact: +1 meal',
          ],
      theme,
      dot: '#3aa856',
    },
  }
  medios.forEach((medio, index) => {
    variants[`pago-${index}`] = {
      title: es ? 'Checkout · $2.490' : 'Checkout · $2,490',
      lines: es
        ? [`pago: ${medio}`, 'transaccion segura 🔒', 'procesando...', '']
        : [`payment: ${medio}`, 'secure transaction 🔒', 'processing...', ''],
      theme,
      dot: '#d99a2b',
    }
  })
  return variants
}

/** Micro de la Good Bag: la dona vuela de la vitrina a la bolsa kraft
 *  y el contador de impacto celebra el +1 (maquina de estados). */
function bagMicro(opts: {
  roomIndex: number
  dona: Mesh
  from: readonly [number, number, number]
  to: readonly [number, number, number]
  impact: ScreenSwap
}): { interactable: Interactable; update(t: number): void } {
  const { dona, from, to, impact } = opts
  let startT = -1
  return {
    interactable: {
      id: `micro-goodmeal-bag-${opts.roomIndex}`,
      x: to[0],
      z: to[2],
      radius: 2.0,
      label: BAG_LABEL,
      onActivate: () => {
        if (startT === -1) {
          startT = -2 // pendiente: el proximo update fija el inicio
          sfx.play('blip')
        }
      },
    },
    update: (t: number) => {
      if (startT === -2) {
        startT = t
        dona.visible = true
      }
      if (startT < 0) {
        return
      }
      const elapsed = t - startT
      if (elapsed < 1.4) {
        // la dona vuela en arco de la vitrina a la bolsa
        const k = elapsed / 1.4
        dona.visible = true
        dona.position.set(
          from[0] + (to[0] - from[0]) * k,
          from[1] + (to[1] - from[1]) * k + Math.sin(k * Math.PI) * 0.55,
          from[2] + (to[2] - from[2]) * k,
        )
        dona.rotation.y = k * 4
      } else if (elapsed < 5.2) {
        dona.visible = false
        impact.show('up')
      } else {
        impact.show('run')
        startT = -1
      }
    },
  }
}

/** Micro del checkout: el pago procesa (ciclando el medio), confirma
 *  en la pantalla del smartphone y el pin geo late de alegria. */
function checkoutMicro(opts: {
  roomIndex: number
  position: readonly [number, number]
  phone: ScreenSwap
  pin: Group
  mediosCount: number
}): { interactable: Interactable; update(t: number): void } {
  const { phone, pin } = opts
  let startT = -1
  let medioIndex = 0
  return {
    interactable: {
      id: `micro-goodmeal-pago-${opts.roomIndex}`,
      x: opts.position[0],
      z: opts.position[1],
      radius: 2.2,
      label: PAGO_LABEL,
      onActivate: () => {
        if (startT === -1) {
          startT = -2
          phone.show(`pago-${medioIndex}`)
          medioIndex = (medioIndex + 1) % opts.mediosCount
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
        // procesando: la pantalla ya muestra el medio elegido
      } else if (elapsed < 5.4) {
        phone.show('ok')
        // el pin geo late mientras el pedido esta confirmado
        pin.scale.setScalar(1 + Math.sin(t * 8) * 0.15)
      } else {
        phone.show('card')
        pin.scale.setScalar(1)
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
      id: `micro-goodmeal-${roomIndex}-laptop${toggle.spot}`,
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

export default function buildGoodmeal(ctx: RoomCtx): RoomBuild {
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

  // rincon dev del canon (fondo +X): 3 puestos — Camila y Matias
  // trabajan en las suyas, la tercera se enciende con E y muestra el
  // contador "bugs recurrentes ↓" (guiño del achievement 3)
  const deskSpots: readonly (readonly [number, number])[] = [
    [1.6, room.z - 3.9],
    [3.4, room.z - 4.3],
    [2.5, room.z - 2.9],
  ]
  const office = officeLayout({
    roomIndex: room.index,
    state,
    spots: deskSpots,
    color: COUNTER_INK,
    poweredSpots: new Set([0, 1]),
    screenTheme,
    screenFor: (index) => LAPTOP_SCREENS[index] ?? LAPTOP_SCREENS[0],
  })
  group.add(office.group)
  staticColliders.push(...office.colliders)
  disposables.push(office)
  interactables.push(...laptopToggles(office, deskSpots, room.index))
  interactables.push(...office.seats)
  const devLabel = label(locale === 'es' ? 'EQUIPO DEV' : 'DEV TEAM', {
    size: 0.13,
    color: theme.accent,
  })
  devLabel.position.set(2.5, 1.85, room.z - 4.5)
  group.add(devLabel)

  // CAFETERIA partner (muro -X, fondo): vitrina con la comida del dia
  // — donas, pan y pizza en colores calidos — mas la caja registradora
  // y el tarro de propinas sobre el mostrador
  group.add(
    outlinedMergedBoxes(
      [
        // mostrador de la vitrina
        { w: 1.1, h: 0.9, d: 3.0, x: -half + 0.75, y: 0.45, z: room.z - 3.6 },
        // tapa de vidrio (caja superior fina)
        {
          w: 1.0,
          h: 0.42,
          d: 2.8,
          x: -half + 0.75,
          y: 1.12,
          z: room.z - 3.6,
        },
        // caja registradora al extremo
        { w: 0.34, h: 0.3, d: 0.34, x: -half + 0.75, y: 1.08, z: room.z - 1.9 },
      ],
      toonMat(COUNTER_INK),
      { inflate: 0.03, castShadow: true },
    ),
    // bandejas de comida dentro de la vitrina
    mergedBoxes(
      [
        { w: 0.7, h: 0.05, d: 0.6, x: -half + 0.75, y: 0.95, z: room.z - 4.6 },
        { w: 0.7, h: 0.05, d: 0.6, x: -half + 0.75, y: 0.95, z: room.z - 3.6 },
        { w: 0.7, h: 0.05, d: 0.6, x: -half + 0.75, y: 0.95, z: room.z - 2.7 },
      ],
      toonMat('#e8e2d0'),
    ),
    // tarro de propinas junto a la caja (procedural)
    mergedBoxes(
      [{ w: 0.12, h: 0.16, d: 0.12, x: -half + 1.1, y: 1.0, z: room.z - 1.95 }],
      toonMat('#dce8e4'),
    ),
  )
  // productos de panaderia como GLB CC0 apetitosos dentro de la vitrina
  group.add(
    placeProp('donut', {
      x: -half + 0.6,
      y: 0.98,
      z: room.z - 4.7,
      width: 0.16,
    }),
    placeProp('donut', {
      x: -half + 0.9,
      y: 0.98,
      z: room.z - 4.5,
      width: 0.16,
    }),
    placeProp('bread', {
      x: -half + 0.6,
      y: 0.98,
      z: room.z - 3.7,
      width: 0.2,
    }),
    placeProp('bread', {
      x: -half + 0.92,
      y: 0.98,
      z: room.z - 3.5,
      width: 0.2,
    }),
    placeProp('pizza', {
      x: -half + 0.72,
      y: 0.98,
      z: room.z - 2.75,
      rotationY: 0.5,
      width: 0.24,
    }),
  )
  staticColliders.push(footprint(-half + 0.75, room.z - 3.6, 1.3, 3.2))
  const cafeLabel = label(locale === 'es' ? 'CAFETERIA' : 'CAFE', {
    size: 0.14,
    color: theme.accent,
  })
  cafeLabel.position.set(-half + 0.75, 2.1, room.z - 3.6)
  cafeLabel.rotation.y = Math.PI / 2
  group.add(cafeLabel)

  // estante del "excedente del dia": lo que quedo perfecto pero no se
  // vendio, marcado para RESCATE (no para el tacho)
  group.add(
    outlinedMergedBoxes(
      [
        { w: 0.5, h: 0.05, d: 1.4, x: -half + 0.4, y: 1.0, z: room.z - 0.9 },
        { w: 0.5, h: 0.05, d: 1.4, x: -half + 0.4, y: 1.5, z: room.z - 0.9 },
        { w: 0.06, h: 1.6, d: 0.06, x: -half + 0.2, y: 0.8, z: room.z - 1.5 },
        { w: 0.06, h: 1.6, d: 0.06, x: -half + 0.2, y: 0.8, z: room.z - 0.3 },
      ],
      toonMat(KRAFT_DARK),
      { castShadow: true },
    ),
    mergedBoxes(
      [
        { w: 0.3, h: 0.08, d: 0.3, x: -half + 0.4, y: 1.07, z: room.z - 1.2 },
        { w: 0.3, h: 0.08, d: 0.3, x: -half + 0.4, y: 1.57, z: room.z - 0.6 },
        { w: 0.16, h: 0.1, d: 0.16, x: -half + 0.4, y: 1.08, z: room.z - 0.5 },
      ],
      toonMat(PAN_BROWN),
    ),
  )
  staticColliders.push(footprint(-half + 0.4, room.z - 0.9, 0.7, 1.6))
  const excedenteLabel = label(
    locale === 'es' ? 'EXCEDENTE DEL DIA' : "TODAY'S SURPLUS",
    { size: 0.11, color: theme.accent },
  )
  excedenteLabel.position.set(-half + 0.45, 1.95, room.z - 0.9)
  excedenteLabel.rotation.y = Math.PI / 2
  group.add(excedenteLabel)

  // mesa de empaque con las Good Bags kraft: tapa enrollada, logo teal
  // y el "?" de la sorpresa — la micro de empacar vive aqui
  group.add(
    desk({
      position: [-half + 1.9, 0, room.z - 0.5],
      rotationY: Math.PI / 2,
      width: 1.6,
      color: KRAFT_DARK,
    }),
    // las 3 Good Bags sobre la mesa (cuerpo kraft + tapa enrollada)
    outlinedMergedBoxes(
      [
        { w: 0.28, h: 0.4, d: 0.24, x: -half + 1.9, y: 0.95, z: room.z - 1.0 },
        { w: 0.32, h: 0.06, d: 0.26, x: -half + 1.9, y: 1.18, z: room.z - 1.0 },
        { w: 0.28, h: 0.4, d: 0.24, x: -half + 1.9, y: 0.95, z: room.z - 0.5 },
        { w: 0.32, h: 0.06, d: 0.26, x: -half + 1.9, y: 1.18, z: room.z - 0.5 },
        { w: 0.28, h: 0.4, d: 0.24, x: -half + 1.9, y: 0.95, z: room.z + 0.0 },
        { w: 0.32, h: 0.06, d: 0.26, x: -half + 1.9, y: 1.18, z: room.z + 0.0 },
      ],
      toonMat(KRAFT),
      { inflate: 0.02, castShadow: true },
    ),
    // logos teal al frente de las bolsas
    mergedBoxes(
      [
        {
          w: 0.02,
          h: 0.12,
          d: 0.12,
          x: -half + 2.05,
          y: 0.95,
          z: room.z - 1.0,
        },
        {
          w: 0.02,
          h: 0.12,
          d: 0.12,
          x: -half + 2.05,
          y: 0.95,
          z: room.z - 0.5,
        },
        { w: 0.02, h: 0.12, d: 0.12, x: -half + 2.05, y: 0.95, z: room.z },
      ],
      toonMat(GM_TEAL),
    ),
  )
  staticColliders.push(footprint(-half + 1.9, room.z - 0.5, 0.8, 1.8))
  const bagsLabel = label('GOOD BAGS · ?', {
    size: 0.12,
    color: theme.accent,
  })
  bagsLabel.position.set(-half + 1.9, 1.55, room.z - 0.5)
  bagsLabel.rotation.y = Math.PI / 2
  group.add(bagsLabel)

  // contador de impacto colgado sobre la zona de empaque: comidas
  // rescatadas + CO2 evitado — la micro de empacar lo hace celebrar
  const impact = switchableMonitor({
    position: [-half + 0.45, 1.62, room.z + 0.9],
    rotationY: Math.PI / 2,
    width: 0.62,
    variants: impactVariantsFor(locale, screenTheme),
    initial: 'run',
  })
  group.add(impact.group)
  disposables.push(impact.screen)

  // la dona que vuela de la vitrina a la Good Bag (micro de empacar)
  const dona = boxMesh(0.16, 0.08, 0.16, toonMat(DONA_PINK))
  dona.visible = false
  group.add(dona)
  const empacar = bagMicro({
    roomIndex: room.index,
    dona,
    from: [-half + 0.75, 1.05, room.z - 3.4],
    to: [-half + 1.9, 1.0, room.z - 0.5],
    impact: impact.screen,
  })
  interactables.push(empacar.interactable)
  updates.push(empacar.update)

  // SMARTPHONE GIGANTE con la app (frente, centro): la card de la
  // Good Bag con precio tachado — la micro del checkout vive aqui
  group.add(
    outlinedMergedBoxes(
      [
        { w: 0.9, h: 0.12, d: 0.7, x: 1.2, y: 0.06, z: room.z + 2.2 },
        { w: 0.14, h: 0.5, d: 0.14, x: 1.2, y: 0.35, z: room.z + 2.2 },
        { w: 1.0, h: 1.9, d: 0.14, x: 1.2, y: 1.45, z: room.z + 2.2 },
      ],
      toonMat('#15151a'),
      { inflate: 0.03, castShadow: true },
    ),
  )
  staticColliders.push(footprint(1.2, room.z + 2.2, 1.1, 0.9))
  const medios =
    locale === 'es'
      ? (['tarjeta ••••4242', 'Webpay', 'MACH'] as const)
      : (['card ••••4242', 'Webpay', 'MACH'] as const)
  const phone = screenVariants({
    width: 0.86,
    height: 1.05,
    variants: phoneVariantsFor(locale, screenTheme, medios),
    initial: 'card',
  })
  phone.mesh.position.set(1.2, 1.62, room.z + 2.2 - 0.08)
  phone.mesh.rotation.y = Math.PI
  group.add(phone.mesh)
  disposables.push(phone)
  const appLabel = label(locale === 'es' ? 'LA APP' : 'THE APP', {
    size: 0.13,
    color: theme.accent,
  })
  appLabel.position.set(1.2, 2.62, room.z + 2.15)
  appLabel.rotation.y = Math.PI
  group.add(appLabel)

  // pin de geolocalizacion flotando sobre el smartphone: el retiro
  const pin = new Group()
  const pinHead = boxMesh(0.22, 0.22, 0.06, basicMat(GM_TEAL))
  pinHead.rotation.z = Math.PI / 4
  pinHead.userData.noOutline = true
  const pinDot = boxMesh(0.08, 0.08, 0.07, basicMat('#ffffff'))
  pinDot.userData.noOutline = true
  pin.add(pinHead, pinDot)
  pin.position.set(1.2, 2.85, room.z + 2.2)
  group.add(pin)
  updates.push((t) => {
    pin.position.y = 2.85 + Math.sin(t * 2) * 0.08
    pin.rotation.y = t * 0.8
  })

  // micro del checkout: pagar la Good Bag (cicla el medio de pago)
  const comprar = checkoutMicro({
    roomIndex: room.index,
    position: [1.2, room.z + 2.2],
    phone,
    pin,
    mediosCount: medios.length,
  })
  interactables.push(comprar.interactable)
  updates.push(comprar.update)

  // plantas GLB CC0 en maceta: el motivo eco de la marca
  group.add(
    placeProp('potted_plant', { x: 3.2, z: room.z + 2.4, width: 0.6 }),
    placeProp('potted_plant', { x: -2.6, z: room.z + 4.2, width: 0.6 }),
    // planta eco extra en el rincon dev
    placeProp('potted_plant', { x: -half + 0.4, z: room.z + 3.0, width: 0.5 }),
  )
  staticColliders.push(
    footprint(3.2, room.z + 2.4, 0.45, 0.45),
    footprint(-2.6, room.z + 4.2, 0.45, 0.45),
  )

  // cuadros de rubro (wallArt): "1/3 se desperdicia", el logo Vue 3 y
  // el mapa de locales inspeccionables (3 fichas — decision del
  // usuario); el tagline oficial queda decorativo
  const art = wallArt({
    roomIndex: room.index,
    theme,
    locale,
    onFicha: actions.openStory,
    frames: [
      {
        key: 'un-tercio',
        position: [-3.6, 2, backZ + 0.08],
        rotationY: 0,
        draw: drawTercio,
        ficha: ART_FICHA_TERCIO,
      },
      {
        key: 'vue-3',
        position: [3.6, 2, backZ + 0.08],
        rotationY: 0,
        draw: drawVueArt,
        ficha: ART_FICHA_VUE,
      },
      {
        key: 'mapa-locales',
        position: [-3.6, 2, frontZ - 0.08],
        rotationY: Math.PI,
        draw: drawMapaArt,
        ficha: ART_FICHA_MAPA,
      },
      {
        key: 'tagline',
        position: [3.6, 2, frontZ - 0.08],
        rotationY: Math.PI,
        draw: drawTaglineArt,
      },
    ],
  })
  staticColliders.push(...art.colliders)
  const sink = { group, interactables, updates }
  addProps(sink, art.props)

  // showcase del software junto a la puerta al pasillo (canon AC-6):
  // la app GoodMeal — E cicla las 3 demos (bags, checkout, Vue 3)
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

  // NPCs del canon (2 enfoques, informe 12): Camila y Matias (devs,
  // sentados en sus laptops), Jorge (empacando Good Bags en la mesa),
  // Valentina (clienta frente al smartphone) y Daniela (PM en ronda).
  const coworkers = npcCoworkers({
    roomIndex: room.index,
    openDialog: actions.openDialog,
    npcs: [
      {
        key: 'camila',
        role: 'coworker',
        spec: {
          skin: '#d9a684',
          hair: { style: 'ponytail', color: '#3a2416' },
          top: GM_TEAL_DARK,
          bottom: '#2e3238',
          accessory: 'badge',
          model: 'sophie',
          faceSeed: 27,
        },
        position: [1.6, 0, room.z - 5.35],
        rotationY: 0,
        pose: 'sit',
        dialog: GOODMEAL_PRESENTE_DIALOGS.camila,
      },
      {
        key: 'matias',
        role: 'coworker',
        spec: {
          skin: '#b5825f',
          hair: { style: 'spiky', color: '#14100c' },
          top: '#3a4a48',
          bottom: '#2e3238',
          accessory: 'glasses',
          model: 'josh',
          faceSeed: 53,
        },
        position: [3.4, 0, room.z - 5.35],
        rotationY: 0,
        pose: 'sit',
        dialog: GOODMEAL_PRESENTE_DIALOGS.matias,
      },
      {
        key: 'jorge',
        role: 'staff',
        spec: {
          skin: '#c98f6a',
          hair: { style: 'short', color: '#2a1a10' },
          top: KRAFT,
          bottom: '#3a4048',
          accessory: 'badge',
          model: 'bryce',
          faceSeed: 66,
        },
        position: [-half + 2.7, 0, room.z - 0.5],
        rotationY: -Math.PI / 2,
        dialog: GOODMEAL_PRESENTE_DIALOGS.jorge,
      },
      {
        key: 'valentina',
        role: 'staff',
        spec: {
          skin: '#e8b48c',
          hair: { style: 'bun', color: '#1a140e' },
          top: '#c05a78',
          bottom: '#3a4048',
          model: 'kate',
          faceSeed: 84,
        },
        position: [1.2, 0, room.z + 0.9],
        rotationY: 0,
        dialog: GOODMEAL_PRESENTE_DIALOGS.valentina,
      },
      {
        key: 'daniela',
        role: 'boss',
        spec: {
          skin: '#e8c49c',
          hair: { style: 'bun', color: '#5a3a1e' },
          top: '#e8e4da',
          bottom: '#2e3238',
          accessory: 'badge',
          model: 'jennifer',
          faceSeed: 91,
        },
        // path rodea el pilar del cuaderno (x=0, room.z - 3.3, footprint
        // 1x1): arranca a +1.1 en x para no coincidir con el pilar y
        // mantiene >=0.5m de margen antes de cruzar hacia el resto de la
        // sala (plan journey-cuaderno-central, AC-5).
        position: [1.1, 0, room.z - 3.2],
        path: [
          [1.1, room.z - 3.2],
          [1.6, room.z - 1.8],
          [-1.8, room.z - 1.4],
          [1.6, room.z + 0.2],
        ],
        speed: 0.5,
        dialog: GOODMEAL_PRESENTE_DIALOGS.daniela,
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
