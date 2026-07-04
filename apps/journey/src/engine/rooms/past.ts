/**
 * @module rooms/past (engine)
 * @description Mini-salas sepia del "antes" (portal al pasado), cada una
 *   con NPCs interactuando con los objetos: aula = el Pablo PRE-universidad
 *   (karate-do en el tatami, videojuegos en la PC — la pregunta semilla
 *   "¿como se hacen?" — y el trabajo de tecnico de aires acondicionados);
 *   corpoelec = oficina de planillas en papel; cima = procesos manuales.
 *   El shell (muros/piso/techo/luz) lo monta world; el look sepia lo remata
 *   el overlay CSS del HUD.
 */
import { type CanvasTexture, Group, Mesh, MeshBasicMaterial } from 'three'
import type { Box2 } from '../../lib/collision'
import type { Locale, RoomDef } from '../../lib/rooms'
import { makeNpc, type NpcHandle } from '../character'
import type { Interactable } from '../state'
import {
  boxMesh,
  disposeDeep,
  label,
  makeCanvasTexture,
  mergedBoxes,
  outlineGroup,
  screenPanel,
  toonMat,
  unitGeo,
} from '../toon'
import type { PastCtx, RoomBuild } from '../world'
import { desk, exitPortal, footprint, paperStack } from './props'

const PAST_SCREEN = { screenBg: '#2c2620', screenFg: '#b08a6a', ink: '#201a10' }

/** Escena del "antes" de una sala: props + colliders + NPCs en accion. */
interface PastSet {
  group: Group
  colliders: Box2[]
  npcs: NpcHandle[]
}

/** Pila de papeles cargada al frente del NPC (oficina pre-digital). */
function carryPapers(npc: NpcHandle): void {
  npc.group.add(paperStack({ position: [0, 1.02, 0.2], count: 6 }))
}

// ---------------------------------------------------------------------------
// Aula: el Pablo de ANTES de estudiar (no-tecnologico)
// ---------------------------------------------------------------------------

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

/** PC de escritorio noventera con el juego corriendo (CRT + tower). */
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

/** Rincon de tecnico A/C: unidad de muro abierta, otra en el piso, caja. */
function acCorner(x: number, z: number, colliders: Box2[]): Group {
  const group = new Group()
  // unidad montada en el muro derecho, con el panel frontal abierto
  const wallUnit = new Group()
  wallUnit.position.set(x + 2.8, 1.8, z + 1.2)
  wallUnit.rotation.y = -Math.PI / 2
  const body = boxMesh(1.05, 0.36, 0.24, toonMat('#cec8b4'))
  const vents = boxMesh(0.9, 0.08, 0.02, toonMat('#5a5244'))
  vents.position.set(0, -0.08, 0.13)
  vents.userData.noOutline = true
  const openPanel = boxMesh(0.95, 0.3, 0.02, toonMat('#bdb6a0'))
  openPanel.position.set(0, -0.3, 0.16)
  openPanel.rotation.x = 0.85
  wallUnit.add(body, vents, openPanel)
  // unidad en el piso a medio desarmar + tapa apoyada + caja de herramientas
  const floorUnit = boxMesh(0.95, 0.34, 0.32, toonMat('#b8b0a0'))
  floorUnit.position.set(x + 2.3, 0.17, z + 1.2)
  const lid = boxMesh(0.9, 0.02, 0.3, toonMat('#a8a090'))
  lid.position.set(x + 1.72, 0.4, z + 1.35)
  lid.rotation.z = 1.25
  const toolbox = mergedBoxes(
    [
      { w: 0.42, h: 0.2, d: 0.24, x: 0, y: 0.1, z: 0 },
      { w: 0.3, h: 0.05, d: 0.05, x: 0, y: 0.28, z: 0 },
    ],
    toonMat('#8a4a3a'),
  )
  toolbox.position.set(x + 2.3, 0, z + 0.55)
  group.add(wallUnit, floorUnit, lid, toolbox)
  colliders.push(
    footprint(x + 2.3, z + 1.2, 1.05, 0.5),
    footprint(x + 2.3, z + 0.55, 0.5, 0.35),
  )
  return group
}

/**
 * El "antes" del aula: Pablo pre-uni. Karate-do (el mismo, con gi y
 * cinturon, en kihon contra el makiwara), un amigo jugando en su PC (la
 * pregunta que desperto todo: ¿como se HACEN los juegos?) y el rincon del
 * trabajo de tecnico de aires acondicionados que pagaba la universidad.
 */
