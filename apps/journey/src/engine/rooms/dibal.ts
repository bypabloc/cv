/**
 * @module rooms/dibal (engine)
 * @description Sala 4 — Dibal (SaaS POS de restaurantes, Peru, 2018-21),
 *   construida al CANON de sala (plan journey-salas-estandar, informe
 *   11): presente en DOS mitades — SALON (mesas con comensales, moza con
 *   tablet, caja con POS + impresora termica + boleta SUNAT flotante) y
 *   COCINA (mesada, pantalla KDS con tarjetas de comanda, impresora KOT,
 *   pase "para servir"). `officeLayout` como la MESA DE PABLO (decision
 *   del usuario: Pablo fue el UNICO dev — su laptop encendida con codigo
 *   Laravel/Vue + 1 libre togglable con E; validateMix off como el
 *   aula). 5 NPCs conversables (`npcCoworkers`, variante unico dev: Don
 *   Ricardo dueño, Milagros moza en ronda, Chef Ernesto en la cocina,
 *   Rosa cajera y Andrea comensal sentada). Cuadros de rubro (`wallArt`:
 *   flujo mozo->KDS, boleta SUNAT y organigrama "De 1 a 5 devs"
 *   inspeccionables — 3 fichas, decision del usuario — mapa
 *   multi-restaurante decorativo) y el `softwareShowcase` junto a la
 *   puerta con 3 demos del POS real (tomar pedido, comanda al KDS,
 *   boleta SUNAT). Micros: enviar una comanda (el sobre navy VUELA de la
 *   tablet al KDS y la tarjeta aparece) y emitir la boleta (la termica
 *   escupe el ticket + "Enviado a SUNAT ✓", ciclando el medio de pago).
 *   Kit informativo ESTANDAR (`infoKit`) en las posiciones canonicas.
 *   Paredes blanco hueso; el rubro vive en piso/props/luz (navy + teal
 *   Dibal; rojo/ambar SOLO en la comanda atrasada del KDS).
 */
import { Group, Mesh, MeshBasicMaterial, PlaneGeometry } from 'three'
import type { Box2 } from '../../lib/collision'
import type { Locale } from '../../lib/rooms'
import { sfx } from '../audio'
import type { NpcHandle } from '../character'
import { DIBAL_PRESENTE_DIALOGS } from '../dialogs/dibal-presente'
import type { Interactable } from '../state'
import {
  basicMat,
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
  npcCoworkers,
  type OfficeLayout,
  officeLayout,
  type PropHandle,
  type ScreenSwap,
  type ShowcaseDemo,
  softwareShowcase,
  switchableMonitor,
  wallArt,
} from './props'

const COMANDA_LABEL = {
  es: 'Enviar una comanda',
  en: 'Send an order',
} as const

const BOLETA_LABEL = {
  es: 'Emitir la boleta',
  en: 'Issue the receipt',
} as const

const LAPTOP_LABELS = {
  on: { es: 'Encender la laptop libre', en: 'Power on the spare laptop' },
  off: { es: 'Apagar la laptop libre', en: 'Power off the spare laptop' },
} as const

/** Pantallas de la mesa de Pablo: el stack real (Laravel + Vue + AWS). */
const LAPTOP_SCREENS = [
  {
    title: 'PedidoController.php',
    lines: [
      'public function store($r) {',
      '  $pedido = Pedido::create(',
      '    $r->validated());',
      '  event(new Enviado($pedido));',
    ],
  },
  {
    title: 'checkout.vue — e-commerce',
    lines: [
      '<script>',
      'export default {',
      "  name: 'Checkout',",
      '  // Vue + AWS, 2019',
    ],
  },
] as const

// --- paleta del rubro (informe 11) ---

const DIBAL_NAVY = '#1b2a4a'
const NAVY_DARK = '#16233f'
const DIBAL_TEAL = '#17b3a6'
const KDS_GREEN = '#3aa856'
const KDS_AMBER = '#d99a2b'
const KDS_RED = '#e23b34'
const INKA_AMBER = '#e8b13c'
const WOOD = '#8a6a4a'
const FOOD_BROWN = '#8a5a30'
const STEEL_KITCHEN = '#b8bcc0'

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

/** Flujo mesa -> tablet -> nube -> KDS: la comanda que ya no toca papel. */
function drawFlujo(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 15px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('DEL SALON A LA COCINA', 20, 36)
  const steps = ['MESA', 'TABLET', 'NUBE', 'KDS COCINA'] as const
  ctx.font = 'bold 10px "Space Mono", ui-monospace, monospace'
  steps.forEach((step, index) => {
    const y = 56 + index * 40
    const active = index === 2
    ctx.strokeStyle = active ? DIBAL_TEAL : ART_INK
    ctx.lineWidth = active ? 3 : 2
    if (active) {
      // la nube: tres arcos sobre la caja
      ctx.beginPath()
      ctx.arc(88, y + 2, 12, Math.PI, 0)
      ctx.arc(112, y - 2, 15, Math.PI, 0)
      ctx.arc(138, y + 2, 12, Math.PI, 0)
      ctx.stroke()
      ctx.fillStyle = DIBAL_TEAL
      ctx.fillText(step, 92, y + 16)
    } else {
      ctx.strokeRect(66, y - 12, 108, 22)
      ctx.fillStyle = ART_INK
      ctx.fillText(step, 74, y + 3)
    }
    if (index < steps.length - 1) {
      ctx.strokeStyle = ART_INK
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.moveTo(120, y + 12)
      ctx.lineTo(120, y + 26)
      ctx.moveTo(116, y + 22)
      ctx.lineTo(120, y + 26)
      ctx.lineTo(124, y + 22)
      ctx.stroke()
    }
  })
  // el sobre navy de la comanda viajando al margen
  ctx.strokeStyle = DIBAL_NAVY
  ctx.lineWidth = 3
  ctx.strokeRect(196, 100, 36, 26)
  ctx.beginPath()
  ctx.moveTo(196, 100)
  ctx.lineTo(214, 116)
  ctx.lineTo(232, 100)
  ctx.stroke()
  ctx.fillStyle = ART_INK
  ctx.globalAlpha = 0.6
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('la comanda ya no toca papel', 20, 238)
  ctx.globalAlpha = 1
}

/** Boleta electronica B001 con IGV, QR y el sello de SUNAT. */
function drawBoletaArt(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 15px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('BOLETA ELECTRONICA', 20, 36)
  // el ticket termico: borde dentado arriba
  ctx.strokeStyle = ART_INK
  ctx.lineWidth = 2
  ctx.strokeRect(52, 52, 152, 150)
  ctx.beginPath()
  for (let i = 0; i < 10; i += 1) {
    ctx.moveTo(52 + i * 15.2, 52)
    ctx.lineTo(52 + i * 15.2 + 7.6, 46)
    ctx.lineTo(52 + (i + 1) * 15.2, 52)
  }
  ctx.stroke()
  ctx.font = 'bold 9px "Space Mono", ui-monospace, monospace'
  ctx.fillText('BOLETA DE VENTA', 78, 70)
  ctx.fillText('ELECTRONICA', 90, 82)
  ctx.fillStyle = DIBAL_NAVY
  ctx.fillText('B001-00001547', 84, 98)
  ctx.fillStyle = ART_INK
  ctx.fillText('ceviche    S/ 42', 64, 116)
  ctx.fillText('lomo salt. S/ 38', 64, 128)
  ctx.fillText('IGV 18%  S/ 13.73', 64, 142)
  ctx.fillText('TOTAL    S/ 90.00', 64, 154)
  // QR: modulos 5x5 deterministas
  for (let i = 0; i < 25; i += 1) {
    if (i % 3 !== 1) {
      ctx.fillRect(64 + (i % 5) * 7, 164 + Math.floor(i / 5) * 7, 6, 6)
    }
  }
  ctx.fillStyle = DIBAL_TEAL
  ctx.font = 'bold 8px "Space Mono", ui-monospace, monospace'
  ctx.fillText('ENVIADO A', 118, 176)
  ctx.fillText('SUNAT ✓', 118, 186)
  ctx.fillStyle = ART_INK
  ctx.globalAlpha = 0.6
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('el fisco en linea, sin miedo', 20, 238)
  ctx.globalAlpha = 1
}

