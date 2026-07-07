/**
 * @module rooms/past/ipasme (engine)
 * @description El "antes" de IPASME al nivel del canon (informe 09): el
 *   Departamento de Historias Medicas en papel, sepia y sin fin.
 *   Estanterias metalicas de carpetas manila hasta el techo (lotes
 *   fusionados), la pila de fichas traspapeladas volcada en el piso, el
 *   "hueco" delator con su tarjeton solitario, el escritorio de admision
 *   saturado (planillas, telefono descolgado, lista de pendientes) y el
 *   reloj de pared que cobra los "varios minutos" por paciente. Buscar la
 *   historia de un afiliado a mano (8 min, solo aparece el tarjeton) como
 *   objeto de busqueda lenta. 3 NPCs frustrados conversables: Argenis
 *   hurgando el archivo con cuatro medicos esperando, Yuleima cargando
 *   las carpetas de los tres Perez y Petra viendo crecer la cola (el
 *   arco: Argenis y Yuleima reaparecen en el presente usando el sistema).
 */
import { Group, Mesh, MeshBasicMaterial, PlaneGeometry } from 'three'
import type { Box2 } from '../../../lib/collision'
import type { Locale } from '../../../lib/rooms'
import { sfx } from '../../audio'
import { makeNpc, type NpcHandle } from '../../character'
import { npcTalk } from '../../dialog'
import { IPASME_PASADO_DIALOGS } from '../../dialogs/ipasme-pasado'
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

const IPASME_STORY: Record<Locale, { title: string; paragraphs: string[] }> = {
  es: {
    title: 'Antes del sistema (2014)',
    paragraphs: [
      'Cada afiliado del IPASME tenia su historia medica en una carpeta ' +
        'manila con numeracion escrita a mano. Decadas de expedientes ' +
        'llenaban un cuarto-archivo sin fin: al sacar una carpeta se ' +
        'dejaba un tarjeton en el hueco... y un tarjeton mal puesto era ' +
        'una historia perdida.',
      'Buscar la historia de un paciente costaba varios minutos — con ' +
        'suerte. Sin el numero a mano, un apellido repetido mandaba a la ' +
        'enfermera de vuelta con tres carpetas equivocadas, y la cola de ' +
        'la recepcion no bajaba nunca.',
      'Ese año un junior recien llegado propuso otra cosa: un sistema ' +
        'digital de historias medicas — Java de escritorio, POO y CRUD — ' +
        'que reemplazara el papel. Cruza de vuelta y lo ves funcionando.',
    ],
  },
  en: {
    title: 'Before the system (2014)',
    paragraphs: [
      'Every IPASME member had a medical record in a manila folder with ' +
        'a hand-written number. Decades of files packed an endless ' +
        'archive room: pulling a folder meant leaving a tracer card in ' +
        'the gap... and a misplaced card meant a lost record.',
      'Finding a patient’s record took several minutes — with luck. ' +
        'Without the number at hand, a repeated surname sent the nurse ' +
        'back with three wrong folders, and the reception queue never ' +
        'shrank.',
      'That year a newly arrived junior proposed something else: a ' +
        'digital medical records system — desktop Java, OOP and CRUD — ' +
        'to replace the paper. Cross back and you can see it running.',
    ],
  },
}

