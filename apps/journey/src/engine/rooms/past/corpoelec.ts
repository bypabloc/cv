/**
 * @module rooms/past/corpoelec (engine)
 * @description El "antes" de CORPOELEC al nivel del canon (informe 08):
 *   oficina sepia de planillas en papel SIN el sistema. Tres escritorios
 *   rotulados SEDE YARACUY / CARABOBO / LARA con pilas de planillas
 *   duplicadas, el archivador saturado que se abre/cierra, y los MISMOS
 *   equipos que el presente guarda ordenados en cajas — walkie-talkies,
 *   radios, telefonos, una PC apagada — aqui regados por suelo y mesas
 *   sin etiqueta. Buscar el equipo 0042 a mano (22 min, copia
 *   desactualizada) como objeto de busqueda lenta. 3 NPCs frustrados
 *   conversables: Dubraska cargando planillas, Wilmer de rodillas
 *   hurgando el archivador por un radio sin registro, y el oficinista
 *   que transcribe seriales (el arco: Dubraska y Wilmer reaparecen en el
 *   presente usando el sistema).
 */
import { Group } from 'three'
import type { Box2 } from '../../../lib/collision'
import type { Locale } from '../../../lib/rooms'
import { sfx } from '../../audio'
import { makeNpc, type NpcHandle } from '../../character'
import { npcTalk } from '../../dialog'
import { CORPOELEC_PASADO_DIALOGS } from '../../dialogs/corpoelec-pasado'
import type { Interactable } from '../../state'
import {
  boxMesh,
  label,
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

const CORPOELEC_STORY: Record<Locale, { title: string; paragraphs: string[] }> =
  {
    es: {
      title: 'Antes del sistema (2013)',
      paragraphs: [
        'Cada sede llevaba su propia copia en papel del inventario: Yaracuy ' +
          'una, Carabobo otra distinta, y la de Lara aparecia... a veces. ' +
          'Nadie sabia cual valia.',
        'Localizar un equipo era abrir carpetas durante 20 minutos o mas — ' +
          'si el registro no estaba traspapelado o copiado con errores.',
        'Ese año un pasante propuso otra cosa: un sistema de inventario que ' +
          'funcionara aun sin conexion y sincronizara las 3 sedes en una ' +
          'sola base. Cruza de vuelta y lo ves funcionando.',
      ],
    },
    en: {
      title: 'Before the system (2013)',
      paragraphs: [
        'Each site kept its own paper copy of the inventory: Yaracuy had ' +
          'one, Carabobo a different one, and the Lara copy showed up... ' +
          'sometimes. Nobody knew which one was right.',
        'Locating an asset meant digging through folders for 20+ minutes — ' +
          'if the record was not misplaced or copied with errors.',
        'That year an intern proposed something else: an inventory system ' +
          'that worked even offline and kept the 3 sites in one database. ' +
          'Cross back and you can see it running.',
      ],
    },
  }

const SEARCH_PAPER_LABEL = {
  es: 'Buscar el equipo 0042 en las planillas',
  en: 'Search the paper records for asset 0042',
} as const

const DRAWER_LABEL_OPEN = {
  es: 'Abrir el archivador',
  en: 'Open the filing cabinet',
} as const

const DRAWER_LABEL_CLOSE = {
  es: 'Cerrar el archivador',
  en: 'Close the filing cabinet',
} as const

/** El "antes" de CORPOELEC: planillas duplicadas y busqueda a mano. */
export function corpoelecPast(
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
  const stacks: Group[] = []
  const sedeNames =
    locale === 'es'
      ? (['SEDE YARACUY', 'SEDE CARABOBO', 'SEDE LARA'] as const)
      : (['YARACUY SITE', 'CARABOBO SITE', 'LARA SITE'] as const)
  for (const [index, dx] of [-2.2, 0, 2.2].entries()) {
    const stack = paperStack({ position: [x + dx, 0.76, z - 0.6], count: 12 })
    stacks.push(stack)
    group.add(desk({ position: [x + dx, 0, z - 0.6], color: '#4c4740' }), stack)
    colliders.push(footprint(x + dx, z - 0.6, 1.3, 0.8))
    // cada escritorio es "una sede": la misma planilla copiada tres veces
    const sede = label(sedeNames[index] ?? '', {
      size: 0.12,
      color: '#e8d8b0',
    })
    sede.position.set(x + dx, 1.35, z - 0.6)
    group.add(sede)
  }
  const cabinet = boxMesh(0.6, 1.8, 0.5, toonMat('#5a5750'))
  cabinet.position.set(x + 3.6, 0.9, z + 2.2)
  group.add(cabinet)
  colliders.push(footprint(x + 3.6, z + 2.2, 0.7, 0.6))

  // los MISMOS equipos que el presente guarda etiquetados en cajas,
  // aqui regados por suelo y mesas sin orden ni etiqueta (1 lote sepia):
  // walkie-talkies, radio base, telefono descolgado, laptop gruesa y la
  // PC apagada polvorienta del rincon
  group.add(
    outlinedMergedBoxes(
      [
        // walkie tirado en el piso + su antena
        { w: 0.09, h: 0.06, d: 0.24, x: x - 1.1, y: 0.03, z: z + 1.4 },
        { w: 0.14, h: 0.02, d: 0.02, x: x - 0.95, y: 0.02, z: z + 1.5 },
        // radio base torcida sobre el escritorio central
        { w: 0.3, h: 0.12, d: 0.22, x: x + 0.45, y: 0.82, z: z - 0.75 },
        // telefono con el auricular descolgado al lado
        { w: 0.22, h: 0.08, d: 0.2, x: x - 2.6, y: 0.8, z: z - 0.4 },
        { w: 0.06, h: 0.05, d: 0.18, x: x - 2.38, y: 0.785, z: z - 0.32 },
        // laptop gruesa cerrada en el piso, contra una pata
        { w: 0.32, h: 0.06, d: 0.24, x: x + 1.5, y: 0.03, z: z + 0.2 },
        // PC de escritorio apagada y polvorienta en el rincon + monitor
        { w: 0.2, h: 0.52, d: 0.46, x: x - 3.4, y: 0.26, z: z + 2.3 },
        { w: 0.34, h: 0.3, d: 0.36, x: x - 3.35, y: 0.67, z: z + 2.3 },
      ],
      toonMat('#4a453c'),
      { castShadow: true },
    ),
  )
  colliders.push(footprint(x - 3.38, z + 2.3, 0.5, 0.6))

  // micro: buscar el 0042 a mano — las pilas tiemblan y el veredicto
  // flota unos segundos (papel = 20+ min y copia desactualizada)
  const verdict = label(
    locale === 'es'
      ? '22 min despues: copia DESACTUALIZADA'
      : '22 min later: an OUTDATED copy',
    { size: 0.13, color: '#e8d8b0' },
  )
  verdict.position.set(x, 1.5, z - 0.6)
  verdict.visible = false
  group.add(verdict)
  let searchT = -1
  interactables.push({
    id: 'past-search',
    x,
    z: z - 0.6,
    radius: 2.1,
    label: SEARCH_PAPER_LABEL,
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
      for (const [i, stack] of stacks.entries()) {
        stack.rotation.y = Math.sin(t * 24 + i * 2.1) * 0.08
      }
    } else if (elapsed < 5.5) {
      for (const stack of stacks) {
        stack.rotation.y = 0
      }
      verdict.visible = true
    } else {
      verdict.visible = false
      searchT = -1
    }
  })

  // micro: el archivador se abre/cierra (cajon deslizante + planillas)
  const drawer = boxMesh(0.5, 0.26, 0.45, toonMat('#4a4740'))
  drawer.position.set(x + 3.6, 1.2, z + 2.2)
  const drawerPapers = paperStack({
    position: [x + 3.6, 1.33, z + 1.88],
    count: 5,
  })
  drawerPapers.visible = false
  group.add(drawer, drawerPapers)
  let drawerOpen = false
  const drawerItem: Interactable = {
    id: 'past-drawer',
    x: x + 3.6,
    z: z + 2.2,
    radius: 2,
    label: { ...DRAWER_LABEL_OPEN },
    onActivate: () => {
      drawerOpen = !drawerOpen
      sfx.play('door')
      drawerItem.label = drawerOpen ? DRAWER_LABEL_CLOSE : DRAWER_LABEL_OPEN
    },
  }
  interactables.push(drawerItem)
  updates.push((_t, dt) => {
    const target = drawerOpen ? z + 2.2 - 0.42 : z + 2.2
    drawer.position.z += (target - drawer.position.z) * Math.min(1, dt * 6)
    drawerPapers.visible = drawerOpen && drawer.position.z < z + 2.2 - 0.3
  })

  // Dubraska (antes) cargando planillas entre los escritorios y el
  // archivador — misma cara y peinado que su version del presente
  const dubraska = makeNpc({
    skin: '#d9a684',
    hair: { style: 'ponytail', color: '#1c1410' },
    top: '#8a8270',
    bottom: '#5a5548',
    model: 'kate',
    faceSeed: 67,
    position: [x - 2.2, 0, z + 0.5],
    path: [
      [x - 2.2, z + 0.5],
      [x + 3.0, z + 1.8],
      [x + 0.3, z + 2.4],
    ],
    speed: 0.55,
  })
  carryPapers(dubraska)
  // el oficinista que transcribe seriales a mano en su escritorio
  const transcriber = makeNpc({
    skin: '#e8b48c',
    hair: { style: 'short', color: '#3a2a1a' },
    top: '#6a6152',
    bottom: '#4a4438',
    accessory: 'glasses',
    model: 'james',
    faceSeed: 53,
    position: [x, 0, z + 0.1],
    rotationY: Math.PI,
  })
  // Wilmer (antes) de rodillas frente al archivador, hurgando carpetas
  // por el radio que nadie registro — el mismo veterano del presente
  const wilmer = makeNpc({
    skin: '#b5825f',
    hair: { style: 'short', color: '#8a8a92' },
    top: '#6a6a52',
    bottom: '#4a4438',
    model: 'pete',
    faceSeed: 51,
    position: [x + 2.9, 0, z + 2.1],
    rotationY: Math.PI / 2,
    pose: 'kneel',
  })
  group.add(paperStack({ position: [x + 2.5, 0, z + 1.6], count: 8 }))
  npcs.push(dubraska, transcriber, wilmer)
  const talks = [
    npcTalk({
      id: 'talk-past-corpoelec-dubraska',
      npc: dubraska,
      dialog: CORPOELEC_PASADO_DIALOGS.dubraska,
      openDialog: actions.openDialog,
    }),
    npcTalk({
      id: 'talk-past-corpoelec-transcribe',
      npc: transcriber,
      dialog: CORPOELEC_PASADO_DIALOGS['oficinista-transcribe'],
      openDialog: actions.openDialog,
    }),
    npcTalk({
      id: 'talk-past-corpoelec-wilmer',
      npc: wilmer,
      dialog: CORPOELEC_PASADO_DIALOGS.wilmer,
      openDialog: actions.openDialog,
    }),
  ]
  for (const talk of talks) {
    interactables.push(talk.interactable)
    updates.push(talk.update)
  }

  const story = CORPOELEC_STORY[locale]
  const panel = screenPanel({
    title: locale === 'es' ? 'planillas duplicadas' : 'duplicated records',
    lines:
      locale === 'es'
        ? [
            'sede A: copia 1',
            'sede B: copia 2 (distinta)',
            'sede C: perdida',
            '',
            '[E] leer la historia',
          ]
        : [
            'site A: copy 1',
            'site B: copy 2 (different)',
            'site C: lost',
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