/** Mapa multi-restaurante: la costa, los pines y la nube que los une. */
function drawMapa(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 15px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('DIBAL · MULTI-LOCAL', 20, 36)
  // costa del Peru estilizada
  ctx.strokeStyle = ART_INK
  ctx.lineWidth = 3
  ctx.beginPath()
  ctx.moveTo(70, 60)
  ctx.lineTo(96, 92)
  ctx.lineTo(92, 130)
  ctx.lineTo(120, 176)
  ctx.lineTo(150, 208)
  ctx.stroke()
  // la nube SaaS arriba a la derecha
  ctx.strokeStyle = DIBAL_TEAL
  ctx.beginPath()
  ctx.arc(176, 78, 13, Math.PI, 0)
  ctx.arc(198, 74, 15, Math.PI, 0)
  ctx.arc(219, 78, 12, Math.PI, 0)
  ctx.moveTo(163, 78)
  ctx.lineTo(231, 78)
  ctx.stroke()
  // pines de restaurantes conectados a la nube
  const pins = [
    [116, 118],
    [128, 152],
    [148, 182],
  ] as const
  for (const [px, py] of pins) {
    ctx.strokeStyle = DIBAL_TEAL
    ctx.globalAlpha = 0.5
    ctx.setLineDash([4, 4])
    ctx.beginPath()
    ctx.moveTo(px, py - 10)
    ctx.lineTo(197, 84)
    ctx.stroke()
    ctx.setLineDash([])
    ctx.globalAlpha = 1
    ctx.fillStyle = DIBAL_NAVY
    ctx.beginPath()
    ctx.arc(px, py, 7, 0, Math.PI * 2)
    ctx.fill()
    ctx.fillStyle = ART_PAPER
    ctx.beginPath()
    ctx.arc(px, py, 2.6, 0, Math.PI * 2)
    ctx.fill()
  }
  ctx.fillStyle = ART_INK
  ctx.globalAlpha = 0.6
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('una nube, muchos locales', 20, 238)
  ctx.globalAlpha = 1
}

/** Organigrama "De 1 a 5 devs": founding dev -> tech lead (eje leader). */
function drawEquipo(ctx: CanvasRenderingContext2D, size: number): void {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 15px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('DE 1 A 5 DEVS', 20, 36)
  // nodo raiz: Pablo
  ctx.strokeStyle = DIBAL_NAVY
  ctx.lineWidth = 3
  ctx.strokeRect(72, 54, 112, 30)
  ctx.fillStyle = DIBAL_NAVY
  ctx.font = 'bold 10px "Space Mono", ui-monospace, monospace'
  ctx.fillText('PABLO', 108, 67)
  ctx.font = '8px "Space Mono", ui-monospace, monospace'
  ctx.fillText('founding dev · lead', 90, 79)
  // 4 nodos hijos
  ctx.strokeStyle = ART_INK
  ctx.lineWidth = 2
  for (let i = 0; i < 4; i += 1) {
    const x = 32 + i * 52
    ctx.strokeRect(x, 128, 40, 26)
    ctx.beginPath()
    ctx.moveTo(128, 84)
    ctx.lineTo(128, 106)
    ctx.lineTo(x + 20, 106)
    ctx.lineTo(x + 20, 128)
    ctx.stroke()
    ctx.fillStyle = ART_INK
    ctx.font = 'bold 9px "Space Mono", ui-monospace, monospace'
    ctx.fillText(`dev ${i + 2}`, x + 6, 144)
  }
  // timeline 2018 -> 2021
  ctx.strokeStyle = DIBAL_TEAL
  ctx.lineWidth = 3
  ctx.beginPath()
  ctx.moveTo(40, 190)
  ctx.lineTo(216, 190)
  ctx.stroke()
  ctx.fillStyle = DIBAL_TEAL
  ctx.beginPath()
  ctx.arc(40, 190, 5, 0, Math.PI * 2)
  ctx.arc(216, 190, 5, 0, Math.PI * 2)
  ctx.fill()
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 9px "Space Mono", ui-monospace, monospace'
  ctx.fillText('2018 · MVP', 24, 208)
  ctx.fillText('2021 · produccion', 138, 208)
  ctx.globalAlpha = 0.6
  ctx.font = '11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('liderazgo desde cero', 20, 238)
  ctx.globalAlpha = 1
}

const ART_FICHA_FLUJO = {
  title: {
    es: 'La comanda que dejo el papel',
    en: 'The order that left paper behind',
  },
  paragraphs: {
    es: [
      'En 2018 Dibal contrato a Pablo como su PRIMER desarrollador — ' +
        'el equipo completo era el. Su encargo: construir desde cero ' +
        'un sistema web multi-restaurante (jQuery + Laravel) que ' +
        'ordenara la operacion diaria de los locales.',
      'El corazon es este flujo: la moza toma el pedido en la tablet, ' +
        'la comanda viaja por la nube y aparece en la pantalla de la ' +
        'cocina al instante, con hora y observaciones. Los papelitos ' +
        'perdidos y los pedidos gritados se acabaron el mismo dia.',
      'Despues llego el e-commerce en Vue: el cliente pide solo y el ' +
        'pedido entra al mismo flujo, integrando la gestion del ' +
        'restaurante con la experiencia del cliente y minimizando la ' +
        'interaccion humana.',
    ],
    en: [
      'In 2018 Dibal hired Pablo as its FIRST developer — he was the ' +
        'entire team. His mission: build from scratch a ' +
        'multi-restaurant web system (jQuery + Laravel) to bring order ' +
        'to the daily operation of the venues.',
      'This flow is the heart of it: the waitress takes the order on ' +
        'the tablet, it travels through the cloud and appears on the ' +
        'kitchen screen instantly, with time and notes. Lost paper ' +
        'slips and shouted orders ended that same day.',
      'Then came the Vue e-commerce: customers order on their own and ' +
        'it enters the same flow, integrating restaurant management ' +
        'with the customer experience while minimising human ' +
        'interaction.',
    ],
  },
} as const

const ART_FICHA_BOLETA = {
  title: {
    es: 'El sello que quito el miedo',
    en: 'The stamp that removed the fear',
  },
  paragraphs: {
    es: [
      'En Peru el comprobante electronico es OBLIGATORIO: SUNAT — el ' +
        'fisco — exige declarar cada venta, y multa al que no cumple. ' +
        'La boleta de venta electronica lleva su serie (B001), su IGV ' +
        'del 18% y un codigo QR para consultarla.',
      'El sistema integra la facturacion DIRECTO con SUNAT: al ' +
        'cobrar, la boleta se emite, se imprime en la termica y se ' +
        'envia al fisco en el mismo gesto. Vuelve aceptada con su ' +
        'constancia — el sello "Enviado a SUNAT correctamente".',
      'Para el dueño eso significo cero multas y la caja cuadrada en ' +
        'vivo. La facturacion electronica ilimitada es, hasta hoy, la ' +
        'funcion insignia del producto Dibal.',
    ],
    en: [
      'In Peru the electronic receipt is MANDATORY: SUNAT — the tax ' +
        'authority — requires every sale to be declared, and fines ' +
        'whoever fails. The electronic receipt carries its series ' +
        '(B001), its 18% IGV tax and a QR code to verify it.',
      'The system integrates invoicing DIRECTLY with SUNAT: at ' +
        'checkout the receipt is issued, printed on the thermal ' +
        'printer and sent to the taxman in one gesture. It comes back ' +
        'accepted with its proof — the "Sent to SUNAT" stamp.',
      'For the owner that meant zero fines and a till balanced live. ' +
        'Unlimited e-invoicing remains, to this day, the flagship ' +
        'feature of the Dibal product.',
    ],
  },
} as const

