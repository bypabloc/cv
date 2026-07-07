/**
 * @module postfx (engine)
 * @description Pipeline de postprocesado del estilo Spider-Verse
 *   (docs/specs/journey-spiderverse-style/): halftone (Ben-Day dots, shader
 *   oficial de three.js) + aberracion cromatica (RGBShiftShader oficial).
 *
 *   El contorno de tinta de los personajes NO va aca: es un shell
 *   inverted-hull SKINNED barato (toon.ts::skinnedOutline, 1 draw por mesh),
 *   mucho mas liviano que el OutlinePass screen-space que se uso antes (que
 *   re-renderizaba cada SkinnedMesh a un buffer aparte + depth + 2 blurs a
 *   resolucion completa). El composer corre a resolucion CAPADA (moderada)
 *   para bajar el fill-rate; los puntos del halftone disimulan la perdida de
 *   nitidez. `setPixelRatio` deja que app.ts baje mas la resolucion del
 *   composer cuando el FPS cae (auto-degradado).
 */
import type { Camera, Scene, WebGLRenderer } from 'three'
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js'
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js'
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js'
import { ShaderPass } from 'three/examples/jsm/postprocessing/ShaderPass.js'
import { HalftoneShader } from 'three/examples/jsm/shaders/HalftoneShader.js'
import { RGBShiftShader } from 'three/examples/jsm/shaders/RGBShiftShader.js'

export interface PostFx {
  composer: EffectComposer
  render(): void
  resize(width: number, height: number): void
  /** Baja/sube la resolucion interna del composer (auto-degradado por FPS). */
  setPixelRatio(value: number): void
  dispose(): void
}

/**
 * @function createPostFx
 * @description Arma el composer: Render -> Halftone (Ben-Day dots) -> RGBShift
 *   (aberracion) -> Output (resuelve tone mapping/color space del renderer).
 *   El composer se fija a `pixelRatio` (capado, no el DPR completo del
 *   renderer) — es la palanca #1 de fill-rate en este pipeline.
 */
export function createPostFx(opts: {
  renderer: WebGLRenderer
  scene: Scene
  camera: Camera
  width: number
  height: number
  pixelRatio: number
}): PostFx {
  const { renderer, scene, camera } = opts

  const composer = new EffectComposer(renderer)
  composer.setPixelRatio(opts.pixelRatio)
  composer.setSize(opts.width, opts.height)
  composer.addPass(new RenderPass(scene, camera))

  const halftone = new ShaderPass(HalftoneShader)
  halftone.uniforms.radius.value = 2.5
  halftone.uniforms.scatter.value = 0
  halftone.uniforms.width.value = opts.width
  halftone.uniforms.height.value = opts.height
  // LINEAR (no multiply): mezcla el COLOR REAL con los puntos sin aplastar
  // los oscuros -> paleta clara/pastel con Ben-Day visible. `blending` = cuanto
  // pesan los puntos (0.4 => 60% color + 40% puntos). Multiply a 0.85
  // crusheaba todo a negro (a*(1-b)) y por eso NPCs/props se veian oscuros.
  halftone.uniforms.blending.value = 0.4
  halftone.uniforms.blendingMode.value = 1 // LINEAR
  composer.addPass(halftone)

  const chromaticAberration = new ShaderPass(RGBShiftShader)
  chromaticAberration.uniforms.amount.value = 0.0012
  composer.addPass(chromaticAberration)

  composer.addPass(new OutputPass())

  return {
    composer,
    render: () => composer.render(),
    resize(width, height) {
      composer.setSize(width, height)
      halftone.uniforms.width.value = width
      halftone.uniforms.height.value = height
    },
    setPixelRatio(value) {
      composer.setPixelRatio(value)
    },
    dispose() {
      halftone.dispose()
      chromaticAberration.dispose()
      composer.dispose()
    },
  }
}
