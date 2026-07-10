/**
 * @module rooms/past/cofasa (engine)
 * @description El "antes" de Cofasa al nivel del canon (informe 10): el
 *   registro manual de paradas, sepia y a contrarreloj. El escritorio de
 *   supervision junto a la linea con planillas apiladas, tachadas y a
 *   medio cuadrar, la calculadora vieja, el reloj de pared que cobra los
 *   minutos, la torre andon en ROJO FIJO (la linea detenida y nadie sabe
 *   por que) y la llenadora de ampollas parada con papeles traspapelados
 *   en el piso. Consolidar las planillas a mano (los totales no cuadran)
 *   como objeto de busqueda lenta. 3 NPCs frustrados conversables:
 *   Nelida cronometrando con el reloj de pulsera, Rafael mirando la
 *   maquina detenida sin datos y Carmen cargando las planillas que ni
 *   cuadran entre si (el arco: los tres reaparecen en el presente
 *   usando el sistema).
 */
import { Group, Mesh, MeshBasicMaterial, PlaneGeometry } from 'three'
import type { Box2 } from '../../../lib/collision'
import type { Locale } from '../../../lib/rooms'
import { sfx } from '../../audio'
import { makeNpc, type NpcHandle } from '../../character'
import { npcTalk } from '../../dialog'
import { COFASA_PASADO_DIALOGS } from '../../dialogs/cofasa-pasado'
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
import { footprint, paperStack } from '../props'
import { placeProp } from '../props-catalog'
import {
  carryPapers,
  PAST_SCREEN,
  PAST_STORY_LABEL,
  type PastSet,
} from './shared'

const COFASA_STORY: Record<Locale, { title: string; paragraphs: string[] }> = {
  es: {
    title: 'Antes del sistema (2017)',
    paragraphs: [
      'Cada parada de maquina de la planta se registraba a mano: la ' +
        'supervisora cargaba una libreta y cronometraba con el reloj de ' +
        'pulsera. Una fila por parada — hora, maquina y la causa que ' +
        'alcanzara a ver — entre el ruido y el apuro del turno.',
      'Al final del turno venia lo peor: consolidar. Pasar la libreta a ' +
        'la planilla, sumar tiempos a calculadora y pelear con totales ' +
        'que no cuadraban ni entre planillas. Un reporte de ' +
        'productividad costaba VARIAS horas... y nadie sabia cual causa ' +
        'se comia el tiempo de la linea.',
      'Ese año llego un desarrollador web con un cuaderno: propuso un ' +
        'sistema (jQuery + Laravel, en la red local de la planta) que ' +
        'registrara cada parada al momento, con causa y hora. Cruza de ' +
        'vuelta y lo ves funcionando.',
    ],
  },
  en: {
    title: 'Before the system (2017)',
    paragraphs: [
      'Every machine stoppage in the plant was logged by hand: the ' +
        'supervisor carried a notebook and timed things with her ' +
        'wristwatch. One row per stoppage — time, machine and whatever ' +
        'cause she managed to see — amid the noise and rush of the ' +
        'shift.',
      'The worst came at end of shift: consolidating. Copying the ' +
        'notebook into the sheet, adding times on a calculator and ' +
        'fighting totals that did not match even across sheets. One ' +
        'productivity report cost SEVERAL hours... and nobody knew ' +
        'which cause was eating the line’s time.',
      'That year a web developer arrived with a notebook of his own: ' +
        'he proposed a system (jQuery + Laravel, on the plant’s ' +
        'local network) to log every stoppage as it happened, with ' +
        'cause and time. Cross back and you can see it running.',
    ],
  },
}

