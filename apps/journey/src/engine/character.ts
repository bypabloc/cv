/**
 * @module character (engine)
 * @description Generador de personajes anime/chibi 100% procedural (cero
 *   .glb): un solo builder parametrizado construye al jugador y a todos los
 *   NPCs. Cara dibujada en CanvasTexture (ojos grandes + parpadeo), 4
 *   estilos de pelo, accesorios, walk/idle por codigo y patrulla por
 *   waypoints. Todo toon + outline (AC-6/AC-7).
 */
import {
  CanvasTexture,
  CircleGeometry,
  ConeGeometry,
  Group,
  Mesh,
  MeshBasicMaterial,
  SphereGeometry,
  SRGBColorSpace,
} from 'three'
import {
  basicMat,
  makeRng,
  mergedBoxes,
  outlineGroup,
  toonMat,
  unitGeo,
} from './toon'

export type HairStyle = 'short' | 'spiky' | 'ponytail' | 'bun'
export type Accessory = 'helmet' | 'glasses' | 'tie' | 'badge'

export interface CharacterSpec {
  skin: string
  hair: { style: HairStyle; color: string }
  top: string
  bottom: string
  accessory?: Accessory
  /** Varia ojos/cejas/boca y la fase del parpadeo deterministicamente. */
  faceSeed: number
}

export interface CharacterHandle {
  group: Group
  setWalking(on: boolean): void
  update(t: number, dt: number): void
  /** POV oculta al jugador. */
  setVisible(on: boolean): void
  dispose(): void
}

export interface NpcHandle {
  group: Group
  update(t: number, dt: number): void
  dispose(): void
}

// full: la sombra la da la direccional (blob apagado); reduced: blob SIEMPRE
let shadowMode: 'cast' | 'blob' = 'cast'

export function configureCharacters(opts: { shadows?: 'cast' | 'blob' }): void {
  if (opts.shadows) {
    shadowMode = opts.shadows
  }
}

// ---------------------------------------------------------------------------
// Cara (canvas 128 transparente, dos texturas: ojos abiertos / cerrados)
// ---------------------------------------------------------------------------

interface FaceParams {
  eyeRx: number
  eyeRy: number
  browTilt: number
  mouthCurve: number
  blush: boolean
}

function faceParams(seed: number): FaceParams {
  const rng = makeRng(seed >>> 0 || 1)
  return {
    eyeRx: 9 + rng() * 4,
    eyeRy: 12 + rng() * 5,
    browTilt: (rng() - 0.5) * 0.5,
    mouthCurve: 2 + rng() * 6,
    blush: rng() > 0.55,
  }
}

function drawEye(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  params: FaceParams,
  closed: boolean,
): void {
  if (closed) {
    ctx.strokeStyle = '#141018'
    ctx.lineWidth = 4
    ctx.beginPath()
    ctx.arc(x, y - 2, params.eyeRx, Math.PI * 0.15, Math.PI * 0.85)
    ctx.stroke()
    return
  }
  // ovalo negro grande estilo anime + brillo + parpado superior
  ctx.fillStyle = '#141018'
  ctx.beginPath()
  ctx.ellipse(x, y, params.eyeRx, params.eyeRy, 0, 0, Math.PI * 2)
  ctx.fill()
  ctx.fillStyle = '#ffffff'
  ctx.beginPath()
  ctx.ellipse(
    x - params.eyeRx * 0.35,
    y - params.eyeRy * 0.4,
    params.eyeRx * 0.32,
    params.eyeRy * 0.28,
    0,
    0,
    Math.PI * 2,
  )
  ctx.fill()
  ctx.strokeStyle = '#141018'
  ctx.lineWidth = 4
  ctx.beginPath()
  ctx.arc(x, y - 3, params.eyeRx + 2, Math.PI * 1.15, Math.PI * 1.85)
  ctx.stroke()
}

