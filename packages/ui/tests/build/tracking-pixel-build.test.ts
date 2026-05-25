/**
 * @description Build-test: assert que el dist contiene los valores
 *   correctos cuando se buildea con env vars. Capa B del plan
 *   build-env-vars-per-env.
 *
 *   Se construye apps/hub como representante de las 6 apps. El test es
 *   lento (~30-60s) porque corre `pnpm --filter @portfolio/hub run build`.
 *   Por eso vive en tests/build/ aparte de tests/unit/.
 *
 *   Cubre los 3 escenarios:
 *   1. build con env vars CORRECTAS -> dist contiene
 *      data-api-endpoint matchando PUBLIC_API_ENDPOINT y hrefs al env
 *   2. build con BASE_DOMAIN=dev pero PUBLIC_API_ENDPOINT=prod ->
 *      FALLA con mensaje de mismatch (Capa A funciona)
 *   3. build sin PUBLIC_API_ENDPOINT -> FALLA con "vacio" (Capa A)
 */
import { type ExecSyncOptions, execSync } from 'node:child_process'
import { existsSync, readFileSync } from 'node:fs'
import { join } from 'node:path'

import { beforeAll, describe, expect, it } from 'vitest'

const REPO_ROOT = join(import.meta.dirname, '../../../..')
const HUB_DIST = join(REPO_ROOT, 'apps/hub/dist')
const HUB_INDEX = join(HUB_DIST, 'index.html')

const ENV_DEV = {
  BASE_DOMAIN: 'portfolio.dev.the-full-stack.com',
  BASE_SCHEME: 'https',
  PUBLIC_API_ENDPOINT: 'https://api.portfolio.dev.the-full-stack.com',
  PUBLIC_TURNSTILE_SITEKEY: 'fake-test-sitekey-not-real',
}

function runBuild(envOverrides: Record<string, string | undefined>): {
  ok: boolean
  stderr: string
} {
  // Limpiar dist antes de cada build para que el grep no lea un dist
  // viejo si el build falla.
  execSync(`rm -rf ${HUB_DIST}`, { cwd: REPO_ROOT })
  const env = { ...process.env, ...envOverrides }
  // Eliminar keys cuyo valor sea undefined (env de Node no acepta undefined)
  for (const k of Object.keys(env)) {
    if (env[k] === undefined) {
      delete env[k]
    }
  }
  const opts: ExecSyncOptions = {
    cwd: REPO_ROOT,
    env: env as NodeJS.ProcessEnv,
    stdio: 'pipe',
  }
  try {
    execSync('pnpm --filter @portfolio/hub run build', opts)
    return { ok: true, stderr: '' }
  } catch (err) {
    const e = err as { stderr?: Buffer | string; stdout?: Buffer | string }
    const stderr = String(e.stderr ?? '') + String(e.stdout ?? '')
    return { ok: false, stderr }
  }
}

describe('TrackingPixel build-time wiring', () => {
  describe('build con env vars correctas (BASE_DOMAIN=dev)', () => {
    beforeAll(() => {
      const result = runBuild(ENV_DEV)
      if (!result.ok) {
        throw new Error(
          `Build con env vars correctas FALLO inesperadamente:\n${result.stderr}`,
        )
      }
    }, 120_000)

    it('Given BASE_DOMAIN=dev When inspecciono dist/index.html Then data-api-endpoint matchea PUBLIC_API_ENDPOINT', () => {
      expect(existsSync(HUB_INDEX)).toBe(true)
      const html = readFileSync(HUB_INDEX, 'utf-8')
      expect(html).toContain(
        'data-api-endpoint="https://api.portfolio.dev.the-full-stack.com"',
      )
    })

    it('Given BASE_DOMAIN=dev When inspecciono hrefs Then NO apuntan a prod', () => {
      const html = readFileSync(HUB_INDEX, 'utf-8')
      const prodHrefs = html.match(
        /href="https:\/\/[a-z]+\.portfolio\.the-full-stack\.com[^"]*"/g,
      )
      expect(prodHrefs ?? []).toEqual([])
    })

    it('Given BASE_DOMAIN=dev When inspecciono hrefs Then dropdown apunta a *.portfolio.dev.*', () => {
      const html = readFileSync(HUB_INDEX, 'utf-8')
      expect(html).toMatch(
        /href="https:\/\/fintech\.portfolio\.dev\.the-full-stack\.com"/,
      )
    })
  })

  describe('build con env vars rotas (debe FALLAR — Capa A)', () => {
    it('Given PUBLIC_API_ENDPOINT vacio When ejecuto build Then falla con mensaje del guard', () => {
      const result = runBuild({
        ...ENV_DEV,
        PUBLIC_API_ENDPOINT: '',
      })
      expect(result.ok).toBe(false)
      expect(result.stderr).toMatch(/PUBLIC_API_ENDPOINT vacio/)
    }, 120_000)

    it('Given PUBLIC_API_ENDPOINT apunta a prod pero BASE_DOMAIN=dev When build Then falla con mismatch', () => {
      const result = runBuild({
        ...ENV_DEV,
        PUBLIC_API_ENDPOINT: 'https://api.portfolio.the-full-stack.com',
      })
      expect(result.ok).toBe(false)
      expect(result.stderr).toMatch(/no matchea BASE_DOMAIN/)
    }, 120_000)
  })
})
