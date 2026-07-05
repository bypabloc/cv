/**
 * @module rooms/past/dibal (engine)
 * @description El "antes" de Dibal al nivel del canon (informe 11): el
 *   restaurante manual de 2018, sepia y a los gritos. Papelitos de
 *   comanda por todos lados — pinchados en el clavo del pase, tirados
 *   por el piso y UNO perdido a mitad de camino entre el salon y la
 *   cocina —, la cocina descifrando letras con dos platos equivocados
 *   en el pase, la caja con talonario de papel carbon, calculadora
 *   vieja y un cajon que no cuadra (falta S/40), y el reloj de pared
 *   cobrando el cierre a medianoche. Seguir el papelito perdido como
 *   objeto de busqueda lenta. 3 NPCs frustrados conversables (nombres
 *   distintos: "el equipo de antes"): Julio corriendo y gritando
 *   pedidos, Doña Carmen adivinando caligrafias y Elena llenando
 *   boletas a mano con el susto de SUNAT encima.
 */
import { Group, Mesh, MeshBasicMaterial, PlaneGeometry } from 'three'
import type { Box2 } from '../../../lib/collision'
import type { Locale } from '../../../lib/rooms'
import { sfx } from '../../audio'
import { makeNpc, type NpcHandle } from '../../character'
import { npcTalk } from '../../dialog'
import { DIBAL_PASADO_DIALOGS } from '../../dialogs/dibal-pasado'
import type { Interactable } from '../../state'
import {
  boxMesh,
  label,
  makeCanvasTexture,
  mergedBoxes,
  outlinedMergedBoxes,
  screenPanel,
  toonMat,
} from '../../toon'
import type { PastCtx } from '../../world'
import { desk, footprint, paperStack } from '../props'
import {
  carryPapers,
  PAST_SCREEN,
  PAST_STORY_LABEL,
  type PastSet,
} from './shared'

const DIBAL_STORY: Record<Locale, { title: string; paragraphs: string[] }> = {
  es: {
    title: 'Antes del sistema (2018)',
    paragraphs: [
      'El restaurante funcionaba a papel y pulmon: el mozo anotaba la ' +
        'comanda en una libreta, corria a la cocina, pinchaba el ' +
        'papelito en un clavo y GRITABA el pedido por encima de las ' +
        'ollas. Los papelitos se manchaban, se volaban... y el de la ' +
        'mesa 6 se perdia siempre en el camino.',
      'La cocina adivinaba caligrafias — ¿dos ceviches o dos ' +
        'cevichitos? — y los platos salian mal. En la caja, cada ' +
        'boleta se llenaba A MANO con papel carbon, el IGV se ' +
        'calculaba a calculadora y el cuadre estiraba el cierre hasta ' +
        'la medianoche, con el susto de una multa de SUNAT siempre ' +
        'encima.',
      'Ese año Dibal contrato a su PRIMER desarrollador: un muchacho ' +
        'que pregunto, miro el caos de papelitos y propuso un sistema ' +
        'web donde la comanda viajara sola del salon a la cocina y la ' +
        'boleta se enviara sola al fisco. Cruza de vuelta y lo ves ' +
        'funcionando.',
    ],
  },
  en: {
    title: 'Before the system (2018)',
    paragraphs: [
      'The restaurant ran on paper and lungs: the waiter wrote the ' +
        'order in a notepad, ran to the kitchen, pinned the slip on a ' +
        'nail and SHOUTED the order over the pots. Slips got stained, ' +
        'blew away... and table 6’s always got lost on the way.',
      'The kitchen guessed at handwriting — two ceviches or two small ' +
        'ones? — and dishes went out wrong. At the till, every receipt ' +
        'was filled BY HAND with carbon paper, the tax was worked out ' +
        'on a calculator and balancing stretched closing time to ' +
        'midnight, with the fear of a SUNAT fine always looming.',
      'That year Dibal hired its FIRST developer: a kid who asked ' +
        'questions, looked at the paper chaos and proposed a web ' +
        'system where the order would travel on its own from floor to ' +
        'kitchen and the receipt would file itself with the taxman. ' +
        'Cross back and you can see it running.',
    ],
  },
}