function drawFace(
  ctx: CanvasRenderingContext2D,
  size: number,
  spec: CharacterSpec,
  params: FaceParams,
  closed: boolean,
): void {
  ctx.clearRect(0, 0, size, size)
  const eyeY = 58
  const eyeXs: readonly [number, number] = [44, 84]
  for (const x of eyeXs) {
    drawEye(ctx, x, eyeY, params, closed)
  }
  // cejas (trazo de tinta con tilt por seed)
  ctx.strokeStyle = '#141018'
  ctx.lineWidth = 4
  ctx.lineCap = 'round'
  for (const [i, x] of eyeXs.entries()) {
    const dir = i === 0 ? -1 : 1
    ctx.beginPath()
    ctx.moveTo(x - 11, eyeY - 24 + dir * params.browTilt * 8)
    ctx.lineTo(x + 11, eyeY - 24 - dir * params.browTilt * 8)
    ctx.stroke()
  }
  // boca pequeña
  ctx.lineWidth = 3.5
  ctx.beginPath()
  ctx.moveTo(64 - 8, 94)
  ctx.quadraticCurveTo(64, 94 + params.mouthCurve, 64 + 8, 94)
  ctx.stroke()
  // rubor opcional
  if (params.blush) {
    ctx.fillStyle = 'rgba(232,120,120,0.3)'
    for (const x of [30, 98]) {
      ctx.beginPath()
      ctx.ellipse(x, 82, 9, 5, 0, 0, Math.PI * 2)
      ctx.fill()
    }
  }
  // lentes dibujados sobre la cara (accesorio glasses)
  if (spec.accessory === 'glasses') {
    ctx.strokeStyle = '#141018'
    ctx.lineWidth = 3.5
    for (const x of eyeXs) {
      ctx.strokeRect(x - 15, eyeY - 15, 30, 30)
    }
    ctx.beginPath()
    ctx.moveTo(59, eyeY)
    ctx.lineTo(69, eyeY)
    ctx.stroke()
  }
}

function makeFaceTexture(
  spec: CharacterSpec,
  params: FaceParams,
  closed: boolean,
): CanvasTexture {
  const size = 128
  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = size
  const ctx = canvas.getContext('2d')
  if (!ctx) {
    throw new Error('character: canvas 2d context no disponible')
  }
  drawFace(ctx, size, spec, params, closed)
  const texture = new CanvasTexture(canvas)
  texture.colorSpace = SRGBColorSpace
  return texture
}

// ---------------------------------------------------------------------------
// Pelo + accesorios (lo que mas distingue a cada NPC)
// ---------------------------------------------------------------------------

interface OwnedGeos {
  list: { dispose(): void }[]
}

function buildHair(
  head: Group,
  spec: CharacterSpec,
  owned: OwnedGeos,
): Group | null {
  const units = unitGeo()
  const hairMat = toonMat(spec.hair.color)
  // casquete: esfera achatada que envuelve la parte alta de la cabeza
  const cap = new Mesh(units.sphere, hairMat)
  cap.scale.set(0.5, 0.4, 0.5)
  cap.position.set(0, 0.08, -0.02)
  head.add(cap)
  const style = spec.hair.style
  if (style === 'short') {
    for (const x of [-0.12, 0.12]) {
      const lock = new Mesh(units.box, hairMat)
      lock.scale.set(0.07, 0.12, 0.05)
      lock.position.set(x, 0.05, 0.19)
      lock.rotation.x = 0.25
      lock.userData.noOutline = true
      head.add(lock)
    }
    return null
  }
  if (style === 'spiky') {
    const cone = new ConeGeometry(0.055, 0.17, 6)
    owned.list.push(cone)
    const rng = makeRng((spec.faceSeed >>> 0) + 7)
    for (let i = 0; i < 6; i += 1) {
      const spike = new Mesh(cone, hairMat)
      const angle = (i / 6) * Math.PI * 2
      spike.position.set(
        Math.cos(angle) * 0.13,
        0.24 + rng() * 0.03,
        Math.sin(angle) * 0.13 - 0.02,
      )
      spike.rotation.set(Math.sin(angle) * 0.6, 0, -Math.cos(angle) * 0.6)
      spike.userData.noOutline = true
      head.add(spike)
    }
    return null
  }
  if (style === 'ponytail') {
    const tail = new Group()
    tail.position.set(0, 0.12, -0.2)
    const strand = new Mesh(units.cylinder, hairMat)
    strand.scale.set(0.14, 0.34, 0.14)
    strand.position.set(0, -0.16, -0.04)
    strand.rotation.x = 0.35
    strand.userData.noOutline = true
    tail.add(strand)
    const tip = new Mesh(units.sphere, hairMat)
    tip.scale.setScalar(0.15)
    tip.position.set(0, -0.32, -0.1)
    tip.userData.noOutline = true
    tail.add(tip)
    head.add(tail)
    return tail
  }
  // bun
  const bun = new Mesh(units.sphere, hairMat)
  bun.scale.setScalar(0.22)
  bun.position.set(0, 0.24, -0.06)
  head.add(bun)
  return null
}

