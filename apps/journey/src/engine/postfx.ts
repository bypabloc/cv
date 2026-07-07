/**
 * @module postfx (engine)
 * @description Pipeline de postprocesado del estilo Spider-Verse
 *   (docs/specs/journey-spiderverse-style/): halftone (Ben-Day dots,
 *   shader oficial de three.js) + aberracion cromatica (RGBShiftShader
 *   oficial) + contorno de tinta via OutlinePass (screen-space, funciona
 *   sobre SkinnedMesh deformandose — reemplaza el inverted-hull SOLO para
 *   personajes; los props que sigan con mergedBoxes conservan su hull).
 */
import {
  type Camera,
  Color,
  type Scene,
  Vector2,
  type WebGLRenderer,
} from 'three'
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js'
import { OutlinePass } from 'three/examples/jsm/postprocessing/OutlinePass.js'
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js'
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js'
import { ShaderPass } from 'three/examples/jsm/postprocessing/ShaderPass.js'
import { HalftoneShader } from 'three/examples/jsm/shaders/HalftoneShader.js'
import { RGBShiftShader } from 'three/examples/jsm/shaders/RGBShiftShader.js'
import { INK } from './toon'

export interface PostFx {
  composer: EffectComposer
  outline: OutlinePass
  render(): void
  resize(width: number, height: number): void
  dispose(): void
}

/**
 * @function createPostFx
 * @description Arma el composer: Render -> Outline (tinta) -> Halftone
 *   (Ben-Day dots) -> RGBShift (aberracion) -> Output (resuelve tone
 *   mapping/color space del renderer). Los NPCs se agregan a
 *   `outline.selectedObjects` desde character.ts para recibir contorno.
 */
export function createPostFx(opts: {
  renderer: WebGLRenderer
  scene: Scene
  camera: Camera
  width: number
  height: number
}): PostFx {
  const { renderer, scene, camera } = opts
  const size = new Vector2(opts.width, opts.height)

  const composer = new EffectComposer(renderer)
  composer.addPass(new RenderPass(scene, camera))

  const outline = new OutlinePass(size.clone(), scene, camera)
  outline.edgeStrength = 6
  outline.edgeThickness = 1.6
  outline.edgeGlow = 0
  outline.visibleEdgeColor = new Color(INK)
  outline.hiddenEdgeColor = new Color(INK)
  composer.addPass(outline)

  const halftone = new ShaderPass(HalftoneShader)
  halftone.uniforms.radius.value = 2.5
  halftone.uniforms.scatter.value = 0
  halftone.uniforms.width.value = opts.width
  halftone.uniforms.height.value = opts.height
  // blending alto: el color original manda, los puntos son una textura de
  // sombreado sutil encima (no reemplazan el color como a blending bajo)
  halftone.uniforms.blending.value = 0.85
  halftone.uniforms.blendingMode.value = 2 // multiply: los puntos oscurecen, no reemplazan el color
  composer.addPass(halftone)

  const chromaticAberration = new ShaderPass(RGBShiftShader)
  chromaticAberration.uniforms.amount.value = 0.0012
  composer.addPass(chromaticAberration)

  composer.addPass(new OutputPass())

  function resize(width: number, height: number): void {
    composer.setSize(width, height)
    outline.setSize(width, height)
    halftone.uniforms.width.value = width
    halftone.uniforms.height.value = height
  }

  function dispose(): void {
    outline.dispose()
    halftone.dispose()
    chromaticAberration.dispose()
    composer.dispose()
  }

  return {
    composer,
    outline,
    render: () => composer.render(),
    resize,
    dispose,
  }
}
