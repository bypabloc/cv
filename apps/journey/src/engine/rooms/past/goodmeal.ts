/**
 * @module rooms/past/goodmeal (engine)
 * @description El "antes" de GoodMeal al nivel del canon (informe 12):
 *   el cierre del local en 2021, sepia y de noche. La vitrina a medio
 *   vaciar con la comida PERFECTA del dia, el carro de desechos, el
 *   tacho grande rebosante, las bolsas negras apiladas junto a la
 *   puerta trasera y el reloj cobrando el cierre. Ningun cliente,
 *   ningun smartphone, ninguna Good Bag: el excedente va derecho a la
 *   basura. Ver la comida irse al tacho como objeto de busqueda lenta.
 *   3 NPCs resignados conversables (decision del usuario: los 3):
 *   Rodrigo cargando bolsas, Ignacia vaciando la vitrina que atendio
 *   todo el dia y el Sr. Peña sacando la cuenta de la merma.
 */
import { Group, Mesh, MeshBasicMaterial, PlaneGeometry } from 'three'
import type { Box2 } from '../../../lib/collision'
import type { Locale } from '../../../lib/rooms'
import { sfx } from '../../audio'
import { makeNpc, type NpcHandle } from '../../character'
import { npcTalk } from '../../dialog'
import { GOODMEAL_PASADO_DIALOGS } from '../../dialogs/goodmeal-pasado'
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
import { desk, footprint } from '../props'
import { PAST_SCREEN, PAST_STORY_LABEL, type PastSet } from './shared'

const GOODMEAL_STORY: Record<Locale, { title: string; paragraphs: string[] }> =
  {
    es: {
      title: 'Antes de la app (2021)',
      paragraphs: [
        'Cada noche el local cerraba con la vitrina todavia llena: ' +
          'pan, donas y pizza en perfecto estado. A las diez ya no ' +
          'habia a quien venderselos, regalarlos era imposible a esa ' +
          'hora... y la regla del "todo fresco mañana" mandaba: bolsa ' +
          'negra, puerta trasera, camion de la basura.',
        'El dueño sacaba la misma cuenta cada noche: producto pagado ' +
          'dos veces — materia prima y horas de horno — que no ' +
          'devolvia un peso, y encima habia que pagar por botarlo. ' +
          'Casi un quinto de lo producido moria asi, mientras a unas ' +
          'cuadras alguien se lo habria comido feliz.',
        'En 2021 una app chilena ataco exactamente este momento: ' +
          'publicar el excedente como bolsas sorpresa rebajadas y ' +
          'venderlo ANTES del cierre. Pablo trabajo en esa app — ' +
          'GoodMeal — modernizando su frontend con Vue 3 y reforzando ' +
          'su flujo de pagos. Cruza de vuelta y la ves funcionando.',
      ],
    },
    en: {
      title: 'Before the app (2021)',
      paragraphs: [
        'Every night the venue closed with the display case still ' +
          'full: bread, donuts and pizza in perfect shape. By ten ' +
          'there was nobody left to sell them to, giving them away ' +
          'was impossible at that hour... and the "all fresh ' +
          'tomorrow" rule dictated: black bag, back door, garbage ' +
          'truck.',
        'The owner ran the same numbers every night: product paid ' +
          'for twice — raw material and oven hours — returning not a ' +
          'peso, plus a fee to haul it away. Nearly a fifth of the ' +
          'production died like this, while a few blocks away ' +
          'someone would have eaten it happily.',
        'In 2021 a Chilean app attacked exactly this moment: list ' +
          'the surplus as discounted surprise bags and sell it ' +
          'BEFORE closing. Pablo worked on that app — GoodMeal — ' +
          'modernising its frontend with Vue 3 and hardening its ' +
          'payment flow. Cross back and you can see it running.',
      ],
    },
  }

