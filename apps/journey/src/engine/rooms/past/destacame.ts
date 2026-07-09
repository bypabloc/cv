/**
 * @module rooms/past/destacame (engine)
 * @description El "antes" de Destacame al nivel del canon (informe 13):
 *   el drama de deudas previo a la plataforma, sepia + coral de mora y
 *   SIN el azul de marca (el azul llega con el presente). El rincon de
 *   los deudores — cartas de cobranza apiladas, el telefono del
 *   cobrador, el gauge de score clavado en rojo —, la ventanilla de la
 *   sucursal con su cartel de "vuelva mañana", y el escritorio del
 *   operador desbordado que arma cada campaña a mano en planillas
 *   (horas, cafe frio, reloj tarde). Intentar pagar la deuda sin
 *   sistema como objeto de busqueda lenta: la carta viaja a la
 *   ventanilla, rebota, y el veredicto flota. 3 NPCs resignados
 *   conversables (decision del usuario: los 3): Don Hernan, Marta y
 *   Nicolas.
 */
import { Group, Mesh, MeshBasicMaterial, PlaneGeometry } from 'three'
import type { Box2 } from '../../../lib/collision'
import type { Locale } from '../../../lib/rooms'
import { sfx } from '../../audio'
import { makeNpc, type NpcHandle } from '../../character'
import { npcTalk } from '../../dialog'
import { DESTACAME_PASADO_DIALOGS } from '../../dialogs/destacame-pasado'
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
import { PAST_SCREEN, PAST_STORY_LABEL, type PastSet } from './shared'

const DESTACAME_STORY: Record<Locale, { title: string; paragraphs: string[] }> =
  {
    es: {
      title: 'Antes de la plataforma (2021)',
      paragraphs: [
        'Deber plata era un tramite a oscuras: cartas de cobranza que ' +
          'asustan, llamadas que humillan y un score que nadie te ' +
          'deja ver. Para regularizar habia que ir a la sucursal, ' +
          'hacer fila y rogar — sin saber si existia un descuento, ' +
          'porque nadie lo ofrecia de frente.',
        'Adentro no era mejor: cada campaña de ofertas se armaba A ' +
          'MANO sobre planillas aisladas. Horas de un operador, cada ' +
          'vez, con errores que llegaban a clientes reales. Un solo ' +
          'pais, interfaces heredadas, y servicios que no se hablaban ' +
          'entre si.',
        'Destacame ataco ese drama con una plataforma: el score ' +
          'gratis y claro, la deuda negociable con hasta 95% de ' +
          'descuento, el pago 100% online con la banca. Pablo ' +
          'construyo sus interfaces Vue/Nuxt, se volvio full stack ' +
          'con Python/Django, y termino de arquitecto orquestandola ' +
          'para Chile y Mexico. Cruza de vuelta y la ves funcionando.',
      ],
    },
    en: {
      title: 'Before the platform (2021)',
      paragraphs: [
        'Owing money was a procedure in the dark: scary collection ' +
          'letters, humiliating calls and a score nobody let you ' +
          'see. To regularise you had to go to the branch, queue and ' +
          'beg — never knowing if a discount existed, because nobody ' +
          'offered it up front.',
        'Inside it was no better: every offer campaign was built BY ' +
          'HAND over siloed spreadsheets. Hours of an operator’s ' +
          'day, every time, with errors reaching real customers. One ' +
          'country, legacy interfaces, and services that did not ' +
          'talk to each other.',
        'Destacame attacked that drama with a platform: the score ' +
          'free and clear, debt negotiable at up to 95% off, payment ' +
          '100% online with the banks. Pablo built its Vue/Nuxt ' +
          'interfaces, went full stack with Python/Django, and ended ' +
          'up as the architect orchestrating it for Chile and ' +
          'Mexico. Cross back and you can see it running.',
      ],
    },
  }

