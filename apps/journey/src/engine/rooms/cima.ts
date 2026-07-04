/**
 * @module rooms/cima (engine)
 * @description Sala 2 — LA CIMA (Destacame Fullstack & Lider, CL+MX,
 *   2022-hoy). War room azul #0052CC: mesa de reunion, paneles de
 *   observabilidad y vibe coding, grafo de microservicios (canvas ink),
 *   escritorio ultrawide code-base -> forks, puerta PROXIMAMENTE y CTA de
 *   contacto. Micro-interaccion: orquestacion CL <-> MX (pulso).
 */
import {
  Group,
  Mesh,
  MeshBasicMaterial,
  OctahedronGeometry,
  PointLight,
} from 'three'
import type { Box2 } from '../../lib/collision'
import { sfx } from '../audio'
import { makeNpc, type NpcHandle } from '../character'
import type { Interactable } from '../state'
import {
  boxMesh,
  disposeDeep,
  label,
  makeCanvasTexture,
  outlinedMergedBoxes,
  outlineGroup,
  screenPanel,
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
  monitor,
  pastPortal,
  screenVariants,
} from './props'

const MICRO_LABEL = {
  es: 'Orquestar Chile + Mexico',
  en: 'Orchestrate Chile + Mexico',
} as const

const CONTACT_LABEL = {
  es: 'Contactar a Pablo',
  en: 'Contact Pablo',
} as const

/** Grafo de microservicios dibujado en canvas (estilo tinta plana). */
function graphTexture() {
  return makeCanvasTexture(512, (ctx, size) => {
    ctx.fillStyle = '#0a1220'
    ctx.fillRect(0, 0, size, size)
    const nodes: readonly (readonly [number, number, string])[] = [
      [256, 90, 'gateway'],
      [120, 220, 'scoring'],
      [256, 230, 'pagos'],
      [392, 220, 'campanas'],
      [180, 370, 'usuarios'],
      [340, 370, 'deudas'],
    ]
    ctx.strokeStyle = '#2d5bb9'
    ctx.lineWidth = 4
    const edges: readonly (readonly [number, number])[] = [
      [0, 1],
      [0, 2],
      [0, 3],
      [1, 4],
      [2, 4],
      [2, 5],
      [3, 5],
    ]
    for (const [a, b] of edges) {
      const na = nodes[a]
      const nb = nodes[b]
      if (!na || !nb) {
        continue
      }
      ctx.beginPath()
      ctx.moveTo(na[0], na[1])
      ctx.lineTo(nb[0], nb[1])
      ctx.stroke()
    }
    for (const [x, y, name] of nodes) {
      ctx.fillStyle = '#0f2547'
      ctx.strokeStyle = '#5aa2ff'
      ctx.beginPath()
      ctx.arc(x, y, 34, 0, Math.PI * 2)
      ctx.fill()
      ctx.stroke()
      ctx.fillStyle = '#bcd6ff'
      ctx.font = '18px monospace'
      ctx.textAlign = 'center'
      ctx.fillText(name, x, y + 6)
    }
    ctx.textAlign = 'left'
    ctx.fillStyle = '#5aa2ff'
    ctx.font = 'bold 22px monospace'
    ctx.fillText('django microservices', 24, 470)
  })
}

