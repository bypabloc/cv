/**
 * @module rooms/futuro (engine)
 * @description Sala 8 — FUTURO (SINTETICA, cierre del recorrido), al canon
 *   con las excepciones documentadas del informe 14: SIN grieta al pasado
 *   (no hay "antes" de una vision), SIN showcase de producto (no es una
 *   empresa) y 1 solo NPC — "Pablo del futuro" — en vez del mix 2C+2P.
 *   Composicion axial: el jugador entra por el muro trasero y el recorrido
 *   termina de frente a la puerta PROXIMAMENTE grande (muro final) con el
 *   CTA de contacto — el holograma — en el eje, delante de ella. La vision
 *   (ideas elegidas por el usuario 2026-07-05): Staff/Principal, IA que
 *   pasa de herramienta a producto propio (copilots, indie/SaaS a costo
 *   ~0, emprendimiento LATAM), multiplicar via mentoria + open source +
 *   contenido publico, nuevos conocimientos y nuevos rubros ("cada reto
 *   nuevo es una sala nueva"). Props: pizarra de roadmap (5 nodos
 *   ascendentes, via wallArt), 4 laminas (3 fichas: manifiesto, productos
 *   propios, comunidad; la meta-narrativa del journey queda decorativa),
 *   rincon de escritorios ligero (3 puestos, laptops apagadas togglables
 *   con pantallas de "lo que viene") e infoKit SIN portal. Paredes blanco
 *   hueso; acento azul-violeta #5a6ff0 — la luz mas clara del recorrido.
 */
import { Group, Mesh, OctahedronGeometry } from 'three'
import type { Box2 } from '../../lib/collision'
import type { Locale } from '../../lib/rooms'
import { sfx } from '../audio'
import type { NpcHandle } from '../character'
import { FUTURO_PRESENTE_DIALOGS } from '../dialogs/futuro-presente'
import type { Interactable } from '../state'
import {
  boxMesh,
  type DrawFn,
  disposeDeep,
  label,
  outlineGroup,
  toonMat,
  toonMatOwn,
} from '../toon'
import type { RoomBuild, RoomCtx } from '../world'
import {
  footprint,
  infoKit,
  npcCoworkers,
  type OfficeLayout,
  officeLayout,
  type PropHandle,
  wallArt,
} from './props'
import { placeProp } from './props-catalog'

const CONTACT_LABEL = {
  es: 'Contactar a Pablo',
  en: 'Contact Pablo',
} as const

const LAPTOP_LABELS = {
  on: { es: 'Encender la laptop', en: 'Power on the laptop' },
  off: { es: 'Apagar la laptop', en: 'Power off the laptop' },
} as const

/** Pantallas de los puestos vacios: lo que viene, en codigo. */
const LAPTOP_SCREENS = [
  {
    title: 'agente.ts — copilot',
    lines: [
      'const agent = new Agent({',
      "  model: 'claude',",
      '  tools: [cv, contacto],',
      '})  // en construccion',
    ],
  },
  {
    title: 'roadmap.md',
    lines: [
      '- [x] fintech a escala',
      '- [ ] producto IA propio',
      '- [ ] mentoria x comunidad',
      '- [ ] rubro nuevo: ¿?',
    ],
  },
  {
    title: 'ideas.py — indie',
    lines: [
      'ideas = ["saas latam",',
      '  "copilot de dominio",',
      '  "oss tooling"]',
      'ship(ideas.pop())  # hoy',
    ],
  },
] as const

// mobiliario sci-fi CC0 (Kenney Space Station Kit, ver public/models/CREDITS.md):
// la vision futura estrena estaciones de trabajo del pack espacial (texturadas
// con su colormap; el toon shading las integra al resto de la sala)
const SPACE_DESK = '/models/furniture/space/table.glb'
const SPACE_CHAIR = '/models/furniture/space/chair.glb'

// --- paleta de la vision (informe 14) ---

const FUT_VIOLET = '#5a6ff0'
const FUT_VIOLET_DARK = '#39418c'
const ART_PAPER = '#f8f6f0'
const ART_INK = '#1c2136'
const PANEL_INK = '#141830'

// --- laminas Canvas (tinta plana) ---

