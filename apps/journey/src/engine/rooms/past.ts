/**
 * @module rooms/past (engine)
 * @description Mini-salas sepia del "antes" (portal al pasado, 9x9), cada
 *   una con NPCs interactuando con los objetos: aula = el Pablo
 *   PRE-universidad (kihon de karate contra el makiwara, un amigo jugando
 *   en la PC — la pregunta semilla "¿como se hacen?" — y un tecnico
 *   reparando el aire acondicionado, que se puede ENCENDER con E);
 *   corpoelec = oficina de planillas en papel; cima = procesos manuales.
 *   El panel "antes de la uni" se expande con E a la historia completa.
 *   El shell lo monta world; el look sepia lo remata el overlay del HUD.
 */
import { type CanvasTexture, Group, Mesh, MeshBasicMaterial } from 'three'
import type { Box2 } from '../../lib/collision'
import type { Locale } from '../../lib/rooms'
import { makeNpc, type NpcHandle } from '../character'
import type { EngineState, Interactable } from '../state'
import { unregisterInteractable } from '../state'
import {
  boxMesh,
  disposeDeep,
  label,
  makeCanvasTexture,
  mergedBoxes,
  outlineGroup,
  screenPanel,
  toonMat,
  toonMatOwn,
  unitGeo,
} from '../toon'
import type { PastCtx, RoomBuild } from '../world'
import { chair, desk, exitPortal, footprint, paperStack } from './props'

const PAST_SCREEN = { screenBg: '#2c2620', screenFg: '#b08a6a', ink: '#201a10' }

/** Escena del "antes" de una sala: props + colliders + NPCs en accion. */
interface PastSet {
  group: Group
  colliders: Box2[]
  npcs: NpcHandle[]
  interactables: Interactable[]
  updates: ((t: number, dt: number) => void)[]
}

/** Pila de papeles cargada al frente del NPC (oficina pre-digital). */
function carryPapers(npc: NpcHandle): void {
  npc.group.add(paperStack({ position: [0, 1.02, 0.2], count: 6 }))
}

// ---------------------------------------------------------------------------
// Aula: el Pablo de ANTES de estudiar (no-tecnologico)
// ---------------------------------------------------------------------------

/** La historia completa detras del panel (se abre con E). */
const STORY: Record<Locale, { title: string; paragraphs: string[] }> = {
  es: {
    title: 'Antes de la universidad',
    paragraphs: [
      'Practicaba Karate-Do: la disciplina y la constancia de repetir un ' +
        'golpe mil veces me marcaron mas que cualquier manual.',
      'Pasaba horas jugando videojuegos en la PC. Un dia la pregunta ' +
        'cambio: ya no era "¿como se gana?" sino "¿como se HACE esto?". ' +
        'Esa curiosidad fue la semilla de la programacion.',
      'Trabajaba como tecnico de aires acondicionados para pagarme la ' +
        'universidad: diagnosticar, desarmar, reparar. Sin saberlo, ya ' +
        'estaba debuggeando.',
    ],
  },
  en: {
    title: 'Before university',
    paragraphs: [
      'I practiced Karate-Do: the discipline of repeating a strike a ' +
        'thousand times taught me more than any manual.',
      'I spent hours playing PC video games. One day the question ' +
        'changed: not "how do I win?" but "how is this MADE?". That ' +
        'curiosity was the seed of programming.',
      'I worked as an air-conditioning technician to pay for university: ' +
        'diagnose, take apart, repair. I was already debugging without ' +
        'knowing it.',
    ],
  },
}

const STORY_LABEL = {
  es: 'Leer mi historia',
  en: 'Read my story',
} as const

const AC_LABEL = {
  es: 'Encender el aire acondicionado',
  en: 'Power on the AC unit',
} as const