const TRY_LABEL = {
  es: 'Intentar pagar la deuda',
  en: 'Try to pay the debt',
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

/** El gauge del score clavado en la zona roja (sepia + coral). */
function drawGaugeMora(ctx: CanvasRenderingContext2D, size: number): void {
  ctx.fillStyle = '#3a3126'
  ctx.fillRect(0, 0, size, size)
  ctx.strokeStyle = '#6a5f4e'
  ctx.lineWidth = 4
  ctx.strokeRect(6, 6, size - 12, size - 12)
  const c = size / 2
  const cy = size * 0.62
  // el arco: solo el tramo coral tiene color; el resto es sepia
  ctx.lineWidth = 12
  ctx.strokeStyle = '#c05a4a'
  ctx.beginPath()
  ctx.arc(c, cy, 74, Math.PI, Math.PI * 1.36)
  ctx.stroke()
  ctx.strokeStyle = '#6a5f4e'
  ctx.beginPath()
  ctx.arc(c, cy, 74, Math.PI * 1.36, Math.PI * 2)
  ctx.stroke()
  // la aguja clavada en el coral
  ctx.strokeStyle = '#e8d8b0'
  ctx.lineWidth = 5
  ctx.beginPath()
  ctx.moveTo(c, cy)
  const angle = Math.PI * 1.14
  ctx.lineTo(c + Math.cos(angle) * 60, cy + Math.sin(angle) * 60)
  ctx.stroke()
  ctx.fillStyle = '#e8d8b0'
  ctx.font = 'bold 26px "Space Mono", ui-monospace, monospace'
  ctx.fillText('487', c - 24, cy + 40)
  ctx.font = 'bold 12px "Space Mono", ui-monospace, monospace'
  ctx.fillStyle = '#c05a4a'
  ctx.fillText('MOROSO', c - 26, cy + 60)
}

/** El "antes" de Destacame: deudas sin gestionar y campañas a mano. */
export function destacamePast(
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

  // el rincon de los deudores: la mesita con las cartas de cobranza
  // apiladas y el telefono que no deja de sonar (el cobrador)
  group.add(
    desk({
      position: [x - 3.0, 0, z - 0.3],
      rotationY: Math.PI / 2,
      width: 1.4,
      color: '#4c4740',
    }),
    paperStack({ position: [x - 3.0, 0.76, z - 0.7] }),
    paperStack({ position: [x - 2.95, 0.76, z + 0.1], count: 12 }),
    // el telefono de disco: base + auricular
    mergedBoxes(
      [
        { w: 0.24, h: 0.1, d: 0.3, x: x - 3.1, y: 0.81, z: z - 1.15 },
        { w: 0.3, h: 0.07, d: 0.1, x: x - 3.1, y: 0.92, z: z - 1.15 },
      ],
      toonMat('#3a352c'),
    ),
  )
  colliders.push(footprint(x - 3.0, z - 0.3, 1.0, 2.2))
  const cartasSign = label(
    locale === 'es' ? 'cartas de cobranza' : 'collection letters',
    { size: 0.1, color: '#e8d8b0' },
  )
  cartasSign.position.set(x - 3.0, 1.5, z - 0.3)
  cartasSign.rotation.y = Math.PI / 2
  group.add(cartasSign)

  // el gauge del score clavado en rojo, colgado en el muro del fondo
  const mora = new Mesh(
    new PlaneGeometry(1.3, 1.3),
    new MeshBasicMaterial({ map: makeCanvasTexture(256, drawGaugeMora) }),
  )
  mora.position.set(x - 2.2, 2.1, z - depth / 2 + 0.1)
  mora.userData.noOutline = true
  group.add(mora)

  // la ventanilla de la sucursal: el UNICO lugar donde negociar — con
  // barrotes, cartel de horario y el "vuelva mañana" listo
  group.add(
    outlinedMergedBoxes(
      [
        { w: 1.6, h: 1.0, d: 0.5, x: x + 0.7, y: 0.5, z: z - 1.6 },
        { w: 1.6, h: 0.14, d: 0.5, x: x + 0.7, y: 1.9, z: z - 1.6 },
        { w: 0.06, h: 0.8, d: 0.06, x: x + 0.15, y: 1.4, z: z - 1.6 },
        { w: 0.06, h: 0.8, d: 0.06, x: x + 0.45, y: 1.4, z: z - 1.6 },
        { w: 0.06, h: 0.8, d: 0.06, x: x + 0.75, y: 1.4, z: z - 1.6 },
        { w: 0.06, h: 0.8, d: 0.06, x: x + 1.05, y: 1.4, z: z - 1.6 },
        { w: 0.06, h: 0.8, d: 0.06, x: x + 1.35, y: 1.4, z: z - 1.6 },
      ],
      toonMat('#5a5244'),
      { castShadow: true },
    ),
  )
  colliders.push(footprint(x + 0.7, z - 1.6, 1.8, 0.7))
  const ventanillaSign = label(
    locale === 'es' ? 'SUCURSAL · atencion 9-14' : 'BRANCH · open 9-14',
    { size: 0.11, color: '#e8d8b0' },
  )
  ventanillaSign.position.set(x + 0.7, 2.2, z - 1.6)
  group.add(ventanillaSign)

  // el escritorio del operador desbordado: planillas por todos lados,
  // la calculadora y el cafe que se enfrio hace dos horas
  group.add(
    desk({
      position: [x + 2.6, 0, z + 0.9],
      color: '#4c4740',
      width: 1.5,
    }),
    paperStack({ position: [x + 2.1, 0.76, z + 0.75], count: 14 }),
    paperStack({ position: [x + 3.1, 0.76, z + 0.8], count: 10 }),
    mergedBoxes(
      [
        // la calculadora y el cafe frio
        { w: 0.16, h: 0.05, d: 0.24, x: x + 2.6, y: 0.78, z: z + 0.6 },
        { w: 0.12, h: 0.14, d: 0.12, x: x + 2.85, y: 0.83, z: z + 1.1 },
      ],
      toonMat('#3a352c'),
    ),
  )
  colliders.push(footprint(x + 2.6, z + 0.9, 1.6, 0.9))
  const planillasSign = label(
    locale === 'es' ? 'campaña de hoy: fila 8.413' : "today's batch: row 8,413",
    { size: 0.1, color: '#e8d8b0' },
  )
  planillasSign.position.set(x + 2.6, 1.5, z + 0.9)
  group.add(planillasSign)

  // el reloj que cobra las horas del proceso manual
  const clock = new Group()
  clock.position.set(x + 1.6, 2.5, z - depth / 2 + 0.1)
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
    // la aguja da una vuelta cada ~12 s: las horas que nadie devuelve
    hand.rotation.z = -t * 0.52
  })

  // micro: intentar pagar la deuda — la carta viaja a la ventanilla,
  // rebota con el "vuelva mañana" y el veredicto flota unos segundos
  const carta = boxMesh(0.3, 0.02, 0.42, toonMat('#e8e2d0'))
  carta.position.set(x - 3.0, 0.92, z - 0.7)
  group.add(carta)
  const verdict = label(
    locale === 'es'
      ? 'sin descuento · "vuelva mañana"'
      : 'no discount · "come back tomorrow"',
    { size: 0.12, color: '#e8d8b0' },
  )
  verdict.position.set(x - 0.6, 1.9, z - 0.9)
  verdict.visible = false
  group.add(verdict)
  const cartaFrom = [x - 3.0, 0.92, z - 0.7] as const
  const cartaTo = [x + 0.7, 1.15, z - 1.35] as const
  let tryT = -1
  interactables.push({
    id: 'past-search',
    x: x - 3.0,
    z: z - 0.7,
    radius: 2.2,
    label: TRY_LABEL,
    onActivate: () => {
      if (tryT === -1) {
        tryT = -2 // pendiente: el proximo update fija el inicio
        sfx.play('blip')
      }
    },
  })
  updates.push((t) => {
    if (tryT === -2) {
      tryT = t
    }
    if (tryT < 0) {
      return
    }
    const elapsed = t - tryT
    if (elapsed < 1.5) {
      // la carta vuela esperanzada hacia la ventanilla...
      const k = elapsed / 1.5
      carta.position.set(
        cartaFrom[0] + (cartaTo[0] - cartaFrom[0]) * k,
        cartaFrom[1] +
          (cartaTo[1] - cartaFrom[1]) * k +
          Math.sin(k * Math.PI) * 0.5,
        cartaFrom[2] + (cartaTo[2] - cartaFrom[2]) * k,
      )
      carta.rotation.y = k * 3
    } else if (elapsed < 2.4) {
      // ...y la ventanilla la devuelve sin respuesta
      const k = (elapsed - 1.5) / 0.9
      carta.position.set(
        cartaTo[0] - (cartaTo[0] - cartaFrom[0]) * k * 0.5,
        cartaTo[1] + Math.sin(k * Math.PI) * 0.3,
        cartaTo[2] - (cartaTo[2] - cartaFrom[2]) * k * 0.5,
      )
    } else if (elapsed < 5.8) {
      verdict.visible = true
    } else {
      verdict.visible = false
      carta.position.set(cartaFrom[0], cartaFrom[1], cartaFrom[2])
      carta.rotation.y = 0
      tryT = -1
    }
  })

  // Don Hernan (antes) entre su mesita y la ventanilla, sin saber por
  // cual de las tres deudas empezar
  const hernan = makeNpc({
    skin: '#c98f6a',
    hair: { style: 'short', color: '#d8d2c4' },
    top: '#6a6152',
    bottom: '#4a4438',
    model: 'adam',
    faceSeed: 37,
    position: [x - 1.6, 0, z + 0.7],
    path: [
      [x - 1.6, z + 0.7],
      [x - 0.2, z - 0.6],
      [x - 2.2, z + 1.3],
    ],
    speed: 0.55,
  })
  // Marta (antes) cabizbaja frente a la mesita de las cartas
  const marta = makeNpc({
    skin: '#d9a684',
    hair: { style: 'bun', color: '#2a1a12' },
    top: '#7a6a58',
    bottom: '#4a4438',
    model: 'suzie',
    faceSeed: 54,
    position: [x - 2.2, 0, z - 0.3],
    rotationY: -Math.PI / 2,
  })
  // Nicolas (antes) clavado en su escritorio de planillas
  const nicolas = makeNpc({
    skin: '#b5825f',
    hair: { style: 'spiky', color: '#1a140e' },
    top: '#8a8270',
    bottom: '#5a5548',
    accessory: 'glasses',
    model: 'roth',
    faceSeed: 76,
    position: [x + 2.6, 0, z + 1.7],
    rotationY: Math.PI,
  })
  npcs.push(hernan, marta, nicolas)
  const talks = [
    npcTalk({
      id: 'talk-past-destacame-hernan',
      npc: hernan,
      dialog: DESTACAME_PASADO_DIALOGS.hernan,
      openDialog: actions.openDialog,
    }),
    npcTalk({
      id: 'talk-past-destacame-marta',
      npc: marta,
      dialog: DESTACAME_PASADO_DIALOGS.marta,
      openDialog: actions.openDialog,
    }),
    npcTalk({
      id: 'talk-past-destacame-nicolas',
      npc: nicolas,
      dialog: DESTACAME_PASADO_DIALOGS.nicolas,
      openDialog: actions.openDialog,
    }),
  ]
  for (const talk of talks) {
    interactables.push(talk.interactable)
    updates.push(talk.update)
  }

  const story = DESTACAME_STORY[locale]
  const panel = screenPanel({
    title: locale === 'es' ? 'deber plata a oscuras' : 'owing in the dark',
    lines:
      locale === 'es'
        ? [
            'el score: invisible',
            'el descuento: secreto',
            'pagar: fila en sucursal',
            'la campaña: horas a mano',
            '',
            '[E] leer la historia',
          ]
        : [
            'the score: invisible',
            'the discount: secret',
            'paying: branch queues',
            'campaigns: hours by hand',
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
