/**
 * @module rooms/past/corpoelec (engine)
 * @description El "antes" de CORPOELEC: oficina de planillas en papel.
 *   Buscar el equipo 0042 a mano (22 min, copia desactualizada), el
 *   archivador que se abre/cierra y oficinistas cargando/transcribiendo
 *   planillas. Etapa 2 (informe 08) lo refactoriza al nivel del presente.
 */
import { Group } from 'three'
import type { Box2 } from '../../../lib/collision'
import type { Locale } from '../../../lib/rooms'
import { sfx } from '../../audio'
import { makeNpc, type NpcHandle } from '../../character'
import { npcTalk } from '../../dialog'
import { CORPOELEC_PASADO_DIALOGS } from '../../dialogs/corpoelec-pasado'
import type { Interactable } from '../../state'
import { boxMesh, label, screenPanel, toonMat } from '../../toon'
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
  for (const dx of [-2.2, 0, 2.2]) {
    const stack = paperStack({ position: [x + dx, 0.76, z - 0.6], count: 12 })
    stacks.push(stack)
    group.add(desk({ position: [x + dx, 0, z - 0.6], color: '#4c4740' }), stack)
    colliders.push(footprint(x + dx, z - 0.6, 1.3, 0.8))
  }
  const cabinet = boxMesh(0.6, 1.8, 0.5, toonMat('#5a5750'))
  cabinet.position.set(x + 3.6, 0.9, z + 2.2)
  group.add(cabinet)
  colliders.push(footprint(x + 3.6, z + 2.2, 0.7, 0.6))

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

  // oficinista cargando planillas entre los escritorios y el archivador
  const carrier = makeNpc({
    skin: '#d9a684',
    hair: { style: 'bun', color: '#2a1c12' },
    top: '#8a8270',
    bottom: '#5a5548',
    faceSeed: 41,
    position: [x - 2.2, 0, z + 0.5],
    path: [
      [x - 2.2, z + 0.5],
      [x + 3.0, z + 1.8],
      [x + 0.3, z + 2.4],
    ],
    speed: 0.55,
  })
  carryPapers(carrier)
  // otro transcribiendo a mano en su escritorio
  const transcriber = makeNpc({
    skin: '#e8b48c',
    hair: { style: 'short', color: '#3a2a1a' },
    top: '#6a6152',
    bottom: '#4a4438',
    accessory: 'glasses',
    faceSeed: 53,
    position: [x, 0, z + 0.1],
    rotationY: Math.PI,
  })
  npcs.push(carrier, transcriber)
  const talks = [
    npcTalk({
      id: 'talk-past-corpoelec-planillas',
      npc: carrier,
      dialog: CORPOELEC_PASADO_DIALOGS['oficinista-planillas'],
      openDialog: actions.openDialog,
    }),
    npcTalk({
      id: 'talk-past-corpoelec-transcribe',
      npc: transcriber,
      dialog: CORPOELEC_PASADO_DIALOGS['oficinista-transcribe'],
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