const CONSOLIDATE_LABEL = {
  es: 'Consolidar las planillas',
  en: 'Consolidate the paper sheets',
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

/** El "antes" de Cofasa: paradas anotadas a mano junto a la linea. */
export function cofasaPast(
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

  // llenadora de ampollas DETENIDA contra el muro izquierdo: el mismo
  // volumen del presente pero apagada, en tonos sepia
  group.add(
    outlinedMergedBoxes(
      [
        { w: 1.1, h: 1.5, d: 0.9, x: x - 3.2, y: 0.75, z: z - 1.6 },
        { w: 0.5, h: 0.4, d: 0.5, x: x - 3.2, y: 1.7, z: z - 1.6 },
        { w: 0.3, h: 0.24, d: 0.3, x: x - 3.2, y: 1.28, z: z - 0.95 },
        // banda corta con ampollas quietas a medio llenar
        { w: 0.7, h: 0.74, d: 1.6, x: x - 3.2, y: 0.37, z: z + 0.4 },
      ],
      toonMat('#6a5f4e'),
      { castShadow: true },
    ),
    mergedBoxes(
      Array.from({ length: 5 }, (_, i) => ({
        w: 0.07,
        h: 0.16,
        d: 0.07,
        x: x - 3.3 + (i % 2) * 0.24,
        y: 0.82,
        z: z - 0.2 + i * 0.24,
      })),
      toonMat('#8a6e3c'),
    ),
  )
  colliders.push(
    footprint(x - 3.2, z - 1.6, 1.3, 1.1),
    footprint(x - 3.2, z + 0.4, 0.9, 1.8),
  )
  const stoppedSign = label(
    locale === 'es' ? '¿por que se paro?' : 'why did it stop?',
    { size: 0.11, color: '#e8d8b0' },
  )
  stoppedSign.position.set(x - 3.2, 2.3, z - 1.2)
  group.add(stoppedSign)

  // torre andon en ROJO FIJO: la linea detenida y cero visibilidad
  group.add(
    outlinedMergedBoxes(
      [
        { w: 0.3, h: 0.06, d: 0.3, x: x - 1.9, y: 0.03, z: z - 1.3 },
        { w: 0.08, h: 1.1, d: 0.08, x: x - 1.9, y: 0.6, z: z - 1.3 },
        { w: 0.2, h: 0.16, d: 0.2, x: x - 1.9, y: 1.24, z: z - 1.3 },
        { w: 0.2, h: 0.16, d: 0.2, x: x - 1.9, y: 1.42, z: z - 1.3 },
      ],
      toonMat('#4c4740'),
      { castShadow: true },
    ),
  )
  const andonRed = boxMesh(0.2, 0.16, 0.2, toonMat('#8a2e28'))
  andonRed.position.set(x - 1.9, 1.6, z - 1.3)
  group.add(andonRed)
  colliders.push(footprint(x - 1.9, z - 1.3, 0.4, 0.4))

  // escritorio de supervision GLB saturado: planillas apiladas, calculadora
  // vieja y la pila de reportes a medio consolidar
  group.add(
    placeProp('desk_office', {
      x: x + 1.3,
      z: z + 0.6,
      width: 1.6,
      color: '#4c4740',
    }),
  )
  colliders.push(footprint(x + 1.3, z + 0.6, 1.7, 0.8))
  group.add(
    paperStack({ position: [x + 0.75, 0.745, z + 0.6], count: 12 }),
    paperStack({ position: [x + 1.5, 0.745, z + 0.75], count: 8 }),
    paperStack({ position: [x + 2.0, 0, z + 1.1], count: 14 }),
    // calculadora vieja: cuerpo + visor
    mergedBoxes(
      [
        { w: 0.16, h: 0.05, d: 0.22, x: x + 1.85, y: 0.77, z: z + 0.5 },
        { w: 0.12, h: 0.02, d: 0.06, x: x + 1.85, y: 0.8, z: z + 0.42 },
      ],
      toonMat('#3a352c'),
    ),
  )
  const sinCuadrar = label(
    locale === 'es' ? 'SIN CUADRAR: 62' : 'UNBALANCED: 62',
    { size: 0.12, color: '#e8d8b0' },
  )
  sinCuadrar.position.set(x + 1.3, 1.3, z + 0.6)
  group.add(sinCuadrar)

  // planillas traspapeladas por el piso: datos crudos que nunca se
  // vuelven indicadores
  group.add(
    mergedBoxes(
      [
        { w: 0.32, h: 0.04, d: 0.44, x: x + 0.2, y: 0.02, z: z + 1.6 },
        {
          w: 0.32,
          h: 0.03,
          d: 0.44,
          x: x - 0.5,
          y: 0.015,
          z: z + 2.0,
          rotY: 0.4,
        },
        {
          w: 0.3,
          h: 0.03,
          d: 0.4,
          x: x + 2.6,
          y: 0.015,
          z: z - 0.3,
          rotY: -0.3,
        },
        {
          w: 0.3,
          h: 0.03,
          d: 0.4,
          x: x - 1.2,
          y: 0.015,
          z: z + 0.9,
          rotY: 0.8,
        },
      ],
      toonMat('#b09a6e'),
    ),
  )

  // reloj de pared que cobra los minutos: la aguja avanza sin piedad
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
    // la aguja da una vuelta cada ~12 s: el turno que se va
    hand.rotation.z = -t * 0.52
  })

  // micro: consolidar las planillas a mano — la pila tiembla y el
  // veredicto flota unos segundos (los totales no cuadran)
  const verdict = label(
    locale === 'es'
      ? '3 horas despues: los totales NO cuadran'
      : '3 hours later: the totals do NOT match',
    { size: 0.13, color: '#e8d8b0' },
  )
  verdict.position.set(x + 1.3, 2.4, z + 0.6)
  verdict.visible = false
  group.add(verdict)
  const shakyStack = paperStack({
    position: [x + 1.15, 0.745, z + 0.35],
    count: 9,
  })
  group.add(shakyStack)
  let consolidateT = -1
  interactables.push({
    id: 'past-search',
    x: x + 1.3,
    z: z + 0.6,
    radius: 2.2,
    label: CONSOLIDATE_LABEL,
    onActivate: () => {
      if (consolidateT === -1) {
        consolidateT = -2 // pendiente: el proximo update fija el inicio
        sfx.play('blip')
      }
    },
  })
  updates.push((t) => {
    if (consolidateT === -2) {
      consolidateT = t
    }
    if (consolidateT < 0) {
      return
    }
    const elapsed = t - consolidateT
    if (elapsed < 2.2) {
      shakyStack.rotation.y = Math.sin(t * 22) * 0.14
    } else if (elapsed < 5.5) {
      shakyStack.rotation.y = 0
      verdict.visible = true
    } else {
      verdict.visible = false
      consolidateT = -1
    }
  })

  // Nelida (antes) sentada en el escritorio de supervision, libreta y
  // reloj en mano — la misma supervisora del presente
  const nelida = makeNpc({
    skin: '#d9a684',
    hair: { style: 'bun', color: '#2a1a12' },
    top: '#8a8270',
    bottom: '#5a5548',
    accessory: 'badge',
    model: 'elizabeth',
    faceSeed: 42,
    position: [x + 1.3, 0, z + 0.05],
    rotationY: 0,
    pose: 'sit',
  })
  // Rafael (antes) parado frente a la llenadora detenida, mirandola
  // sin datos — el mismo operario del presente
  const rafael = makeNpc({
    skin: '#b5825f',
    hair: { style: 'bun', color: '#d8d2c4' },
    top: '#8a8270',
    bottom: '#6a6152',
    model: 'the-boss',
    faceSeed: 77,
    position: [x - 2.2, 0, z - 0.2],
    rotationY: -Math.PI / 2,
    // crisis del rubro (pedido de Pablo): el shock por la produccion parada
    pose: 'shocked',
  })
  // Carmen (antes) cargando planillas que ni cuadran, de un lado a otro
  const carmen = makeNpc({
    skin: '#e8b48c',
    hair: { style: 'ponytail', color: '#2c1e14' },
    top: '#7a6a58',
    bottom: '#4a4438',
    accessory: 'tie',
    model: 'jennifer',
    faceSeed: 96,
    position: [x + 0.4, 0, z + 1.9],
    path: [
      [x + 0.4, z + 1.9],
      [x + 2.4, z + 0.2],
      [x - 0.8, z + 1.2],
    ],
    speed: 0.5,
  })
  carryPapers(carmen)
  npcs.push(nelida, rafael, carmen)
  const talks = [
    npcTalk({
      id: 'talk-past-cofasa-nelida',
      npc: nelida,
      dialog: COFASA_PASADO_DIALOGS.nelida,
      openDialog: actions.openDialog,
    }),
    npcTalk({
      id: 'talk-past-cofasa-rafael',
      npc: rafael,
      dialog: COFASA_PASADO_DIALOGS.rafael,
      openDialog: actions.openDialog,
    }),
    npcTalk({
      id: 'talk-past-cofasa-carmen',
      npc: carmen,
      dialog: COFASA_PASADO_DIALOGS.carmen,
      openDialog: actions.openDialog,
    }),
  ]
  for (const talk of talks) {
    interactables.push(talk.interactable)
    updates.push(talk.update)
  }

  const story = COFASA_STORY[locale]
  const panel = screenPanel({
    title: locale === 'es' ? 'paradas en papel' : 'downtime on paper',
    lines:
      locale === 'es'
        ? [
            'registro: libreta y reloj',
            'reporte: horas a mano',
            'causas de parada:',
            '  nadie las mide',
            '',
            '[E] leer la historia',
          ]
        : [
            'log: notebook and watch',
            'report: hours by hand',
            'stoppage causes:',
            '  nobody measures them',
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
