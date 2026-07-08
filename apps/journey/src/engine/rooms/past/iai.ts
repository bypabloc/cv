/**
 * @module rooms/past/iai (engine)
 * @description El "antes" del IAI al nivel del canon (informe 16): la
 *   oficina tecnica de obra publica en Excel y papel, sepia y sin fin.
 *   El meson saturado (planos, calculadora, escalimetro, computos a
 *   medio tachar), las pilas de carpetas manila por obra con el hueco
 *   delator de la carpeta que falta, las impresiones de Excel pegadas
 *   con cinta (APUs vencidos: indices BCV SEP/OCT/NOV), el telefono
 *   descolgado (el instituto pidiendo el consolidado), el reloj de
 *   pared que cobra las jornadas y una sola PC vieja compartida con su
 *   Excel. Consolidar el avance de todas las obras a mano (la carpeta
 *   de la via agricola no aparece) como objeto de busqueda lenta. 3
 *   NPCs frustrados conversables: Belkis rehaciendo cuarenta APU por
 *   los indices nuevos, el Ing. Gregorio con la valuacion de la calle
 *   19 en tres papeles que no cuadran y Pastor Rivas, maestro de obra,
 *   esperando la firma para que su cuadrilla cobre (el arco: Belkis y
 *   Gregorio reaparecen en el presente usando el sistema).
 */
