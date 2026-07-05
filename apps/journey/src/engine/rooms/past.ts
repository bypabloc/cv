/**
 * @module rooms/past (engine)
 * @description Mini-salas sepia del "antes" (portal al pasado, 9x9), las
 *   TRES con paridad de interacciones: NPCs conversables con E (arboles de
 *   dialogo de dialogs/*-pasado), panel que expande la historia completa y
 *   micro-interacciones tematicas. Aula = el Pablo PRE-uni (salta al
 *   hablarle, kihon contra el makiwara), el amigo gamer y el tecnico con
 *   el A/C encendible/apagable. Corpoelec = buscar el 0042 entre planillas
 *   (22 min) + archivador que se abre. Cima = el telefono-integracion que
 *   suena + la pila del admin manual. El shell lo monta world; el look
 *   sepia lo remata el overlay del HUD.
 */
import {
  CanvasTexture,
  Group,
  Mesh,
  MeshBasicMaterial,
  SRGBColorSpace,
} from 'three'
import type { Box2 } from '../../lib/collision'
import type { Locale } from '../../lib/rooms'
import { sfx } from '../audio'
import { makeNpc, type NpcHandle } from '../character'
import { npcTalk } from '../dialog'
import { AULA_PASADO_DIALOGS } from '../dialogs/aula-pasado'
import { CIMA_PASADO_DIALOGS } from '../dialogs/cima-pasado'
import { CORPOELEC_PASADO_DIALOGS } from '../dialogs/corpoelec-pasado'
import type { Interactable } from '../state'
import {
  basicMat,
  boxMesh,
  disposeDeep,
  label,
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

const PAST_STORY_LABEL = {
  es: 'Leer la historia',
  en: 'Read the story',
} as const

const AC_LABEL_ON = {
  es: 'Encender el aire acondicionado',
  en: 'Power on the AC unit',
} as const

const AC_LABEL_OFF = {
  es: 'Apagar el aire acondicionado',
  en: 'Power off the AC unit',
} as const

interface AnimatedScreen {
  texture: CanvasTexture
  update(t: number): void
}

/**
 * Pantalla de la PC de juegos: homenaje procedural a GTA San Andreas
 * (2004, la epoca): tercera persona con el personaje de espaldas, calle
 * con un auto CRUZANDO, palmeras y el HUD clasico — radar circular
 * abajo-izquierda con blip parpadeante, hora, dinero verde y barras de
 * vida/chaleco. Redibuja el canvas ~8 fps (256px, costo trivial).
 */
function gtaScreen(): AnimatedScreen {
  const size = 256
  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = size
  const maybeCtx = canvas.getContext('2d')
  if (!maybeCtx) {
    throw new Error('past: canvas 2d context no disponible')
  }
  const ctx = maybeCtx
  const texture = new CanvasTexture(canvas)
  texture.colorSpace = SRGBColorSpace
  let last = -1

  function draw(t: number): void {
    // atardecer naranja (Los Santos vibes)
    ctx.fillStyle = '#e0904e'
    ctx.fillRect(0, 0, size, 78)
    ctx.fillStyle = '#ecb066'
    ctx.fillRect(0, 78, size, 30)
    ctx.fillStyle = '#f7e6b0'
    ctx.beginPath()
    ctx.arc(198, 56, 15, 0, Math.PI * 2)
    ctx.fill()
    // skyline en silueta
    ctx.fillStyle = '#5a4458'
    ctx.fillRect(8, 62, 26, 46)
    ctx.fillRect(44, 48, 20, 60)
    ctx.fillRect(72, 70, 30, 38)
    ctx.fillRect(150, 66, 22, 42)
    // palmeras
    ctx.strokeStyle = '#3a2c28'
    ctx.lineWidth = 5
    ctx.lineCap = 'round'
    for (const px of [122, 236]) {
      ctx.beginPath()
      ctx.moveTo(px, 108)
      ctx.lineTo(px - 4, 58)
      ctx.stroke()
      ctx.strokeStyle = '#3f6a38'
      ctx.lineWidth = 4
      for (const dir of [-1, -0.4, 0.4, 1]) {
        ctx.beginPath()
        ctx.moveTo(px - 4, 58)
        ctx.quadraticCurveTo(px - 4 + dir * 14, 48, px - 4 + dir * 22, 56)
        ctx.stroke()
      }
      ctx.strokeStyle = '#3a2c28'
      ctx.lineWidth = 5
    }
    // calle + linea discontinua + acera
    ctx.fillStyle = '#3a3a42'
    ctx.fillRect(0, 108, size, 88)
    ctx.fillStyle = '#d8d0a8'
    for (let x = 0; x < size; x += 34) {
      ctx.fillRect(x, 150, 18, 4)
    }
    ctx.fillStyle = '#6a625a'
    ctx.fillRect(0, 196, size, 60)
    // auto lowrider cruzando (loop ~6 s)
    const carX = ((t * 46) % (size + 150)) - 75
    ctx.fillStyle = '#7a2430'
    ctx.fillRect(carX, 122, 62, 16)
    ctx.fillRect(carX + 14, 112, 32, 12)
    ctx.fillStyle = '#141018'
    ctx.beginPath()
    ctx.arc(carX + 14, 140, 7, 0, Math.PI * 2)
    ctx.arc(carX + 48, 140, 7, 0, Math.PI * 2)
    ctx.fill()
    // personaje de espaldas (tercera persona) en la acera
    ctx.fillStyle = '#2c3e2c'
    ctx.fillRect(118, 196, 20, 26)
    ctx.fillStyle = '#274a8c'
    ctx.fillRect(118, 222, 20, 20)
    ctx.fillStyle = '#c98f6a'
    ctx.fillRect(122, 184, 12, 12)
    // HUD clasico: hora + dinero + barras vida/chaleco
    ctx.font = 'bold 16px monospace'
    ctx.fillStyle = '#f2f2f2'
    ctx.fillText('12:00', 192, 24)
    ctx.fillStyle = '#4dcc7a'
    ctx.fillText('$0035000', 160, 44)
    ctx.fillStyle = '#c23b3b'
    ctx.fillRect(160, 52, 62, 7)
    ctx.fillStyle = '#c8c8d0'
    ctx.fillRect(160, 62, 46, 7)
    // radar circular abajo-izquierda + blip parpadeante + flecha
    ctx.fillStyle = 'rgba(18,22,18,0.92)'
    ctx.beginPath()
    ctx.arc(38, 216, 28, 0, Math.PI * 2)
    ctx.fill()
    ctx.strokeStyle = '#c8b878'
    ctx.lineWidth = 3
    ctx.stroke()
    if (Math.floor(t * 2) % 2 === 0) {
      ctx.fillStyle = '#e8c84a'
      ctx.fillRect(48, 202, 6, 6)
    }
    ctx.fillStyle = '#f2f2f2'
    ctx.beginPath()
    ctx.moveTo(38, 209)
    ctx.lineTo(33, 222)
    ctx.lineTo(43, 222)
    ctx.closePath()
    ctx.fill()
  }

  return {
    texture,
    update(t) {
      if (t - last < 0.12) {
        return
      }
      last = t
      draw(t)
      texture.needsUpdate = true
    },
  }
}

/** PC de escritorio noventera con el juego corriendo (CRT + teclado). */
function gamingPc(): { group: Group; update(t: number): void } {
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
  const game = gtaScreen()
  const screen = new Mesh(
    unitGeo().plane,
    new MeshBasicMaterial({ map: game.texture }),
  )
  screen.scale.set(0.42, 0.3, 1)
  screen.position.set(0, 0.28, 0.105)
  screen.userData.noOutline = true
  group.add(body, screen)
  return { group, update: (t) => game.update(t) }
}

/**
 * Rincon de tecnico A/C: unidad de muro con la salida de aire inferior
 * REDISEÑADA (marco + 3 lamas orientables — antes era una tapa colgando
 * sin sentido). Con E se ENCIENDE: LED verde, las lamas se abren y
 * oscilan, y salen lineas de brisa estilo manga. Ademas: otra unidad a
 * medio desarmar en el piso, su tapa apoyada y la caja de herramientas.
 */
function acCorner(
  x: number,
  z: number,
  colliders: Box2[],
): {
  group: Group
  interactable: Interactable
  update(t: number, dt: number): void
} {
  const group = new Group()
  // unidad montada en el muro derecho
  const wallUnit = new Group()
  wallUnit.position.set(x + 4.3, 1.8, z + 1.8)
  wallUnit.rotation.y = -Math.PI / 2
  const body = boxMesh(1.05, 0.36, 0.24, toonMat('#cec8b4'))
  // salida de aire inferior: marco + 3 lamas con pivote (cerradas al
  // arrancar; al encender se abren y oscilan barriendo el aire)
  const outletFrame = boxMesh(0.94, 0.03, 0.06, toonMat('#a8a292'))
  outletFrame.position.set(0, -0.185, 0.1)
  outletFrame.userData.noOutline = true
  const louvers: Mesh[] = []
  const louverGroup = new Group()
  louverGroup.position.set(0, -0.17, 0.08)
  for (const [i, dy] of [-0.01, -0.05, -0.09].entries()) {
    const louver = boxMesh(0.86, 0.014, 0.07, toonMat('#8f897a'))
    louver.position.set(0, dy, i * 0.015)
    louver.rotation.x = 0.12
    louver.userData.noOutline = true
    louvers.push(louver)
    louverGroup.add(louver)
  }
  wallUnit.add(louverGroup)
  const ledMat = toonMatOwn('#b23a3a', {
    emissive: '#b23a3a',
    emissiveIntensity: 1.1,
  })
  const led = new Mesh(unitGeo().sphere, ledMat)
  led.scale.setScalar(0.05)
  led.position.set(0.42, 0.1, 0.14)
  led.userData.noOutline = true
  // lineas de brisa manga (aparecen al encender, derivan hacia el piso)
  const breeze: Mesh[] = []
  const breezeMat = basicMat('#f5f2e8', { transparent: true, opacity: 0.3 })
  for (let i = 0; i < 4; i += 1) {
    const line = new Mesh(unitGeo().box, breezeMat)
    line.scale.set(0.4 - i * 0.04, 0.012, 0.012)
    line.position.set((i - 1.5) * 0.18, -0.25, 0.16)
    line.visible = false
    line.userData.noOutline = true
    breeze.push(line)
    wallUnit.add(line)
  }
  wallUnit.add(body, outletFrame, led)
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
  // toggle ilimitado: encender abre lamas + brisa; apagar las cierra
  let powered = false
  const item: Interactable = {
    id: 'past-ac',
    x: x + 3.9,
    z: z + 1.8,
    radius: 2,
    label: { ...AC_LABEL_ON },
    onActivate: () => {
      powered = !powered
      const color = powered ? '#4dcc7a' : '#b23a3a'
      ledMat.color.set(color)
      ledMat.emissive.set(color)
      sfx.play(powered ? 'breeze-on' : 'shutdown')
      item.label = powered ? AC_LABEL_OFF : AC_LABEL_ON
    },
  }
  return {
    group,
    interactable: item,
    update: (t, dt) => {
      if (!powered) {
        // lamas se cierran suave y la brisa desaparece
        for (const louver of louvers) {
          louver.rotation.x = Math.max(louver.rotation.x - dt * 1.6, 0.12)
        }
        for (const line of breeze) {
          line.visible = false
        }
        return
      }
      // lamas: se abren suave y luego barren oscilando
      const sweep = 0.55 + Math.sin(t * 1.6) * 0.2
      for (const louver of louvers) {
        louver.rotation.x = Math.min(louver.rotation.x + dt * 1.2, sweep)
      }
      // brisa manga: las lineas derivan hacia el piso y reinician
      for (const [i, line] of breeze.entries()) {
        line.visible = true
        const phase = (t * 0.55 + i / 4) % 1
        line.position.y = -0.24 - phase * 0.85
        line.position.z = 0.14 + phase * 0.55
        line.scale.x = (0.42 - i * 0.04) * (1 - phase * 0.55)
      }
      // aire audible al acercarse (keep-alive)
      sfx.feed('past-ac-breeze', 'breeze', x + 3.9, z + 1.8)
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
  // hablarle al Pablo del pasado: SALTA (tobi geri) y abre su arbol
  const karateTalk = npcTalk({
    id: 'talk-past-aula-karate',
    npc: karateka,
    dialog: AULA_PASADO_DIALOGS['pablo-karateka'],
    openDialog: actions.openDialog,
    onGreet: () => {
      karateka.jump()
      sfx.play('blip')
    },
  })
  interactables.push(karateTalk.interactable)
  updates.push(karateTalk.update)

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
  pc.group.position.set(x + 3.2, 0.75, z - 2.4)
  pc.group.rotation.y = -Math.PI / 2
  group.add(pc.group)
  updates.push((t) => pc.update(t))
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
  const gamer = makeNpc({
    skin: '#c98f6a',
    hair: { style: 'spiky', color: '#2a1c10' },
    top: '#7a5c48',
    bottom: '#4a4438',
    faceSeed: 29,
    position: [x + 2.6, 0, z - 2.4],
    rotationY: Math.PI / 2,
    pose: 'sit',
  })
  npcs.push(gamer)
  const gamerTalk = npcTalk({
    id: 'talk-past-aula-gamer',
    npc: gamer,
    dialog: AULA_PASADO_DIALOGS['pablo-gamer'],
    openDialog: actions.openDialog,
  })
  interactables.push(gamerTalk.interactable)
  updates.push(gamerTalk.update)
  // la pregunta que lo cambio todo, flotando sobre la pantalla
  const seed = label(
    locale === 'es' ? '¿como se HACEN los juegos?' : 'how are games MADE?',
    { size: 0.14, color: '#e8d8b0' },
  )
  seed.position.set(x + 2.9, 1.95, z - 2.4)
  seed.rotation.y = -Math.PI / 2
  group.add(seed)

  // --- aires acondicionados: tecnico arrodillado reparando + encendido
  const ac = acCorner(x, z, colliders)
  group.add(ac.group)
  interactables.push(ac.interactable)
  updates.push(ac.update)
  const tecnicoAc = makeNpc({
    skin: '#d9a684',
    hair: { style: 'short', color: '#2a1c12' },
    top: '#5a6a73',
    bottom: '#3a4048',
    faceSeed: 47,
    position: [x + 2.95, 0, z + 1.8],
    rotationY: Math.PI / 2,
    pose: 'kneel',
  })
  npcs.push(tecnicoAc)
  const tecnicoTalk = npcTalk({
    id: 'talk-past-aula-tecnico',
    npc: tecnicoAc,
    dialog: AULA_PASADO_DIALOGS['pablo-tecnico'],
    openDialog: actions.openDialog,
  })
  interactables.push(tecnicoTalk.interactable)
  updates.push(tecnicoTalk.update)

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

function corpoelecPast(
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

// ---------------------------------------------------------------------------
// Cima: procesos manuales, un solo pais
// ---------------------------------------------------------------------------

const CIMA_STORY: Record<Locale, { title: string; paragraphs: string[] }> = {
  es: {
    title: 'Antes de la plataforma',
    paragraphs: [
      'El admin de campañas se armaba a mano: horas de planillas para ' +
        'lanzar una sola campaña.',
      'Cada area era un silo. La "integracion" entre servicios era una ' +
        'llamada telefonica o alguien corriendo con papeles entre ' +
        'escritorios.',
      'Con esos procesos, operar UN pais ya era cuesta arriba — ' +
        'expandirse a otro era impensable. La plataforma de ' +
        'microservicios cambio esa historia: cruza de vuelta y mirala ' +
        'orquestar Chile y Mexico.',
    ],
  },
  en: {
    title: 'Before the platform',
    paragraphs: [
      'The campaign admin was assembled by hand: hours of spreadsheets ' +
        'to launch a single campaign.',
      'Every area was a silo. "Integration" between services was a ' +
        'phone call, or someone running papers between desks.',
      'With those processes, operating in ONE country was already an ' +
        'uphill battle — expanding to another was unthinkable. The ' +
        'microservices platform changed that story: cross back and ' +
        'watch it orchestrate Chile and Mexico.',
    ],
  },
}

const PHONE_LABEL = {
  es: 'Llamar por telefono (la integracion v0)',
  en: 'Make a phone call (integration v0)',
} as const

const PILE_LABEL = {
  es: 'Revisar la pila del admin de campañas',
  en: 'Check the campaign-admin pile',
} as const

function cimaPast(
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
  const pile = paperStack({ position: [x - 0.4, 0.76, z - 0.6], count: 16 })
  group.add(
    desk({ position: [x, 0, z - 0.6], width: 1.6, color: '#3c3a44' }),
    pile,
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

  // micro: el telefono suena — asi se "integraban" los servicios
  const phoneVerdict = label(
    locale === 'es'
      ? 'integracion v0: una llamada y a esperar'
      : 'integration v0: one phone call, then wait',
    { size: 0.12, color: '#e8d8b0' },
  )
  phoneVerdict.position.set(x + 0.45, 1.45, z - 0.7)
  phoneVerdict.visible = false
  group.add(phoneVerdict)
  let ringT = -1
  interactables.push({
    id: 'past-phone',
    x: x + 0.45,
    z: z - 0.7,
    radius: 2,
    label: PHONE_LABEL,
    onActivate: () => {
      if (ringT === -1) {
        ringT = -2
        sfx.play('ring')
      }
    },
  })
  updates.push((t) => {
    if (ringT === -2) {
      ringT = t
    }
    if (ringT < 0) {
      return
    }
    const elapsed = t - ringT
    if (elapsed < 1.6) {
      phone.rotation.z = Math.sin(t * 40) * 0.12
    } else if (elapsed < 5) {
      phone.rotation.z = 0
      phoneVerdict.visible = true
    } else {
      phoneVerdict.visible = false
      ringT = -1
    }
  })

  // micro: la pila del admin manual — el costo real en horas
  const pileVerdict = label(
    locale === 'es'
      ? 'una campaña = 6+ horas a mano'
      : 'one campaign = 6+ hours by hand',
    { size: 0.12, color: '#e8d8b0' },
  )
  pileVerdict.position.set(x - 0.4, 1.5, z - 0.6)
  pileVerdict.visible = false
  group.add(pileVerdict)
  let pileT = -1
  interactables.push({
    id: 'past-pile',
    x: x - 0.4,
    z: z - 0.6,
    radius: 1.9,
    label: PILE_LABEL,
    onActivate: () => {
      if (pileT === -1) {
        pileT = -2
        sfx.play('blip')
      }
    },
  })
  updates.push((t) => {
    if (pileT === -2) {
      pileT = t
    }
    if (pileT < 0) {
      return
    }
    const elapsed = t - pileT
    if (elapsed < 1.2) {
      pile.rotation.y = Math.sin(t * 26) * 0.07
    } else if (elapsed < 4.5) {
      pile.rotation.y = 0
      pileVerdict.visible = true
    } else {
      pileVerdict.visible = false
      pileT = -1
    }
  })

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
  const operator = makeNpc({
    skin: '#e8b48c',
    hair: { style: 'bun', color: '#3a2a1a' },
    top: '#6a5c48',
    bottom: '#4a4438',
    accessory: 'tie',
    faceSeed: 73,
    position: [x + 0.5, 0, z + 0.1],
    rotationY: Math.PI,
  })
  npcs.push(runner, operator)
  const talks = [
    npcTalk({
      id: 'talk-past-cima-runner',
      npc: runner,
      dialog: CIMA_PASADO_DIALOGS['runner-papeles'],
      openDialog: actions.openDialog,
    }),
    npcTalk({
      id: 'talk-past-cima-operador',
      npc: operator,
      dialog: CIMA_PASADO_DIALOGS['operador-telefono'],
      openDialog: actions.openDialog,
    }),
  ]
  for (const talk of talks) {
    interactables.push(talk.interactable)
    updates.push(talk.update)
  }

  const story = CIMA_STORY[locale]
  const panel = screenPanel({
    title: locale === 'es' ? 'procesos manuales' : 'manual processes',
    lines:
      locale === 'es'
        ? [
            'admin de campanas: horas',
            'servicios sin orquestar',
            'un solo pais, silos',
            '',
            '[E] leer la historia',
          ]
        : [
            'campaign admin: hours',
            'services not orchestrated',
            'one country, silos',
            '',
            '[E] read the story',
          ],
    theme: PAST_SCREEN,
    width: 2,
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

function buildSet(ctx: PastCtx): PastSet {
  const { def, pastRoom, state, actions } = ctx
  const { x, z, depth } = pastRoom
  if (def.id === 'aula') {
    return aulaPast(x, z, depth, state.locale, actions)
  }
  if (def.id === 'corpoelec') {
    return corpoelecPast(x, z, depth, state.locale, actions)
  }
  return cimaPast(x, z, depth, state.locale, actions)
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

  // grieta de salida PEGADA al muro trasero, mirando a la sala
  const exit = exitPortal({
    roomIndex: pastRoom.index,
    position: [pastRoom.x, 0, pastRoom.z + pastRoom.depth / 2 - 0.08],
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