const ART_FICHA_EQUIPO = {
  title: {
    es: 'De unico dev a tech lead',
    en: 'From only dev to tech lead',
  },
  paragraphs: {
    es: [
      'Pablo entro a Dibal siendo el UNICO desarrollador. Casi tres ' +
        'años despues, el equipo era de ~5 personas — y fue el quien ' +
        'lo hizo crecer: recibia a cada dev nuevo, le enseñaba el ' +
        'sistema y definia los estandares y flujos de trabajo.',
      'Como lider tecnico definio arquitecturas adaptadas al negocio, ' +
        'incluyendo un modelo de MICROFRONTENDS: piezas del frontend ' +
        'que evolucionan de forma independiente, con menos ' +
        'acoplamiento, para que el equipo avanzara en paralelo.',
      'Tambien llevo la plataforma a AWS (EC2, RDS, S3, AutoScaling, ' +
        'Load Balancer): disponibilidad en los picos de demanda y ' +
        'deploys que pasaron de jornadas manuales a un proceso ' +
        'repetible de pocas horas. El eje de liderazgo mas fuerte de ' +
        'su CV nacio aqui.',
    ],
    en: [
      'Pablo joined Dibal as the ONLY developer. Almost three years ' +
        'later the team was ~5 people — and he grew it himself: he ' +
        'onboarded every new dev, taught them the system and defined ' +
        'the standards and workflows.',
      'As tech lead he designed architectures fit for the business, ' +
        'including a MICROFRONTENDS model: frontend pieces that ' +
        'evolve independently, with less coupling, so the team could ' +
        'move in parallel.',
      'He also took the platform to AWS (EC2, RDS, S3, AutoScaling, ' +
        'Load Balancer): availability at demand peaks and deploys ' +
        'that went from manual all-day efforts to a repeatable ' +
        'process of a few hours. The strongest leadership axis of his ' +
        'CV was born here.',
    ],
  },
} as const

// --- demos del showcase: el POS Dibal (navy + teal, touch-first) ---

const POS_BG = '#f4f6f8'
const POS_INK = '#1c2430'
const POS_LINE = '#c8d0d8'

/** Chrome del POS moderno: barra navy + acento teal. */
function posChrome(
  ctx: CanvasRenderingContext2D,
  size: number,
  title: string,
): void {
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, size, size)
  ctx.fillStyle = DIBAL_NAVY
  ctx.fillRect(0, 0, size, 26)
  ctx.fillStyle = DIBAL_TEAL
  ctx.fillRect(0, 26, size, 3)
  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 12px "Space Grotesk", system-ui, sans-serif'
  ctx.textAlign = 'left'
  ctx.textBaseline = 'alphabetic'
  ctx.fillText(title, 8, 18)
}

/** Demo 1: tomar pedido — chips, grid de platos y carrito armandose. */
function drawDemoPedido(
  ctx: CanvasRenderingContext2D,
  size: number,
  t: number,
): void {
  posChrome(ctx, size, 'Dibal POS · Mesa 4')
  const chips = ['Ceviches', 'Criollos', 'Bebidas'] as const
  const activeChip = Math.floor(t * 0.5) % chips.length
  chips.forEach((chip, index) => {
    const x = 10 + index * 74
    ctx.fillStyle = index === activeChip ? DIBAL_TEAL : POS_BG
    ctx.fillRect(x, 38, 68, 18)
    ctx.fillStyle = index === activeChip ? '#ffffff' : POS_INK
    ctx.font = 'bold 9px "Space Grotesk", system-ui, sans-serif'
    ctx.fillText(chip, x + 8, 50)
  })
  const platos = [
    ['Ceviche', 'S/ 42'],
    ['Lomo saltado', 'S/ 38'],
    ['Aji de gallina', 'S/ 36'],
    ['Inca Kola', 'S/ 10'],
  ] as const
  platos.forEach(([name, price], index) => {
    const x = 10 + (index % 2) * 82
    const y = 66 + Math.floor(index / 2) * 46
    ctx.strokeStyle = POS_LINE
    ctx.lineWidth = 1.5
    ctx.strokeRect(x, y, 76, 38)
    ctx.fillStyle = POS_INK
    ctx.font = 'bold 9px "Space Grotesk", system-ui, sans-serif'
    ctx.fillText(name, x + 6, y + 15)
    ctx.fillStyle = DIBAL_TEAL
    ctx.font = 'bold 10px "Space Mono", ui-monospace, monospace'
    ctx.fillText(price, x + 6, y + 30)
  })
  // carrito lateral
  ctx.fillStyle = POS_BG
  ctx.fillRect(178, 38, size - 188, 128)
  ctx.fillStyle = POS_INK
  ctx.font = 'bold 9px "Space Mono", ui-monospace, monospace'
  ctx.fillText('1x ceviche', 184, 56)
  ctx.fillText('1x lomo', 184, 70)
  ctx.globalAlpha = 0.7
  ctx.fillText('obs: sin', 184, 88)
  ctx.fillText('cebolla', 184, 100)
  ctx.globalAlpha = 1
  ctx.fillText('S/ 90.00', 184, 126)
  // boton enviar pulsando
  const pulse = 0.75 + Math.sin(t * 3) * 0.25
  ctx.globalAlpha = pulse
  ctx.fillStyle = DIBAL_TEAL
  ctx.fillRect(10, 172, size - 20, 26)
  ctx.globalAlpha = 1
  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 11px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('Enviar a cocina →', 78, 189)
  ctx.fillStyle = POS_INK
  ctx.globalAlpha = 0.6
  ctx.font = '9px "Space Mono", ui-monospace, monospace'
  ctx.fillText('moza: Milagros · sin papel', 10, 216)
  ctx.globalAlpha = 1
}

/** Demo 2: el KDS — la tarjeta entra animada y el cronometro colorea. */
function drawDemoKds(
  ctx: CanvasRenderingContext2D,
  size: number,
  t: number,
): void {
  ctx.fillStyle = '#0c1a22'
  ctx.fillRect(0, 0, size, size)
  ctx.fillStyle = DIBAL_TEAL
  ctx.font = 'bold 12px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('Dibal KDS · Cocina', 8, 18)
  ctx.fillStyle = '#ffffff'
  ctx.globalAlpha = 0.25
  ctx.fillRect(0, 26, size, 2)
  ctx.globalAlpha = 1
  const cycle = (t * 0.9) % 6
  // tarjeta 1: entra deslizando desde la izquierda
  const slide = Math.min(1, cycle / 0.8)
  const x1 = -80 + slide * 90
  ctx.fillStyle = '#122834'
  ctx.fillRect(x1, 38, 108, 92)
  const age = Math.min(1, cycle / 5)
  const timer = age < 0.5 ? KDS_GREEN : age < 0.8 ? KDS_AMBER : KDS_RED
  ctx.fillStyle = timer
  ctx.fillRect(x1, 38, 108, 6)
  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 10px "Space Mono", ui-monospace, monospace'
  ctx.fillText('MESA 4 · 20:41', x1 + 8, 60)
  ctx.font = '9px "Space Mono", ui-monospace, monospace'
  ctx.fillText('1x ceviche', x1 + 8, 76)
  ctx.fillText('1x lomo saltado', x1 + 8, 90)
  ctx.fillStyle = KDS_AMBER
  ctx.fillText('obs: sin cebolla', x1 + 8, 106)
  ctx.fillStyle = timer
  const mm = Math.floor(age * 9)
  ctx.fillText(
    `⏱ 0${mm}:${String(Math.floor(age * 54) % 60).padStart(2, '0')}`,
    x1 + 8,
    122,
  )
  // tarjeta 2: lista para servir
  ctx.fillStyle = '#122834'
  ctx.fillRect(130, 38, 108, 92)
  ctx.fillStyle = DIBAL_TEAL
  ctx.fillRect(130, 38, 108, 6)
  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 10px "Space Mono", ui-monospace, monospace'
  ctx.fillText('MESA 2 · 20:33', 138, 60)
  ctx.font = '9px "Space Mono", ui-monospace, monospace'
  ctx.fillText('2x aji gallina', 138, 76)
  ctx.fillStyle = DIBAL_TEAL
  ctx.fillRect(138, 92, 90, 20)
  ctx.fillStyle = '#0c1a22'
  ctx.font = 'bold 9px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('PARA SERVIR', 146, 105)
  // boton listo
  ctx.strokeStyle = DIBAL_TEAL
  ctx.lineWidth = 2
  ctx.strokeRect(10, 150, 100, 24)
  ctx.fillStyle = DIBAL_TEAL
  ctx.font = 'bold 10px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('Listo ✓', 40, 166)
  ctx.fillStyle = '#ffffff'
  ctx.globalAlpha = 0.5
  ctx.font = '9px "Space Mono", ui-monospace, monospace'
  ctx.fillText('verde→ambar→rojo: la espera', 10, 200)
  ctx.fillText('de la mesa decide el orden', 10, 214)
  ctx.globalAlpha = 1
}