const WATCH_LABEL = {
  es: 'Ver la comida irse al tacho',
  en: 'Watch the food go to the bin',
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

/** El "antes" de GoodMeal: el cierre botando la comida perfecta. */
export function goodmealPast(
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

  // vitrina a medio vaciar contra el muro izquierdo: la comida del
  // dia — perfecta — esperando la bolsa negra
  group.add(
    outlinedMergedBoxes(
      [
        { w: 1.0, h: 0.9, d: 2.2, x: x - 3.2, y: 0.45, z: z - 0.6 },
        { w: 0.9, h: 0.4, d: 2.0, x: x - 3.2, y: 1.1, z: z - 0.6 },
      ],
      toonMat('#6a5f4e'),
      { castShadow: true },
    ),
    // bandejas con lo que queda (sepia): pan, donas, media pizza
    mergedBoxes(
      [
        { w: 0.6, h: 0.05, d: 0.5, x: x - 3.2, y: 0.94, z: z - 1.3 },
        { w: 0.6, h: 0.05, d: 0.5, x: x - 3.2, y: 0.94, z: z - 0.1 },
        { w: 0.18, h: 0.09, d: 0.14, x: x - 3.3, y: 1.0, z: z - 1.35 },
        { w: 0.16, h: 0.07, d: 0.16, x: x - 3.05, y: 0.99, z: z - 1.2 },
        { w: 0.18, h: 0.06, d: 0.16, x: x - 3.25, y: 0.99, z: z - 0.05 },
      ],
      toonMat('#b09a6e'),
    ),
  )
  colliders.push(footprint(x - 3.2, z - 0.6, 1.2, 2.4))
  const vitrinaSign = label(
    locale === 'es' ? 'perfecta... y sobrando' : 'perfect... and left over',
    { size: 0.11, color: '#e8d8b0' },
  )
  vitrinaSign.position.set(x - 3.2, 1.8, z - 0.6)
  vitrinaSign.rotation.y = Math.PI / 2
  group.add(vitrinaSign)

  // carro de desechos: la vitrina se vuelca aqui en vez de rescatarse
  group.add(
    outlinedMergedBoxes(
      [
        { w: 0.8, h: 0.5, d: 0.55, x: x - 1.7, y: 0.5, z: z - 1.2 },
        { w: 0.08, h: 0.3, d: 0.08, x: x - 2.0, y: 0.15, z: z - 1.4 },
        { w: 0.08, h: 0.3, d: 0.08, x: x - 1.4, y: 0.15, z: z - 1.0 },
      ],
      toonMat('#4c4740'),
      { castShadow: true },
    ),
    // bandeja inclinada volcando comida al carro
    mergedBoxes(
      [
        {
          w: 0.5,
          h: 0.04,
          d: 0.4,
          x: x - 1.7,
          y: 0.82,
          z: z - 1.2,
          rotY: 0.4,
        },
        { w: 0.14, h: 0.07, d: 0.12, x: x - 1.8, y: 0.7, z: z - 1.1 },
        { w: 0.12, h: 0.06, d: 0.12, x: x - 1.6, y: 0.68, z: z - 1.3 },
      ],
      toonMat('#b09a6e'),
    ),
  )
  colliders.push(footprint(x - 1.7, z - 1.2, 1.0, 0.8))

  // el tacho grande rebosante + el cartel gris del flujo inverso
  group.add(
    outlinedMergedBoxes(
      [{ w: 0.7, h: 0.8, d: 0.7, x: x + 0.3, y: 0.4, z: z - 1.5 }],
      toonMat('#3a352c'),
      { castShadow: true },
    ),
    // comida asomando por encima del borde
    mergedBoxes(
      [
        { w: 0.2, h: 0.1, d: 0.18, x: x + 0.15, y: 0.86, z: z - 1.55 },
        { w: 0.16, h: 0.09, d: 0.16, x: x + 0.45, y: 0.85, z: z - 1.4 },
        { w: 0.18, h: 0.08, d: 0.14, x: x + 0.3, y: 0.9, z: z - 1.6 },
      ],
      toonMat('#b09a6e'),
    ),
  )
  colliders.push(footprint(x + 0.3, z - 1.5, 0.9, 0.9))
  const cartelSign = label(
    locale === 'es' ? 'excedente → basura' : 'surplus → garbage',
    { size: 0.12, color: '#8a8270' },
  )
  cartelSign.position.set(x + 0.3, 1.6, z - 1.5)
  group.add(cartelSign)

  // bolsas negras apiladas junto a la puerta trasera: la cosecha
  // triste de cada cierre (siluetas de cajas adentro)
  group.add(
    outlinedMergedBoxes(
      [
        { w: 0.5, h: 0.55, d: 0.5, x: x + 1.8, y: 0.275, z: z - 1.6 },
        { w: 0.46, h: 0.5, d: 0.46, x: x + 2.4, y: 0.25, z: z - 1.45 },
        { w: 0.44, h: 0.42, d: 0.44, x: x + 2.1, y: 0.86, z: z - 1.55 },
      ],
      toonMat('#26221c'),
      { castShadow: true },
    ),
  )
  colliders.push(footprint(x + 2.1, z - 1.5, 1.3, 0.9))
  const bolsasSign = label(
    locale === 'es' ? 'puerta trasera · 22:40' : 'back door · 10:40 pm',
    { size: 0.1, color: '#e8d8b0' },
  )
  bolsasSign.position.set(x + 2.1, 1.4, z - 1.5)
  group.add(bolsasSign)

  // la caja del dueño: calculadora vieja y la cuenta que nunca cuadra
  group.add(
    desk({
      position: [x + 2.3, 0, z + 0.7],
      color: '#4c4740',
      width: 1.3,
    }),
    mergedBoxes(
      [
        { w: 0.16, h: 0.05, d: 0.22, x: x + 2.5, y: 0.77, z: z + 0.65 },
        { w: 0.12, h: 0.02, d: 0.06, x: x + 2.5, y: 0.8, z: z + 0.57 },
        { w: 0.24, h: 0.03, d: 0.3, x: x + 2.05, y: 0.76, z: z + 0.75 },
      ],
      toonMat('#3a352c'),
    ),
  )
  colliders.push(footprint(x + 2.3, z + 0.7, 1.4, 0.8))
  const mermaSign = label(
    locale === 'es' ? 'merma de hoy: -20% (?)' : "today's waste: -20% (?)",
    { size: 0.11, color: '#e8d8b0' },
  )
  mermaSign.position.set(x + 2.3, 1.3, z + 0.7)
  group.add(mermaSign)

  // reloj de pared que cobra el cierre: la noche avanza y la comida
  // sigue saliendo por la puerta de atras
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
    // la aguja da una vuelta cada ~12 s: el cierre que no perdona
    hand.rotation.z = -t * 0.52
  })

  // micro: ver la comida irse al tacho — la dona vuela de la vitrina
  // al tacho, cae adentro y el veredicto flota unos segundos
  const dona = boxMesh(0.16, 0.08, 0.16, toonMat('#b09a6e'))
  dona.position.set(x - 3.2, 1.0, z - 0.2)
  group.add(dona)
  const verdict = label(
    locale === 'es'
      ? 'hoy se botaron 12 kg de comida perfecta'
      : '12 kg of perfect food binned today',
    { size: 0.12, color: '#e8d8b0' },
  )
  verdict.position.set(x - 0.9, 1.9, z - 0.7)
  verdict.visible = false
  group.add(verdict)
  let watchT = -1
  interactables.push({
    id: 'past-search',
    x: x - 3.2,
    z: z - 0.2,
    radius: 2.2,
    label: WATCH_LABEL,
    onActivate: () => {
      if (watchT === -1) {
        watchT = -2 // pendiente: el proximo update fija el inicio
        sfx.play('blip')
      }
    },
  })
  updates.push((t) => {
    if (watchT === -2) {
      watchT = t
    }
    if (watchT < 0) {
      return
    }
    const elapsed = t - watchT
    if (elapsed < 1.4) {
      // vuela de la vitrina hacia el tacho...
      const k = elapsed / 1.4
      dona.position.set(
        x - 3.2 + (x + 0.3 - (x - 3.2)) * k,
        1.0 + Math.sin(k * Math.PI) * 0.6,
        z - 0.2 + (z - 1.5 - (z - 0.2)) * k,
      )
      dona.rotation.y = k * 5
    } else if (elapsed < 2.0) {
      // ...y se hunde entre las bolsas, donde nadie la rescata
      const k = (elapsed - 1.4) / 0.6
      dona.position.set(x + 0.3, 1.0 * (1 - k) + 0.5, z - 1.5)
    } else if (elapsed < 5.6) {
      dona.visible = false
      verdict.visible = true
    } else {
      verdict.visible = false
      dona.visible = true
      dona.position.set(x - 3.2, 1.0, z - 0.2)
      dona.rotation.y = 0
      watchT = -1
    }
  })

  // Rodrigo (antes) cargando la bolsa negra entre el tacho y la
  // puerta trasera — el encargado del cierre
  const rodrigo = makeNpc({
    skin: '#b5825f',
    hair: { style: 'short', color: '#1a140e' },
    top: '#8a8270',
    bottom: '#5a5548',
    model: 'male-casual',
    faceSeed: 31,
    position: [x - 2.2, 0, z + 1.2],
    path: [
      [x - 2.2, z + 1.2],
      [x - 0.4, z - 0.5],
      [x + 1.3, z + 0.6],
    ],
    speed: 0.7,
  })
  const bolsa = boxMesh(0.3, 0.34, 0.26, toonMat('#26221c'))
  bolsa.position.set(0, 0.95, 0.24)
  rodrigo.group.add(bolsa)
  // Ignacia (antes) frente a la vitrina que atendio todo el dia,
  // vaciandola bandeja a bandeja
  const ignacia = makeNpc({
    skin: '#d9a684',
    hair: { style: 'ponytail', color: '#2a1a12' },
    top: '#7a6a58',
    bottom: '#4a4438',
    accessory: 'badge',
    model: 'female-casual',
    faceSeed: 58,
    position: [x - 2.4, 0, z - 0.6],
    rotationY: -Math.PI / 2,
  })
  // el Sr. Peña (antes) en su caja, calculadora en mano, sacando la
  // cuenta de la merma del dia
  const pena = makeNpc({
    skin: '#c98f6a',
    hair: { style: 'short', color: '#d8d2c4' },
    top: '#6a6152',
    bottom: '#4a4438',
    accessory: 'tie',
    model: 'male-suit',
    faceSeed: 73,
    position: [x + 2.3, 0, z + 0.05],
    rotationY: 0,
  })
  npcs.push(rodrigo, ignacia, pena)
  const talks = [
    npcTalk({
      id: 'talk-past-goodmeal-rodrigo',
      npc: rodrigo,
      dialog: GOODMEAL_PASADO_DIALOGS.rodrigo,
      openDialog: actions.openDialog,
    }),
    npcTalk({
      id: 'talk-past-goodmeal-ignacia',
      npc: ignacia,
      dialog: GOODMEAL_PASADO_DIALOGS.ignacia,
      openDialog: actions.openDialog,
    }),
    npcTalk({
      id: 'talk-past-goodmeal-pena',
      npc: pena,
      dialog: GOODMEAL_PASADO_DIALOGS.pena,
      openDialog: actions.openDialog,
    }),
  ]
  for (const talk of talks) {
    interactables.push(talk.interactable)
    updates.push(talk.update)
  }

  const story = GOODMEAL_STORY[locale]
  const panel = screenPanel({
    title: locale === 'es' ? 'la vitrina al tacho' : 'the case into the bin',
    lines:
      locale === 'es'
        ? [
            'cierre: 22:00, vitrina llena',
            'venderla: no hay a quien',
            'regalarla: no hay como',
            'destino: bolsa negra',
            '',
            '[E] leer la historia',
          ]
        : [
            'closing: 10 pm, case full',
            'sell it: nobody around',
            'give it: no way to',
            'destination: black bag',
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
