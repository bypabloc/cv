/**
 * @module npc-outline (engine)
 * @description Contorno de NPCs humanoides `SkinnedMesh` via `OutlinePass`
 *   (post-procesamiento screen-space, `EffectComposer`). Reemplaza el
 *   inverted-hull actual (`toon.ts` / `outlineGroup`) SOLO para NPCs
 *   riggeados: ese tecnica infla normales sobre la geometria FUENTE y es
 *   fragil bajo deformacion de skinning (confirmado en el research, ver
 *   .claude/docs/journey-npc-realism/02-export-y-threejs-integracion.md).
 *   Los props/paredes estaticos de la sala NO se tocan — siguen con
 *   `mergedBoxes`/`outlinedMergedBoxes` de `toon.ts`.
 *
 * ESTADO (2026-07-06): listo para usarse en cuanto haya NPCs `SkinnedMesh`
 * reales en la escena (ver npc-gltf-loader.ts). El presupuesto de draw
 * calls/sala resultante de sumar este composer NO esta medido todavia
 * (AC-8 del plan docs/specs/journey-npc-realism/) — no asumir numeros.
 */
import type { Camera, Object3D, Scene, WebGLRenderer } from 'three'
import { Vector2 } from 'three'
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js'
import { OutlinePass } from 'three/examples/jsm/postprocessing/OutlinePass.js'
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js'
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js'

export interface NpcOutlineComposer {
  composer: EffectComposer
  /** Reemplaza la lista completa de NPCs con contorno (llamar al cambiar de sala/al entrar-salir NPCs de vista). */
  setOutlinedObjects(objects: Object3D[]): void
  render(deltaSeconds: number): void
  setSize(width: number, height: number): void
  dispose(): void
}

/**
 * Arma el `EffectComposer` con `OutlinePass` para los NPCs humanoides de
 * la sala. El color de tinta (`#141018`) es consistente con el resto del
 * contorno manga-ink de la sala (ver `toon.ts`).
 *
 * @example
 *   const npcOutline = createNpcOutlineComposer({ renderer, scene, camera, width, height })
 *   npcOutline.setOutlinedObjects([npc1.object, npc2.object])
 *   // en el loop de render, en vez de renderer.render(scene, camera):
 *   npcOutline.render(dt)
 */
export function createNpcOutlineComposer(opts: {
  renderer: WebGLRenderer
  scene: Scene
  camera: Camera
  width: number
  height: number
}): NpcOutlineComposer {
  const { renderer, scene, camera, width, height } = opts

  const composer = new EffectComposer(renderer)
  composer.addPass(new RenderPass(scene, camera))

  const outlinePass = new OutlinePass(new Vector2(width, height), scene, camera)
  outlinePass.edgeStrength = 2.5
  outlinePass.edgeThickness = 1
  // OutlinePass compone el contorno con AdditiveBlending (glow de seleccion,
  // ver getOverlayMaterial() en three/examples/jsm/postprocessing/
  // OutlinePass.js) — un color casi negro (`#141018`, el ink del resto de
  // la sala) es invisible ahi sin importar edgeStrength: additive solo
  // puede ACLARAR, nunca oscurecer. Blanco calido es lo mas cercano al
  // contorno manga-ink que esta tecnica puede dar; el ink oscuro real
  // requeriria un shader de silueta propio (Etapa 2, fuera de este AC-7).
  outlinePass.visibleEdgeColor.set('#f5f2ea')
  outlinePass.hiddenEdgeColor.set('#f5f2ea')
  composer.addPass(outlinePass)

  composer.addPass(new OutputPass())

  return {
    composer,
    setOutlinedObjects(objects: Object3D[]): void {
      outlinePass.selectedObjects = objects
    },
    render(deltaSeconds: number): void {
      composer.render(deltaSeconds)
    },
    setSize(newWidth: number, newHeight: number): void {
      composer.setSize(newWidth, newHeight)
      outlinePass.resolution.set(newWidth, newHeight)
    },
    dispose(): void {
      composer.dispose()
    },
  }
}