/** Pantalla de la PC de juegos: shooter retro pixel-art (la semilla). */
function gameTexture(): CanvasTexture {
  return makeCanvasTexture(256, (ctx, size) => {
    ctx.fillStyle = '#0c0a14'
    ctx.fillRect(0, 0, size, size)
    const rows: readonly string[] = ['#c86a4a', '#c8a04a', '#7aa04a']
    rows.forEach((color, row) => {
      ctx.fillStyle = color
      for (let col = 0; col < 6; col += 1) {
        const x = 34 + col * 34
        const y = 52 + row * 30
        ctx.fillRect(x, y, 18, 12)
        ctx.fillRect(x + 3, y - 5, 12, 5)
      }
    })
    // nave del jugador + disparo en vuelo
    ctx.fillStyle = '#e8d8b0'
    ctx.fillRect(118, 210, 22, 10)
    ctx.fillRect(126, 202, 6, 8)
    ctx.fillRect(128, 162, 3, 22)
    ctx.font = 'bold 16px monospace'
    ctx.fillStyle = '#b08a6a'
    ctx.fillText('SCORE 12500', 20, 26)
    ctx.fillText('HI 99999', 164, 26)
  })
}

/** PC de escritorio noventera con el juego corriendo (CRT + teclado). */
function gamingPc(): Group {
  const group = new Group()
  const body = mergedBoxes(
    [
      { w: 0.52, h: 0.4, d: 0.16, x: 0, y: 0.28, z: 0.02 },
      { w: 0.4, h: 0.32, d: 0.26, x: 0, y: 0.28, z: -0.16 },
      { w: 0.28, h: 0.06, d: 0.26, x: 0, y: 0.03, z: -0.05 },
      // teclado al frente
      { w: 0.42, h: 0.03, d: 0.16, x: 0, y: 0.015, z: 0.28 },
    ],
    toonMat('#c8c0a8'),
  )
  const screen = new Mesh(
    unitGeo().plane,
    new MeshBasicMaterial({ map: gameTexture() }),
  )
  screen.scale.set(0.42, 0.3, 1)
  screen.position.set(0, 0.28, 0.105)
  screen.userData.noOutline = true
  group.add(body, screen)
  return group
}

/**
 * Rincon de tecnico A/C: unidad de muro con el panel abierto (se puede
 * ENCENDER con E: LED verde + el panel se cierra), otra unidad a medio
 * desarmar en el piso y la caja de herramientas.
 */
function acCorner(
  x: number,
  z: number,
  state: EngineState,
  colliders: Box2[],
): {
  group: Group
  interactable: Interactable
  update(t: number, dt: number): void
} {
  const group = new Group()
  // unidad montada en el muro derecho, con el panel frontal abierto
  const wallUnit = new Group()
  wallUnit.position.set(x + 4.3, 1.8, z + 1.8)
  wallUnit.rotation.y = -Math.PI / 2
  const body = boxMesh(1.05, 0.36, 0.24, toonMat('#cec8b4'))
  const vents = boxMesh(0.9, 0.08, 0.02, toonMat('#5a5244'))
  vents.position.set(0, -0.08, 0.13)
  vents.userData.noOutline = true
  const openPanel = boxMesh(0.95, 0.3, 0.02, toonMat('#bdb6a0'))
  openPanel.position.set(0, -0.3, 0.16)
  openPanel.rotation.x = 0.85
  const ledMat = toonMatOwn('#b23a3a', {
    emissive: '#b23a3a',
    emissiveIntensity: 1.1,
  })
  const led = new Mesh(unitGeo().sphere, ledMat)
  led.scale.setScalar(0.05)
  led.position.set(0.42, 0.1, 0.14)
  led.userData.noOutline = true
  wallUnit.add(body, vents, openPanel, led)
  // unidad en el piso a medio desarmar + tapa apoyada + herramientas
  const floorUnit = boxMesh(0.95, 0.34, 0.32, toonMat('#b8b0a0'))
  floorUnit.position.set(x + 3.5, 0.17, z + 1.8)
  const lid = boxMesh(0.9, 0.02, 0.3, toonMat('#a8a090'))
  lid.position.set(x + 2.95, 0.4, z + 2.05)
  lid.rotation.z = 1.25
  lid.userData.noOutline = true
  const toolbox = mergedBoxes(
    [
      { w: 0.42, h: 0.2, d: 0.24, x: 0, y: 0.1, z: 0 },
      { w: 0.3, h: 0.05, d: 0.05, x: 0, y: 0.28, z: 0 },
    ],
    toonMat('#8a4a3a'),
  )
  toolbox.position.set(x + 3.5, 0, z + 1.1)
  group.add(wallUnit, floorUnit, lid, toolbox)
  colliders.push(
    footprint(x + 3.5, z + 1.8, 1.05, 0.5),
    footprint(x + 3.5, z + 1.1, 0.5, 0.35),
  )
  let powered = false
  return {
    group,
    interactable: {
      id: 'past-ac',
      x: x + 3.9,
      z: z + 1.8,
      radius: 2,
      label: AC_LABEL,
      onActivate: () => {
        powered = true
        ledMat.color.set('#4dcc7a')
        ledMat.emissive.set('#4dcc7a')
        unregisterInteractable(state, 'past-ac')
      },
    },
    update: (_t, dt) => {
      // reparado y encendido: el panel frontal se cierra suave
      if (powered && openPanel.rotation.x > 0.06) {
        openPanel.rotation.x = Math.max(0.06, openPanel.rotation.x - dt * 1.1)
      }
    },
  }
}