/** Accesorios de torso van al group (posiciones absolutas, sin heredar la
 *  escala del torso); el casco va sobre el pelo en el head group. */
function buildAccessory(head: Group, group: Group, spec: CharacterSpec): void {
  const units = unitGeo()
  if (spec.accessory === 'helmet') {
    const helmetMat = toonMat('#f2b705')
    const dome = new Mesh(units.sphere, helmetMat)
    dome.scale.set(0.56, 0.42, 0.56)
    dome.position.set(0, 0.12, -0.02)
    const brim = new Mesh(units.cylinder, helmetMat)
    brim.scale.set(0.62, 0.03, 0.62)
    brim.position.set(0, 0.02, -0.02)
    brim.userData.noOutline = true
    head.add(dome, brim)
    return
  }
  if (spec.accessory === 'tie') {
    const tie = new Mesh(units.box, toonMat('#8a2431'))
    tie.scale.set(0.07, 0.26, 0.03)
    tie.position.set(0, 0.86, 0.15)
    tie.userData.noOutline = true
    group.add(tie)
    return
  }
  if (spec.accessory === 'badge') {
    const badge = new Mesh(units.box, basicMat('#e8e2d0'))
    badge.scale.set(0.09, 0.11, 0.02)
    badge.position.set(-0.12, 0.88, 0.14)
    badge.userData.noOutline = true
    group.add(badge)
  }
}

// ---------------------------------------------------------------------------
// Builder principal
// ---------------------------------------------------------------------------

const HIP_Y = 0.52
const SHOULDER_Y = 0.96
const HEAD_Y = 1.22

interface Parts {
  legL: Group
  legR: Group
  armL: Group
  armR: Group
  torso: Mesh
  head: Group
  tail: Group | null
}

// Las extremidades NO llevan hull (presupuesto AC-10): el contorno de
// silueta lo dan cabeza/pelo/torso; las piezas chicas se leen igual.
// Pierna + zapato van fusionados en 1 mesh (mismo material del bottom).
function buildLimb(
  x: number,
  pivotY: number,
  scale: readonly [number, number, number],
  material: ReturnType<typeof toonMat>,
  withShoe: boolean,
  owned?: OwnedGeos,
): Group {
  const units = unitGeo()
  const limb = new Group()
  limb.position.set(x, pivotY, 0)
  if (withShoe && owned) {
    const mesh = mergedBoxes(
      [
        {
          w: scale[0],
          h: scale[1],
          d: scale[2],
          x: 0,
          y: -scale[1] / 2,
          z: 0,
        },
        {
          w: scale[0] + 0.02,
          h: 0.07,
          d: 0.2,
          x: 0,
          y: -scale[1] + 0.035,
          z: 0.04,
        },
      ],
      material,
    )
    mesh.userData.noOutline = true
    owned.list.push(mesh.geometry)
    limb.add(mesh)
    return limb
  }
  const mesh = new Mesh(units.box, material)
  mesh.scale.set(scale[0], scale[1], scale[2])
  mesh.position.y = -scale[1] / 2
  mesh.userData.noOutline = true
  limb.add(mesh)
  return limb
}