/** Demo 3: la boleta SUNAT — el ticket sube de la termica con su QR. */
function drawDemoBoleta(
  ctx: CanvasRenderingContext2D,
  size: number,
  t: number,
): void {
  posChrome(ctx, size, 'Dibal POS · Caja')
  ctx.fillStyle = POS_INK
  ctx.font = 'bold 10px "Space Mono", ui-monospace, monospace'
  ctx.fillText('op. gravada  S/ 76.27', 10, 52)
  ctx.fillText('IGV 18%      S/ 13.73', 10, 68)
  ctx.font = 'bold 12px "Space Mono", ui-monospace, monospace'
  ctx.fillText('TOTAL        S/ 90.00', 10, 88)
  const medios = ['Efectivo', 'Tarjeta', 'Yape'] as const
  const activo = Math.floor(t * 0.5) % medios.length
  medios.forEach((medio, index) => {
    const y = 104 + index * 22
    ctx.fillStyle = index === activo ? DIBAL_TEAL : POS_BG
    ctx.fillRect(10, y, 74, 18)
    ctx.fillStyle = index === activo ? '#ffffff' : POS_INK
    ctx.font = 'bold 9px "Space Grotesk", system-ui, sans-serif'
    ctx.fillText(medio, 18, y + 12)
  })
  ctx.fillStyle = DIBAL_TEAL
  ctx.fillRect(10, 176, 86, 24)
  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 10px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('Emitir boleta', 16, 192)
  // la termica a la derecha: ranura + ticket subiendo en loop
  ctx.fillStyle = NAVY_DARK
  ctx.fillRect(118, 188, 116, 22)
  const rise = Math.min(1, ((t * 0.9) % 5) / 1.4)
  const ticketH = 120 * rise
  ctx.fillStyle = '#ffffff'
  ctx.strokeStyle = POS_LINE
  ctx.lineWidth = 1.5
  ctx.fillRect(132, 188 - ticketH, 88, ticketH)
  ctx.strokeRect(132, 188 - ticketH, 88, ticketH)
  if (rise > 0.5) {
    ctx.fillStyle = POS_INK
    ctx.font = 'bold 8px "Space Mono", ui-monospace, monospace'
    ctx.fillText('BOLETA B001-', 140, 196 - ticketH + 14)
    ctx.fillText('00001547', 148, 196 - ticketH + 24)
    for (let i = 0; i < 16; i += 1) {
      if (i % 3 !== 1) {
        ctx.fillRect(
          148 + (i % 4) * 6,
          196 - ticketH + 32 + Math.floor(i / 4) * 6,
          5,
          5,
        )
      }
    }
  }
  if (rise >= 1) {
    ctx.fillStyle = KDS_GREEN
    ctx.font = 'bold 9px "Space Grotesk", system-ui, sans-serif'
    ctx.fillText('Enviado a SUNAT ✓', 124, 224)
  }
}

/** Los 3 mockups HTML del panel operable (POS navy + teal). */
function showcaseDemos(): ShowcaseDemo[] {
  const chrome = (title: string): string =>
    '<div style="background:#1b2a4a;color:#fff;padding:.45rem .6rem;' +
    `font-weight:700;border-bottom:3px solid #17b3a6">${title}</div>`
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
    '<span style="display:inline-block;background:#17b3a6;color:#fff;' +
    `padding:.3rem .8rem;font-weight:700;margin:.3rem 0">${text}</span>`
  return [
    {
      key: 'pedido',
      title: {
        es: 'Tomar pedido (tablet)',
        en: 'Take an order (tablet)',
      },
      draw: drawDemoPedido,
      panel: {
        brand: DIBAL_NAVY,
        html: {
          es:
            chrome('Dibal POS · Tomar pedido — Mesa 4 · Moza: Milagros') +
            '<p style="margin:.6rem 0 .3rem"><strong>Categorias:</strong> ' +
            'Ceviches · Criollos · Bebidas</p>' +
            gridTable(
              ['Plato', 'Precio', 'Carrito'],
              [
                ['Ceviche', 'S/ 42.00', '1'],
                ['Lomo saltado', 'S/ 38.00', '1'],
                ['Aji de gallina', 'S/ 36.00', '—'],
                ['Inca Kola', 'S/ 10.00', '1'],
              ],
            ) +
            '<p style="margin:.4rem 0 0">obs: <em>sin cebolla</em> · ' +
            'TOTAL S/ 90.00</p>' +
            tealBtn('Enviar a cocina →') +
            '<p style="opacity:.7;margin:.5rem 0 0">La comanda viaja del ' +
            'salon a la cocina en tiempo real — sin papelitos ni gritos. ' +
            'Plataforma POS multi-restaurante construida DESDE CERO por ' +
            'Pablo, primer dev de Dibal (jQuery + Laravel, luego Vue · ' +
            '2018-2021)</p>',
          en:
            chrome(
              'Dibal POS · Take an order — Table 4 · Waitress: ' + 'Milagros',
            ) +
            '<p style="margin:.6rem 0 .3rem"><strong>Categories:</strong> ' +
            'Ceviches · Creole · Drinks</p>' +
            gridTable(
              ['Dish', 'Price', 'Cart'],
              [
                ['Ceviche', 'S/ 42.00', '1'],
                ['Lomo saltado', 'S/ 38.00', '1'],
                ['Aji de gallina', 'S/ 36.00', '—'],
                ['Inca Kola', 'S/ 10.00', '1'],
              ],
            ) +
            '<p style="margin:.4rem 0 0">note: <em>no onion</em> · ' +
            'TOTAL S/ 90.00</p>' +
            tealBtn('Send to kitchen →') +
            '<p style="opacity:.7;margin:.5rem 0 0">The order travels ' +
            'from the floor to the kitchen in real time — no paper ' +
            'slips, no shouting. Multi-restaurant POS platform built ' +
            'FROM SCRATCH by Pablo, Dibal’s first dev (jQuery + ' +
            'Laravel, then Vue · 2018-2021)</p>',
        },
      },
    },
    {
      key: 'kds',
      title: {
        es: 'Comanda al KDS (cocina)',
        en: 'Order to the KDS (kitchen)',
      },
      draw: drawDemoKds,
      panel: {
        brand: DIBAL_NAVY,
        html: {
          es:
            chrome('Dibal KDS · Pantalla de cocina') +
            gridTable(
              ['Comanda', 'Hora', 'Espera', 'Estado'],
              [
                [
                  'MESA 4 · ceviche + lomo (sin cebolla)',
                  '20:41',
                  '01:12',
                  '🟢 en cola',
                ],
                [
                  'MESA 7 · 2x arroz con mariscos',
                  '20:35',
                  '06:48',
                  '🟡 en fuego',
                ],
                ['MESA 2 · 2x aji de gallina', '20:33', '—', 'PARA SERVIR'],
              ],
            ) +
            tealBtn('Listo ✓ → PARA SERVIR') +
            '<p style="opacity:.7;margin:.5rem 0 0">Las tarjetas entran ' +
            'en orden de llegada con hora y observaciones textuales; el ' +
            'cronometro colorea la urgencia (verde→ambar→rojo) y la mesa ' +
            'que mas espera sale primero. El "Listo" avisa a la moza al ' +
            'instante — la cocina y el salon hablan un solo idioma</p>',
          en:
            chrome('Dibal KDS · Kitchen display') +
            gridTable(
              ['Order', 'Time', 'Waiting', 'Status'],
              [
                [
                  'TABLE 4 · ceviche + lomo (no onion)',
                  '20:41',
                  '01:12',
                  '🟢 queued',
                ],
                ['TABLE 7 · 2x seafood rice', '20:35', '06:48', '🟡 cooking'],
                ['TABLE 2 · 2x aji de gallina', '20:33', '—', 'READY TO SERVE'],
              ],
            ) +
            tealBtn('Done ✓ → READY TO SERVE') +
            '<p style="opacity:.7;margin:.5rem 0 0">Cards arrive in ' +
            'order with time and verbatim notes; the timer colours the ' +
            'urgency (green→amber→red) and the longest-waiting table ' +
            'goes out first. "Done" notifies the waitress instantly — ' +
            'kitchen and floor speak one language</p>',
        },
      },
    },
    {
      key: 'boleta',
      title: {
        es: 'Boleta SUNAT (caja)',
        en: 'SUNAT receipt (till)',
      },
      draw: drawDemoBoleta,
      panel: {
        brand: DIBAL_NAVY,
        html: {
          es:
            chrome('Dibal POS · Caja — Boleta electronica') +
            gridTable(
              ['Concepto', 'Monto'],
              [
                ['Op. gravada', 'S/ 76.27'],
                ['IGV (18%)', 'S/ 13.73'],
                ['TOTAL', 'S/ 90.00'],
              ],
            ) +
            '<p style="margin:.4rem 0 0">Medio de pago: <strong>Yape' +
            '</strong> · Efectivo · Tarjeta</p>' +
            tealBtn('Emitir boleta') +
            '<p style="margin:.5rem 0 0"><code>BOLETA DE VENTA ' +
            'ELECTRONICA B001-00001547</code> · QR de consulta · ' +
            '<strong style="color:#3aa856">Enviado a SUNAT ' +
            'correctamente ✓</strong></p>' +
            '<p style="opacity:.7;margin:.5rem 0 0">Facturacion ' +
            'electronica directa al fisco peruano: cero multas, caja ' +
            'cuadrada en vivo. Desplegada en AWS (EC2/RDS/S3/' +
            'AutoScaling/Load Balancer) · Founding Dev & Tech Lead, ' +
            '2018-2021</p>',
          en:
            chrome('Dibal POS · Till — Electronic receipt') +
            gridTable(
              ['Item', 'Amount'],
              [
                ['Taxable base', 'S/ 76.27'],
                ['IGV (18%)', 'S/ 13.73'],
                ['TOTAL', 'S/ 90.00'],
              ],
            ) +
            '<p style="margin:.4rem 0 0">Payment method: <strong>Yape' +
            '</strong> · Cash · Card</p>' +
            tealBtn('Issue receipt') +
            '<p style="margin:.5rem 0 0"><code>ELECTRONIC SALES ' +
            'RECEIPT B001-00001547</code> · verification QR · ' +
            '<strong style="color:#3aa856">Sent to SUNAT ' +
            'successfully ✓</strong></p>' +
            '<p style="opacity:.7;margin:.5rem 0 0">E-invoicing ' +
            'straight to the Peruvian tax authority: zero fines, a ' +
            'till balanced live. Deployed on AWS (EC2/RDS/S3/' +
            'AutoScaling/Load Balancer) · Founding Dev & Tech Lead, ' +
            '2018-2021</p>',
        },
      },
    },
  ]
}

