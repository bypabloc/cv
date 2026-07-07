/**
 * @module npc-gltf-loader (engine)
 * @description Carga humanoides `.glb` riggeados (pipeline
 *   docs/specs/journey-npc-realism, devtools/npc_pipeline) via
 *   `GLTFLoader` + `SkinnedMesh` + `AnimationMixer`. Reemplaza la
 *   construccion procedural de `character.ts` (primitivas fusionadas) por
 *   un asset externo, manteniendo el mismo vocabulario de poses
 *   (`CharacterPose`) para que el resto del motor (rooms/dialog/hud) no
 *   necesite cambios cuando esta pieza se cablee.
 *
 * ESTADO (2026-07-06): el asset real (`/models/npc-base.glb`, generado por
 * `devtools/npc_pipeline` — MPFB2 + Rigify + 2 clips `idle`/`walk`) ya
 * existe. Los nombres de clip exportados son exactamente `idle` y `walk`
 * (ver docs/specs/journey-npc-realism/mpfb2-api-discovery.md — el
 * exportador glTF nombra el clip segun el NLA track, no la accion; el
 * script `animate.py` los alinea a proposito).
 */
import {
  type AnimationAction,
  type AnimationClip,
  AnimationMixer,
  Group,
  type Object3D,
} from 'three'
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { clone as cloneSkeleton } from 'three/examples/jsm/utils/SkeletonUtils.js'
import type { Box2 } from '../lib/collision'
import {
  type CharacterPose,
  moveAlongPath,
  type NpcHandle,
  type NpcOpts,
} from './character'

/** Resultado de cargar el `.glb` base UNA sola vez (se clona por NPC). */
export interface NpcGltfBase {
  scene: Object3D
  animations: AnimationClip[]
}

export interface GltfNpcHandle {
  /** Raiz de la instancia clonada — se agrega a la escena como cualquier Group. */
  object: Object3D
  /** Cambia de pose con crossfade suave (0.3s) entre clips. */
  playPose(pose: CharacterPose): void
  /** Avanza el mixer. Llamar una vez por frame con el delta en segundos. */
  update(dt: number): void
  dispose(): void
}

const loader = new GLTFLoader()
// El .glb final esta comprimido con Meshopt (glTF-Transform CLI, ver
// devtools/npc_pipeline `export`) — sin esto GLTFLoader lanza
// "setMeshoptDecoder must be called before loading compressed files".
loader.setMeshoptDecoder(MeshoptDecoder)

/**
 * Carga el `.glb` base UNA sola vez (cachear el resultado en el caller —
 * todas las instancias de NPC clonan de este mismo `NpcGltfBase`).
 *
 * @example
 *   const base = await loadNpcGltfBase('/models/npc-base.glb')
 *   const npc = spawnGltfNpc(base)
 *   scene.add(npc.object)
 */
export async function loadNpcGltfBase(url: string): Promise<NpcGltfBase> {
  const gltf = await loader.loadAsync(url)
  return { scene: gltf.scene, animations: gltf.animations }
}

/**
 * Instancia un NPC a partir del `.glb` base ya cargado.
 *
 * `SkeletonUtils.clone()` (aqui `cloneSkeleton`) es OBLIGATORIO para
 * clonar un `SkinnedMesh` — `Object3D.clone()` nativo NO preserva el
 * binding skeleton<->mesh (ver
 * .claude/docs/journey-npc-realism/02-export-y-threejs-integracion.md).
 */
export function spawnGltfNpc(base: NpcGltfBase): GltfNpcHandle {
  const object = cloneSkeleton(base.scene)
  const mixer = new AnimationMixer(object)

  const actions = new Map<CharacterPose, AnimationAction>()
  for (const clip of base.animations) {
    // Los clips se nombran igual que CharacterPose en el pipeline Blender
    // (idle/walk/talk/sit) — ver
    // .claude/docs/journey-npc-realism/01-pipeline-blender-headless.md.
    actions.set(clip.name as CharacterPose, mixer.clipAction(clip, object))
  }

  let currentAction: AnimationAction | undefined

  function playPose(pose: CharacterPose): void {
    const nextAction = actions.get(pose)
    if (!nextAction || nextAction === currentAction) {
      return
    }
    nextAction.reset().fadeIn(0.3).play()
    currentAction?.fadeOut(0.3)
    currentAction = nextAction
  }

  function update(dt: number): void {
    mixer.update(dt)
  }

  function dispose(): void {
    mixer.stopAllAction()
    mixer.uncacheRoot(object)
  }

  return { object, playPose, update, dispose }
}

