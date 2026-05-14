/**
 * @description Helper test que regenera los baselines JSON usados por
 *   data-parity.test.ts. Vive como test porque corre dentro del contexto
 *   Vite/Vitest, donde `import.meta.glob` (usado por los index.ts de cada
 *   data dir) funciona. Un script standalone con tsx falla.
 *
 *   Activacion: setear env var REGEN_BASELINE=1 antes de correr Vitest.
 *
 *   Uso:
 *     REGEN_BASELINE=1 pnpm --filter @portfolio/content run test
 *
 *   Por default no hace nada (it.skipIf), para que un `pnpm test` normal no
 *   sobrescriba accidentalmente el baseline.
 *
 *   Este test se conserva como herramienta operativa, no como test
 *   funcional. NO contar para coverage.
 */
import { writeFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, it } from 'vitest'
import {
  awards,
  certificates,
  education,
  experiences,
  languages,
  profile,
  projects,
  publications,
  references,
  skills,
} from '../../src/index'

const baselineDir = resolve(__dirname, '../fixtures/baseline')
const shouldRegen = process.env.REGEN_BASELINE === '1'

describe('regenerate baseline (opt-in via REGEN_BASELINE=1)', () => {
  it.skipIf(!shouldRegen)(
    'Given current YAML data When env flag is set Then writes baseline JSON files',
    () => {
      const entities: Record<string, unknown> = {
        profile,
        experiences,
        projects,
        certificates,
        publications,
        awards,
        skills,
        education,
        references,
        languages,
      }
      for (const [name, data] of Object.entries(entities)) {
        const path = resolve(baselineDir, `${name}.json`)
        writeFileSync(path, `${JSON.stringify(data, null, 2)}\n`, 'utf8')
      }
    },
  )
})
