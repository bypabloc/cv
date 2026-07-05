/**
 * @module rooms/corpoelec (engine)
 * @description Sala 1 — CORPOELEC (central electrica estatal, VE, 2013).
 *   Transformador con bujes, cajas de inventario, monitor con la tabla
 *   OFFLINE, ventana con torres (canvas ink), casco de seguridad y guiño
 *   YARACUY·CARABOBO·LARA. Micros: tablero rojo <-> verde (toggle),
 *   buscar el equipo 0042 (papel lento vs sistema inmediato) y el monitor
 *   con el codigo PHP + jQuery de la epoca. 2 NPCs tecnicos con casco,
 *   conversables con E (arboles de dialogo bilingues).
 */
import { Group, Mesh, MeshBasicMaterial, PointLight } from 'three'
import type { Box2 } from '../../lib/collision'
import { sfx } from '../audio'
import { makeNpc, type NpcHandle } from '../character'
import { npcTalk } from '../dialog'
import { CORPOELEC_PRESENTE_DIALOGS } from '../dialogs/corpoelec-presente'
import type { Interactable } from '../state'
import {
  boxMesh,
  disposeDeep,
  label,
  makeCanvasTexture,
  outlinedMergedBoxes,
  outlineGroup,
  toonMat,
  toonMatOwn,
  unitGeo,
} from '../toon'
import type { RoomBuild, RoomCtx } from '../world'
import {
  desk,
  fichaBoard,
  footprint,
  lecternNotebook,
  pastPortal,
  switchableMonitor,
} from './props'

const BOARD_LABEL_ON = {
  es: 'Energizar el tablero de control',
  en: 'Power up the control board',
} as const

const BOARD_LABEL_OFF = {
  es: 'Cortar el tablero de control',
  en: 'Power down the control board',
} as const

const SEARCH_LABEL = {
  es: 'Buscar el equipo 0042',
  en: 'Look up asset 0042',
} as const

const CODE_LABEL_PHP = {
  es: 'Ver el codigo PHP (backend)',
  en: 'View the PHP code (backend)',
} as const

const CODE_LABEL_JQUERY = {
  es: 'Ver el codigo jQuery (tabla)',
  en: 'View the jQuery code (grid)',
} as const

/** Transformador: caja gris + aletas + 3 bujes ceramicos (primitivas). */
function transformer(position: readonly [number, number, number]): Group {
  const group = new Group()
  group.position.set(position[0], position[1], position[2])
  const body = boxMesh(1.3, 1.4, 0.9, toonMat('#5c6168'))
  body.position.y = 0.7
  body.castShadow = true
  group.add(body)
  const units = unitGeo()
  for (const x of [-0.5, 0, 0.5]) {
    const bushing = new Mesh(units.cylinder, toonMat('#b8b4a8'))
    bushing.scale.set(0.17, 0.35, 0.17)
    bushing.position.set(x, 1.55, 0)
    group.add(bushing)
  }
  for (const x of [-0.72, 0.72]) {
    const fin = boxMesh(0.12, 1.2, 0.7, toonMat('#4c5057'))
    fin.position.set(x, 0.7, 0)
    group.add(fin)
  }
  return group
}

/** Ventana con torres de alta tension: silueta ink, cielo en 2 bandas. */
function towersWindow(position: readonly [number, number, number]): Group {
  const texture = makeCanvasTexture(256, (ctx, size) => {
    // cielo en 2 bandas planas (sin gradiente suave — look de tinta)
    ctx.fillStyle = '#5a6a85'
    ctx.fillRect(0, 0, size, size * 0.55)
    ctx.fillStyle = '#c88d5a'
    ctx.fillRect(0, size * 0.55, size, size * 0.45)
    ctx.strokeStyle = '#14161a'
    ctx.lineWidth = 5
    ctx.lineCap = 'round'
    for (const cx of [64, 160]) {
      ctx.beginPath()
      ctx.moveTo(cx - 22, size)
      ctx.lineTo(cx, 60)
      ctx.lineTo(cx + 22, size)
      ctx.moveTo(cx - 26, 110)
      ctx.lineTo(cx + 26, 110)
      ctx.moveTo(cx - 18, 80)
      ctx.lineTo(cx + 18, 80)
      ctx.stroke()
    }
    ctx.beginPath()
    ctx.moveTo(38, 112)
    ctx.quadraticCurveTo(112, 150, 186, 112)
    ctx.stroke()
  })
  const group = new Group()
  group.position.set(position[0], position[1], position[2])
  group.rotation.y = -Math.PI / 2
  const pane = new Mesh(
    unitGeo().plane,
    new MeshBasicMaterial({ map: texture }),
  )
  pane.scale.set(1.8, 1.2, 1)
  pane.userData.noOutline = true
  const frame = boxMesh(2, 1.4, 0.05, toonMat('#2a2d33'))
  frame.position.z = -0.03
  group.add(pane, frame)
  return group
}