/**
 * El "antes" del aula: Pablo pre-uni. Kihon de karate contra el makiwara,
 * un amigo jugando en su PC (la pregunta que desperto todo) y el trabajo
 * de tecnico de aires acondicionados que pagaba la universidad.
 */
function aulaPast(
  x: number,
  z: number,
  depth: number,
  locale: Locale,
  state: EngineState,
  actions: PastCtx['actions'],
): PastSet {
  const group = new Group()
  const colliders: Box2[] = []
  const npcs: NpcHandle[] = []
  const interactables: Interactable[] = []
  const updates: ((t: number, dt: number) => void)[] = []

  // --- karate-do: tatami + makiwara + el Pablo de antes en kihon
  const tatami = new Mesh(unitGeo().plane, toonMat('#6a5c40'))
  tatami.rotation.x = -Math.PI / 2
  tatami.scale.set(3, 3.4, 1)
  tatami.position.set(x - 2.6, 0.012, z - 0.8)
  tatami.userData.noOutline = true
  const makiwara = mergedBoxes(
    [
      { w: 0.14, h: 1.5, d: 0.14, x: 0, y: 0.75, z: 0 },
      { w: 0.3, h: 0.4, d: 0.09, x: 0, y: 1.2, z: 0.1 },
    ],
    toonMat('#8a7050'),
  )
  makiwara.position.set(x - 2.6, 0, z - 2.7)
  group.add(tatami, makiwara)
  colliders.push(footprint(x - 2.6, z - 2.7, 0.4, 0.35))
  const karateka = makeNpc({
    skin: '#e8b48c',
    hair: { style: 'short', color: '#181410' },
    top: '#eae6da',
    bottom: '#eae6da',
    faceSeed: 5, // la misma cara del jugador: es el
    position: [x - 2.6, 0, z - 1.9],
    rotationY: Math.PI,
    pose: 'fight',
  })
  const belt = boxMesh(0.36, 0.07, 0.24, toonMat('#141018'))
  belt.position.y = 0.62
  belt.userData.noOutline = true
  karateka.group.add(belt)
  npcs.push(karateka)

  // --- videojuegos: la PC con el shooter corriendo + un amigo SENTADO
  group.add(
    desk({
      position: [x + 3.2, 0, z - 2.4],
      rotationY: -Math.PI / 2,
      width: 1.3,
      color: '#4a3b2a',
    }),
  )
  colliders.push(footprint(x + 3.2, z - 2.4, 0.8, 1.5))
  const pc = gamingPc()
  pc.position.set(x + 3.2, 0.75, z - 2.4)
  pc.rotation.y = -Math.PI / 2
  group.add(pc)
  const tower = boxMesh(0.22, 0.5, 0.42, toonMat('#b8b098'))
  tower.position.set(x + 3.25, 0.25, z - 1.5)
  group.add(tower)
  colliders.push(footprint(x + 3.25, z - 1.5, 0.3, 0.5))
  group.add(
    chair({
      position: [x + 2.6, 0, z - 2.4],
      rotationY: Math.PI / 2,
      color: '#4a3b2a',
    }),
  )
  npcs.push(
    makeNpc({
      skin: '#c98f6a',
      hair: { style: 'spiky', color: '#2a1c10' },
      top: '#7a5c48',
      bottom: '#4a4438',
      faceSeed: 29,
      position: [x + 2.6, 0, z - 2.4],
      rotationY: Math.PI / 2,
      pose: 'sit',
    }),
  )
  // la pregunta que lo cambio todo, flotando sobre la pantalla
  const seed = label(
    locale === 'es' ? '¿como se HACEN los juegos?' : 'how are games MADE?',
    { size: 0.14, color: '#e8d8b0' },
  )
  seed.position.set(x + 2.9, 1.95, z - 2.4)
  seed.rotation.y = -Math.PI / 2
  group.add(seed)

  // --- aires acondicionados: tecnico arrodillado reparando + encendido
  const ac = acCorner(x, z, state, colliders)
  group.add(ac.group)
  interactables.push(ac.interactable)
  updates.push(ac.update)
  npcs.push(
    makeNpc({
      skin: '#d9a684',
      hair: { style: 'short', color: '#2a1c12' },
      top: '#5a6a73',
      bottom: '#3a4048',
      faceSeed: 47,
      position: [x + 2.95, 0, z + 1.8],
      rotationY: Math.PI / 2,
      pose: 'kneel',
    }),
  )

  // panel-resumen: se expande con E a la historia completa (DOM)
  const story = STORY[locale]
  const panel = screenPanel({
    title: locale === 'es' ? 'antes de la uni' : 'before uni',
    lines:
      locale === 'es'
        ? [
            'karate-do: disciplina',
            'videojuegos: ¿como se hacen?',
            'aires A/C: pagando la uni',
            '',
            '[E] leer la historia',
          ]
        : [
            'karate-do: discipline',
            'video games: how are they made?',
            'AC repair: paying for uni',
            '',
            '[E] read the story',
          ],
    theme: PAST_SCREEN,
    width: 2,
    height: 1.25,
  })
  panel.position.set(x, 1.7, z - depth / 2 + 0.12)
  group.add(panel)
  interactables.push({
    id: 'past-story',
    x,
    z: z - depth / 2 + 0.5,
    radius: 2.4,
    label: STORY_LABEL,
    onActivate: () => actions.openStory(story.title, story.paragraphs),
  })
  return { group, colliders, npcs, interactables, updates }
}

