/**
 * @module rooms/furniture (engine)
 * @description Mobiliario CC0 (Kenney Furniture Kit) para el estilo
 *   Spider-Verse (docs/specs/journey-spiderverse-style/, T4). Carga un GLB
 *   estatico UNA vez (cacheado por url) y lo clona por instancia: convierte
 *   sus materiales planos a `toonMat` (mismo lenguaje que el resto), auto-
 *   escala al bounding box (robusto ante la escala de cualquier pack), apoya
 *   la base en el piso y agrega el contorno de tinta. Handle SINCRONO (grupo
 *   vacio) poblado async, igual que makeCharacter — no bloquea el build de la
 *   sala.
 */
import {
  Box3,
  Color,
  Group,
  type Material,
  Mesh,
  MeshStandardMaterial,
  type Object3D,
} from 'three'
import { gltfLoader } from '../loaders'
import { outlineGroup, toonMat } from '../toon'

const modelCache = new Map<string, Promise<Object3D>>()

function loadFurnitureModel(url: string): Promise<Object3D> {
  let promise = modelCache.get(url)
  if (!promise) {
    promise = gltfLoader.loadAsync(url).then((gltf) => gltf.scene)
    modelCache.set(url, promise)
  }
  return promise
}

/** Levanta la luminosidad de los colores muy oscuros (sin desaturar). */
function liftDark(hex: string): string {
  const color = new Color(hex)
  const hsl = { h: 0, s: 0, l: 0 }
  color.getHSL(hsl)
  if (hsl.l < 0.42) {
    color.setHSL(hsl.h, hsl.s, 0.42)
  }
  return `#${color.getHexString()}`
}

function toonifyFurniture(
  mesh: Mesh,
  tint: Record<string, string> | undefined,
  color: string | undefined,
): void {
  const applyOne = (material: Material): Material => {
    if (!(material instanceof MeshStandardMaterial)) {
      return material
    }
    // prioridad: tint por nombre de material > color plano > color original
    const override = tint?.[material.name] ?? color
    if (material.map && override === undefined) {
      // modelo texturado (ej. atlas colormap del pack sci-fi): preserva la
      // textura y solo aplica el toon shading sobre blanco (no la tiñe).
      return toonMat('#ffffff', { map: material.map })
    }
    const hex = override ?? liftDark(`#${material.color.getHexString()}`)
    return toonMat(hex)
  }
  mesh.material = Array.isArray(mesh.material)
    ? mesh.material.map(applyOne)
    : applyOne(mesh.material)
}

export interface FurnitureOpts {
  url: string
  x: number
  z: number
  rotationY?: number
  /** Ancho objetivo (unidades de mundo): auto-escala desde el bounding box. */
  targetWidth?: number
  /** Recolor por nombre de material del pack (ej. asiento del rubro). */
  tint?: Record<string, string>
  /** Color plano que sobreescribe TODOS los materiales (ej. madera). */
  color?: string
  /** Contorno de tinta (default true). */
  outline?: boolean
}

/**
 * @function placeFurniture
 * @description Devuelve un `Group` posicionado de inmediato; carga y puebla el
 *   GLB async. Reusa la geometry del modelo cacheado (marcada shared para que
 *   el disposeDeep de la sala no la libere) y materiales pooled del toon.
 */
export function placeFurniture(opts: FurnitureOpts): Group {
  const group = new Group()
  group.position.set(opts.x, 0, opts.z)
  group.rotation.y = opts.rotationY ?? 0

  loadFurnitureModel(opts.url)
    .then((model) => {
      const clone = model.clone(true)
      clone.traverse((obj: Object3D) => {
        if (obj instanceof Mesh) {
          // clone() comparte la geometry con el modelo cacheado -> shared
          // para que disposeDeep de una sala no la libere (corromperia el
          // resto de instancias).
          obj.geometry.userData.shared = true
          obj.castShadow = true
          toonifyFurniture(obj, opts.tint, opts.color)
        }
      })
      const box = new Box3().setFromObject(clone)
      if (opts.targetWidth) {
        const width = box.max.x - box.min.x
        const scale = width > 0 ? opts.targetWidth / width : 1
        clone.scale.setScalar(scale)
        box.setFromObject(clone)
      }
      // apoya la base del mueble en el piso (y=0 del grupo)
      clone.position.y = -box.min.y
      group.add(clone)
      if (opts.outline !== false) {
        outlineGroup(clone, 1.03)
      }
    })
    .catch((err: unknown) => {
      console.error(`[furniture] no se pudo cargar ${opts.url}`, err)
    })

  return group
}
