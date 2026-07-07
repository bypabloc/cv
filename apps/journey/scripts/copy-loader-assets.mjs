/**
 * @description Copia los decoders de DRACOLoader/KTX2Loader
 *   (`node_modules/three/examples/jsm/libs/{draco,basis}`) a `public/` para
 *   que Astro los sirva estaticos. `setDecoderPath`/`setTranscoderPath`
 *   reciben un prefijo de directorio (concatenan el nombre de archivo
 *   internamente), por eso se copia la carpeta completa en vez de assets
 *   individuales con hash de Vite.
 */
import { cp, mkdir } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const THREE_LIBS = resolve(__dirname, '../node_modules/three/examples/jsm/libs')
const PUBLIC_DIR = resolve(__dirname, '../public')

async function copyLib(name) {
  const src = resolve(THREE_LIBS, name)
  const dest = resolve(PUBLIC_DIR, name)
  await cp(src, dest, { recursive: true })
  console.info(`[public] copied ${name}/ decoder assets`)
}

async function main() {
  await mkdir(PUBLIC_DIR, { recursive: true })
  await copyLib('draco')
  await copyLib('basis')
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