/**
 * @function makeCharacter
 * @description Construye un chibi anime (~1.5 m) desde su spec. Proporciones
 *   canon anime (cabeza grande), cara canvas con parpadeo, pelo por estilo,
 *   accesorios y contorno de tinta. Materiales del pool toon (compartidos).
 */
export function makeCharacter(spec: CharacterSpec): CharacterHandle {
  const units = unitGeo()
  const owned: OwnedGeos = { list: [] }
  const group = new Group()

  const legL = buildLimb(
    -0.09,
    HIP_Y,
    [0.13, HIP_Y, 0.16],
    toonMat(spec.bottom),
    true,
    owned,
  )
  const legR = buildLimb(
    0.09,
    HIP_Y,
    [0.13, HIP_Y, 0.16],
    toonMat(spec.bottom),
    true,
    owned,
  )
  const armL = buildLimb(
    -0.26,
    SHOULDER_Y,
    [0.1, 0.4, 0.12],
    toonMat(spec.top),
    false,
  )
  const armR = buildLimb(
    0.26,
    SHOULDER_Y,
    [0.1, 0.4, 0.12],
    toonMat(spec.top),
    false,
  )

  const torso = new Mesh(units.box, toonMat(spec.top))
  torso.scale.set(0.42, 0.48, 0.26)
  torso.position.y = 0.76

  const head = new Group()
  head.position.y = HEAD_Y
  const skull = new Mesh(units.sphere, toonMat(spec.skin))
  skull.scale.setScalar(0.44)
  head.add(skull)

  // cara: parche esferico (sigue la curvatura de la cabeza) con canvas
  const params = faceParams(spec.faceSeed)
  const openTex = makeFaceTexture(spec, params, false)
  const closedTex = makeFaceTexture(spec, params, true)
  const faceGeo = new SphereGeometry(
    0.228,
    12,
    9,
    Math.PI / 2 - 0.75,
    1.5,
    Math.PI / 2 - 0.55,
    1.05,
  )
  owned.list.push(faceGeo)
  const faceMat = new MeshBasicMaterial({ map: openTex, transparent: true })
  const face = new Mesh(faceGeo, faceMat)
  face.userData.noOutline = true
  head.add(face)

  const tail = buildHair(head, spec, owned)
  buildAccessory(head, group, spec)

  group.add(legL, legR, armL, armR, torso, head)

  if (shadowMode === 'cast') {
    group.traverse((obj) => {
      if (obj instanceof Mesh && obj.userData.noOutline !== true) {
        obj.castShadow = true
      }
    })
  } else {
    const blobGeo = new CircleGeometry(0.35, 18)
    owned.list.push(blobGeo)
    const blob = new Mesh(
      blobGeo,
      basicMat('#000000', { transparent: true, opacity: 0.28 }),
    )
    blob.rotation.x = -Math.PI / 2
    blob.position.y = 0.012
    blob.userData.noOutline = true
    group.add(blob)
  }

  outlineGroup(group, 1.05)

  const parts: Parts = { legL, legR, armL, armR, torso, head, tail }
  let walking = false
  let cycle = 0
  const blinkPhase = ((spec.faceSeed % 97) / 97) * 5
  const blinkInterval = 3 + ((spec.faceSeed % 31) / 31) * 3
  let eyesClosed = false

  function poseWalk(dt: number): void {
    cycle += dt
    const swing = Math.sin(cycle * 7)
    parts.legL.rotation.x = swing * 0.6
    parts.legR.rotation.x = -swing * 0.6
    parts.armL.rotation.x = -swing * 0.48
    parts.armR.rotation.x = swing * 0.48
    group.position.y = Math.abs(swing) * 0.03
    group.rotation.x = 0.05
  }

  function poseIdle(t: number, dt: number): void {
    const decay = Math.min(1, dt * 8)
    parts.legL.rotation.x *= 1 - decay
    parts.legR.rotation.x *= 1 - decay
    parts.armL.rotation.x = Math.sin(t * 1.6) * 0.06
    parts.armR.rotation.x = -Math.sin(t * 1.6) * 0.06
    group.position.y = Math.sin(t * 1.6) * 0.012
    group.rotation.x = 0
    // respiracion: el torso "late" apenas
    parts.torso.scale.y = 0.48 * (1 + Math.sin(t * 1.6) * 0.012)
  }

  function updateBlink(t: number): void {
    const closed = (t + blinkPhase) % blinkInterval < 0.12
    if (closed !== eyesClosed) {
      eyesClosed = closed
      faceMat.map = closed ? closedTex : openTex
    }
  }

  return {
    group,
    setWalking(on) {
      walking = on
    },
    update(t, dt) {
      if (walking) {
        poseWalk(dt)
      } else {
        poseIdle(t, dt)
      }
      if (parts.tail) {
        parts.tail.rotation.z = Math.sin(t * 2.2) * 0.12
      }
      updateBlink(t)
    },
    setVisible(on) {
      group.visible = on
    },
    dispose() {
      openTex.dispose()
      closedTex.dispose()
      faceMat.dispose()
      for (const geo of owned.list) {
        geo.dispose()
      }
    },
  }
}

