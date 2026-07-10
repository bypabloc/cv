/**
 * @module character (engine)
 * @description Personajes cel-shaded (docs/specs/journey-spiderverse-style/):
 *   cuerpos humanoides Mixamo CC0 con CARA PINTADA (textura), rig
 *   `mixamorig:*` NATIVO — las animaciones (tambien de Mixamo) se aplican
 *   sin retarget. Cada GLB (cuerpo + su set de clips ya mergeados en Blender,
 *   ver scripts/blender/build-character.py) se carga UNA vez y se clona por
 *   instancia via SkeletonUtils. El look Arcane-lite lo da MeshToonMaterial
 *   con la textura de cara como `map` + gradientMap de bandas duras
 *   (CHARACTER_GRADIENT). El state machine de alto nivel (patrulla,
 *   conversacion, salto, sfx) es el MISMO del sistema anterior.
 */

import type { AnimationAction, AnimationClip, Material } from 'three'
import {
  AnimationMixer,
  Color,
  Group,
  Mesh,
  MeshStandardMaterial,
  type Object3D,
} from 'three'
import { clone as cloneSkeleton } from 'three/examples/jsm/utils/SkeletonUtils.js'
import type { Box2 } from '../lib/collision'
import { sfx } from './audio'
import { gltfLoader } from './loaders'
import { CHARACTER_GRADIENT, toonMat } from './toon'

export type HairStyle = 'short' | 'spiky' | 'ponytail' | 'bun'
export type Accessory = 'helmet' | 'glasses' | 'tie' | 'badge'
/**
 * Poses del recorrido. Cada una mapea a un clip Mixamo real (POSE_CLIP).
 * Base: idle/walk/sit/wave/talk/typing. Extendidas por el mapeo de salas
 * (tmp/mixamo/*.md): crisis del pasado de cada oficina, facetas del pasado
 * del aula (karate/gamer/tecnico), cruce de portal, telefono, futuro.
 * Un clip ausente en un GLB cae a 'idle' (fallback en playPose).
 */
export type CharacterPose =
  | 'idle'
  | 'walk'
  | 'sit'
  | 'kneel'
  | 'standUp'
  | 'wave'
  | 'talk'
  | 'typing'
  | 'sitTalk'
  | 'phone'
  | 'point'
  | 'write'
  // pasado del aula (facetas de Pablo)
  | 'fight'
  | 'karateKick'
  | 'punch'
  | 'gaming'
  | 'acLookUp'
  | 'carryBox'
  // crisis del pasado de las oficinas
  | 'panic'
  | 'shocked'
  | 'argue'
  | 'yelling'
  | 'frustrated'
  | 'defeated'
  | 'injured'
  | 'nervous'
  | 'disbelief'
  | 'shoved'
  // futuro
  | 'relaxed'
  | 'stretch'
  // cruce de portal
  | 'portal'

/**
 * Cuerpos GLB CC0 disponibles (Mixamo Characters, rig mixamorig nativo, ver
 * public/models/characters/CREDITS.md). 23 cuerpos con cara pintada: elenco
 * casual/oficina (hombres + mujeres) + roles tematicos (salud, obra, jefe,
 * ejecutiva, profesora). 'base' = el cuerpo del jugador Pablo (+ sus facetas
 * en el pasado del aula). Los nombres antiguos (male-casual/female-office/...)
 * se conservan como ALIAS de compatibilidad (MODEL_ALIAS) mientras se migra
 * el reparto de las salas.
 */