/** Boleta flotante sobre la caja: el comprobante con su sello SUNAT. */
function drawBoletaFloat(ctx: CanvasRenderingContext2D, size: number): void {
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(6, 2, size - 12, size - 4)
  ctx.strokeStyle = '#c8d0d8'
  ctx.lineWidth = 3
  ctx.strokeRect(6, 2, size - 12, size - 4)
  ctx.fillStyle = '#1c2430'
  ctx.font = 'bold 11px "Space Mono", ui-monospace, monospace'
  ctx.textAlign = 'center'
  ctx.fillText('BOLETA', size / 2, 26)
  ctx.fillText('ELECTRONICA', size / 2, 40)
  ctx.fillStyle = DIBAL_NAVY
  ctx.fillText('B001-00001547', size / 2, 58)
  ctx.textAlign = 'left'
  // QR
  ctx.fillStyle = '#1c2430'
  for (let i = 0; i < 25; i += 1) {
    if (i % 3 !== 1) {
      ctx.fillRect(20 + (i % 5) * 7, 68 + Math.floor(i / 5) * 7, 6, 6)
    }
  }
  ctx.fillStyle = DIBAL_TEAL
  ctx.font = 'bold 9px "Space Mono", ui-monospace, monospace'
  ctx.fillText('ACEPTADO', 64, 84)
  ctx.fillText('SUNAT ✓', 64, 96)
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

/** Micro de la comanda: el sobre vuela de la tablet al KDS y la
 *  tarjeta aparece, madura y pasa a "para servir" (maquina de estados). */
function comandaMicro(opts: {
  roomIndex: number
  sobre: Mesh
  from: readonly [number, number, number]
  to: readonly [number, number, number]
  kds: ScreenSwap
}): { interactable: Interactable; update(t: number): void } {
  const { sobre, from, to, kds } = opts
  let startT = -1
  return {
    interactable: {
      id: `micro-dibal-comanda-${opts.roomIndex}`,
      x: from[0],
      z: from[2],
      radius: 2.0,
      label: COMANDA_LABEL,
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
        sobre.visible = true
      }
      if (startT < 0) {
        return
      }
      const elapsed = t - startT
      if (elapsed < 1.6) {
        // el sobre vuela en arco de la tablet al KDS
        const k = elapsed / 1.6
        sobre.visible = true
        sobre.position.set(
          from[0] + (to[0] - from[0]) * k,
          from[1] + (to[1] - from[1]) * k + Math.sin(k * Math.PI) * 0.6,
          from[2] + (to[2] - from[2]) * k,
        )
        sobre.rotation.y = k * 4
      } else if (elapsed < 5.5) {
        sobre.visible = false
        kds.show('nueva')
      } else if (elapsed < 8.2) {
        kds.show('listo')
      } else {
        kds.show('run')
        startT = -1
      }
    },
  }
}

/** Micro de la boleta: la termica escupe el ticket, el sello de SUNAT
 *  flota unos segundos y el POS cicla el medio de pago registrado. */
function boletaMicro(opts: {
  roomIndex: number
  position: readonly [number, number]
  ticket: Mesh
  badge: { visible: boolean }
  pos: ScreenSwap
  mediosCount: number
}): { interactable: Interactable; update(t: number): void } {
  const { ticket, badge, pos } = opts
  let startT = -1
  let medioIndex = 0
  return {
    interactable: {
      id: `micro-dibal-boleta-${opts.roomIndex}`,
      x: opts.position[0],
      z: opts.position[1],
      radius: 2.0,
      label: BOLETA_LABEL,
      onActivate: () => {
        if (startT === -1) {
          startT = -2
          pos.show(`boleta-${medioIndex}`)
          medioIndex = (medioIndex + 1) % opts.mediosCount
          sfx.play('blip')
        }
      },
    },
    update: (t: number) => {
      if (startT === -2) {
        startT = t
        ticket.visible = true
      }
      if (startT < 0) {
        return
      }
      const elapsed = t - startT
      if (elapsed < 1.0) {
        ticket.visible = true
        ticket.position.y = 1.1 + elapsed * 0.22
      } else if (elapsed < 4.6) {
        badge.visible = true
      } else {
        badge.visible = false
        ticket.visible = false
        ticket.position.y = 1.1
        pos.show('venta')
        startT = -1
      }
    },
  }
}

