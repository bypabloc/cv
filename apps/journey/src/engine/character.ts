/**
 * @module character (engine)
 * @description Personajes estilo Spider-Verse (docs/specs/journey-spiderverse-style/):
 *   humanoide riggeado CC0 (Quaternius "Hoodie Character", ver
 *   public/models/characters/CREDITS.md) cargado UNA vez y clonado por
 *   instancia via SkeletonUtils. El estado de alto nivel (patrulla,
 *   conversacion, salto, sfx) es el MISMO state machine del sistema
 *   procedural anterior — solo cambia como se anima el cuerpo (AnimationMixer
 *   + clips reales en vez de rotar limbs a mano).
 */

import type { AnimationAction, AnimationClip, Material } from 'three'
import {
  AnimationMixer,
  Color,
  Group,
  Mesh,
  MeshStandardMaterial,
  type Object3D,
  SkinnedMesh,
} from 'three'
import { clone as cloneSkeleton } from 'three/examples/jsm/utils/SkeletonUtils.js'
import type { Box2 } from '../lib/collision'
import { sfx } from './audio'
import { gltfLoader } from './loaders'
import { skinnedOutline, toonMat } from './toon'

export type HairStyle = 'short' | 'spiky' | 'ponytail' | 'bun'
export type Accessory = 'helmet' | 'glasses' | 'tie' | 'badge'
/**
 * Poses fijas ademas de idle/walk: fight = golpe repetido, sit/kneel =
 * aproximados a idle (el pack Quaternius no trae esos clips — riesgo 2 de
 * docs/specs/journey-spiderverse-style/05-riesgos-y-decisiones-abiertas.md),
 * wave = saludo, talk = gesticulando (clip Interact).
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
  /** Sin uso en el modelo GLB (se preserva por compatibilidad de API). */
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

// full: la sombra la da la direccional; reduced: sin sombra en el personaje
// (blob queda pendiente de reintroducir sobre el GLB — riesgo menor)
let shadowMode: 'cast' | 'blob' = 'cast'

export function configureCharacters(opts: { shadows?: 'cast' | 'blob' }): void {
  if (opts.shadows) {
    shadowMode = opts.shadows
  }
}

// ---------------------------------------------------------------------------
// Carga del modelo base (una vez, cacheada — todas las instancias clonan)
// ---------------------------------------------------------------------------

const MODEL_URL = '/models/characters/base.glb'
const CLIP_PREFIX = 'CharacterArmature|'

const POSE_CLIP: Record<CharacterPose, string> = {
  idle: `${CLIP_PREFIX}Idle`,
  walk: `${CLIP_PREFIX}Walk`,
  fight: `${CLIP_PREFIX}Punch_Left`,
  sit: `${CLIP_PREFIX}Idle`,
  kneel: `${CLIP_PREFIX}Idle`,
  wave: `${CLIP_PREFIX}Wave`,
  talk: `${CLIP_PREFIX}Interact`,
}

interface LoadedModel {
  scene: Object3D
  animations: AnimationClip[]
}

let modelPromise: Promise<LoadedModel> | null = null

function loadModel(): Promise<LoadedModel> {
  if (!modelPromise) {
    modelPromise = gltfLoader
      .loadAsync(MODEL_URL)
      .then((gltf) => ({ scene: gltf.scene, animations: gltf.animations }))
  }
  return modelPromise
}

/**
 * Lleva un color a rango PASTEL: piso de luminosidad + techo de saturacion.
 * El pack Quaternius trae partes casi negras (#1a1410, #2c2018) que
 * `toonifyMesh` no recolorea; sin esto los NPCs se ven negros bajo el toon
 * shading. Pedido del dueno (2026-07-07): paleta clara/pastel.
 */
function pastelize(hex: string): string {
  const color = new Color(hex)
  const hsl = { h: 0, s: 0, l: 0 }
  color.getHSL(hsl)
  color.setHSL(hsl.h, Math.min(hsl.s, 0.68), Math.max(hsl.l, 0.56))
  return `#${color.getHexString()}`
}

/** Slots de material del pack Quaternius que se retinen por CharacterSpec. */
function colorForSlot(
  materialName: string,
  spec: CharacterSpec,
): string | null {
  if (materialName === 'Purple') {
    return spec.top
  }
  if (materialName === 'LightBlue') {
    return spec.bottom
  }
  if (materialName === 'Skin') {
    return spec.skin
  }
  if (materialName === 'Hair') {
    return spec.hair.color
  }
  return null
}

/**
 * @function toonifyMesh
 * @description Reemplaza el material PBR del GLB (MeshStandardMaterial,
 *   metalness ~0.4 sin environment map -> renderiza negro) por el
 *   MeshToonMaterial pooled del proyecto — mismo lenguaje de shading que
 *   paredes/props, y evita el problema de PBR sin IBL. Los slots mapeados
 *   por CharacterSpec (Purple/LightBlue/Skin/Hair) toman el color de la
 *   spec; el resto conserva el color base del material original.
 */