export type CharacterModel =
  // elenco base — casual / oficina
  | 'base'
  | 'brian'
  | 'james'
  | 'adam'
  | 'leonard'
  | 'josh'
  | 'bryce'
  | 'david'
  | 'lewis'
  | 'louise'
  | 'kate'
  | 'michelle'
  | 'sophie'
  | 'jackie'
  | 'elizabeth'
  | 'claire'
  | 'suzie'
  // roles tematicos
  | 'chad' // enfermero (scrubs)
  | 'pete' // obrero (chaleco + casco)
  | 'the-boss' // obrero/capataz (rustico)
  | 'joe' // jefe (traje)
  | 'roth' // formal / ingeniero
  | 'jennifer' // ejecutiva
  | 'martha' // profesora / supervisora (mayor)
  // alias de compatibilidad (reparto viejo Quaternius -> Mixamo)
  | 'male-casual'
  | 'male-suit'
  | 'male-worker'
  | 'female-casual'
  | 'female-office'
  | 'female-worker'

export interface CharacterSpec {
  skin: string
  hair: { style: HairStyle; color: string }
  top: string
  bottom: string
  accessory?: Accessory
  /** Cuerpo GLB (default 'base' = Pablo, Hoodie masculino). */
  model?: CharacterModel
  /** Sin uso en el modelo GLB (se preserva por compatibilidad de API). */
  faceSeed: number
}

/**
 * Velocidad (m/s) a la que "camina" el clip Walk de Mixamo: medido en Blender
 * (avance del root Hips 1.84 m en 2.03 s del ciclo). El sistema mueve al NPC
 * por codigo a otra velocidad; para que los pies NO patinen, el clip Walk se
 * reproduce con timeScale = velocidadReal / WALK_CLIP_SPEED (mas lento si el
 * NPC avanza mas despacio). Ver setWalkSpeed.
 */
const WALK_CLIP_SPEED = 0.91