import { Group, Mesh, MeshBasicMaterial, PlaneGeometry } from 'three'
import type { Box2 } from '../../../lib/collision'
import type { Locale } from '../../../lib/rooms'
import { sfx } from '../../audio'
import { makeNpc, type NpcHandle } from '../../character'
import { npcTalk } from '../../dialog'
import { IAI_PASADO_DIALOGS } from '../../dialogs/iai-pasado'
import type { Interactable } from '../../state'
import {
  boxMesh,
  label,
  makeCanvasTexture,
  mergedBoxes,
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

const IAI_STORY: Record<Locale, { title: string; paragraphs: string[] }> = {
  es: {
    title: 'Antes del sistema (2015)',
    paragraphs: [
      'El presupuesto de cada obra del instituto vivia en Excel y ' +
        'papel: partidas COVENIN calculadas a mano, APUs que habia que ' +
        'rehacer completos cada vez que el BCV publicaba indices ' +
        'nuevos, y cada quien con su propia copia — ninguna cuadraba ' +
        'con las demas.',
      'Las valuaciones de avance eran una pelea de papeles: la hoja de ' +
        'medicion de la obra, la copia en limpio y la planilla de ' +
        'presupuestos, con tres montos distintos. Mientras el inspector ' +
        'las cuadraba, el contratista no cobraba — y el consolidado que ' +
        'pedia la presidencia tardaba jornadas enteras.',
      'Ese año un equipo de tres tesistas liderado por Pablo propuso ' +
        'otra cosa: un sistema de escritorio en Java con una PC como ' +
        'servidor central en red local — una sola base de datos para ' +
        'presupuestos, APU y valuaciones. Cruza de vuelta y lo ves ' +
        'funcionando.',
    ],
  },
  en: {
    title: 'Before the system (2015)',
    paragraphs: [
      'Every works budget at the institute lived in Excel and paper: ' +
        'COVENIN line items computed by hand, unit-price analyses redone ' +
        'in full every time the Central Bank published new indexes, and ' +
        'everyone keeping their own copy — none of them matching.',
      'Progress valuations were a paper fight: the on-site measurement ' +
        'sheet, the clean copy and the budget desk sheet, with three ' +
        'different amounts. While the inspector squared them, the ' +
        'contractor went unpaid — and the consolidated report the ' +
        'presidency asked for took whole workdays.',
      'That year a team of three thesis students led by Pablo proposed ' +
        'something else: a Java desktop system with one PC as the ' +
        'central server on a local network — a single database for ' +
        'budgets, analyses and valuations. Cross back and you can see ' +
        'it running.',
    ],
  },
}

const CONSOLIDAR_LABEL = {
  es: 'Consolidar el avance a mano',
  en: 'Consolidate progress by hand',
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

/** Impresion de Excel pegada con cinta: grilla + indices BCV del mes. */
function drawExcelPrint(month: string) {
  return (ctx: CanvasRenderingContext2D, size: number): void => {
    ctx.fillStyle = '#e8dfc4'
    ctx.fillRect(0, 0, size, size)
    ctx.strokeStyle = '#8a7a58'
    ctx.lineWidth = 2
    for (let i = 1; i < 6; i += 1) {
      ctx.beginPath()
      ctx.moveTo(0, (i / 6) * size)
      ctx.lineTo(size, (i / 6) * size)
      ctx.stroke()
      ctx.beginPath()
      ctx.moveTo((i / 6) * size, 0)
      ctx.lineTo((i / 6) * size, size)
      ctx.stroke()
    }
    ctx.fillStyle = '#3a2c18'
    ctx.font = 'bold 30px "Space Mono", ui-monospace, monospace'
    ctx.fillText('INDICES', 20, 60)
    ctx.fillText(`BCV ${month}`, 20, 108)
    ctx.font = '24px "Space Mono", ui-monospace, monospace'
    ctx.fillText('APU: rehacer', 20, 170)
    // tachon de vencido
    ctx.strokeStyle = '#8a3a2e'
    ctx.lineWidth = 7
    ctx.beginPath()
    ctx.moveTo(16, 200)
    ctx.lineTo(size - 16, 150)
    ctx.stroke()
    // cinta adhesiva en las esquinas
    ctx.fillStyle = 'rgba(240,232,200,0.85)'
    ctx.fillRect(-10, -10, 60, 34)
    ctx.fillRect(size - 50, -10, 60, 34)
  }
}

/** Torre de carpetas manila desordenada (bloques girados). */
function folderTower(
  x: number,
  z: number,
  count: number,
): {
  w: number
  h: number
  d: number
  x: number
  y: number
  z: number
  rotY: number
}[] {
  return Array.from({ length: count }, (_, i) => ({
    w: 0.34,
    h: 0.055,
    d: 0.46,
    x,
    y: 0.03 + i * 0.055,
    z,
    rotY: Math.sin(i * 3.1 + x) * 0.3,
  }))
}

/** El "antes" del IAI: presupuestos a mano y el consolidado que no sale. */
export function iaiPast(
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

  // meson tecnico saturado: planos enrollados, calculadora, escalimetro
  // y hojas de computos metricos a medio tachar
  const meson = desk({
    position: [x - 1.6, 0, z - 0.8],
    color: '#4c4740',
    width: 2.2,
  })
  group.add(meson)
  colliders.push(footprint(x - 1.6, z - 0.8, 2.3, 0.9))
  group.add(
    paperStack({ position: [x - 2.3, 0.745, z - 0.9], count: 11 }),
    paperStack({ position: [x - 1.0, 0.745, z - 0.6], count: 7 }),
    // calculadora + escalimetro + rollos de planos sobre el meson
    mergedBoxes(
      [
        { w: 0.14, h: 0.03, d: 0.2, x: x - 1.55, y: 0.76, z: z - 1.0 },
        { w: 0.4, h: 0.02, d: 0.03, x: x - 1.25, y: 0.755, z: z - 0.95 },
        { w: 0.09, h: 0.09, d: 0.7, x: x - 1.9, y: 0.79, z: z - 0.65 },
        { w: 0.08, h: 0.08, d: 0.6, x: x - 1.75, y: 0.86, z: z - 0.7 },
      ],
      toonMat('#7a6a52'),
    ),
  )

  // pilas de carpetas manila por obra: torres desordenadas en el piso
  // (la montaña que hay que recorrer para consolidar) + el hueco delator
  const towers = mergedBoxes(
    [
      ...folderTower(x + 1.8, z - 1.4, 9),
      ...folderTower(x + 2.5, z - 1.1, 6),
      ...folderTower(x + 2.1, z - 0.3, 11),
      ...folderTower(x + 1.3, z + 0.4, 5),
      ...folderTower(x - 3.1, z + 1.4, 7),
    ],
    toonMat('#b09a6e'),
  )
  group.add(towers)
  colliders.push(
    footprint(x + 2.0, z - 0.8, 1.8, 1.6),
    footprint(x - 3.1, z + 1.4, 0.6, 0.6),
  )
  // el hueco delator: el espacio de LA carpeta que falta, señalado
  const holeSign = label(
    locale === 'es' ? '¿quien tiene la carpeta?' : 'who has the folder?',
    { size: 0.1, color: '#e8d8b0' },
  )
  holeSign.position.set(x + 1.3, 1.05, z + 0.4)
  group.add(holeSign)

  // impresiones de Excel pegadas con cinta: APUs vencidos por indices
  const prints: readonly (readonly [string, number])[] = [
    ['SEP', x - 1.1],
    ['OCT', x + 0.1],
    ['NOV', x + 1.3],
  ]
  for (const [month, px] of prints) {
    const print = new Mesh(
      new PlaneGeometry(0.5, 0.5),
      new MeshBasicMaterial({
        map: makeCanvasTexture(128, drawExcelPrint(month)),
      }),
    )
    print.position.set(px, 1.9, z - depth / 2 + 0.06)
    print.rotation.z = Math.sin(px * 7) * 0.06
    print.userData.noOutline = true
    group.add(print)
  }

  // escritorio de la unica PC vieja compartida (Excel abierto) +
  // telefono descolgado: el instituto pidiendo el consolidado
  const pcDesk = desk({
    position: [x - 0.2, 0, z + 2.0],
    color: '#4c4740',
    width: 1.5,
  })
  group.add(pcDesk)
  colliders.push(footprint(x - 0.2, z + 2.0, 1.6, 0.8))
  const pcScreen = screenPanel({
    title: 'presupuesto_v6_FINAL.xls',
    lines:
      locale === 'es'
        ? [
            'E-411  812 ¿o 790?',
            'total: #########',
            'copia de Belkis: otra',
            'copia inspector: otra',
          ]
        : [
            'E-411  812 or 790?',
            'total: #########',
            "Belkis's copy: differs",
            "inspector's: differs",
          ],
    theme: PAST_SCREEN,
    width: 0.62,
    height: 0.44,
  })
  pcScreen.position.set(x - 0.2, 1.05, z + 2.1)
  pcScreen.rotation.y = Math.PI
  group.add(pcScreen)
  group.add(
    mergedBoxes(
      [
        // torre vieja bajo el escritorio + teclado
        { w: 0.2, h: 0.42, d: 0.4, x: x + 0.35, y: 0.21, z: z + 2.0 },
        { w: 0.36, h: 0.025, d: 0.14, x: x - 0.2, y: 0.76, z: z + 1.75 },
        // telefono con el auricular descolgado
        { w: 0.22, h: 0.08, d: 0.2, x: x - 0.75, y: 0.78, z: z + 2.15 },
        { w: 0.06, h: 0.05, d: 0.18, x: x - 0.95, y: 0.765, z: z + 2.05 },
      ],
      toonMat('#3a352c'),
    ),
  )
  const consolidadoSign = label(
    locale === 'es' ? 'CONSOLIDADO: VIERNES' : 'CONSOLIDATED: FRIDAY',
    { size: 0.12, color: '#e8d8b0' },
  )
  consolidadoSign.position.set(x - 0.2, 1.45, z + 2.0)
  group.add(consolidadoSign)

  // reloj de pared que cobra las jornadas: la aguja avanza sin piedad
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
    hand.rotation.z = -t * 0.52
  })

  // micro: consolidar el avance a mano — las torres tiemblan buscando
  // la carpeta de la via agricola y el veredicto flota unos segundos
  const verdict = label(
    locale === 'es'
      ? '20 min despues: falta la carpeta de la VIA AGRICOLA'
      : '20 min later: the RURAL ROAD folder is missing',
    { size: 0.13, color: '#e8d8b0' },
  )
  verdict.position.set(x + 2.0, 2.2, z - 0.8)
  verdict.visible = false
  group.add(verdict)
  let searchT = -1
  interactables.push({
    id: 'past-search',
    x: x + 2.0,
    z: z - 0.8,
    radius: 2.2,
    label: CONSOLIDAR_LABEL,
    onActivate: () => {
      if (searchT === -1) {
        searchT = -2 // pendiente: el proximo update fija el inicio
        sfx.play('blip')
      }
    },
  })
  updates.push((t) => {
    if (searchT === -2) {
      searchT = t
    }
    if (searchT < 0) {
      return
    }
    const elapsed = t - searchT
    if (elapsed < 2.2) {
      towers.rotation.y = Math.sin(t * 20) * 0.012
    } else if (elapsed < 5.5) {
      towers.rotation.y = 0
      verdict.visible = true
    } else {
      verdict.visible = false
      searchT = -1
    }
  })

  // Belkis (antes) en el meson, rehaciendo APUs con la calculadora —
  // misma cara y peinado que su version de hoy, ropa apagada
  const belkis = makeNpc({
    skin: '#d9a684',
    hair: { style: 'bun', color: '#3a2418' },
    top: '#7a6a58',
    bottom: '#4a4438',
    accessory: 'glasses',
    model: 'female-casual',
    faceSeed: 62,
    position: [x - 1.6, 0, z - 1.5],
    rotationY: Math.PI,
  })
  // Ing. Gregorio (antes) cargando sus tres papeles entre el meson y
  // la PC compartida — mismo inspector del presente
  const gregorio = makeNpc({
    skin: '#c98f6a',
    hair: { style: 'short', color: '#7a7a82' },
    top: '#8a8270',
    bottom: '#4a4438',
    accessory: 'badge',
    model: 'male-suit',
    faceSeed: 53,
    position: [x + 0.6, 0, z + 0.8],
    path: [
      [x + 0.6, z + 0.8],
      [x - 1.2, z + 1.4],
      [x + 1.0, z + 1.8],
    ],
    speed: 0.5,
  })
  carryPapers(gregorio)
  // Pastor Rivas, maestro de obra con su casco, esperando la firma
  // junto a la salida (viene de la calle 19 por tercera vez)
  const pastor = makeNpc({
    skin: '#a06a48',
    hair: { style: 'short', color: '#181410' },
    top: '#c9b089',
    bottom: '#4a4438',
    accessory: 'helmet',
    model: 'male-worker',
    faceSeed: 66,
    position: [x + 3.0, 0, z + 2.2],
    rotationY: -Math.PI / 2,
  })
  npcs.push(belkis, gregorio, pastor)
  const talks = [
    npcTalk({
      id: 'talk-past-iai-belkis',
      npc: belkis,
      dialog: IAI_PASADO_DIALOGS.belkis,
      openDialog: actions.openDialog,
    }),
    npcTalk({
      id: 'talk-past-iai-gregorio',
      npc: gregorio,
      dialog: IAI_PASADO_DIALOGS.gregorio,
      openDialog: actions.openDialog,
    }),
    npcTalk({
      id: 'talk-past-iai-pastor',
      npc: pastor,
      dialog: IAI_PASADO_DIALOGS.pastor,
      openDialog: actions.openDialog,
    }),
  ]
  for (const talk of talks) {
    interactables.push(talk.interactable)
    updates.push(talk.update)
  }

  const story = IAI_STORY[locale]
  const panel = screenPanel({
    title: locale === 'es' ? 'obras en papel' : 'works on paper',
    lines:
      locale === 'es'
        ? [
            'APU: a mano, x40',
            'valuacion: 3 papeles',
            'consolidado: jornadas',
            'copias: ninguna cuadra',
            '',
            '[E] leer la historia',
          ]
        : [
            'APU: by hand, x40',
            'valuation: 3 papers',
            'consolidated: days',
            'copies: none match',
            '',
            '[E] read the story',
          ],
    theme: PAST_SCREEN,
    width: 1.8,
    height: 1.25,
  })
  panel.position.set(x + 3.2, 1.6, z - depth / 2 + 0.12)
  group.add(panel)
  interactables.push({
    id: 'past-story',
    x: x + 3.2,
    z: z - depth / 2 + 0.5,
    radius: 2.4,
    label: PAST_STORY_LABEL,
    onActivate: () => actions.openStory(story.title, story.paragraphs),
  })
  return { group, colliders, npcs, interactables, updates }
}