type MonitorVariant = {
  title: string
  lines: string[]
  theme: { screenBg: string; screenFg: string; ink: string }
  dot: string
}

/** Variantes del KDS: cola normal, comanda nueva y "para servir". */
function kdsVariantsFor(
  locale: Locale,
  theme: MonitorVariant['theme'],
): Record<string, MonitorVariant> {
  const es = locale === 'es'
  return {
    run: {
      title: es ? 'KDS · cocina' : 'KDS · kitchen',
      lines: es
        ? [
            'M2 · lomo saltado  05:12',
            'M5 · ceviche x2    02:40',
            '',
            'sin comandas nuevas',
          ]
        : [
            'T2 · lomo saltado  05:12',
            'T5 · ceviche x2    02:40',
            '',
            'no new orders',
          ],
      theme,
      dot: KDS_GREEN,
    },
    nueva: {
      title: es ? 'KDS · NUEVA COMANDA' : 'KDS · NEW ORDER',
      lines: es
        ? [
            'MESA 4 · 20:41',
            '1x ceviche      S/ 42',
            '1x lomo saltado S/ 38',
            'obs: sin cebolla',
          ]
        : [
            'TABLE 4 · 20:41',
            '1x ceviche      S/ 42',
            '1x lomo saltado S/ 38',
            'note: no onion',
          ],
      theme,
      dot: KDS_AMBER,
    },
    listo: {
      title: es ? 'KDS · cocina' : 'KDS · kitchen',
      lines: es
        ? ['MESA 4: PARA SERVIR', 'la moza ya lo ve', 'tiempo total: 03:12', '']
        : [
            'TABLE 4: READY TO SERVE',
            'the waitress sees it',
            'total time: 03:12',
            '',
          ],
      theme,
      dot: KDS_GREEN,
    },
  }
}