function artBase(ctx: CanvasRenderingContext2D, size: number): void {
  ctx.fillStyle = ART_PAPER
  ctx.fillRect(0, 0, size, size)
  ctx.strokeStyle = ART_INK
  ctx.globalAlpha = 0.35
  ctx.lineWidth = 3
  ctx.strokeRect(10, 10, size - 20, size - 20)
  ctx.globalAlpha = 1
}

/** Manifiesto: la estrella polar y la flecha ascendente de la vision. */
function drawManifiesto(locale: Locale): DrawFn {
  return (ctx, size) => {
    artBase(ctx, size)
    ctx.fillStyle = ART_INK
    ctx.font = 'bold 15px "Space Grotesk", system-ui, sans-serif'
    ctx.fillText(
      locale === 'es' ? 'HACIA DONDE VOY' : 'WHERE I AM HEADING',
      20,
      36,
    )
    // flecha ascendente (la carrera sigue subiendo)
    ctx.strokeStyle = FUT_VIOLET
    ctx.lineWidth = 5
    ctx.beginPath()
    ctx.moveTo(36, 210)
    ctx.lineTo(150, 120)
    ctx.lineTo(196, 88)
    ctx.stroke()
    ctx.fillStyle = FUT_VIOLET
    ctx.beginPath()
    ctx.moveTo(214, 74)
    ctx.lineTo(186, 82)
    ctx.lineTo(202, 100)
    ctx.closePath()
    ctx.fill()
    // estrella polar
    ctx.font = 'bold 30px "Space Grotesk", system-ui, sans-serif'
    ctx.fillText('★', 208, 62)
    ctx.fillStyle = ART_INK
    ctx.font = 'bold 11px "Space Mono", ui-monospace, monospace'
    ctx.fillText('staff/principal · IA', 36, 230)
    ctx.fillText(
      locale === 'es' ? 'mentoria · productos' : 'mentorship · products',
      36,
      244,
    )
  }
}

/** Productos propios: la caja que se lanza (IA · SaaS · LATAM). */
const drawProductos: DrawFn = (ctx, size) => {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 15px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('SHIP IT', 20, 36)
  // cohete: cuerpo + punta + llama
  ctx.fillStyle = FUT_VIOLET
  ctx.fillRect(112, 82, 32, 74)
  ctx.beginPath()
  ctx.moveTo(128, 52)
  ctx.lineTo(108, 84)
  ctx.lineTo(148, 84)
  ctx.closePath()
  ctx.fill()
  ctx.fillStyle = '#e2a53a'
  ctx.beginPath()
  ctx.moveTo(118, 158)
  ctx.lineTo(128, 184)
  ctx.lineTo(138, 158)
  ctx.closePath()
  ctx.fill()
  // los 3 tanques de carga
  ctx.strokeStyle = ART_INK
  ctx.lineWidth = 3
  const cargas: readonly (readonly [number, string])[] = [
    [26, 'IA'],
    [96, 'SaaS'],
    [166, 'LATAM'],
  ]
  ctx.font = 'bold 10px "Space Mono", ui-monospace, monospace'
  for (const [x, name] of cargas) {
    ctx.strokeRect(x, 198, 64, 30)
    ctx.fillStyle = ART_INK
    ctx.fillText(name, x + 8, 217)
  }
}

/** Comunidad: el grafo de gente conectada + oss/blog/talks. */
const drawComunidad: DrawFn = (ctx, size) => {
  artBase(ctx, size)
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 15px "Space Grotesk", system-ui, sans-serif'
  ctx.fillText('MULTIPLICAR', 20, 36)
  // grafo: nodo central (Pablo) conectado a la comunidad
  const nodes: readonly (readonly [number, number])[] = [
    [128, 128],
    [56, 84],
    [200, 84],
    [48, 180],
    [128, 208],
    [208, 180],
  ]
  ctx.strokeStyle = FUT_VIOLET
  ctx.lineWidth = 3
  for (const [x, y] of nodes.slice(1)) {
    ctx.beginPath()
    ctx.moveTo(128, 128)
    ctx.lineTo(x, y)
    ctx.stroke()
  }
  for (const [i, [x, y]] of nodes.entries()) {
    ctx.fillStyle = i === 0 ? FUT_VIOLET : ART_PAPER
    ctx.beginPath()
    ctx.arc(x, y, i === 0 ? 16 : 11, 0, Math.PI * 2)
    ctx.fill()
    ctx.strokeStyle = ART_INK
    ctx.stroke()
  }
  ctx.fillStyle = ART_INK
  ctx.font = 'bold 11px "Space Mono", ui-monospace, monospace'
  ctx.fillText('oss · blog · talks', 66, 240)
}