// ---------------------------------------------------------------------------
// Corpoelec: oficina de planillas en papel
// ---------------------------------------------------------------------------

function corpoelecPast(x: number, z: number, depth: number): PastSet {
  const group = new Group()
  const colliders: Box2[] = []
  const npcs: NpcHandle[] = []
  for (const dx of [-2.2, 0, 2.2]) {
    group.add(
      desk({ position: [x + dx, 0, z - 0.6], color: '#4c4740' }),
      paperStack({ position: [x + dx, 0.76, z - 0.6], count: 12 }),
    )
    colliders.push(footprint(x + dx, z - 0.6, 1.3, 0.8))
  }
  const cabinet = boxMesh(0.6, 1.8, 0.5, toonMat('#5a5750'))
  cabinet.position.set(x + 3.6, 0.9, z + 2.2)
  group.add(cabinet)
  colliders.push(footprint(x + 3.6, z + 2.2, 0.7, 0.6))
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
  npcs.push(
    carrier,
    // otro transcribiendo a mano en su escritorio
    makeNpc({
      skin: '#e8b48c',
      hair: { style: 'short', color: '#3a2a1a' },
      top: '#6a6152',
      bottom: '#4a4438',
      accessory: 'glasses',
      faceSeed: 53,
      position: [x, 0, z + 0.1],
      rotationY: Math.PI,
    }),
  )
  const panel = screenPanel({
    title: 'planillas duplicadas',
    lines: ['sede A: copia 1', 'sede B: copia 2 (distinta)', 'sede C: perdida'],
    theme: PAST_SCREEN,
    width: 1.8,
    height: 1.1,
  })
  panel.position.set(x, 1.6, z - depth / 2 + 0.12)
  group.add(panel)
  return { group, colliders, npcs, interactables: [], updates: [] }
}

// ---------------------------------------------------------------------------
// Cima: procesos manuales, un solo pais
// ---------------------------------------------------------------------------