// ---------------------------------------------------------------------------
// NPCs (idle o patrulla por waypoints — port de moveAlongPath)
// ---------------------------------------------------------------------------

export interface NpcOpts extends CharacterSpec {
  position: readonly [number, number, number]
  /** Waypoints XZ: con 2+ puntos patrulla el loop; sin path, idle. */
  path?: readonly (readonly [number, number])[]
  rotationY?: number
  speed?: number
}

/** Avanza por los waypoints en loop a velocidad constante y orienta. */
function moveAlongPath(
  root: Group,
  points: readonly (readonly [number, number])[],
  t: number,
  speed: number,
): void {
  let total = 0
  const lengths: number[] = []
  for (let i = 0; i < points.length; i += 1) {
    const a = points[i]
    const b = points[(i + 1) % points.length]
    const len = a && b ? Math.hypot(b[0] - a[0], b[1] - a[1]) : 0
    lengths.push(len)
    total += len
  }
  if (total === 0) {
    return
  }
  let dist = (t * speed) % total
  let segment = 0
  while (segment < lengths.length && dist > (lengths[segment] ?? 0)) {
    dist -= lengths[segment] ?? 0
    segment += 1
  }
  const a = points[segment % points.length]
  const b = points[(segment + 1) % points.length]
  const len = lengths[segment % lengths.length] ?? 1
  if (!a || !b) {
    return
  }
  const k = len > 0 ? dist / len : 0
  root.position.x = a[0] + (b[0] - a[0]) * k
  root.position.z = a[1] + (b[1] - a[1]) * k
  root.rotation.y = Math.atan2(b[0] - a[0], b[1] - a[1])
}

export function makeNpc(opts: NpcOpts): NpcHandle {
  const character = makeCharacter(opts)
  const { group } = character
  group.position.set(opts.position[0], opts.position[1], opts.position[2])
  group.rotation.y = opts.rotationY ?? 0
  // fase estable por instancia (evita NPCs sincronizados)
  const phase =
    (opts.position[0] * 7.3 + opts.position[2] * 3.1) % (Math.PI * 2)
  const walking = (opts.path?.length ?? 0) >= 2
  const speed = opts.speed ?? 0.7
  character.setWalking(walking)

  return {
    group,
    update(t, dt) {
      const tt = t + phase
      if (walking && opts.path) {
        moveAlongPath(group, opts.path, tt, speed)
      } else {
        group.rotation.y = (opts.rotationY ?? 0) + Math.sin(tt * 0.7) * 0.08
      }
      character.update(tt, dt)
    },
    dispose() {
      character.dispose()
    },
  }
}