export default function buildCorpoelec(ctx: RoomCtx): RoomBuild {
  const { def, room, theme, state, actions } = ctx
  const group = new Group()
  const interactables: Interactable[] = []
  const updates: ((t: number, dt: number) => void)[] = []
  const npcs: NpcHandle[] = []
  const disposables: { dispose(): void }[] = []
  const staticColliders: Box2[] = []
  const half = room.width / 2

  group.add(transformer([-half + 1.4, 0, room.z - 2.2]))
  staticColliders.push(footprint(-half + 1.4, room.z - 2.2, 1.8, 1.1))

  // cajas de inventario fusionadas con contorno correcto (2 draw calls)
  group.add(
    outlinedMergedBoxes(
      [
        { w: 0.6, h: 0.6, d: 0.6, x: half - 1, y: 0.3, z: room.z - 2.6 },
        { w: 0.6, h: 0.6, d: 0.6, x: half - 1.7, y: 0.3, z: room.z - 2.4 },
        { w: 0.6, h: 0.6, d: 0.6, x: half - 1, y: 0.9, z: room.z - 2.6 },
        { w: 0.6, h: 0.6, d: 0.6, x: half - 1.1, y: 0.3, z: room.z - 1.7 },
      ],
      toonMat('#8a6f4d'),
      { castShadow: true },
    ),
  )
  staticColliders.push(footprint(half - 1.35, room.z - 2.15, 1.6, 1.6))
  const inventoryLabel = label(
    state.locale === 'es' ? 'INVENTARIO' : 'INVENTORY',
    { size: 0.16, color: '#f2b705' },
  )
  inventoryLabel.position.set(half - 1, 1.35, room.z - 2.6)
  inventoryLabel.rotation.y = Math.PI
  group.add(inventoryLabel)

  // monitor del inventario: arranca OFFLINE, el tablero lo pone ONLINE
  const screenTheme = {
    screenBg: theme.screenBg,
    screenFg: theme.screenFg,
    ink: theme.ink,
  }
  group.add(
    desk({ position: [1.4, 0, room.z + 2.4], width: 1.4, color: '#3a3e44' }),
  )
  staticColliders.push(footprint(1.4, room.z + 2.4, 1.5, 0.8))
  const inventory = switchableMonitor({
    position: [1.4, 0.72, room.z + 2.3],
    rotationY: Math.PI,
    width: 0.72,
    variants: {
      offline: {
        title: '[OFFLINE] inventario',
        lines: [
          'ID    EQUIPO       SEDE',
          '0041  transformador yaracuy',
          '0042  aislador      carabobo',
          '0043  medidor       lara',
          'busqueda: en papel...',
        ],
        theme: screenTheme,
        dot: '#cc3b3b',
      },
      online: {
        title: '[ONLINE] inventario',
        lines: [
          'ID    EQUIPO       SEDE',
          '0041  transformador yaracuy',
          '0042  aislador      carabobo',
          '0043  medidor       lara',
          'sync 3 sedes: OK   2ms',
        ],
        theme: screenTheme,
        dot: '#4dcc7a',
      },
      'search-offline': {
        title: '[OFFLINE] buscando 0042...',
        lines: [
          'sistema sin energia',
          'revisando planillas a mano',
          'carpeta 7 de 38...',
          'tiempo estimado: 20+ min',
        ],
        theme: screenTheme,
        dot: '#cc3b3b',
      },
      'search-online': {
        title: '[ONLINE] buscar: 0042',
        lines: [
          '> buscar "0042"',
          '0042  aislador  carabobo',
          'ubicacion: deposito B-3',
          'tiempo: 0.2 s',
        ],
        theme: screenTheme,
        dot: '#4dcc7a',
      },
    },
    initial: 'offline',
  })
  group.add(inventory.group)
  disposables.push(inventory.screen)

  // segundo monitor: el codigo REAL de la epoca (PHP + jQuery, 2013),
  // pegado al muro del fondo; E alterna backend <-> tabla
  group.add(
    desk({
      position: [-1.8, 0, room.z - room.depth / 2 + 0.7],
      width: 1.5,
      color: '#3a3e44',
    }),
  )
  staticColliders.push(footprint(-1.8, room.z - room.depth / 2 + 0.7, 1.6, 0.9))
  const code = switchableMonitor({
    position: [-1.8, 0.72, room.z - room.depth / 2 + 0.75],
    width: 0.8,
    variants: {
      jquery: {
        title: 'inventario.js — jQuery',
        lines: [
          "$('#tabla').on('click',",
          "  'tr', mostrarEquipo)",
          "$.get('/api/equipos',",
          '  pintarTabla) // 2013',
        ],
        theme: screenTheme,
        dot: '#3f9d63',
      },
      php: {
        title: 'equipos.php — PHP',
        lines: [
          '$rs = mysql_query(',
          "  'SELECT * FROM equipos');",
          'while ($eq = fetch($rs))',
          '  guardarOffline($eq);',
        ],
        theme: screenTheme,
        dot: '#3f9d63',
      },
    },
    initial: 'jquery',
  })
  group.add(code.group)
  disposables.push(code.screen)
  let codeOnPhp = false
  const codeItem: Interactable = {
    id: `micro-corpoelec-code-${room.index}`,
    x: -1.8,
    z: room.z - room.depth / 2 + 0.7,
    radius: 2,
    label: { ...CODE_LABEL_PHP },
    onActivate: () => {
      codeOnPhp = !codeOnPhp
      code.screen.show(codeOnPhp ? 'php' : 'jquery')
      sfx.play('blip')
      codeItem.label = codeOnPhp ? CODE_LABEL_JQUERY : CODE_LABEL_PHP
    },
  }
  interactables.push(codeItem)

  // ventana con torres + casco de seguridad sobre el escritorio
  // (corrida hacia el fondo: el frente del muro +X es de la grieta)
  group.add(towersWindow([half - 0.42, 1.7, room.z - 1.2]))
  const helmet = new Group()
  helmet.position.set(1.9, 0.85, room.z + 2.3)
  const units = unitGeo()
  const dome = new Mesh(units.sphere, toonMat('#f2b705'))
  dome.scale.set(0.32, 0.22, 0.32)
  dome.position.y = 0.02
  const brim = new Mesh(units.cylinder, toonMat('#f2b705'))
  brim.scale.set(0.44, 0.02, 0.44)
  helmet.add(dome, brim)
  group.add(helmet)

  // guiño geografico discreto en el muro -X (al fondo, sobre el
  // transformador — el frente de ese muro es del cuaderno flotante)
  const geo = label('YARACUY · CARABOBO · LARA', {
    size: 0.22,
    color: theme.accent,
  })
  geo.position.set(-half + 0.3, 2.5, room.z - 2.3)
  geo.rotation.y = Math.PI / 2
  group.add(geo)

  // micro-interaccion: tablero de medidores rojo -> verde + luz de estado
  // (muro +X entre la ventana y la grieta al pasado)
  const microId = `micro-corpoelec-${room.index}`
  const micro = new Group()
  micro.position.set(half - 0.42, 0, room.z + 0.6)
  micro.rotation.y = -Math.PI / 2
  const panel = boxMesh(1.6, 1.1, 0.08, toonMat('#2e3238'))
  panel.position.set(0, 1.5, 0)
  micro.add(panel)
  const lampMat = toonMatOwn('#cc3b3b', {
    emissive: '#cc3b3b',
    emissiveIntensity: 1.2,
  })
  const gaugeMat = toonMatOwn('#d8d4c8', {
    emissive: '#cc3b3b',
    emissiveIntensity: 0.35,
  })
  for (const x of [-0.5, 0, 0.5]) {
    const gauge = new Mesh(units.cylinder, gaugeMat)
    gauge.scale.set(0.22, 0.03, 0.22)
    gauge.rotation.x = Math.PI / 2
    gauge.position.set(x, 1.72, 0.06)
    const lamp = new Mesh(units.sphere, lampMat)
    lamp.scale.setScalar(0.1)
    lamp.position.set(x, 1.28, 0.06)
    micro.add(gauge, lamp)
  }
  const statusLight =
    state.tier === 'full' ? new PointLight('#cc3b3b', 1.6, 4) : null
  if (statusLight) {
    statusLight.position.set(0, 1.5, 0.5)
    micro.add(statusLight)
  }
  group.add(micro)
  // toggle ilimitado: energizar/cortar arrastra lamparas + monitor + label
  let energized = false
  const boardItem: Interactable = {
    id: microId,
    x: half - 0.42,
    z: room.z + 0.6,
    radius: 2,
    label: { ...BOARD_LABEL_ON },
    onActivate: () => {
      energized = !energized
      const color = energized ? '#4dcc7a' : '#cc3b3b'
      lampMat.color.set(color)
      lampMat.emissive.set(color)
      gaugeMat.emissive.set(color)
      statusLight?.color.set(color)
      inventory.screen.show(energized ? 'online' : 'offline')
      sfx.play(energized ? 'boot' : 'shutdown')
      boardItem.label = energized ? BOARD_LABEL_OFF : BOARD_LABEL_ON
    },
  }
  interactables.push(boardItem)

  // micro "buscar un equipo": papel lento vs sistema inmediato, segun
  // este energizado el tablero; la pantalla vuelve sola a los ~3 s
  let searchUntil = -1
  interactables.push({
    id: `micro-corpoelec-search-${room.index}`,
    x: 1.4,
    z: room.z + 2.4,
    radius: 1.9,
    label: SEARCH_LABEL,
    onActivate: () => {
      inventory.screen.show(energized ? 'search-online' : 'search-offline')
      sfx.play('blip')
      searchUntil = -2 // pendiente: el proximo update fija el fin
    },
  })
  updates.push((t) => {
    if (searchUntil === -2) {
      searchUntil = t + 3
    }
    if (searchUntil > 0 && t > searchUntil) {
      searchUntil = -1
      inventory.screen.show(energized ? 'online' : 'offline')
    }
  })

  // pizarras tituladas: RETOS (muro del fondo) / APRENDIZAJES (muro izq)
  const texts = def.texts[state.locale]
  const retos = fichaBoard({
    roomIndex: room.index,
    kind: 'retos',
    position: [-1.6, 0, room.z + room.depth / 2 - 0.35],
    rotationY: Math.PI,
    theme,
    locale: state.locale,
    preview: texts.retos,
    onOpen: actions.openFicha,
  })
  const aprendizajes = fichaBoard({
    roomIndex: room.index,
    kind: 'aprendizajes',
    position: [-half + 0.35, 0, room.z - 0.4],
    rotationY: Math.PI / 2,
    theme,
    locale: state.locale,
    preview: texts.aprendizajes,
    onOpen: actions.openFicha,
  })
  // grieta al pasado en el muro +X (la mano izquierda de quien avanza)
  const portal = pastPortal({
    room,
    position: [half - 0.1, 0, room.z + 2.8],
    rotationY: -Math.PI / 2,
    accent: theme.accent,
    year: def.year,
    locale: state.locale,
    onEnter: actions.enterPast,
  })
  // cuaderno flotante con la reseña, en el -X (la derecha del jugador),
  // pegado a la puerta de salida
  const nota = lecternNotebook({
    roomIndex: room.index,
    position: [-half + 0.9, 0, room.z + 2.7],
    rotationY: Math.PI / 2,
    theme,
    notebook: { title: texts.title, lines: texts.notebook },
    story: { title: texts.title, paragraphs: texts.resena },
    withLight: state.tier === 'full',
    onOpen: actions.openStory,
  })
  staticColliders.push(footprint(-half + 0.9, room.z + 2.7, 0.7, 0.7))
  for (const prop of [retos, aprendizajes, portal, nota]) {
    group.add(prop.group)
    if (prop.interactable) {
      interactables.push(prop.interactable)
    }
    if (prop.update) {
      updates.push(prop.update)
    }
  }

  // NPCs: tecnicos con casco (una en ronda de inspeccion), conversables
  const tecnicoSubestacion = makeNpc({
    skin: '#d9a684',
    hair: { style: 'short', color: '#2a2018' },
    top: '#3f5a73',
    bottom: '#2e3238',
    accessory: 'helmet',
    faceSeed: 51,
    position: [-half + 2.4, 0, room.z - 1.8],
    rotationY: -0.9,
  })
  const tecnicaRonda = makeNpc({
    skin: '#c98f6a',
    hair: { style: 'ponytail', color: '#1c1410' },
    top: '#5a6a48',
    bottom: '#3a4048',
    accessory: 'helmet',
    faceSeed: 67,
    position: [0, 0, room.z],
    path: [
      [0, room.z],
      [half - 2.2, room.z - 2],
      [-1.2, room.z + 1.4],
    ],
    speed: 0.6,
  })
  npcs.push(tecnicoSubestacion, tecnicaRonda)
  for (const npc of npcs) {
    group.add(npc.group)
    updates.push((t, dt) => npc.update(t, dt))
  }
  const talks = [
    npcTalk({
      id: `talk-corpoelec-${room.index}-subestacion`,
      npc: tecnicoSubestacion,
      dialog: CORPOELEC_PRESENTE_DIALOGS['tecnico-subestacion'],
      openDialog: actions.openDialog,
    }),
    npcTalk({
      id: `talk-corpoelec-${room.index}-ronda`,
      npc: tecnicaRonda,
      dialog: CORPOELEC_PRESENTE_DIALOGS['tecnica-ronda'],
      openDialog: actions.openDialog,
    }),
  ]
  for (const talk of talks) {
    interactables.push(talk.interactable)
    updates.push(talk.update)
  }

  outlineGroup(group, 1.03)

  return {
    group,
    interactables,
    colliders: () => [...staticColliders, ...npcs.map((npc) => npc.collider())],
    update: (t, dt) => {
      for (const fn of updates) {
        fn(t, dt)
      }
    },
    dispose: () => {
      for (const npc of npcs) {
        npc.dispose()
      }
      for (const item of disposables) {
        item.dispose()
      }
      disposeDeep(group)
    },
  }
}
