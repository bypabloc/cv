/**
 * @module text-font
 * @description Font self-hosted para drei `<Text>`. Sin `font` explicito,
 *   troika-three-text resuelve los glifos descargando data de un CDN
 *   (unicode-font-resolver via jsdelivr) — la CSP del deploy lo bloquea y
 *   el texto no renderiza. Es el mismo Space Grotesk del DS (@fontsource),
 *   en `.woff` porque troika no soporta woff2. El archivo vive commiteado
 *   en `public/fonts/` (17 KB) para que dev y build lo sirvan igual.
 */
import { configureTextBuilder } from 'troika-three-text'

// Typesetter de troika en el MAIN THREAD: su worker via Blob URL crea el
// worker con `worker-src blob:`, pero el importScripts() interno lo
// gobierna `script-src`, que la CSP mantiene sin blob: (mas estricto).
// Sintoma sin esto: los <Text> suspenden para siempre y la isla queda en
// "Cargando el mundo 3D…". Costo main-thread trivial: 9 textos cortos.
configureTextBuilder({ useWorker: false })

export const TEXT_FONT = '/fonts/space-grotesk-latin-400-normal.woff'