/** Meta-narrativa: como se construyo este journey (decorativa). */
function drawMeta(locale: Locale): DrawFn {
  return (ctx, size) => {
    artBase(ctx, size)
    ctx.fillStyle = ART_INK
    ctx.font = 'bold 15px "Space Grotesk", system-ui, sans-serif'
    ctx.fillText(locale === 'es' ? 'ASI SE HIZO' : 'HOW IT WAS MADE', 20, 36)
    // las 8 salas en fila con la flecha del recorrido
    ctx.strokeStyle = ART_INK
    ctx.lineWidth = 3
    for (let i = 0; i < 8; i += 1) {
      const x = 24 + i * 26
      ctx.strokeRect(x, 70, 20, 20)
    }
    ctx.strokeStyle = FUT_VIOLET
    ctx.beginPath()
    ctx.moveTo(24, 104)
    ctx.lineTo(232, 104)
    ctx.stroke()
    ctx.fillStyle = FUT_VIOLET
    ctx.beginPath()
    ctx.moveTo(240, 104)
    ctx.lineTo(226, 97)
    ctx.lineTo(226, 111)
    ctx.closePath()
    ctx.fill()
    // el stack del propio journey (vibe coding demostrado)
    ctx.fillStyle = ART_INK
    ctx.font = 'bold 12px "Space Mono", ui-monospace, monospace'
    ctx.fillText('Astro + Three.js', 48, 150)
    ctx.fillText('+ Claude Code', 60, 170)
    ctx.font = 'bold 10px "Space Mono", ui-monospace, monospace'
    ctx.fillText(
      locale === 'es'
        ? 'vibe coding, commit a commit'
        : 'vibe coding, commit by commit',
      28,
      208,
    )
  }
}

/** Pizarra de roadmap: 5 nodos ascendentes de la siguiente etapa. */
function drawRoadmap(locale: Locale): DrawFn {
  const labels =
    locale === 'es'
      ? [
          'Staff/Principal',
          'IA a escala',
          'Productos propios',
          'OSS + comunidad',
          'Nuevos rubros',
        ]
      : [
          'Staff/Principal',
          'AI at scale',
          'Own products',
          'OSS + community',
          'New sectors',
        ]
  return (ctx, size) => {
    ctx.fillStyle = '#fdfcf8'
    ctx.fillRect(0, 0, size, size)
    ctx.strokeStyle = ART_INK
    ctx.globalAlpha = 0.3
    ctx.lineWidth = 4
    ctx.strokeRect(8, 8, size - 16, size - 16)
    ctx.globalAlpha = 1
    ctx.fillStyle = ART_INK
    ctx.font = 'bold 17px "Space Grotesk", system-ui, sans-serif'
    ctx.fillText('ROADMAP', 22, 40)
    ctx.font = 'bold 11px "Space Mono", ui-monospace, monospace'
    ctx.fillText(locale === 'es' ? 'lo que viene →' : "what's next →", 130, 40)
    // timeline ascendente: 5 nodos de izquierda-abajo a derecha-arriba
    const pts: readonly (readonly [number, number])[] = [
      [34, 216],
      [82, 186],
      [130, 156],
      [178, 126],
      [226, 96],
    ]
    ctx.strokeStyle = FUT_VIOLET
    ctx.lineWidth = 4
    ctx.beginPath()
    for (const [i, [x, y]] of pts.entries()) {
      if (i === 0) {
        ctx.moveTo(x, y)
      } else {
        ctx.lineTo(x, y)
      }
    }
    ctx.stroke()
    for (const [i, [x, y]] of pts.entries()) {
      ctx.fillStyle = i === pts.length - 1 ? FUT_VIOLET : '#fdfcf8'
      ctx.beginPath()
      ctx.arc(x, y, 7, 0, Math.PI * 2)
      ctx.fill()
      ctx.strokeStyle = ART_INK
      ctx.lineWidth = 2
      ctx.stroke()
      // etiqueta alternada arriba/abajo del nodo para que no se pisen
      const text = labels[i] ?? ''
      ctx.fillStyle = ART_INK
      ctx.font = 'bold 9px "Space Mono", ui-monospace, monospace'
      const tx = Math.min(x - 12, 256 - ctx.measureText(text).width - 10)
      ctx.fillText(text, Math.max(12, tx), i % 2 === 0 ? y + 24 : y - 16)
    }
    // la estrella del ultimo nodo (la vision)
    ctx.fillStyle = FUT_VIOLET
    ctx.font = 'bold 18px "Space Grotesk", system-ui, sans-serif'
    ctx.fillText('★', 234, 84)
  }
}