function toonifyMesh(mesh: Mesh, spec: CharacterSpec): void {
  const applyOne = (material: Material): Material => {
    if (!(material instanceof MeshStandardMaterial)) {
      return material
    }
    const hex =
      colorForSlot(material.name, spec) ?? `#${material.color.getHexString()}`
    return toonMat(pastelize(hex))
  }
  mesh.material = Array.isArray(mesh.material)
    ? mesh.material.map(applyOne)
    : applyOne(mesh.material)
}

// ---------------------------------------------------------------------------
// Builder principal
// ---------------------------------------------------------------------------

/**
 * @function makeCharacter
 * @description Crea el handle SINCRONO (grupo vacio) y puebla el modelo
 *   GLB de forma asincrona apenas resuelve la carga compartida — el
 *   contrato publico no cambia (AC-5): quien llama sigue recibiendo un
 *   `CharacterHandle` usable de inmediato.
 */
export function makeCharacter(spec: CharacterSpec): CharacterHandle {
  const group = new Group()
  let mixer: AnimationMixer | null = null
  const clipMap = new Map<string, AnimationClip>()
  let currentAction: AnimationAction | null = null
  let pose: CharacterPose = 'idle'
  let headYaw: number | null = null
  let headBone: Object3D | null = null
  let disposed = false

  function playClip(name: string): void {
    const clip = clipMap.get(name)
    if (!mixer || !clip) {
      return
    }
    const next = mixer.clipAction(clip)
    next.reset()
    next.fadeIn(0.2)
    next.play()
    if (currentAction && currentAction !== next) {
      currentAction.fadeOut(0.2)
    }
    currentAction = next
  }

  loadModel()
    .then((model) => {
      if (disposed) {
        return
      }
      const clone = cloneSkeleton(model.scene)
      const skinnedMeshes: SkinnedMesh[] = []
      clone.traverse((obj: Object3D) => {
        if (obj instanceof Mesh) {
          // SkeletonUtils.clone COMPARTE la geometry con el modelo cacheado:
          // marcarla shared evita que el disposeDeep de una sala la libere
          // (corromperia el resto de instancias que clonan la misma geometry).
          obj.geometry.userData.shared = true
          obj.castShadow = shadowMode === 'cast'
          toonifyMesh(obj, spec)
        }
        if (obj instanceof SkinnedMesh) {
          skinnedMeshes.push(obj)
        }
        if (obj.name === 'Head') {
          headBone = obj
        }
      })
      // contorno de tinta barato: un shell skinned por mesh (comparte esqueleto
      // y geometry), agregado como HERMANO con el mismo TRS del source para
      // que coincidan. Reemplaza al OutlinePass (5 pasadas fullscreen).
      for (const source of skinnedMeshes) {
        const shell = skinnedOutline(source)
        shell.position.copy(source.position)
        shell.quaternion.copy(source.quaternion)
        shell.scale.copy(source.scale)
        source.parent?.add(shell)
      }
      group.add(clone)
      mixer = new AnimationMixer(clone)
      for (const clip of model.animations) {
        clipMap.set(clip.name, clip)
      }
      playClip(POSE_CLIP[pose])
    })
    .catch((err: unknown) => {
      console.error('[character] no se pudo cargar el modelo base', err)
    })

  return {
    group,
    setWalking(on) {
      pose = on ? 'walk' : 'idle'
      playClip(POSE_CLIP[pose])
    },
    setPose(next) {
      pose = next
      playClip(POSE_CLIP[pose])
    },
    setHeadYaw(yaw) {
      headYaw = yaw
    },
    update(_t, dt) {
      mixer?.update(dt)
      if (headBone) {
        const target = headYaw ?? 0
        const decay = Math.min(1, dt * 8)
        headBone.rotation.y += (target - headBone.rotation.y) * decay
      }
    },
    setVisible(on) {
      group.visible = on
    },
    dispose() {
      disposed = true
      mixer?.stopAllAction()
    },
  }
}

// ---------------------------------------------------------------------------
// NPCs (idle o patrulla por waypoints — mismo state machine que antes)
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

  // throttle de animacion: los NPCs de fondo (idle/sentados, sin hablar)
  // avanzan el mixer a ~22 fps (imperceptible en un idle lento, baja el CPU
  // con varios NPCs por sala). El rig a fondo se "jala" al interactuar: al
  // hablar o caminar la animacion vuelve a full rate.
  const ANIM_STEP = 1 / 22
  let animAccum = 0

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

  /** Avanza el mixer: full rate al interactuar/caminar, ~22 fps de fondo. */
  function advanceAnim(tt: number, dt: number): void {
    if (talking || walking) {
      character.update(tt, dt)
      return
    }
    animAccum += dt
    if (animAccum >= ANIM_STEP) {
      character.update(tt, animAccum)
      animAccum = 0
    }
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
      advanceAnim(tt, dt)
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