function aulaPast(
  x: number,
  z: number,
  depth: number,
  locale: Locale,
): PastSet {
  const group = new Group()
  const colliders: Box2[] = []
  const npcs: NpcHandle[] = []

  // --- karate-do: tatami + makiwara + el Pablo de antes en kihon
  const tatami = new Mesh(unitGeo().plane, toonMat('#6a5c40'))
  tatami.rotation.x = -Math.PI / 2
  tatami.scale.set(2.2, 2.8, 1)
  tatami.position.set(x - 1.7, 0.012, z - 0.2)
  tatami.userData.noOutline = true
  const makiwara = mergedBoxes(
    [
      { w: 0.14, h: 1.5, d: 0.14, x: 0, y: 0.75, z: 0 },
      { w: 0.3, h: 0.4, d: 0.09, x: 0, y: 1.2, z: 0.1 },
    ],
    toonMat('#8a7050'),
  )
  makiwara.position.set(x - 1.7, 0, z - 1.6)
  group.add(tatami, makiwara)
  colliders.push(footprint(x - 1.7, z - 1.6, 0.4, 0.35))
  const karateka = makeNpc({
    skin: '#e8b48c',
    hair: { style: 'short', color: '#181410' },
    top: '#eae6da',
    bottom: '#eae6da',
    faceSeed: 5, // la misma cara del jugador: es el
    position: [x - 1.7, 0, z + 0.6],
    path: [
      [x - 1.7, z + 0.6],
      [x - 1.7, z - 0.85],
    ],
    speed: 0.9,
  })
  const belt = boxMesh(0.36, 0.07, 0.24, toonMat('#141018'))
  belt.position.y = 0.62
  belt.userData.noOutline = true
  karateka.group.add(belt)
  npcs.push(karateka)

  // --- videojuegos: la PC con el shooter corriendo + un amigo jugando
  group.add(
    desk({
      position: [x + 1.9, 0, z - 1.4],
      rotationY: -Math.PI / 2,
      width: 1.3,
      color: '#4a3b2a',
    }),
  )
  colliders.push(footprint(x + 1.9, z - 1.4, 0.8, 1.5))
  const pc = gamingPc()
  pc.position.set(x + 1.9, 0.75, z - 1.4)
  pc.rotation.y = -Math.PI / 2
  group.add(pc)
  const tower = boxMesh(0.22, 0.5, 0.42, toonMat('#b8b098'))
  tower.position.set(x + 1.95, 0.25, z - 0.5)
  group.add(tower)
  colliders.push(footprint(x + 1.95, z - 0.5, 0.3, 0.5))
  npcs.push(
    makeNpc({
      skin: '#c98f6a',
      hair: { style: 'spiky', color: '#2a1c10' },
      top: '#7a5c48',
      bottom: '#4a4438',
      faceSeed: 29,
      position: [x + 1.15, 0, z - 1.4],
      rotationY: Math.PI / 2,
    }),
  )
  // la pregunta que lo cambio todo, flotando sobre la pantalla
  const seed = label(
    locale === 'es' ? '¿como se HACEN los juegos?' : 'how are games MADE?',
    { size: 0.14, color: '#e8d8b0' },
  )
  seed.position.set(x + 1.7, 1.9, z - 1.4)
  seed.rotation.y = -Math.PI / 2
  group.add(seed)

  // --- aires acondicionados: el trabajo que pagaba la universidad
  group.add(acCorner(x, z, colliders))

  const panel = screenPanel({
    title: locale === 'es' ? 'antes de la uni' : 'before uni',
    lines:
      locale === 'es'
        ? [
            'karate-do: disciplina',
            'videojuegos: ¿como se hacen?',
            'aires A/C: pagando la uni',
          ]
        : [
            'karate-do: discipline',
            'video games: how are they made?',
            'AC repair: paying for uni',
          ],
    theme: PAST_SCREEN,
    width: 1.8,
    height: 1.1,
  })
  panel.position.set(x, 1.6, z - depth / 2 + 0.12)
  group.add(panel)
  return { group, colliders, npcs }
}

// ---------------------------------------------------------------------------
// Corpoelec: oficina de planillas en papel
// ---------------------------------------------------------------------------