const SEARCH_FOLDER_LABEL = {
  es: 'Buscar una historia en el archivo',
  en: 'Search the archive for a record',
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

/** Estanteria de archivo: laterales + repisas + filas de carpetas. */
function shelfBoxes(
  x: number,
  z: number,
  width: number,
): {
  metal: { w: number; h: number; d: number; x: number; y: number; z: number }[]
  folders: {
    w: number
    h: number
    d: number
    x: number
    y: number
    z: number
  }[]
} {
  const metal = [
    { w: width, h: 0.05, d: 0.42, x, y: 0.5, z },
    { w: width, h: 0.05, d: 0.42, x, y: 1.1, z },
    { w: width, h: 0.05, d: 0.42, x, y: 1.7, z },
    { w: width, h: 0.05, d: 0.42, x, y: 2.3, z },
    { w: 0.06, h: 2.4, d: 0.42, x: x - width / 2 + 0.03, y: 1.2, z },
    { w: 0.06, h: 2.4, d: 0.42, x: x + width / 2 - 0.03, y: 1.2, z },
  ]
  // filas de carpetas apretadas sobre cada repisa (bloques corridos)
  const folders = [0.5, 1.1, 1.7, 2.3].map((y) => ({
    w: width - 0.24,
    h: 0.34,
    d: 0.3,
    x,
    y: y + 0.2,
    z,
  }))
  return { metal, folders }
}

/** El "antes" de IPASME: el archivo de carpetas y la busqueda a mano. */
export function ipasmePast(
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

  // estanterias de archivo hasta el techo contra ambos muros: la montaña
  // de decadas de expedientes (2 lotes fusionados: metal + manila)
  const left = shelfBoxes(x - 3.2, z - 1.2, 2.6)
  const left2 = shelfBoxes(x - 3.2, z + 1.6, 2.6)
  const right = shelfBoxes(x + 3.2, z - 1.2, 2.6)
  group.add(
    outlinedMergedBoxes(
      [...left.metal, ...left2.metal, ...right.metal],
      toonMat('#5a5750'),
      { castShadow: true },
    ),
    mergedBoxes(
      [...left.folders, ...left2.folders, ...right.folders],
      toonMat('#b09a6e'),
    ),
  )
  colliders.push(
    footprint(x - 3.2, z - 1.2, 2.8, 0.6),
    footprint(x - 3.2, z + 1.6, 2.8, 0.6),
    footprint(x + 3.2, z - 1.2, 2.8, 0.6),
  )

  // el "hueco" delator en la repisa media derecha: la fila se corta y
  // solo queda el tarjeton parado donde falta la carpeta
  const gap = boxMesh(0.03, 0.26, 0.2, toonMat('#e8d8b0'))
  gap.position.set(x + 2.6, 1.32, z - 1.2)
  group.add(gap)
  const gapSign = label(locale === 'es' ? '¿y la carpeta?' : 'where is it?', {
    size: 0.1,
    color: '#e8d8b0',
  })
  gapSign.position.set(x + 2.6, 1.72, z - 0.9)
  group.add(gapSign)

  // fichas traspapeladas: la pila volcada en el piso + carpetas sueltas
  group.add(
    mergedBoxes(
      [
        { w: 0.34, h: 0.05, d: 0.46, x: x + 1.4, y: 0.025, z: z + 0.6 },
        { w: 0.34, h: 0.04, d: 0.46, x: x + 1.55, y: 0.06, z: z + 0.75 },
        { w: 0.34, h: 0.04, d: 0.46, x: x + 1.3, y: 0.09, z: z + 0.5 },
        { w: 0.3, h: 0.03, d: 0.4, x: x + 0.9, y: 0.015, z: z + 1.0 },
        { w: 0.3, h: 0.03, d: 0.4, x: x + 1.8, y: 0.015, z: z + 0.2 },
      ],
      toonMat('#b09a6e'),
    ),
  )

  // escritorio de admision saturado: planillas, telefono descolgado y
  // la lista manuscrita de pendientes por buscar
  const admision = desk({
    position: [x - 0.4, 0, z + 2.0],
    color: '#4c4740',
    width: 1.5,
  })
  group.add(admision)
  colliders.push(footprint(x - 0.4, z + 2.0, 1.6, 0.8))
  group.add(
    paperStack({ position: [x - 0.9, 0.745, z + 2.0], count: 12 }),
    paperStack({ position: [x - 0.1, 0.745, z + 2.15], count: 7 }),
    paperStack({ position: [x + 0.5, 0, z + 2.3], count: 10 }),
    // telefono con el auricular descolgado sobre el escritorio
    mergedBoxes(
      [
        { w: 0.22, h: 0.08, d: 0.2, x: x + 0.15, y: 0.78, z: z + 1.85 },
        { w: 0.06, h: 0.05, d: 0.18, x: x + 0.34, y: 0.765, z: z + 1.78 },
      ],
      toonMat('#3a352c'),
    ),
  )
  const pendientes = label(locale === 'es' ? 'PENDIENTES: 14' : 'PENDING: 14', {
    size: 0.12,
    color: '#e8d8b0',
  })
  pendientes.position.set(x - 0.4, 1.3, z + 2.0)
  group.add(pendientes)

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
    // la aguja da una vuelta cada ~12 s: los minutos que se van
    hand.rotation.z = -t * 0.52
  })

  // micro: buscar una historia a mano — las carpetas tiemblan y el
  // veredicto flota unos segundos (solo aparece el tarjeton)
  const verdict = label(
    locale === 'es'
      ? '8 min despues: solo esta el TARJETON'
      : '8 min later: only the TRACER CARD',
    { size: 0.13, color: '#e8d8b0' },
  )
  verdict.position.set(x + 3.2, 2.7, z - 1.2)
  verdict.visible = false
  group.add(verdict)
  let searchT = -1
  interactables.push({
    id: 'past-search',
    x: x + 3.2,
    z: z - 1.2,
    radius: 2.2,
    label: SEARCH_FOLDER_LABEL,
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
      gap.rotation.z = Math.sin(t * 22) * 0.18
    } else if (elapsed < 5.5) {
      gap.rotation.z = 0
      verdict.visible = true
    } else {
      verdict.visible = false
      searchT = -1
    }
  })

  // Argenis (antes) de rodillas hurgando la estanteria derecha por la
  // carpeta que no aparece — el mismo archivista del presente
  const argenis = makeNpc({
    skin: '#b5825f',
    hair: { style: 'short', color: '#5a5a62' },
    top: '#6a6152',
    bottom: '#4a4438',
    faceSeed: 58,
    position: [x + 2.4, 0, z - 0.6],
    rotationY: Math.PI / 2,
    pose: 'kneel',
  })
  // Yuleima (antes) cargando las carpetas de los tres Perez entre el
  // archivo y la puerta — misma cara y peinado que su version de hoy
  const yuleima = makeNpc({
    skin: '#d9a684',
    hair: { style: 'ponytail', color: '#1c1410' },
    top: '#8a8270',
    bottom: '#5a5548',
    faceSeed: 45,
    position: [x - 1.6, 0, z + 0.4],
    path: [
      [x - 1.6, z + 0.4],
      [x + 1.2, z - 0.9],
      [x - 0.6, z + 1.4],
    ],
    speed: 0.55,
  })
  carryPapers(yuleima)
  // Petra en el escritorio de admision, entre el telefono y la cola
  const petra = makeNpc({
    skin: '#e8b48c',
    hair: { style: 'bun', color: '#3a2a1a' },
    top: '#7a6a58',
    bottom: '#4a4438',
    accessory: 'glasses',
    faceSeed: 29,
    position: [x - 0.4, 0, z + 1.45],
    rotationY: Math.PI,
  })
  npcs.push(argenis, yuleima, petra)
  const talks = [
    npcTalk({
      id: 'talk-past-ipasme-argenis',
      npc: argenis,
      dialog: IPASME_PASADO_DIALOGS.argenis,
      openDialog: actions.openDialog,
    }),
    npcTalk({
      id: 'talk-past-ipasme-yuleima',
      npc: yuleima,
      dialog: IPASME_PASADO_DIALOGS.yuleima,
      openDialog: actions.openDialog,
    }),
    npcTalk({
      id: 'talk-past-ipasme-petra',
      npc: petra,
      dialog: IPASME_PASADO_DIALOGS.petra,
      openDialog: actions.openDialog,
    }),
  ]
  for (const talk of talks) {
    interactables.push(talk.interactable)
    updates.push(talk.update)
  }

  const story = IPASME_STORY[locale]
  const panel = screenPanel({
    title: locale === 'es' ? 'historias en papel' : 'records on paper',
    lines:
      locale === 'es'
        ? [
            'carpeta: numerada a mano',
            'busqueda: varios minutos',
            'tarjeton mal puesto:',
            '  historia perdida',
            '',
            '[E] leer la historia',
          ]
        : [
            'folder: hand-numbered',
            'lookup: several minutes',
            'misplaced tracer card:',
            '  record lost',
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