/** Micro-interaccion: pulso viajando entre CL y MX via el nodo central. */
function buildOrchestration(
  roomIndex: number,
  position: readonly [number, number, number],
): {
  group: Group
  interactable: Interactable
  update(t: number, dt: number): void
  /** true cuando el pulso completo al menos una vez (deploy hecho). */
  completed(): boolean
} {
  const units = unitGeo()
  const group = new Group()
  group.position.set(position[0], position[1], position[2])
  group.rotation.y = Math.PI
  const hubGeo = new OctahedronGeometry(0.22, 0)
  const hub = new Mesh(
    hubGeo,
    toonMat('#0052cc', { emissive: '#3a7bff', emissiveIntensity: 0.8 }),
  )
  hub.position.set(0, 1.7, 0)
  group.add(hub)
  const clMat = toonMatOwn('#16324f', {
    emissive: '#4d9dff',
    emissiveIntensity: 0.4,
  })
  const mxMat = toonMatOwn('#16324f', {
    emissive: '#4d9dff',
    emissiveIntensity: 0.4,
  })
  for (const [x, mat] of [
    [-1.1, clMat],
    [1.1, mxMat],
  ] as const) {
    const node = new Mesh(units.sphere, mat)
    node.scale.setScalar(0.32)
    node.position.set(x, 1.4, 0)
    group.add(node)
  }
  const chileLabel = label('CHILE', { size: 0.16, color: '#9db8ff' })
  chileLabel.position.set(-1.1, 1.08, 0)
  const mexicoLabel = label('MEXICO', { size: 0.16, color: '#9db8ff' })
  mexicoLabel.position.set(1.1, 1.08, 0)
  group.add(chileLabel, mexicoLabel)
  for (const x of [-0.55, 0.55]) {
    const link = new Mesh(
      units.cylinder,
      toonMat('#3a7bff', { emissive: '#3a7bff', emissiveIntensity: 0.5 }),
    )
    link.scale.set(0.03, 1.05, 0.03)
    link.position.set(x, 1.55, 0)
    link.rotation.z = x < 0 ? -0.28 : 0.28
    link.userData.noOutline = true
    group.add(link)
  }
  let pulseStart = -1
  let done = false
  return {
    group,
    interactable: {
      id: `micro-cima-${roomIndex}`,
      x: position[0],
      z: position[2],
      radius: 2.4,
      label: MICRO_LABEL,
      onActivate: () => {
        pulseStart = -2 // marca "pendiente": el proximo update fija el inicio
        sfx.play('boot')
      },
    },
    update: (t) => {
      if (pulseStart === -2) {
        pulseStart = t
      }
      if (pulseStart < 0) {
        return
      }
      const elapsed = t - pulseStart
      if (elapsed > 2.4) {
        pulseStart = -1
        done = true
        clMat.emissiveIntensity = 0.4
        mxMat.emissiveIntensity = 0.4
        return
      }
      const wave = Math.abs(Math.sin(elapsed * Math.PI * 2))
      clMat.emissiveIntensity = 0.4 + wave * 1.4
      mxMat.emissiveIntensity = 0.4 + (1 - wave) * 1.4
    },
    completed: () => done,
  }
}

