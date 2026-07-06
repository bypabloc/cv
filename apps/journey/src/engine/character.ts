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
  Euler,
  Group,
  Matrix4,
  Mesh,
  MeshBasicMaterial,
  Quaternion,
  SphereGeometry,
  SRGBColorSpace,
  Vector3,
} from 'three'
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js'
import type { Box2 } from '../lib/collision'
import { sfx } from './audio'
import { basicMat, makeRng, outlineGroup, toonMat, unitGeo } from './toon'

export type HairStyle = 'short' | 'spiky' | 'ponytail' | 'bun'
export type Accessory = 'helmet' | 'glasses' | 'tie' | 'badge'
/**
 * Poses fijas ademas de idle/walk: fight = kihon de karate (tsuki + mae
 * geri), sit = sentado en silla tipeando, kneel = arrodillado trabajando,
 * wave = saludo con el brazo, talk = gesticulando en conversacion.
 */
export type CharacterPose =
  | 'idle'
  | 'walk'
  | 'fight'
  | 'sit'
  | 'kneel'
  | 'wave'
  | 'talk'

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
  setPose(pose: CharacterPose): void
  /** Giro extra de cabeza (mirar al jugador sin girar el cuerpo). */
  setHeadYaw(yaw: number | null): void
  update(t: number, dt: number): void
  /** POV oculta al jugador. */
  setVisible(on: boolean): void
  dispose(): void
}