export interface CharacterHandle {
  group: Group
  setWalking(on: boolean): void
  /** Velocidad real (m/s) del NPC: calibra el timeScale del clip Walk para
   *  que la cadencia de pasos coincida con el avance (sin patinaje). */
  setWalkSpeed(metersPerSecond: number): void
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
  /** Cambia la pose ACTUAL (ej. una secuencia de combate del karateka). No
   *  interfiere con el estado de patrulla/talk: al hablar/endTalk se retoma
   *  la logica normal. Sin efecto si el NPC esta hablando. */
  setPose(pose: CharacterPose): void
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

/**
 * Alias del reparto viejo (nombres genericos Quaternius) -> un cuerpo Mixamo
 * concreto. Permite que las salas que todavia usan `male-casual`/`female-office`
 * carguen sin editar, hasta migrar el reparto sala por sala.
 */
const MODEL_ALIAS: Record<string, CharacterModel> = {
  'male-casual': 'brian',
  'male-suit': 'joe',
  'male-worker': 'pete',
  'female-casual': 'kate',
  'female-office': 'louise',
  'female-worker': 'jennifer',
}

function resolveModel(model: CharacterModel): CharacterModel {
  return MODEL_ALIAS[model] ?? model
}

function modelUrl(model: CharacterModel): string {
  return `/models/characters/${resolveModel(model)}.glb`
}

/**
 * Pose -> nombre base del clip Mixamo (el mergeado por build-character.py).
 * El exporter glTF de Blender le agrega el sufijo `_Body` al nombre de la
 * Action -> `normalizeClipName` lo quita al indexar. Un clip que un GLB no
 * incluye (porque ese cuerpo no lo usa) cae a 'Idle' en playPose.
 */
const POSE_CLIP: Record<CharacterPose, string> = {
  idle: 'Idle',
  walk: 'Walk',
  sit: 'Sit',
  kneel: 'Sit',
  standUp: 'StandUpDesk',
  wave: 'Wave',
  talk: 'Talk',
  typing: 'Typing',
  sitTalk: 'SittingTalking',
  phone: 'PhoneUse',
  point: 'Pointing',
  write: 'Writing',
  fight: 'KarateIdle',
  karateKick: 'KarateKick',
  punch: 'FightPunch',
  gaming: 'Gaming',
  acLookUp: 'AcLookUp',
  carryBox: 'CarryBox',
  panic: 'PanicRun',
  shocked: 'Shocked',
  argue: 'AngryArgue',
  yelling: 'Yelling',
  frustrated: 'Frustrated',
  defeated: 'DefeatedCollapse',
  injured: 'InjuredIdle',
  nervous: 'NervousWait',
  disbelief: 'Disbelief',
  shoved: 'ShovedReaction',
  relaxed: 'RelaxedIdle',
  stretch: 'Stretching',
  portal: 'PortalFloat',
}

/** El exporter glTF agrega `_Body` al nombre de la Action; se normaliza. */
function normalizeClipName(name: string): string {
  return name.endsWith('_Body') ? name.slice(0, -'_Body'.length) : name
}

interface LoadedModel {
  scene: Object3D
  animations: AnimationClip[]
}

const modelPromises = new Map<CharacterModel, Promise<LoadedModel>>()

function loadModel(model: CharacterModel): Promise<LoadedModel> {
  const real = resolveModel(model)
  let promise = modelPromises.get(real)
  if (!promise) {
    promise = gltfLoader
      .loadAsync(modelUrl(real))
      .then((gltf) => ({ scene: gltf.scene, animations: gltf.animations }))
    modelPromises.set(real, promise)
  }
  return promise
}

/**
 * Levanta SOLO los colores muy oscuros para que no se vean negros,
 * MANTENIENDO la saturacion (colores vibrantes como el journey original, NO
 * pastel lavado — pedido del dueno 2026-07-07). El pack Quaternius trae
 * partes casi negras (#1a1410, #2c2018) que `toonifyMesh` no recolorea.
 */
function brightenColor(hex: string): string {
  const color = new Color(hex)
  const hsl = { h: 0, s: 0, l: 0 }
  color.getHSL(hsl)
  if (hsl.l < 0.44) {
    color.setHSL(hsl.h, hsl.s, 0.44)
  }
  return `#${color.getHexString()}`
}

/**
 * Rim light Arcane de los personajes: borde blanco sutil (fresnel) que separa
 * la silueta del fondo blanco de las salas sin lavar la cara. power alto =
 * borde fino; intensity moderada para que no sea neon.
 */
const CHARACTER_RIM = { color: '#ffffff', power: 3.5, intensity: 0.45 } as const

/**
 * @function toonifyMesh
 * @description Reemplaza el material PBR del GLB (MeshStandardMaterial de
 *   Mixamo, que sin IBL renderiza plano/oscuro) por MeshToonMaterial — mismo
 *   lenguaje de shading que paredes/props. CLAVE: si el material trae textura
 *   (`map`, la CARA PINTADA de Mixamo), se PRESERVA como `map` con color base
 *   blanco (para no teñirla) + CHARACTER_GRADIENT (bandas duras = corte
 *   cel-shading Arcane-lite). Sin textura (ropa de color plano) se usa el
 *   color base del material, levantado si es muy oscuro.
 */
function toonifyMesh(mesh: Mesh): void {
  const applyOne = (material: Material): Material => {
    if (!(material instanceof MeshStandardMaterial)) {
      return material
    }
    if (material.map) {
      // cara/ropa texturizada: preservar la textura, la luz la modula el
      // gradientMap de bandas duras (cel-shading Arcane sobre la textura real)
      // + rim light fresnel que separa la silueta del fondo (look ilustracion).
      return toonMat('#ffffff', {
        map: material.map,
        gradient: CHARACTER_GRADIENT,
        rim: CHARACTER_RIM,
      })
    }
    // material de color plano (sin textura): mismo criterio de antes.
    const hex = `#${material.color.getHexString()}`
    return toonMat(brightenColor(hex), {
      gradient: CHARACTER_GRADIENT,
      rim: CHARACTER_RIM,
    })
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
  // velocidad real del NPC (m/s) para calibrar el timeScale del clip Walk y
  // eliminar el patinaje. 0 (por defecto) => timeScale 1 (jugador en 1a persona).
  let walkSpeed = 0

  /** timeScale del clip Walk segun la velocidad real: cadencia == avance.
   *  Clamp amplio: NPCs lentos (0.5 m/s -> 0.55x) hasta el jugador rapido en
   *  3a persona (3.5 m/s -> 2.2x, trote sin patinar demasiado). */
  function walkTimeScale(): number {
    if (walkSpeed <= 0) {
      return 1
    }
    return Math.min(2.2, Math.max(0.5, walkSpeed / WALK_CLIP_SPEED))
  }

  /** Reproduce una pose: resuelve el clip Mixamo, cae a 'Idle' si falta. */
  function playPose(next: CharacterPose): void {
    if (!mixer) {
      return
    }
    const clip = clipMap.get(POSE_CLIP[next]) ?? clipMap.get('Idle')
    if (!clip) {
      return
    }
    const action = mixer.clipAction(clip)
    action.reset()
    // el clip Walk se ralentiza/acelera para que los pies no patinen respecto
    // al avance real; el resto de poses corren a velocidad natural.
    action.timeScale = next === 'walk' ? walkTimeScale() : 1
    action.fadeIn(0.2)
    action.play()
    if (currentAction && currentAction !== action) {
      currentAction.fadeOut(0.2)
    }
    currentAction = action
  }

  loadModel(spec.model ?? 'base')
    .then((model) => {
      if (disposed) {
        return
      }
      const clone = cloneSkeleton(model.scene)
      // el GLB Mixamo ya viene a metros (build-character.py importa el FBX con
      // global_scale=100: bind pose correcto, cuerpo ~1.7 m). No se escala aca.
      clone.traverse((obj: Object3D) => {
        if (obj instanceof Mesh) {
          // SkeletonUtils.clone COMPARTE la geometry con el modelo cacheado:
          // marcarla shared evita que el disposeDeep de una sala la libere
          // (corromperia el resto de instancias que clonan la misma geometry).
          obj.geometry.userData.shared = true
          obj.castShadow = shadowMode === 'cast'
          obj.frustumCulled = false
          toonifyMesh(obj)
        }
        // build-character.py normaliza los huesos a "mixamorig_<Nombre>"
        // (sin ':', para que Three.js resuelva los tracks). El nodo del head
        // puede aparecer con o sin el ':' saneado por el loader -> se aceptan
        // ambas variantes.
        if (obj.name === 'mixamorig_Head' || obj.name === 'mixamorigHead') {
          headBone = obj
        }
      })
      group.add(clone)
      mixer = new AnimationMixer(clone)
      for (const clip of model.animations) {
        clipMap.set(normalizeClipName(clip.name), clip)
      }
      playPose(pose)
    })
    .catch((err: unknown) => {
      console.error('[character] no se pudo cargar el modelo', err)
    })

  return {
    group,
    setWalking(on) {
      // GUARD: controls llama setWalking cada frame. Sin este guard,
      // playPose -> reset() reinicia el clip Walk al frame 0 en cada cuadro
      // (el personaje avanza pero la animacion queda congelada). Solo se
      // re-dispara el clip cuando la pose CAMBIA.
      const next: CharacterPose = on ? 'walk' : 'idle'
      if (next === pose) {
        return
      }
      pose = next
      playPose(pose)
    },
    setPose(next) {
      if (next === pose) {
        return
      }
      pose = next
      playPose(pose)
    },
    setWalkSpeed(metersPerSecond) {
      walkSpeed = metersPerSecond
      // si ya está caminando, actualiza el timeScale en caliente
      if (pose === 'walk' && currentAction) {
        currentAction.timeScale = walkTimeScale()
      }
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
  /**
   * Pose fija (sin path): cualquier CharacterPose salvo idle/walk (esas las
   * decide el path). Sin pose: idle con sway. Las poses "sentadas"
   * (sit/kneel/typing/sitTalk) no giran el cuerpo al hablar (solo la cabeza).
   */
  pose?: Exclude<CharacterPose, 'idle' | 'walk'>
  /**
   * Si el NPC arranca sentado (typing/sit), al conversar SE LEVANTA
   * (standUp -> gesticula de pie) y al terminar vuelve a sentarse en su pose
   * original. Sin esto, un NPC sentado solo gira la cabeza. Opt-in por sala
   * (el aula lo activa; pedido de Pablo).
   */
  standToTalk?: boolean
}

/** Poses en las que el NPC esta sentado (no gira el cuerpo, solo la cabeza). */
const SEATED_POSES: ReadonlySet<CharacterPose> = new Set<CharacterPose>([
  'sit',
  'kneel',
  'typing',
  'sitTalk',
  'disbelief',
])

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
    // calibra la cadencia del clip Walk a la velocidad real (sin patinaje)
    character.setWalkSpeed(speed)
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
  const seated = opts.pose !== undefined && SEATED_POSES.has(opts.pose)
  // standToTalk: un NPC sentado que, al conversar, se LEVANTA y gesticula de
  // pie (pedido de Pablo, aula). Mientras dura la conversacion se comporta
  // como NO-sentado (gira el cuerpo, saluda). standUpLeft cuenta la transicion
  // del clip StandUpDesk antes de pasar a hablar.
  const standToTalk = opts.standToTalk ?? false
  let standUpLeft = 0
  let talking = false
  let faceYaw = opts.rotationY ?? 0
  let waveLeft = 0
  let jumpLeft = 0
  let walkTime = phase
  /** ¿Funcionalmente sentado ahora? (seated salvo que este de pie hablando). */
  const effSeated = (): boolean => seated && !(standToTalk && talking)

  // throttle de animacion: los NPCs de fondo (idle/sentados, sin hablar)
  // avanzan el mixer a ~22 fps (imperceptible en un idle lento, baja el CPU
  // con varios NPCs por sala). El rig a fondo se "jala" al interactuar: al
  // hablar o caminar la animacion vuelve a full rate.
  const ANIM_STEP = 1 / 22
  let animAccum = 0

  const NPC_RADIUS = 0.26

  /** Conversando: gira suave hacia el jugador y pasa de wave/standUp a talk. */
  function updateTalking(dt: number): void {
    // levantandose (standToTalk): espera a que termine el clip StandUpDesk y
    // recien ahi empieza a gesticular de pie.
    if (standUpLeft > 0) {
      standUpLeft = Math.max(0, standUpLeft - dt)
      if (standUpLeft <= 0) {
        character.setPose('talk')
      } else {
        return
      }
    }
    if (effSeated()) {
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
      } else if (opts.pose === 'sit' || opts.pose === 'typing') {
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
      const willStand = standToTalk && seated // se levanta a hablar
      if (player) {
        faceYaw = Math.atan2(
          player.x - group.position.x,
          player.z - group.position.z,
        )
        if (seated && !willStand) {
          // sentado sin levantarse: solo gira la cabeza al jugador
          let rel = faceYaw - group.rotation.y
          rel = Math.atan2(Math.sin(rel), Math.cos(rel))
          character.setHeadYaw(Math.min(Math.max(rel, -1.1), 1.1))
        }
      }
      if (walking) {
        character.setWalking(false)
      }
      if (willStand) {
        // levantarse: clip StandUpDesk; updateTalking pasa a 'talk' al terminar
        character.setHeadYaw(null)
        character.setPose('standUp')
        standUpLeft = 0.7
      } else if (!seated) {
        character.setPose('wave')
        waveLeft = 0.9
      }
    },
    endTalk() {
      talking = false
      waveLeft = 0
      standUpLeft = 0
      character.setHeadYaw(null)
      if (walking) {
        character.setWalking(true)
      } else if (opts.pose) {
        // vuelve a su pose original (los standToTalk se vuelven a sentar)
        character.setPose(opts.pose)
        group.rotation.y = opts.rotationY ?? 0
      } else {
        character.setPose('idle')
      }
    },
    setPose(next) {
      // no pisa la conversacion (wave/talk); util para secuencias del entorno
      if (!talking) {
        character.setPose(next)
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