export default function buildCima(ctx: RoomCtx): RoomBuild {
  const { def, room, theme, state, actions } = ctx
  const group = new Group()
  const interactables: Interactable[] = []
  const updates: ((t: number, dt: number) => void)[] = []
  const npcs: NpcHandle[] = []
  const disposables: { dispose(): void }[] = []
  const staticColliders: Box2[] = []
  const half = room.width / 2
  const units = unitGeo()
  const screenTheme = {
    screenBg: theme.screenBg,
    screenFg: theme.screenFg,
    ink: theme.ink,
  }

  // mesa de reunion + 6 sillas (fusionadas por material: 3 draw calls),
  // corrida del centro para dejar libre el pasillo de la puerta
  const meeting = new Group()
  meeting.position.set(-1.7, 0, room.z + 1.6)
  const table = outlinedMergedBoxes(
    [
      { w: 3.4, h: 0.07, d: 1.5, x: 0, y: 0.74, z: 0 },
      { w: 0.12, h: 0.74, d: 1.3, x: -1.5, y: 0.37, z: 0 },
      { w: 0.12, h: 0.74, d: 1.3, x: 1.5, y: 0.37, z: 0 },
    ],
    toonMat('#1b2433'),
    { castShadow: true },
  )
  const chairs: readonly (readonly [number, number])[] = [
    [-1.1, -0.9],
    [0, -0.9],
    [1.1, -0.9],
    [-1.1, 0.9],
    [0, 0.9],
    [1.1, 0.9],
  ]
  const chairSet = outlinedMergedBoxes(
    chairs.flatMap(([x, dz]) => [
      { w: 0.44, h: 0.06, d: 0.44, x, y: 0.45, z: dz },
      {
        w: 0.44,
        h: 0.55,
        d: 0.05,
        x,
        y: 0.75,
        z: dz + (dz > 0 ? 0.2 : -0.2),
      },
    ]),
    toonMat('#26303f'),
    { inflate: 0.035 },
  )
  meeting.add(table, chairSet)
  group.add(meeting)
  staticColliders.push(footprint(-1.7, room.z + 1.6, 3.7, 3.2))

  // pared de paneles: observabilidad (se actualiza con la orquestacion)
  // + vibe coding
  const obs = screenVariants({
    width: 2.2,
    height: 1.3,
    variants: {
      live: {
        title: 'observability',
        lines: [
          'p95: 180ms',
          'uptime: 99.97%',
          'campanas: 4 min (antes: horas)',
        ],
        theme: screenTheme,
      },
      deployed: {
        title: 'observability',
        lines: [
          'deploy CL+MX: OK',
          'p95: 95ms   uptime: 99.99%',
          'campanas: 4 min (antes: horas)',
        ],
        theme: screenTheme,
        dot: '#4dcc7a',
      },
    },
    initial: 'live',
  })
  obs.mesh.position.set(-2.2, 1.9, room.z + room.depth / 2 - 0.12)
  obs.mesh.rotation.y = Math.PI
  disposables.push(obs)
  const vibe = screenPanel({
    title: 'vibe coding',
    lines: [
      '> claude "refactor module"',
      'tests: 128 passed',
      'review: aprobado',
    ],
    theme: screenTheme,
    width: 2.2,
    height: 1.3,
  })
  vibe.position.set(2.2, 1.9, room.z + room.depth / 2 - 0.12)
  vibe.rotation.y = Math.PI
  group.add(obs.mesh, vibe)

  // grafo de microservicios en el muro izquierdo
  const graph = new Mesh(
    units.plane,
    new MeshBasicMaterial({ map: graphTexture() }),
  )
  graph.scale.set(2.6, 2.6, 1)
  graph.position.set(-half + 0.12, 2, room.z - 1)
  graph.rotation.y = Math.PI / 2
  graph.userData.noOutline = true
  group.add(graph)

  // setup de escritorio ultrawide: code base -> forks
  group.add(
    desk({
      position: [half - 1.6, 0, room.z - 2.4],
      width: 2,
      color: '#1b2433',
    }),
    monitor({
      position: [half - 1.6, 0.75, room.z - 2.55],
      rotationY: 0.2,
      title: 'code base -> forks',
      lines: ['santander/', 'scotiabank/', 'lider/', 'mismo DS, N entidades'],
      theme: screenTheme,
      width: 1.1,
    }),
  )
  staticColliders.push(footprint(half - 1.6, room.z - 2.4, 2.1, 0.8))

  // micro-interaccion: lanzar la orquestacion CL <-> MX — el pulso viaja
  // y el panel de observabilidad reporta el deploy
  const orchestration = buildOrchestration(room.index, [
    0,
    0,
    room.z - room.depth / 2 + 1.4,
  ])
  group.add(orchestration.group)
  interactables.push(orchestration.interactable)
  updates.push(orchestration.update)
  updates.push(() => {
    if (orchestration.completed()) {
      obs.show('deployed')
    }
  })

  // puerta PROXIMAMENTE al fondo
  const coming = new Group()
  coming.position.set(half - 0.35, 0, room.z - 1.6)
  coming.rotation.y = -Math.PI / 2
  const comingFrame = boxMesh(1.2, 2.1, 0.09, toonMat('#10151f'))
  comingFrame.position.set(0, 1.05, 0)
  const comingPanel = boxMesh(
    1.05,
    1.9,
    0.02,
    toonMat('#141c2b', { emissive: theme.accent, emissiveIntensity: 0.12 }),
  )
  comingPanel.position.set(0, 1.05, 0.05)
  const comingTitle = label(
    state.locale === 'es' ? 'PROXIMAMENTE' : 'COMING SOON',
    { size: 0.16, color: '#9db8ff' },
  )
  comingTitle.position.set(0, 1.35, 0.09)
  const comingSub = label(
    state.locale === 'es' ? 'ideas futuras' : 'future ideas',
    {
      size: 0.1,
      color: '#5f77a8',
    },
  )
  comingSub.position.set(0, 1.1, 0.09)
  coming.add(comingFrame, comingPanel, comingTitle, comingSub)
  group.add(coming)

  // CTA de contacto: holograma girando sobre pedestal
  const beacon = new Group()
  beacon.position.set(half - 1.3, 0, room.z - 0.4)
  const pedestal = new Mesh(units.cylinder, toonMat('#141a26'))
  pedestal.scale.set(0.62, 1, 0.62)
  pedestal.position.y = 0.5
  const holoGeo = new OctahedronGeometry(0.24, 0)
  const holoMat = toonMatOwn('#0052cc', {
    emissive: '#5aa2ff',
    emissiveIntensity: 0.9,
    transparent: true,
    opacity: 0.92,
  })
  const holo = new Mesh(holoGeo, holoMat)
  holo.position.y = 1.35
  holo.rotation.y = 0.6
  beacon.add(pedestal, holo)
  if (state.tier === 'full') {
    const holoLight = new PointLight('#5aa2ff', 2.2, 4)
    holoLight.position.set(0, 1.4, 0)
    beacon.add(holoLight)
  }
  group.add(beacon)
  staticColliders.push(footprint(half - 1.3, room.z - 0.4, 0.8, 0.8))
  interactables.push({
    id: `contact-${room.index}`,
    x: half - 1.3,
    z: room.z - 0.4,
    radius: 2.2,
    label: CONTACT_LABEL,
    onActivate: () => actions.openContact(),
  })
  updates.push((t, dt) => {
    holoMat.emissiveIntensity = 0.9 + Math.sin(t * 2.4) * 0.35
    holo.rotation.y += dt * 0.8
    // hum cristalino del holograma, audible al acercarse
    sfx.feed(`holo-${room.index}`, 'holo', half - 1.3, room.z - 0.4)
  })

  // pizarras tituladas: RETOS (muro frontal) / APRENDIZAJES (muro izq)
  const texts = def.texts[state.locale]
  const retos = fichaBoard({
    roomIndex: room.index,
    kind: 'retos',
    position: [-2.6, 0, room.z - room.depth / 2 + 0.35],
    theme,
    locale: state.locale,
    preview: texts.retos,
    onOpen: actions.openFicha,
  })
  const aprendizajes = fichaBoard({
    roomIndex: room.index,
    kind: 'aprendizajes',
    position: [-half + 0.35, 0, room.z + 1.4],
    rotationY: Math.PI / 2,
    theme,
    locale: state.locale,
    preview: texts.aprendizajes,
    onOpen: actions.openFicha,
  })
  // grieta al pasado, pegada al muro IZQUIERDO
  const portal = pastPortal({
    room,
    position: [-half + 0.1, 0, room.z + room.depth / 2 - 1.4],
    rotationY: Math.PI / 2,
    accent: theme.accent,
    year: def.year,
    locale: state.locale,
    onEnter: actions.enterPast,
  })
  // pilar-atril con la reseña de la etapa, a la DERECHA
  const nota = lecternNotebook({
    roomIndex: room.index,
    position: [half - 1, 0, room.z + 2.9],
    rotationY: -Math.PI / 2,
    theme,
    notebook: { title: texts.title, lines: texts.notebook },
    story: { title: texts.title, paragraphs: texts.resena },
    onOpen: actions.openStory,
  })
  staticColliders.push(footprint(half - 1, room.z + 2.9, 0.7, 0.7))
  for (const prop of [retos, aprendizajes, portal, nota]) {
    group.add(prop.group)
    if (prop.interactable) {
      interactables.push(prop.interactable)
    }
    if (prop.update) {
      updates.push(prop.update)
    }
  }

  // NPCs: equipo en reunion + un dev en ronda (todos distinguibles)
  npcs.push(
    makeNpc({
      skin: '#e8b48c',
      hair: { style: 'ponytail', color: '#3a2a1a' },
      top: '#24466e',
      bottom: '#1c2430',
      accessory: 'tie',
      faceSeed: 71,
      position: [-3.95, 0, room.z + 1.6],
      rotationY: Math.PI / 2,
    }),
    makeNpc({
      skin: '#d9a684',
      hair: { style: 'short', color: '#4a3a28' },
      top: '#3a3f52',
      bottom: '#2a2f3c',
      accessory: 'glasses',
      faceSeed: 83,
      position: [1.6, 0, room.z + 2.6],
      rotationY: -1.1,
    }),
    makeNpc({
      skin: '#c98f6a',
      hair: { style: 'bun', color: '#1c1410' },
      top: '#0e3a80',
      bottom: '#1c2430',
      faceSeed: 97,
      position: [0, 0, room.z - 1],
      path: [
        [0, room.z - 1],
        [-3, room.z - 3],
        [3.2, room.z - 3.4],
      ],
      speed: 0.75,
    }),
  )
  for (const npc of npcs) {
    group.add(npc.group)
    updates.push((t, dt) => npc.update(t, dt))
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