export interface NpcHandle {
  group: Group
  update(t: number, dt: number): void
  /** AABB alrededor de la posicion ACTUAL (bloquea el paso del jugador). */
  collider(): Box2
  /** Modo conversacion: pausa patrulla/sway, mira al jugador y saluda. */
  talk(player?: { x: number; z: number }): void
  /** Cierra la conversacion y retoma patrulla/pose original. */
  endTalk(): void
  /** Salto one-shot (arco ~0.55 s) montado sobre la pose actual. */
  jump(): void
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
  // cejas: arcos suaves y SIMETRICOS (tilt sutil por seed, espejado)
  ctx.strokeStyle = '#141018'
  ctx.lineWidth = 3.5
  ctx.lineCap = 'round'
  for (const [i, x] of eyeXs.entries()) {
    const dir = i === 0 ? -1 : 1
    const tilt = dir * params.browTilt * 4
    ctx.beginPath()
    ctx.moveTo(x - 10, eyeY - 21 + tilt)
    ctx.quadraticCurveTo(x, eyeY - 28, x + 10, eyeY - 21 - tilt)
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
    // C15: los 6 pinchos van FUSIONADOS en una geometry (1 draw call en
    // vez de 6) — la pose de cada uno se hornea con su matrix
    const cone = new ConeGeometry(0.055, 0.17, 6)
    const rng = makeRng((spec.faceSeed >>> 0) + 7)
    const one = new Vector3(1, 1, 1)
    const spikes = Array.from({ length: 6 }, (_, i) => {
      const angle = (i / 6) * Math.PI * 2
      const geo = cone.clone()
      geo.applyMatrix4(
        new Matrix4().compose(
          new Vector3(
            Math.cos(angle) * 0.13,
            0.24 + rng() * 0.03,
            Math.sin(angle) * 0.13 - 0.02,
          ),
          new Quaternion().setFromEuler(
            new Euler(Math.sin(angle) * 0.6, 0, -Math.cos(angle) * 0.6),
          ),
          one,
        ),
      )
      return geo
    })
    cone.dispose()
    const merged = mergeGeometries(spikes)
    for (const geo of spikes) {
      geo.dispose()
    }
    owned.list.push(merged)
    const mesh = new Mesh(merged, hairMat)
    mesh.userData.noOutline = true
    head.add(mesh)
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
// Cuerpos REDONDEADOS: capsulas compartidas del pool (nada de cajas).
function buildLimb(
  x: number,
  pivotY: number,
  kind: 'leg' | 'arm',
  material: ReturnType<typeof toonMat>,
): Group {
  const units = unitGeo()
  const limb = new Group()
  limb.position.set(x, pivotY, 0)
  const geometry = kind === 'leg' ? units.capsuleLeg : units.capsuleArm
  // media altura del capsule (largo + 2 radios) para colgar del pivote
  const half = kind === 'leg' ? 0.25 : 0.195
  const mesh = new Mesh(geometry, material)
  mesh.position.y = -half
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

  const legL = buildLimb(-0.09, HIP_Y, 'leg', toonMat(spec.bottom))
  const legR = buildLimb(0.09, HIP_Y, 'leg', toonMat(spec.bottom))
  const armL = buildLimb(-0.26, SHOULDER_Y, 'arm', toonMat(spec.top))
  const armR = buildLimb(0.26, SHOULDER_Y, 'arm', toonMat(spec.top))

  // torso capsula (redondeado, canon chibi), aplanado hacia el frente
  const torso = new Mesh(units.capsuleTorso, toonMat(spec.top))
  torso.scale.set(1.3, 1, 0.8)
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
  let pose: CharacterPose = 'idle'
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
    // respiracion: el torso "late" apenas (base de la capsula = 1)
    parts.torso.scale.y = 1 + Math.sin(t * 1.6) * 0.012
  }

  /** Kihon: 3 tsuki alternados (golpes rectos) + mae geri (patada).
   *  rotation.x NEGATIVO lleva la extremidad al FRENTE (+Z local): los
   *  golpes/patada salen hacia adelante (antes iban a la espalda). */
  function poseFight(t: number): void {
    const beat = t % 3.6
    let punchL = 0
    let punchR = 0
    let kickR = 0
    if (beat < 2.4) {
      // sin(beat·π·1.25) cierra en 0 justo a los 2.4 s (sin salto)
      const punch = Math.sin(beat * Math.PI * 1.25)
      punchL = Math.max(0, punch) * 1.5
      punchR = Math.max(0, -punch) * 1.5
    } else {
      const kick = Math.sin(((beat - 2.4) / 1.2) * Math.PI)
      kickR = kick * 1.35
      punchL = kick * 0.5
      punchR = kick * 0.5
    }
    parts.armL.rotation.x = -punchL
    parts.armR.rotation.x = -punchR
    parts.legR.rotation.x = -kickR
    parts.legL.rotation.x = 0
    group.position.y = Math.abs(Math.sin(t * 6)) * 0.012
    group.rotation.x = 0
    parts.torso.scale.y = 1
  }

  /** Saludo: brazo derecho arriba oscilando (entrada a la conversacion). */
  function poseWave(t: number): void {
    parts.legL.rotation.x = 0
    parts.legR.rotation.x = 0
    parts.armL.rotation.x = 0
    parts.armR.rotation.x = -2.7
    parts.armR.rotation.z = Math.sin(t * 9) * 0.35
    group.position.y = Math.abs(Math.sin(t * 9)) * 0.02
    group.rotation.x = 0
    parts.torso.scale.y = 1
  }

  /** Conversando: gesticula con los brazos y asiente con la cabeza. */
  function poseTalk(t: number): void {
    parts.legL.rotation.x = 0
    parts.legR.rotation.x = 0
    parts.armL.rotation.x = -0.5 + Math.sin(t * 3.1) * 0.25
    parts.armR.rotation.x = -0.65 + Math.cos(t * 2.6) * 0.3
    parts.head.rotation.x = Math.sin(t * 2.2) * 0.06
    group.position.y = Math.sin(t * 1.8) * 0.015
    group.rotation.x = 0
    parts.torso.scale.y = 1 + Math.sin(t * 1.6) * 0.012
  }

  /** Sentado en silla (tipeando) o arrodillado en el piso (trabajando). */
  function poseSeated(t: number, kind: 'sit' | 'kneel'): void {
    const sitting = kind === 'sit'
    // rotation.x NEGATIVO lleva la extremidad hacia +Z (el frente del
    // chibi). sit: muslos AL FRENTE a altura de asiento; kneel: piernas
    // casi verticales con leve avance (rodillas al frente) y el cuerpo
    // bajado — el tramo bajo el piso no se ve y lee como "de rodillas"
    // (antes +1.0 doblaba las piernas hacia ATRAS: se veian invertidas).
    parts.legL.rotation.x = sitting ? -1.45 : -0.22
    parts.legR.rotation.x = sitting ? -1.45 : -0.22
    group.position.y = sitting ? -0.07 : -0.26
    // brazos hacia ADELANTE (teclado / la unidad que repara)
    const base = sitting ? -0.85 : -0.7
    const speed = sitting ? 9 : 5
    const amp = sitting ? 0.07 : 0.18
    parts.armL.rotation.x = base - Math.sin(t * speed) * amp
    parts.armR.rotation.x = base - Math.cos(t * speed * 0.9) * amp
    group.rotation.x = 0
    parts.torso.scale.y = 1 + Math.sin(t * 1.6) * 0.012
  }

  function updateBlink(t: number): void {
    const closed = (t + blinkPhase) % blinkInterval < 0.12
    if (closed !== eyesClosed) {
      eyesClosed = closed
      faceMat.map = closed ? closedTex : openTex
    }
  }

  let headYaw: number | null = null

  function applyPose(t: number, dt: number): void {
    if (pose === 'walk') {
      poseWalk(dt)
    } else if (pose === 'fight') {
      poseFight(t)
    } else if (pose === 'sit' || pose === 'kneel') {
      poseSeated(t, pose)
    } else if (pose === 'wave') {
      poseWave(t)
    } else if (pose === 'talk') {
      poseTalk(t)
    } else {
      poseIdle(t, dt)
    }
  }

  return {
    group,
    setWalking(on) {
      pose = on ? 'walk' : 'idle'
    },
    setPose(next) {
      pose = next
    },
    setHeadYaw(yaw) {
      headYaw = yaw
    },
    update(t, dt) {
      applyPose(t, dt)
      const decay = Math.min(1, dt * 8)
      if (pose !== 'wave') {
        parts.armR.rotation.z *= 1 - decay
      }
      if (pose !== 'talk') {
        parts.head.rotation.x *= 1 - decay
      }
      // mirar al jugador: la cabeza gira suave hacia el yaw pedido
      parts.head.rotation.y += ((headYaw ?? 0) - parts.head.rotation.y) * decay
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
  /** Pose fija (sin path): fight / sit / kneel. Sin pose: idle con sway. */
  pose?: 'fight' | 'sit' | 'kneel'
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

let npcSeq = 0

/** Duracion (s) del arco de salto one-shot de un NPC. */
const JUMP_DURATION = 0.55

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
  if (walking) {
    character.setWalking(true)
  } else if (opts.pose) {
    character.setPose(opts.pose)
  }

  // sonido: pasos por zancada (caminantes) / tecleo (sentados a la PC),
  // ambos con volumen por cercania al jugador (sfx keep-alive)
  npcSeq += 1
  const sfxId = `npc-${npcSeq}`
  let stride = 0
  let prevX = opts.position[0]
  let prevZ = opts.position[2]

  // conversacion: reloj de patrulla propio (se congela al hablar), giro
  // hacia el jugador (cuerpo de pie / solo cabeza si esta sentado) y
  // saludo breve antes de gesticular
  const seated = opts.pose === 'sit' || opts.pose === 'kneel'
  let talking = false
  let faceYaw = opts.rotationY ?? 0
  let waveLeft = 0
  let jumpLeft = 0
  let walkTime = phase

  const NPC_RADIUS = 0.26

  /** Conversando: gira suave hacia el jugador y pasa de wave a talk. */
  function updateTalking(dt: number): void {
    if (seated) {
      return
    }
    let delta = faceYaw - group.rotation.y
    delta = Math.atan2(Math.sin(delta), Math.cos(delta))
    group.rotation.y += delta * Math.min(1, dt * 10)
    if (waveLeft > 0) {
      waveLeft -= dt
      if (waveLeft <= 0) {
        character.setPose('talk')
      }
    }
  }

  /** Patrulla por waypoints con reloj propio + pasos por zancada. */
  function updatePatrol(dt: number): void {
    if (!opts.path) {
      return
    }
    walkTime += dt
    moveAlongPath(group, opts.path, walkTime, speed)
    stride += Math.hypot(group.position.x - prevX, group.position.z - prevZ)
    prevX = group.position.x
    prevZ = group.position.z
    if (stride > 0.62) {
      stride = 0
      sfx.stepAt(group.position.x, group.position.z)
    }
  }

  /** Salto: arco sobre lo que la pose haya decidido para position.y. */
  function applyJump(dt: number): void {
    if (jumpLeft <= 0) {
      return
    }
    jumpLeft = Math.max(0, jumpLeft - dt)
    const progress = 1 - jumpLeft / JUMP_DURATION
    group.position.y += Math.sin(progress * Math.PI) * 0.5
  }

  return {
    group,
    update(t, dt) {
      const tt = t + phase
      if (talking) {
        updateTalking(dt)
      } else if (walking && opts.path) {
        updatePatrol(dt)
      } else if (!opts.pose) {
        // con pose fija no hay sway: esta concentrado en lo suyo
        group.rotation.y = (opts.rotationY ?? 0) + Math.sin(tt * 0.7) * 0.08
      } else if (opts.pose === 'sit') {
        sfx.feed(sfxId, 'typing', group.position.x, group.position.z)
      }
      character.update(tt, dt)
      applyJump(dt)
    },
    collider() {
      return {
        minX: group.position.x - NPC_RADIUS,
        maxX: group.position.x + NPC_RADIUS,
        minZ: group.position.z - NPC_RADIUS,
        maxZ: group.position.z + NPC_RADIUS,
      }
    },
    talk(player) {
      talking = true
      if (player) {
        faceYaw = Math.atan2(
          player.x - group.position.x,
          player.z - group.position.z,
        )
        if (seated) {
          let rel = faceYaw - group.rotation.y
          rel = Math.atan2(Math.sin(rel), Math.cos(rel))
          character.setHeadYaw(Math.min(Math.max(rel, -1.1), 1.1))
        }
      }
      if (walking) {
        character.setWalking(false)
      }
      if (!seated) {
        character.setPose('wave')
        waveLeft = 0.9
      }
    },
    endTalk() {
      talking = false
      waveLeft = 0
      character.setHeadYaw(null)
      if (walking) {
        character.setWalking(true)
      } else if (opts.pose) {
        character.setPose(opts.pose)
        group.rotation.y = opts.rotationY ?? 0
      } else {
        character.setPose('idle')
      }
    },
    jump() {
      jumpLeft = JUMP_DURATION
    },
    dispose() {
      character.dispose()
    },
  }
}