// --- fichas de las laminas inspeccionables ---

const ART_FICHA_MANIFIESTO = {
  title: { es: 'Hacia donde voy', en: "Where I'm heading" },
  paragraphs: {
    es: [
      'Staff / Principal Engineer sin dejar de construir: que lo que ' +
        'escribo desbloquee a mas gente, decidiendo con codigo en la ' +
        'mano.',
      'La IA deja de ser herramienta y pasa a ser producto: copilots ' +
        'de dominio, automatizaciones y AI workflows a escala de equipo ' +
        '— este journey entero se construyo asi.',
      'Productos propios: indie/SaaS a costo casi cero (como el backend ' +
        'serverless de este portfolio) y un producto para un problema ' +
        'LATAM de verdad.',
      'Multiplicar lo aprendido: mentoria y liderazgo tecnico hacia ' +
        'adentro; open source, charlas y contenido publico hacia afuera.',
      'Y el patron del recorrido sigue: cada rubro nuevo es una sala ' +
        'nueva. Siempre estudiante. Hablemos.',
    ],
    en: [
      'Staff / Principal Engineer while still building: making what I ' +
        'write unblock more people, deciding with code in hand.',
      'AI stops being a tool and becomes a product: domain copilots, ' +
        'automations and AI workflows at team scale — this whole ' +
        'journey was built that way.',
      'Products of my own: indie/SaaS at near-zero cost (like the ' +
        'serverless backend of this portfolio) and a product for a real ' +
        'LATAM problem.',
      'Multiplying what I learned: mentorship and technical leadership ' +
        'inward; open source, talks and public content outward.',
      'And the journey pattern continues: every new sector is a new ' +
        "room. Always a student. Let's talk.",
    ],
  },
} as const

const ART_FICHA_PRODUCTOS = {
  title: { es: 'Productos propios', en: 'Products of my own' },
  paragraphs: {
    es: [
      'Productos con IA: copilots de dominio, automatizaciones y ' +
        'herramientas dev — la evolucion natural del vibe coding: de ' +
        'usar agentes a construir con ellos.',
      'Indie/SaaS: micro-productos monetizados a costo ~$0, con la ' +
        'misma receta serverless de este portfolio (free tier perpetuo, ' +
        'deploy automatico).',
      'Emprendimiento LATAM: la experiencia VE · PE · CL · MX del ' +
        'recorrido apunta a problemas reales — inclusion financiera, ' +
        'pymes, educacion.',
    ],
    en: [
      'AI products: domain copilots, automations and dev tools — the ' +
        'natural evolution of vibe coding: from using agents to ' +
        'building with them.',
      'Indie/SaaS: monetized micro-products at ~$0 cost, with the same ' +
        'serverless recipe as this portfolio (perpetual free tier, ' +
        'automated deploys).',
      'LATAM entrepreneurship: the VE · PE · CL · MX experience of ' +
        'this journey points at real problems — financial inclusion, ' +
        'SMBs, education.',
    ],
  },
} as const

const ART_FICHA_COMUNIDAD = {
  title: { es: 'Comunidad y aprendizaje', en: 'Community and learning' },
  paragraphs: {
    es: [
      'Open source: mantener herramientas propias y contribuir a las ' +
        'que uso todos los dias (Astro, Vue, Django, tooling de IA).',
      'Contenido tecnico publico: blog, charlas y videos — empezando ' +
        'por documentar como se construyo este portfolio (GEO, AI-SEO, ' +
        'vibe coding) como caso de estudio.',
      'Nuevos conocimientos: datos y analytics, seguridad y compliance, ' +
        'cloud avanzado. El aula de la sala 1 nunca se cierra.',
      'Nuevos rubros: energia, salud, farma, gastronomia, food-tech y ' +
        'fintech ya tienen sala. ¿Edtech? ¿Logistica? ¿Agro? El proximo ' +
        'reto decide la proxima.',
    ],
    en: [
      'Open source: maintaining my own tools and contributing to the ' +
        'ones I use daily (Astro, Vue, Django, AI tooling).',
      'Public technical content: blog, talks and videos — starting by ' +
        'documenting how this portfolio was built (GEO, AI-SEO, vibe ' +
        'coding) as a case study.',
      'New knowledge: data and analytics, security and compliance, ' +
        'advanced cloud. The classroom of room 1 never closes.',
      'New sectors: energy, health, pharma, dining, food tech and ' +
        'fintech already have rooms. Edtech? Logistics? Agro? The next ' +
        'challenge decides the next one.',
    ],
  },
} as const