function cimaPast(x: number, z: number, depth: number): PastSet {
  const group = new Group()
  const colliders: Box2[] = []
  const npcs: NpcHandle[] = []
  group.add(
    desk({ position: [x, 0, z - 0.6], width: 1.6, color: '#3c3a44' }),
    paperStack({ position: [x - 0.4, 0.76, z - 0.6], count: 16 }),
  )
  colliders.push(footprint(x, z - 0.6, 1.7, 0.8))
  // telefono de escritorio: la "integracion" de la epoca
  const phone = mergedBoxes(
    [
      { w: 0.18, h: 0.05, d: 0.12, x: 0, y: 0.025, z: 0 },
      { w: 0.2, h: 0.05, d: 0.07, x: 0, y: 0.085, z: 0 },
    ],
    toonMat('#3a3630'),
  )
  phone.position.set(x + 0.45, 0.755, z - 0.7)
  group.add(phone)
  // operador al telefono + alguien corriendo con papeles entre areas
  const runner = makeNpc({
    skin: '#c98f6a',
    hair: { style: 'ponytail', color: '#1c1410' },
    top: '#5a5548',
    bottom: '#3a3630',
    faceSeed: 61,
    position: [x - 3, 0, z + 2.2],
    path: [
      [x - 3, z + 2.2],
      [x + 3, z + 1.6],
      [x + 2, z - 1.8],
    ],
    speed: 1.15,
  })
  carryPapers(runner)
  npcs.push(
    runner,
    makeNpc({
      skin: '#e8b48c',
      hair: { style: 'bun', color: '#3a2a1a' },
      top: '#6a5c48',
      bottom: '#4a4438',
      accessory: 'tie',
      faceSeed: 73,
      position: [x + 0.5, 0, z + 0.1],
      rotationY: Math.PI,
    }),
  )
  const panel = screenPanel({
    title: 'procesos manuales',
    lines: [
      'admin de campanas: horas',
      'servicios sin orquestar',
      'un solo pais, silos',
    ],
    theme: PAST_SCREEN,
    width: 2,
    height: 1.1,
  })
  panel.position.set(x, 1.6, z - depth / 2 + 0.12)
  group.add(panel)
  return { group, colliders, npcs, interactables: [], updates: [] }
}

function buildSet(ctx: PastCtx): PastSet {
  const { def, pastRoom, state, actions } = ctx
  const { x, z, depth } = pastRoom
  if (def.id === 'aula') {
    return aulaPast(x, z, depth, state.locale, state, actions)
  }
  if (def.id === 'corpoelec') {
    return corpoelecPast(x, z, depth)
  }
  return cimaPast(x, z, depth)
}

export default function buildPast(ctx: PastCtx): RoomBuild {
  const { pastRoom, state, actions, returnTo } = ctx
  const group = new Group()
  const updates: ((t: number, dt: number) => void)[] = []

  // (el año lo dice el letrero del portal + el caption del HUD)
  const set = buildSet(ctx)
  group.add(set.group)
  const interactables: Interactable[] = [...set.interactables]
  updates.push(...set.updates)
  for (const npc of set.npcs) {
    group.add(npc.group)
    updates.push((t, dt) => npc.update(t, dt))
  }

  // portal de salida PEGADO al muro trasero, mirando a la sala
  const exit = exitPortal({
    roomIndex: pastRoom.index,
    position: [pastRoom.x, 0, pastRoom.z + pastRoom.depth / 2 - 0.15],
    rotationY: Math.PI,
    locale: state.locale,
    onExit: () => actions.exitPast(returnTo),
  })
  group.add(exit.group)
  if (exit.interactable) {
    interactables.push(exit.interactable)
  }
  if (exit.update) {
    updates.push(exit.update)
  }

  outlineGroup(group, 1.03)

  return {
    group,
    interactables,
    colliders: () => [
      ...set.colliders,
      ...set.npcs.map((npc) => npc.collider()),
    ],
    update: (t, dt) => {
      for (const fn of updates) {
        fn(t, dt)
      }
    },
    dispose: () => {
      for (const npc of set.npcs) {
        npc.dispose()
      }
      disposeDeep(group)
    },
  }
}