function corpoelecPast(x: number, z: number, depth: number): PastSet {
  const group = new Group()
  const colliders: Box2[] = []
  const npcs: NpcHandle[] = []
  for (const dx of [-1.4, 0, 1.4]) {
    group.add(
      desk({ position: [x + dx, 0, z - 0.4], color: '#4c4740' }),
      paperStack({ position: [x + dx, 0.76, z - 0.4], count: 12 }),
    )
    colliders.push(footprint(x + dx, z - 0.4, 1.3, 0.8))
  }
  const cabinet = boxMesh(0.6, 1.8, 0.5, toonMat('#5a5750'))
  cabinet.position.set(x + 2.5, 0.9, z + 1.6)
  group.add(cabinet)
  colliders.push(footprint(x + 2.5, z + 1.6, 0.7, 0.6))
  // oficinista cargando planillas entre los escritorios y el archivador
  const carrier = makeNpc({
    skin: '#d9a684',
    hair: { style: 'bun', color: '#2a1c12' },
    top: '#8a8270',
    bottom: '#5a5548',
    faceSeed: 41,
    position: [x - 1.4, 0, z + 0.5],
    path: [
      [x - 1.4, z + 0.5],
      [x + 2.1, z + 1.2],
      [x + 0.2, z + 1.6],
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
      position: [x, 0, z + 0.3],
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
  return { group, colliders, npcs }
}

// ---------------------------------------------------------------------------
// Cima: procesos manuales, un solo pais
// ---------------------------------------------------------------------------

function cimaPast(x: number, z: number, depth: number): PastSet {
  const group = new Group()
  const colliders: Box2[] = []
  const npcs: NpcHandle[] = []
  group.add(
    desk({ position: [x, 0, z - 0.4], width: 1.6, color: '#3c3a44' }),
    paperStack({ position: [x - 0.4, 0.76, z - 0.4], count: 16 }),
  )
  colliders.push(footprint(x, z - 0.4, 1.7, 0.8))
  // telefono de escritorio: la "integracion" de la epoca
  const phone = mergedBoxes(
    [
      { w: 0.18, h: 0.05, d: 0.12, x: 0, y: 0.025, z: 0 },
      { w: 0.2, h: 0.05, d: 0.07, x: 0, y: 0.085, z: 0 },
    ],
    toonMat('#3a3630'),
  )
  phone.position.set(x + 0.45, 0.755, z - 0.5)
  group.add(phone)
  // operador al telefono + alguien corriendo con papeles entre areas
  const runner = makeNpc({
    skin: '#c98f6a',
    hair: { style: 'ponytail', color: '#1c1410' },
    top: '#5a5548',
    bottom: '#3a3630',
    faceSeed: 61,
    position: [x - 2, 0, z + 1.6],
    path: [
      [x - 2, z + 1.6],
      [x + 2, z + 1.2],
      [x + 1.4, z - 1.2],
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
      position: [x + 0.5, 0, z + 0.3],
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
  return { group, colliders, npcs }
}

function buildSet(
  def: RoomDef,
  x: number,
  z: number,
  depth: number,
  locale: Locale,
): PastSet {
  if (def.id === 'aula') {
    return aulaPast(x, z, depth, locale)
  }
  if (def.id === 'corpoelec') {
    return corpoelecPast(x, z, depth)
  }
  return cimaPast(x, z, depth)
}

export default function buildPast(ctx: PastCtx): RoomBuild {
  const { def, pastRoom, state, actions, returnTo } = ctx
  const group = new Group()
  const interactables: Interactable[] = []
  const updates: ((t: number, dt: number) => void)[] = []

  // cartel ANTES · {año} cerca del techo, mirando a la entrada
  const sign = label(
    state.locale === 'es' ? `ANTES · ${def.year}` : `BEFORE · ${def.year}`,
    { size: 0.3, color: '#c8a878' },
  )
  sign.position.set(
    pastRoom.x,
    pastRoom.height - 0.5,
    pastRoom.z + pastRoom.depth / 2 - 0.3,
  )
  sign.rotation.y = Math.PI
  group.add(sign)

  const set = buildSet(
    def,
    pastRoom.x,
    pastRoom.z,
    pastRoom.depth,
    state.locale,
  )
  group.add(set.group)
  for (const npc of set.npcs) {
    group.add(npc.group)
    updates.push((t, dt) => npc.update(t, dt))
  }

  const exit = exitPortal({
    roomIndex: pastRoom.index,
    position: [pastRoom.x, 0, pastRoom.z + pastRoom.depth / 2 - 0.6],
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