/** E enciende/apaga las laptops libres del rincon (patron canon). */
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
      id: `micro-futuro-${roomIndex}-laptop${toggle.spot}`,
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

export default function buildFuturo(ctx: RoomCtx): RoomBuild {
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
  const sink = { group, interactables, updates }

  // puerta PROXIMAMENTE grande y central en el MURO FINAL del recorrido:
  // el jugador camina +Z durante todo el journey y termina de frente a
  // "lo que viene" (la de Destacame se conserva como guiño chico —
  // decision del usuario: mantener ambas)
  const coming = new Group()
  coming.position.set(0, 0, frontZ - 0.1)
  coming.rotation.y = Math.PI
  const comingFrame = boxMesh(2.3, 2.9, 0.12, toonMat(PANEL_INK))
  comingFrame.position.set(0, 1.45, 0)
  const comingPanelMat = toonMatOwn('#181f38', {
    emissive: theme.accent,
    emissiveIntensity: 0.14,
  })
  const comingPanel = boxMesh(2.05, 2.62, 0.02, comingPanelMat)
  comingPanel.position.set(0, 1.45, 0.07)
  const comingTitle = label(locale === 'es' ? 'PROXIMAMENTE' : 'COMING SOON', {
    size: 0.22,
    color: '#aab4ff',
  })
  comingTitle.position.set(0, 1.85, 0.12)
  const comingSub = label(
    locale === 'es'
      ? 'ideas futuras · nuevos rubros · productos propios'
      : 'future ideas · new sectors · own products',
    { size: 0.09, color: '#7a85c8' },
  )
  comingSub.position.set(0, 1.45, 0.12)
  coming.add(comingFrame, comingPanel, comingTitle, comingSub)
  group.add(coming)
  updates.push((t) => {
    // la puerta "respira": lo que viene todavia se esta encendiendo
    comingPanelMat.emissiveIntensity = 0.14 + (Math.sin(t * 1.6) + 1) * 0.07
  })

  // CTA de contacto FUERTE (informe 14): el holograma sobre pedestal en
  // el eje de la sala, delante de la puerta — el objetivo de negocio
  const beacon = new Group()
  beacon.position.set(0, 0, room.z + 3.0)
  // pedestal GLB CC0 (podio) — el holograma violeta de contacto flota encima
  beacon.add(placeProp('pedestal', { x: 0, z: 0, width: 0.72 }))
  const holoMat = toonMatOwn(FUT_VIOLET, {
    emissive: '#8a9aff',
    emissiveIntensity: 0.9,
    transparent: true,
    opacity: 0.92,
  })
  const holo = new Mesh(new OctahedronGeometry(0.24, 0), holoMat)
  holo.position.y = 1.35
  holo.rotation.y = 0.6
  beacon.add(holo)
  group.add(beacon)
  staticColliders.push(footprint(0, room.z + 3.0, 0.8, 0.8))
  interactables.push({
    id: `contact-${room.index}`,
    x: 0,
    z: room.z + 3.0,
    radius: 2.2,
    label: CONTACT_LABEL,
    onActivate: () => actions.openContact(),
  })
  updates.push((t, dt) => {
    holoMat.emissiveIntensity = 0.9 + Math.sin(t * 2.4) * 0.35
    holo.rotation.y += dt * 0.8
    sfx.feed(`holo-${room.index}`, 'holo', 0, room.z + 3.0)
  })

  // rincon de escritorios ligero (decision del usuario): 3 puestos con
  // las laptops APAGADAS — los proyectos que todavia no empiezan; E las
  // enciende y muestran "lo que viene" en codigo
  const deskSpots: readonly (readonly [number, number])[] = [
    [-3.0, room.z - 2.8],
    [-1.4, room.z - 2.8],
    [-2.2, room.z - 1.2],
  ]
  const office = officeLayout({
    roomIndex: room.index,
    state,
    spots: deskSpots,
    color: PANEL_INK,
    screenTheme,
    screenFor: (index) => LAPTOP_SCREENS[index] ?? LAPTOP_SCREENS[0],
    // T4b: estaciones de trabajo sci-fi (Space Station Kit). El pack es mas
    // grande que el Kenney plano -> se afina la auto-escala.
    furniture: {
      deskUrl: SPACE_DESK,
      chairUrl: SPACE_CHAIR,
      deskWidth: 1.15,
      chairWidth: 0.58,
    },
  })
  group.add(office.group)
  staticColliders.push(...office.colliders)
  disposables.push(office)
  interactables.push(...laptopToggles(office, deskSpots, room.index))
  interactables.push(...office.seats)
  const devLabel = label(
    locale === 'es' ? 'PROXIMOS PROYECTOS' : 'NEXT PROJECTS',
    { size: 0.13, color: theme.accent },
  )
  devLabel.position.set(-2.2, 1.85, room.z - 3.0)
  group.add(devLabel)

  // cuadros + pizarra de roadmap (wallArt): el manifiesto y la
  // meta-narrativa flanquean la puerta en el muro final; productos en el
  // muro -X; comunidad recibe al que entra (muro trasero); la pizarra
  // grande del roadmap vive en el muro +X — donde las otras salas tienen
  // la grieta al pasado, esta mira adelante
  const art = wallArt({
    roomIndex: room.index,
    theme,
    locale,
    onFicha: actions.openStory,
    frames: [
      {
        key: 'manifiesto',
        position: [-3.8, 2, frontZ - 0.08],
        rotationY: Math.PI,
        draw: drawManifiesto(locale),
        ficha: ART_FICHA_MANIFIESTO,
      },
      {
        key: 'meta',
        position: [3.8, 2, frontZ - 0.08],
        rotationY: Math.PI,
        draw: drawMeta(locale),
      },
      {
        key: 'productos',
        position: [-half + 0.08, 2, room.z + 2.4],
        rotationY: Math.PI / 2,
        draw: drawProductos,
        ficha: ART_FICHA_PRODUCTOS,
      },
      {
        key: 'comunidad',
        position: [3.8, 2, backZ + 0.08],
        rotationY: 0,
        draw: drawComunidad,
        ficha: ART_FICHA_COMUNIDAD,
      },
      {
        key: 'roadmap',
        position: [half - 0.08, 1.7, room.z + 2.6],
        rotationY: -Math.PI / 2,
        size: [3.0, 1.7],
        draw: drawRoadmap(locale),
      },
    ],
  })
  staticColliders.push(...art.colliders)
  addProps(sink, art.props)

  // kit informativo estandar SIN la grieta al pasado (excepcion AC-20
  // del informe 14: el futuro no tiene un "antes")
  const texts = def.texts[locale]
  const kit = infoKit({
    room,
    year: def.year,
    theme,
    locale,
    texts,
    withLight: state.tier === 'full',
    withPortal: false,
    // el futuro estrena pizarras de cristal (el estilo nuevo)
    boardStyle: 'glass',
    onFicha: actions.openFicha,
    onEnterPast: actions.enterPast,
    onStory: actions.openStory,
  })
  staticColliders.push(...kit.colliders)
  addProps(sink, kit.props)

  // el unico NPC de la sala (excepcion AC-5 del informe 14): "Pablo del
  // futuro", de pie junto a la pizarra del roadmap, presentandola
  const coworkers = npcCoworkers({
    roomIndex: room.index,
    openDialog: actions.openDialog,
    validateMix: false,
    npcs: [
      {
        key: 'pablo',
        role: 'coworker',
        spec: {
          skin: '#d9a684',
          hair: { style: 'short', color: '#1a1410' },
          top: FUT_VIOLET_DARK,
          bottom: '#23263a',
          accessory: 'glasses',
          faceSeed: 8,
        },
        position: [half - 1.7, 0, room.z + 2.6],
        rotationY: -Math.PI / 2,
        dialog: FUTURO_PRESENTE_DIALOGS.pablo,
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
