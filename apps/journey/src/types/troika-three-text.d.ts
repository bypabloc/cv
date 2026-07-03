/**
 * @type troika-three-text (declaracion minima)
 * @description troika-three-text no publica types y @types/troika-three-text
 *   no existe en el registry. Se declara SOLO lo que journey usa:
 *   configureTextBuilder (apagar el worker por CSP — ver text-font.ts).
 */
declare module 'troika-three-text' {
  export function configureTextBuilder(config: {
    useWorker?: boolean
    sdfGlyphSize?: number
  }): void
}