// ---------------------------------------------------------------------------
// Adaptador NpcHandle: deja cablear un NPC realista en `rooms/` sin tocar
// dialog.ts/hud.ts (mismo contrato que `makeNpc` de character.ts).
// ---------------------------------------------------------------------------

/** Duracion (s) del arco de salto one-shot — igual a `character.ts`. */
const JUMP_DURATION = 0.55
const NPC_RADIUS = 0.26

/** Roots de NPCs GLTF vivos en la sala montada (para `OutlinePass`). */
const liveObjects: Object3D[] = []

/** Objetos GLTF vivos a contornear con `createNpcOutlineComposer` (npc-outline.ts). */
export function getLiveGltfNpcObjects(): readonly Object3D[] {
  return liveObjects
}

let cachedBase: Promise<NpcGltfBase> | null = null

function loadCachedBase(url: string): Promise<NpcGltfBase> {
  cachedBase ??= loadNpcGltfBase(url)
  return cachedBase
}

/**
 * `NpcHandle` respaldado por el `.glb` MPFB2+Rigify (pipeline
 * `devtools/npc_pipeline`) en vez del builder procedural de
 * `character.ts` — mismo contrato (`group`/`update`/`collider`/`talk`/
 * `endTalk`/`jump`/`dispose`) para reemplazar un NPC puntual en
 * `rooms/*.ts` sin tocar `dialog.ts` ni `hud.ts`.
 *
 * Etapa 1 (docs/specs/journey-npc-realism/): solo existen los clips
 * `idle`/`walk` — cualquier NPC con `pose` fija (`sit`/`kneel`/`fight`) o
 * que reciba `talk()` degrada a `idle` (ver animate.py). Reservado para
 * NPCs de patrulla (`path`) sin pose fija, como `estudianteRonda`.
 *
 * La carga del `.glb` es async pero el contrato `NpcHandle` es sincrono
 * (el room build lo es): el `group` se agrega vacio y se puebla en cuanto
 * resuelve `loadCachedBase` (cacheado — todas las instancias de la sala
 * comparten el mismo fetch).
 *
 * @example
 *   const estudianteRonda = spawnRealisticNpc({ ...opts, path: [...] })
 *   npcs.push(estudianteRonda) // igual que makeNpc(...)
 */
export function spawnRealisticNpc(
  opts: NpcOpts,
  glbUrl = '/models/npc-base.glb',
): NpcHandle {
  const group = new Group()
  group.position.set(opts.position[0], opts.position[1], opts.position[2])
  group.rotation.y = opts.rotationY ?? 0

  const phase =
    (opts.position[0] * 7.3 + opts.position[2] * 3.1) % (Math.PI * 2)
  const walking = (opts.path?.length ?? 0) >= 2
  const speed = opts.speed ?? 0.7
  let walkTime = phase
  let talking = false
  let jumpLeft = 0

  let npc: GltfNpcHandle | undefined
  loadCachedBase(glbUrl)
    .then((base) => {
      npc = spawnGltfNpc(base)
      group.add(npc.object)
      liveObjects.push(npc.object)
    })
    .catch((error: unknown) => {
      console.error('[npc-gltf-loader] fallo cargando el NPC realista', error)
    })

  function applyJump(dt: number): void {
    if (jumpLeft <= 0) {
      return
    }
    jumpLeft = Math.max(0, jumpLeft - dt)
    group.position.y += Math.sin((1 - jumpLeft / JUMP_DURATION) * Math.PI) * 0.5
  }

  return {
    group,
    update(_t, dt) {
      if (!talking && walking && opts.path) {
        walkTime += dt
        moveAlongPath(group, opts.path, walkTime, speed)
      }
      npc?.update(dt)
      npc?.playPose(!talking && walking ? 'walk' : 'idle')
      applyJump(dt)
    },
    collider(): Box2 {
      return {
        minX: group.position.x - NPC_RADIUS,
        maxX: group.position.x + NPC_RADIUS,
        minZ: group.position.z - NPC_RADIUS,
        maxZ: group.position.z + NPC_RADIUS,
      }
    },
    talk() {
      talking = true
    },
    endTalk() {
      talking = false
    },
    jump() {
      jumpLeft = JUMP_DURATION
    },
    dispose() {
      if (npc) {
        const idx = liveObjects.indexOf(npc.object)
        if (idx >= 0) {
          liveObjects.splice(idx, 1)
        }
        npc.dispose()
      }
    },
  }
}