/** Variantes del POS: la venta abierta + la boleta por medio de pago. */
function posVariantsFor(
  locale: Locale,
  theme: MonitorVariant['theme'],
  medios: readonly string[],
): Record<string, MonitorVariant> {
  const es = locale === 'es'
  const variants: Record<string, MonitorVariant> = {
    venta: {
      title: es ? 'POS · mesa 4' : 'POS · table 4',
      lines: [
        '1x ceviche      S/ 42.00',
        '1x lomo saltado S/ 38.00',
        '1x Inca Kola    S/ 10.00',
        'TOTAL           S/ 90.00',
      ],
      theme,
      dot: DIBAL_TEAL,
    },
  }
  medios.forEach((medio, index) => {
    variants[`boleta-${index}`] = {
      title: 'BOLETA B001-00001547',
      lines: es
        ? [
            `pago: ${medio}`,
            'op. gravada  S/ 76.27',
            'IGV 18%      S/ 13.73',
            'SUNAT: ACEPTADA ✓',
          ]
        : [
            `payment: ${medio}`,
            'taxable     S/ 76.27',
            'IGV 18%     S/ 13.73',
            'SUNAT: ACCEPTED ✓',
          ],
      theme,
      dot: KDS_GREEN,
    }
  })
  return variants
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
      id: `micro-dibal-${roomIndex}-laptop${toggle.spot}`,
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

export default function buildDibal(ctx: RoomCtx): RoomBuild {
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

  // LA MESA DE PABLO (decision del usuario): el rincon del founding dev
  // en el back-office — su laptop encendida con codigo (el anda
  // caminando el salon) + 1 libre togglable con E
  const deskSpots: readonly (readonly [number, number])[] = [
    [2.4, room.z - 4.0],
    [4.1, room.z - 4.4],
  ]
  const office = officeLayout({
    roomIndex: room.index,
    state,
    spots: deskSpots,
    color: NAVY_DARK,
    poweredSpots: new Set([0]),
    screenTheme,
    screenFor: (index) => LAPTOP_SCREENS[index] ?? LAPTOP_SCREENS[0],
  })
  group.add(office.group)
  staticColliders.push(...office.colliders)
  disposables.push(office)
  interactables.push(...laptopToggles(office, deskSpots, room.index))
  interactables.push(...office.seats)
  const pabloLabel = label(
    locale === 'es' ? 'LA MESA DE PABLO' : "PABLO'S DESK",
    { size: 0.13, color: theme.accent },
  )
  pabloLabel.position.set(3.25, 1.85, room.z - 4.6)
  group.add(pabloLabel)

  // router + cableado teal del rincon dev: el SaaS vive en la nube,
  // pero el local se conecta por aqui
  group.add(
    outlinedMergedBoxes(
      [{ w: 0.5, h: 0.14, d: 0.2, x: 1.2, y: 2.3, z: backZ + 0.16 }],
      toonMat(NAVY_DARK),
      { castShadow: true },
    ),
    mergedBoxes(
      [
        { w: 0.04, h: 1.6, d: 0.04, x: 1.05, y: 1.46, z: backZ + 0.1 },
        { w: 0.04, h: 2.0, d: 0.04, x: 1.35, y: 1.26, z: backZ + 0.1 },
        { w: 1.2, h: 0.04, d: 0.04, x: 1.95, y: 2.34, z: backZ + 0.1 },
      ],
      toonMat(DIBAL_TEAL),
    ),
  )

  // COCINA (muro -X, fondo): mesada corrida con hornillas, ollas y la
  // campana — la mitad que recibe las comandas
  group.add(
    outlinedMergedBoxes(
      [
        // mesada en L + cuerpo bajo
        { w: 1.1, h: 0.9, d: 2.8, x: -half + 0.75, y: 0.45, z: room.z - 4.2 },
        // hornillas sobre la mesada
        {
          w: 0.6,
          h: 0.06,
          d: 0.6,
          x: -half + 0.75,
          y: 0.93,
          z: room.z - 4.9,
        },
        { w: 0.6, h: 0.06, d: 0.6, x: -half + 0.75, y: 0.93, z: room.z - 4.1 },
        // campana extractora colgada
        { w: 1.0, h: 0.5, d: 1.6, x: -half + 0.75, y: 2.35, z: room.z - 4.5 },
        // soporte del KDS sobre el pase
        { w: 0.08, h: 0.5, d: 0.08, x: -half + 1.4, y: 2.0, z: room.z - 3.0 },
      ],
      toonMat(STEEL_KITCHEN),
      { castShadow: true },
    ),
    // ollas humeantes sobre las hornillas
    mergedBoxes(
      [
        { w: 0.4, h: 0.26, d: 0.4, x: -half + 0.75, y: 1.1, z: room.z - 4.9 },
        { w: 0.32, h: 0.2, d: 0.32, x: -half + 0.75, y: 1.06, z: room.z - 4.1 },
      ],
      toonMat('#3a4048'),
    ),
  )
  staticColliders.push(footprint(-half + 0.75, room.z - 4.2, 1.3, 3.0))
  const cocinaLabel = label(locale === 'es' ? 'COCINA' : 'KITCHEN', {
    size: 0.14,
    color: theme.accent,
  })
  cocinaLabel.position.set(-half + 0.75, 2.85, room.z - 4.2)
  cocinaLabel.rotation.y = Math.PI / 2
  group.add(cocinaLabel)

  // pantalla KDS colgada mirando a la cocina: tarjetas de comanda con
  // cronometro — la micro de la comanda la hace reaccionar
  const kds = switchableMonitor({
    position: [-half + 1.4, 1.62, room.z - 3.0],
    rotationY: Math.PI / 2,
    width: 0.62,
    variants: kdsVariantsFor(locale, screenTheme),
    initial: 'run',
  })
  group.add(kds.group)
  disposables.push(kds.screen)

  // pase de cocina: los platos emplatados "para servir" + la impresora
  // de cocina (KOT) escupiendo su ticket
  group.add(
    desk({
      position: [-half + 2.5, 0, room.z - 3.4],
      rotationY: Math.PI / 2,
      width: 1.5,
      color: NAVY_DARK,
    }),
    // platos para servir sobre el pase
    mergedBoxes(
      [
        { w: 0.26, h: 0.04, d: 0.26, x: -half + 2.4, y: 0.77, z: room.z - 3.8 },
        { w: 0.26, h: 0.04, d: 0.26, x: -half + 2.6, y: 0.77, z: room.z - 3.1 },
      ],
      toonMat('#f0efe8'),
    ),
    mergedBoxes(
      [
        { w: 0.16, h: 0.08, d: 0.16, x: -half + 2.4, y: 0.82, z: room.z - 3.8 },
        { w: 0.16, h: 0.08, d: 0.16, x: -half + 2.6, y: 0.82, z: room.z - 3.1 },
      ],
      toonMat(WOOD),
    ),
    // impresora KOT: cuerpo + ticket asomando
    mergedBoxes(
      [
        {
          w: 0.22,
          h: 0.16,
          d: 0.24,
          x: -half + 2.55,
          y: 0.83,
          z: room.z - 2.85,
        },
        {
          w: 0.14,
          h: 0.12,
          d: 0.02,
          x: -half + 2.55,
          y: 1.0,
          z: room.z - 2.94,
        },
      ],
      toonMat('#3a4048'),
    ),
  )
  staticColliders.push(footprint(-half + 2.5, room.z - 3.4, 0.9, 1.6))

  // Chef Ernesto vigila el pase; el label del "para servir" lo corona
  const paseLabel = label(locale === 'es' ? 'PARA SERVIR' : 'READY TO SERVE', {
    size: 0.12,
    color: theme.accent,
  })
  paseLabel.position.set(-half + 2.5, 1.5, room.z - 3.4)
  paseLabel.rotation.y = Math.PI / 2
  group.add(paseLabel)

  // SALON: 3 mesas con manteles navy, platos de comida peruana e Inca
  // Kola; comensales de fondo fusionados (relleno barato, decision 10)
  const mesas: readonly (readonly [number, number])[] = [
    [-1.4, room.z + 0.4],
    [1.6, room.z + 1.2],
    [-0.4, room.z + 2.9],
  ]
  const diningChair = (x: number, cz: number, dir: 1 | -1) => [
    { w: 0.42, h: 0.05, d: 0.42, x, y: 0.44, z: cz },
    { w: 0.42, h: 0.5, d: 0.05, x, y: 0.72, z: cz - dir * 0.2 },
    { w: 0.05, h: 0.44, d: 0.05, x: x - 0.17, y: 0.22, z: cz - dir * 0.1 },
    { w: 0.05, h: 0.44, d: 0.05, x: x + 0.17, y: 0.22, z: cz - dir * 0.1 },
  ]
  group.add(
    outlinedMergedBoxes(
      mesas.flatMap(([x, z]) => [
        { w: 0.95, h: 0.06, d: 0.95, x, y: 0.74, z },
        { w: 0.14, h: 0.74, d: 0.14, x, y: 0.37, z },
        ...diningChair(x, z - 0.6, 1),
        ...diningChair(x, z + 0.6, -1),
      ]),
      toonMat(DIBAL_NAVY),
      { inflate: 0.035, castShadow: true },
    ),
    // platos con comida (ceviche blanco, lomo marron) sobre las mesas
    mergedBoxes(
      mesas.flatMap(([x, z]) => [
        { w: 0.22, h: 0.03, d: 0.22, x: x - 0.2, y: 0.79, z: z - 0.14 },
        { w: 0.22, h: 0.03, d: 0.22, x: x + 0.2, y: 0.79, z: z + 0.14 },
      ]),
      toonMat('#f0efe8'),
    ),
    mergedBoxes(
      mesas.flatMap(([x, z], index) => [
        {
          w: 0.13,
          h: 0.06,
          d: 0.13,
          x: x - 0.2,
          y: 0.82,
          z: z - 0.14,
          rotY: index,
        },
        { w: 0.13, h: 0.06, d: 0.13, x: x + 0.2, y: 0.82, z: z + 0.14 },
      ]),
      toonMat(FOOD_BROWN),
    ),
    // botellas de Inca Kola: el amarillo dorado de cada mesa
    mergedBoxes(
      mesas.map(([x, z]) => ({
        w: 0.07,
        h: 0.26,
        d: 0.07,
        x: x + 0.02,
        y: 0.9,
        z: z - 0.02,
      })),
      toonMat(INKA_AMBER),
    ),
  )
  for (const [x, z] of mesas) {
    staticColliders.push(footprint(x, z, 1.15, 1.15))
  }

  // comensales de fondo (siluetas fusionadas: torso + cabeza sentados)
  group.add(
    outlinedMergedBoxes(
      [
        // mesa A: pareja
        { w: 0.4, h: 0.56, d: 0.3, x: -1.4, y: 0.72, z: room.z - 0.25 },
        { w: 0.24, h: 0.24, d: 0.24, x: -1.4, y: 1.14, z: room.z - 0.25 },
        { w: 0.4, h: 0.56, d: 0.3, x: -1.4, y: 0.72, z: room.z + 1.05 },
        { w: 0.24, h: 0.24, d: 0.24, x: -1.4, y: 1.14, z: room.z + 1.05 },
        // mesa B: un comensal solo
        { w: 0.4, h: 0.56, d: 0.3, x: 1.6, y: 0.72, z: room.z + 1.85 },
        { w: 0.24, h: 0.24, d: 0.24, x: 1.6, y: 1.14, z: room.z + 1.85 },
      ],
      toonMat('#243044'),
      { castShadow: true },
    ),
  )
  staticColliders.push(
    footprint(-1.4, room.z - 0.25, 0.5, 0.5),
    footprint(-1.4, room.z + 1.05, 0.5, 0.5),
    footprint(1.6, room.z + 1.85, 0.5, 0.5),
  )

  // soporte de la tablet de pedidos (la micro de la comanda vive aqui)
  group.add(
    outlinedMergedBoxes(
      [
        { w: 0.3, h: 0.06, d: 0.3, x: 0.7, y: 0.03, z: room.z - 0.9 },
        { w: 0.08, h: 0.95, d: 0.08, x: 0.7, y: 0.53, z: room.z - 0.9 },
        { w: 0.34, h: 0.24, d: 0.04, x: 0.7, y: 1.1, z: room.z - 0.9 },
      ],
      toonMat(NAVY_DARK),
      { castShadow: true },
    ),
  )
  staticColliders.push(footprint(0.7, room.z - 0.9, 0.45, 0.45))
  const tabletGlow = boxMesh(0.28, 0.18, 0.012, basicMat(DIBAL_TEAL))
  tabletGlow.position.set(0.7, 1.1, room.z - 0.925)
  tabletGlow.userData.noOutline = true
  group.add(tabletGlow)

  // el sobre navy de la comanda: vuela de la tablet al KDS al activar
  const sobre = boxMesh(0.2, 0.05, 0.28, toonMat(DIBAL_NAVY))
  sobre.visible = false
  group.add(sobre)
  const comanda = comandaMicro({
    roomIndex: room.index,
    sobre,
    from: [0.7, 1.15, room.z - 0.9],
    to: [-half + 1.4, 1.62, room.z - 3.0],
    kds: kds.screen,
  })
  interactables.push(comanda.interactable)
  updates.push(comanda.update)

  // CAJA (frente, lado -X): mostrador navy con el POS, la impresora
  // termica, el cajon de soles y la boleta flotante con su sello
  group.add(
    outlinedMergedBoxes(
      [
        { w: 1.7, h: 0.95, d: 0.6, x: -2.8, y: 0.475, z: room.z + 4.5 },
        // cajon de dinero bajo el POS (frente con manija)
        { w: 0.44, h: 0.14, d: 0.05, x: -3.1, y: 0.62, z: room.z + 4.19 },
        { w: 0.14, h: 0.03, d: 0.03, x: -3.1, y: 0.62, z: room.z + 4.16 },
      ],
      toonMat(DIBAL_NAVY),
      { inflate: 0.03, castShadow: true },
    ),
  )
  staticColliders.push(footprint(-2.8, room.z + 4.5, 1.9, 0.8))
  const cajaLabel = label(locale === 'es' ? 'CAJA' : 'TILL', {
    size: 0.14,
    color: theme.accent,
  })
  cajaLabel.position.set(-2.8, 1.7, room.z + 4.5)
  cajaLabel.rotation.y = Math.PI
  group.add(cajaLabel)

  // terminal POS todo-en-uno sobre el mostrador: cicla el medio de pago
  const medios =
    locale === 'es'
      ? (['efectivo', 'tarjeta', 'Yape'] as const)
      : (['cash', 'card', 'Yape'] as const)
  const pos = switchableMonitor({
    position: [-3.15, 0.95, room.z + 4.55],
    rotationY: Math.PI,
    width: 0.52,
    variants: posVariantsFor(locale, screenTheme, medios),
    initial: 'venta',
  })
  group.add(pos.group)
  disposables.push(pos.screen)

  // impresora termica + rollo de repuesto sobre el mostrador
  group.add(
    mergedBoxes(
      [
        { w: 0.26, h: 0.18, d: 0.28, x: -2.35, y: 1.04, z: room.z + 4.5 },
        { w: 0.14, h: 0.14, d: 0.14, x: -2.06, y: 1.02, z: room.z + 4.56 },
      ],
      toonMat('#3a4048'),
    ),
  )
  const ticket = boxMesh(0.16, 0.24, 0.012, basicMat('#ffffff'))
  ticket.position.set(-2.35, 1.1, room.z + 4.38)
  ticket.visible = false
  ticket.userData.noOutline = true
  group.add(ticket)
  const sunatBadge = label(
    locale === 'es' ? 'Enviado a SUNAT ✓' : 'Sent to SUNAT ✓',
    { size: 0.12, color: KDS_GREEN },
  )
  sunatBadge.position.set(-2.35, 1.55, room.z + 4.3)
  sunatBadge.rotation.y = Math.PI
  sunatBadge.visible = false
  group.add(sunatBadge)

  // micro: emitir la boleta — la termica escupe el ticket, el POS
  // registra el medio de pago (ciclando) y el sello aparece
  const boleta = boletaMicro({
    roomIndex: room.index,
    position: [-2.4, room.z + 4.4],
    ticket,
    badge: sunatBadge,
    pos: pos.screen,
    mediosCount: medios.length,
  })
  interactables.push(boleta.interactable)
  updates.push(boleta.update)

  // comprobante flotante sobre la caja: la boleta con QR y sello,
  // meciendose como recordatorio del diferenciador legal
  const boletaFloat = new Mesh(
    new PlaneGeometry(0.46, 0.62),
    new MeshBasicMaterial({
      map: makeCanvasTexture(128, drawBoletaFloat),
      transparent: false,
    }),
  )
  boletaFloat.position.set(-2.8, 2.15, room.z + 4.5)
  boletaFloat.rotation.y = Math.PI
  boletaFloat.userData.noOutline = true
  group.add(boletaFloat)
  updates.push((t) => {
    boletaFloat.position.y = 2.15 + Math.sin(t * 1.4) * 0.06
  })

  // cuadros de rubro (wallArt): flujo mozo->KDS, boleta SUNAT y el
  // organigrama "De 1 a 5 devs" inspeccionables (3 fichas — decision
  // del usuario); el mapa multi-restaurante queda decorativo
  const art = wallArt({
    roomIndex: room.index,
    theme,
    locale,
    onFicha: actions.openStory,
    frames: [
      {
        key: 'flujo-mozo-kds',
        position: [-3.6, 2, backZ + 0.08],
        rotationY: 0,
        draw: drawFlujo,
        ficha: ART_FICHA_FLUJO,
      },
      {
        key: 'boleta-sunat',
        position: [3.6, 2, backZ + 0.08],
        rotationY: 0,
        draw: drawBoletaArt,
        ficha: ART_FICHA_BOLETA,
      },
      {
        key: 'de-1-a-5-devs',
        position: [-3.6, 2, frontZ - 0.08],
        rotationY: Math.PI,
        draw: drawEquipo,
        ficha: ART_FICHA_EQUIPO,
      },
      {
        key: 'mapa-dibal',
        position: [3.6, 2, frontZ - 0.08],
        rotationY: Math.PI,
        draw: drawMapa,
      },
    ],
  })
  staticColliders.push(...art.colliders)
  const sink = { group, interactables, updates }
  addProps(sink, art.props)

  // showcase del software junto a la puerta al pasillo (canon AC-6):
  // el POS Dibal — E cicla las 3 demos (pedido, KDS, boleta)
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

  // NPCs del canon (variante unico dev, informe 11): Don Ricardo
  // (dueño, junto a la mesa de Pablo), Milagros (moza en ronda por el
  // salon), Ernesto (cocinero en el pase), Rosa (cajera tras el
  // mostrador) y Andrea (comensal sentada en su mesa).
  const coworkers = npcCoworkers({
    roomIndex: room.index,
    openDialog: actions.openDialog,
    validateMix: false,
    npcs: [
      {
        key: 'ricardo',
        role: 'boss',
        spec: {
          skin: '#b5825f',
          hair: { style: 'short', color: '#3a3430' },
          top: '#e8e4da',
          bottom: '#2e3238',
          accessory: 'tie',
          model: 'joe',
          faceSeed: 18,
        },
        position: [3.2, 0, room.z - 3.3],
        rotationY: Math.PI,
        dialog: DIBAL_PRESENTE_DIALOGS.ricardo,
      },
      {
        key: 'milagros',
        role: 'staff',
        spec: {
          skin: '#c98f6a',
          hair: { style: 'ponytail', color: '#1a140e' },
          top: NAVY_DARK,
          bottom: '#2e3238',
          accessory: 'badge',
          model: 'suzie',
          faceSeed: 35,
        },
        position: [0.7, 0, room.z - 0.4],
        path: [
          [0.7, room.z - 0.4],
          [-1.6, room.z + 1.1],
          [1.8, room.z + 2.0],
        ],
        speed: 0.55,
        dialog: DIBAL_PRESENTE_DIALOGS.milagros,
      },
      {
        key: 'ernesto',
        role: 'staff',
        spec: {
          skin: '#8a5a3c',
          hair: { style: 'bun', color: '#f0f2f4' },
          top: '#f0eee8',
          bottom: '#c8ccd2',
          accessory: 'badge',
          model: 'pete',
          faceSeed: 56,
        },
        position: [-half + 1.7, 0, room.z - 4.3],
        rotationY: Math.PI / 2,
        dialog: DIBAL_PRESENTE_DIALOGS.ernesto,
      },
      {
        key: 'rosa',
        role: 'staff',
        spec: {
          skin: '#d9a684',
          hair: { style: 'bun', color: '#2a1a12' },
          top: DIBAL_NAVY,
          bottom: '#3a4048',
          accessory: 'badge',
          model: 'louise',
          faceSeed: 71,
        },
        position: [-2.8, 0, room.z + 5.15],
        rotationY: Math.PI,
        dialog: DIBAL_PRESENTE_DIALOGS.rosa,
      },
      {
        key: 'andrea',
        role: 'staff',
        spec: {
          skin: '#e8b48c',
          hair: { style: 'ponytail', color: '#2c1e14' },
          top: '#7a4fc0',
          bottom: '#3a4048',
          model: 'michelle',
          faceSeed: 88,
        },
        position: [-0.4, 0, room.z + 2.3],
        rotationY: 0,
        pose: 'sit',
        dialog: DIBAL_PRESENTE_DIALOGS.andrea,
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