const FOLLOW_LABEL = {
  es: 'Seguir el papelito perdido',
  en: 'Follow the lost order slip',
} as const

/** Cara del reloj de pared: esfera sepia con marcas horarias. */
function drawClockFace(ctx: CanvasRenderingContext2D, size: number): void {
  const c = size / 2
  ctx.fillStyle = '#e8d8b0'
  ctx.beginPath()
  ctx.arc(c, c, c - 8, 0, Math.PI * 2)
  ctx.fill()
  ctx.strokeStyle = '#201a10'
  ctx.lineWidth = 6
  ctx.stroke()
  for (let i = 0; i < 12; i += 1) {
    const angle = (i / 12) * Math.PI * 2
    const r0 = c - 16
    const r1 = i % 3 === 0 ? c - 34 : c - 24
    ctx.beginPath()
    ctx.moveTo(c + Math.cos(angle) * r0, c + Math.sin(angle) * r0)
    ctx.lineTo(c + Math.cos(angle) * r1, c + Math.sin(angle) * r1)
    ctx.lineWidth = i % 3 === 0 ? 5 : 3
    ctx.stroke()
  }
}

/** El "antes" de Dibal: el restaurante manual de papelitos y gritos. */
export function dibalPast(
  x: number,
  z: number,
  depth: number,
  locale: Locale,
  actions: PastCtx['actions'],
): PastSet {
  const group = new Group()
  const colliders: Box2[] = []
  const npcs: NpcHandle[] = []
  const interactables: Interactable[] = []
  const updates: ((t: number, dt: number) => void)[] = []

  // cocina contra el muro izquierdo: mesada sepia con ollas frias y el
  // pase con DOS platos equivocados esperando a nadie
  group.add(
    outlinedMergedBoxes(
      [
        { w: 1.0, h: 0.9, d: 2.4, x: x - 3.3, y: 0.45, z: z - 0.6 },
        { w: 0.9, h: 0.5, d: 1.4, x: x - 3.3, y: 2.3, z: z - 0.7 },
        // el pase: mesa angosta hacia el salon
        { w: 0.7, h: 0.86, d: 1.6, x: x - 2.4, y: 0.43, z: z - 0.6 },
      ],
      toonMat('#6a5f4e'),
      { castShadow: true },
    ),
    mergedBoxes(
      [
        { w: 0.36, h: 0.22, d: 0.36, x: x - 3.3, y: 1.0, z: z - 1.2 },
        { w: 0.3, h: 0.18, d: 0.3, x: x - 3.3, y: 0.98, z: z - 0.2 },
        // los dos platos equivocados en el pase
        { w: 0.24, h: 0.04, d: 0.24, x: x - 2.4, y: 0.88, z: z - 1.0 },
        { w: 0.24, h: 0.04, d: 0.24, x: x - 2.4, y: 0.88, z: z - 0.3 },
        { w: 0.14, h: 0.07, d: 0.14, x: x - 2.4, y: 0.92, z: z - 1.0 },
        { w: 0.14, h: 0.07, d: 0.14, x: x - 2.4, y: 0.92, z: z - 0.3 },
      ],
      toonMat('#4c4740'),
    ),
  )
  colliders.push(
    footprint(x - 3.3, z - 0.6, 1.2, 2.6),
    footprint(x - 2.4, z - 0.6, 0.9, 1.8),
  )
  const wrongSign = label(
    locale === 'es' ? '¿esto quien lo pidio?' : 'who ordered this?',
    { size: 0.11, color: '#e8d8b0' },
  )
  wrongSign.position.set(x - 2.4, 1.5, z - 0.65)
  group.add(wrongSign)

  // el clavo del pase: la tabla con papelitos pinchados (el "sistema")
  group.add(
    outlinedMergedBoxes(
      [{ w: 0.7, h: 0.5, d: 0.05, x: x - 2.85, y: 1.6, z: z - 0.6 }],
      toonMat('#5a5044'),
      { castShadow: true },
    ),
    mergedBoxes(
      Array.from({ length: 6 }, (_, i) => ({
        w: 0.14,
        h: 0.18,
        d: 0.015,
        x: x - 2.85 + ((i % 3) - 1) * 0.2,
        y: 1.6 + (i < 3 ? 0.1 : -0.12),
        z: z - 0.62,
        rotY: Math.sin(i * 3.1) * 0.12,
      })),
      toonMat('#b09a6e'),
    ),
  )
  const clavoSign = label(
    locale === 'es'
      ? '¿dos ceviches o dos cevichitos?'
      : 'two ceviches or two small ones?',
    { size: 0.1, color: '#e8d8b0' },
  )
  clavoSign.position.set(x - 2.85, 2.1, z - 0.6)
  group.add(clavoSign)

  // mesas del salon sepia con papelitos encima (los pedidos que fueron)
  const mesas: readonly (readonly [number, number])[] = [
    [x + 0.6, z + 1.6],
    [x + 2.6, z + 0.9],
  ]
  group.add(
    outlinedMergedBoxes(
      mesas.flatMap(([mx, mz]) => [
        { w: 0.95, h: 0.06, d: 0.95, x: mx, y: 0.74, z: mz },
        { w: 0.14, h: 0.74, d: 0.14, x: mx, y: 0.37, z: mz },
        { w: 0.42, h: 0.05, d: 0.42, x: mx, y: 0.44, z: mz - 0.6 },
        { w: 0.42, h: 0.5, d: 0.05, x: mx, y: 0.72, z: mz - 0.8 },
      ]),
      toonMat('#6a5f4e'),
      { castShadow: true },
    ),
    mergedBoxes(
      mesas.map(([mx, mz]) => ({
        w: 0.16,
        h: 0.015,
        d: 0.2,
        x: mx + 0.18,
        y: 0.78,
        z: mz - 0.1,
        rotY: 0.4,
      })),
      toonMat('#b09a6e'),
    ),
  )
  for (const [mx, mz] of mesas) {
    colliders.push(footprint(mx, mz, 1.15, 1.15))
  }

  // caja del talonario: boletas a mano, papel carbon, calculadora
  // vieja y el post-it del cajon descuadrado
  const caja = desk({
    position: [x + 1.6, 0, z - 1.2],
    color: '#4c4740',
    width: 1.5,
  })
  group.add(caja)
  colliders.push(footprint(x + 1.6, z - 1.2, 1.6, 0.8))
  group.add(
    paperStack({ position: [x + 1.15, 0.745, z - 1.2], count: 10 }),
    paperStack({ position: [x + 2.2, 0, z - 0.75], count: 12 }),
    mergedBoxes(
      [
        // talonario abierto + papel carbon asomando
        { w: 0.24, h: 0.03, d: 0.3, x: x + 1.7, y: 0.76, z: z - 1.3 },
        { w: 0.22, h: 0.008, d: 0.26, x: x + 1.74, y: 0.78, z: z - 1.26 },
        // calculadora vieja: cuerpo + visor
        { w: 0.16, h: 0.05, d: 0.22, x: x + 2.1, y: 0.77, z: z - 1.1 },
        { w: 0.12, h: 0.02, d: 0.06, x: x + 2.1, y: 0.8, z: z - 1.18 },
        // el cajon de dinero entreabierto
        { w: 0.4, h: 0.12, d: 0.3, x: x + 1.35, y: 0.66, z: z - 0.92 },
      ],
      toonMat('#3a352c'),
    ),
  )
  const faltaSign = label(
    locale === 'es' ? 'falta S/40 (?)' : 'S/40 missing (?)',
    { size: 0.12, color: '#e8d8b0' },
  )
  faltaSign.position.set(x + 1.6, 1.3, z - 1.2)
  group.add(faltaSign)

  // papelitos traspapelados por el piso: comandas que nunca llegaron
  group.add(
    mergedBoxes(
      [
        { w: 0.14, h: 0.012, d: 0.18, x: x - 0.4, y: 0.006, z: z + 0.9 },
        {
          w: 0.14,
          h: 0.012,
          d: 0.18,
          x: x - 1.5,
          y: 0.006,
          z: z + 0.2,
          rotY: 0.7,
        },
        {
          w: 0.14,
          h: 0.012,
          d: 0.18,
          x: x + 1.9,
          y: 0.006,
          z: z + 1.9,
          rotY: -0.4,
        },
        {
          w: 0.14,
          h: 0.012,
          d: 0.18,
          x: x - 2.0,
          y: 0.006,
          z: z + 1.4,
          rotY: 1.1,
        },
        { w: 0.14, h: 0.012, d: 0.18, x: x + 0.2, y: 0.006, z: z - 1.6 },
      ],
      toonMat('#b09a6e'),
    ),
  )

  // uno mas VUELA en circulos: el papelito que nadie alcanza
  const volando = boxMesh(0.14, 0.012, 0.18, toonMat('#c8b58a'))
  volando.userData.noOutline = true
  group.add(volando)
  updates.push((t) => {
    volando.position.set(
      x + Math.cos(t * 0.7) * 1.6,
      1.1 + Math.sin(t * 1.9) * 0.25,
      z + 0.6 + Math.sin(t * 0.7) * 1.2,
    )
    volando.rotation.set(t * 1.3, t * 0.8, 0)
  })

  // reloj de pared que cobra los minutos: el cierre a medianoche
  const clock = new Group()
  clock.position.set(x, 2.5, z - depth / 2 + 0.1)
  const faceMesh = new Mesh(
    new PlaneGeometry(0.72, 0.72),
    new MeshBasicMaterial({ map: makeCanvasTexture(128, drawClockFace) }),
  )
  faceMesh.userData.noOutline = true
  const hand = boxMesh(0.04, 0.26, 0.02, toonMat('#201a10'))
  hand.position.z = 0.02
  hand.userData.noOutline = true
  clock.add(faceMesh, hand)
  group.add(clock)
  updates.push((t) => {
    // la aguja da una vuelta cada ~12 s: el cierre que no llega
    hand.rotation.z = -t * 0.52
  })

  // micro: seguir el papelito perdido — sale de la mesa 6 hacia la
  // cocina, cae a mitad de camino y el veredicto flota unos segundos
  const perdido = boxMesh(0.16, 0.014, 0.2, toonMat('#e0d0a0'))
  perdido.position.set(x + 0.6, 0.78, z + 1.5)
  group.add(perdido)
  const verdict = label(
    locale === 'es'
      ? 'la comanda de la mesa 6 nunca llego a cocina'
      : 'table 6’s order never reached the kitchen',
    { size: 0.12, color: '#e8d8b0' },
  )
  verdict.position.set(x - 0.9, 1.9, z + 0.5)
  verdict.visible = false
  group.add(verdict)
  let followT = -1
  interactables.push({
    id: 'past-search',
    x: x + 0.6,
    z: z + 1.6,
    radius: 2.2,
    label: FOLLOW_LABEL,
    onActivate: () => {
      if (followT === -1) {
        followT = -2 // pendiente: el proximo update fija el inicio
        sfx.play('blip')
      }
    },
  })
  updates.push((t) => {
    if (followT === -2) {
      followT = t
    }
    if (followT < 0) {
      return
    }
    const elapsed = t - followT
    if (elapsed < 1.4) {
      // vuela de la mesa hacia la cocina...
      const k = elapsed / 1.4
      perdido.position.set(
        x + 0.6 + (x - 0.9 - (x + 0.6)) * k,
        0.78 + Math.sin(k * Math.PI) * 0.7,
        z + 1.5 + (z + 0.3 - (z + 1.5)) * k,
      )
      perdido.rotation.y = k * 5
    } else if (elapsed < 2.2) {
      // ...y cae a mitad de camino, donde nadie lo ve
      const k = (elapsed - 1.4) / 0.8
      perdido.position.set(x - 0.9, 0.78 * (1 - k) + 0.01, z + 0.3)
    } else if (elapsed < 5.8) {
      verdict.visible = true
    } else {
      verdict.visible = false
      perdido.position.set(x + 0.6, 0.78, z + 1.5)
      perdido.rotation.y = 0
      followT = -1
    }
  })

  // Julio (antes) corriendo entre el salon y la cocina con la libreta
  // y los papelitos — el pregonero del restaurante
  const julio = makeNpc({
    skin: '#b5825f',
    hair: { style: 'short', color: '#1a140e' },
    top: '#8a8270',
    bottom: '#5a5548',
    faceSeed: 24,
    position: [x + 0.6, 0, z + 2.4],
    path: [
      [x + 0.6, z + 2.4],
      [x - 1.7, z + 0.5],
      [x + 2.3, z - 0.1],
    ],
    speed: 0.85,
  })
  carryPapers(julio)
  // Doña Carmen (antes) frente al clavo del pase, descifrando letras
  const carmen = makeNpc({
    skin: '#8a5a3c',
    hair: { style: 'bun', color: '#d8d2c4' },
    top: '#8a8270',
    bottom: '#6a6152',
    faceSeed: 47,
    position: [x - 1.8, 0, z - 0.6],
    rotationY: -Math.PI / 2,
  })
  // Elena (antes) sentada en la caja, talonario y calculadora
  const elena = makeNpc({
    skin: '#d9a684',
    hair: { style: 'ponytail', color: '#2a1a12' },
    top: '#7a6a58',
    bottom: '#4a4438',
    accessory: 'badge',
    faceSeed: 92,
    position: [x + 1.6, 0, z - 1.75],
    rotationY: 0,
    pose: 'sit',
  })
  npcs.push(julio, carmen, elena)
  const talks = [
    npcTalk({
      id: 'talk-past-dibal-julio',
      npc: julio,
      dialog: DIBAL_PASADO_DIALOGS.julio,
      openDialog: actions.openDialog,
    }),
    npcTalk({
      id: 'talk-past-dibal-carmen',
      npc: carmen,
      dialog: DIBAL_PASADO_DIALOGS.carmen,
      openDialog: actions.openDialog,
    }),
    npcTalk({
      id: 'talk-past-dibal-elena',
      npc: elena,
      dialog: DIBAL_PASADO_DIALOGS.elena,
      openDialog: actions.openDialog,
    }),
  ]
  for (const talk of talks) {
    interactables.push(talk.interactable)
    updates.push(talk.update)
  }

  const story = DIBAL_STORY[locale]
  const panel = screenPanel({
    title: locale === 'es' ? 'comandas en papelitos' : 'orders on paper slips',
    lines:
      locale === 'es'
        ? [
            'pedido: libreta y grito',
            'cocina: adivinar letras',
            'boleta: a mano, carbon',
            'cierre: medianoche',
            '',
            '[E] leer la historia',
          ]
        : [
            'order: notepad and shout',
            'kitchen: guess handwriting',
            'receipt: by hand, carbon',
            'closing: midnight',
            '',
            '[E] read the story',
          ],
    theme: PAST_SCREEN,
    width: 1.8,
    height: 1.25,
  })
  panel.position.set(x, 1.6, z - depth / 2 + 0.12)
  group.add(panel)
  interactables.push({
    id: 'past-story',
    x,
    z: z - depth / 2 + 0.5,
    radius: 2.4,
    label: PAST_STORY_LABEL,
    onActivate: () => actions.openStory(story.title, story.paragraphs),
  })
  return { group, colliders, npcs, interactables, updates }
}
