/**
 * @module loaders (engine)
 * @description Carga de assets 3D reales CC0 (estilo Spider-Verse,
 *   docs/specs/journey-spiderverse-style/): singleton de GLTFLoader
 *   configurado con DRACOLoader (geometria) + KTX2Loader (texturas). Los
 *   decoders viven en public/draco/ y public/basis/ (copiados desde
 *   node_modules/three via scripts/copy-loader-assets.mjs en prebuild).
 */
import type { WebGLRenderer } from 'three'
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { KTX2Loader } from 'three/examples/jsm/loaders/KTX2Loader.js'

const dracoLoader = new DRACOLoader()
dracoLoader.setDecoderPath('/draco/')

const ktx2Loader = new KTX2Loader()
ktx2Loader.setTranscoderPath('/basis/')

const gltfLoader = new GLTFLoader()
gltfLoader.setDRACOLoader(dracoLoader)
gltfLoader.setKTX2Loader(ktx2Loader)

let detected = false

/**
 * @function configureLoaders
 * @description Detecta soporte KTX2 del renderer (una vez, en el cold
 *   start de app.ts). Debe llamarse ANTES de cualquier loadAsync().
 */
export function configureLoaders(renderer: WebGLRenderer): void {
  if (detected) {
    return
  }
  ktx2Loader.detectSupport(renderer)
  detected = true
}

export { dracoLoader, gltfLoader, ktx2Loader }
