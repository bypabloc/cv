/**
 * @description Tests para bundlePagesFunction — usa esbuild para bundlear
 *   un .ts standalone en un .js Worker-compatible.
 */
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { bundlePagesFunction } from '../../src/lib/bundle-pages-function'

describe('bundlePagesFunction', () => {
  let workDir: string

  beforeEach(async () => {
    workDir = await mkdtemp(join(tmpdir(), 'mdx-bundle-'))
  })

  afterEach(async () => {
    await rm(workDir, { recursive: true, force: true })
  })

  it('Given TS entrypoint simple When bundle Then escribe ESM .js', async () => {
    const entry = join(workDir, 'mcp.ts')
    const out = join(workDir, 'mcp.js')
    await writeFile(
      entry,
      `export const onRequestPost = async (): Promise<Response> => {
        return new Response('{"ok":true}', { status: 200 })
      }`,
    )

    await bundlePagesFunction({ entryPoint: entry, outFile: out })

    const bundled = await readFile(out, 'utf8')
    expect(bundled).toContain('onRequestPost')
    expect(bundled).toContain('Response')
    expect(bundled).not.toContain(': Promise<Response>')
  })

  it('Given entrypoint con import local When bundle Then inlinea la dep', async () => {
    const helper = join(workDir, 'helper.ts')
    const entry = join(workDir, 'mcp.ts')
    const out = join(workDir, 'mcp.js')
    await writeFile(helper, `export const FLAG = 'XYZ123'`)
    await writeFile(
      entry,
      `import { FLAG } from './helper'
       export const onRequestPost = () => new Response(FLAG)`,
    )

    await bundlePagesFunction({ entryPoint: entry, outFile: out })

    const bundled = await readFile(out, 'utf8')
    expect(bundled).toContain('XYZ123')
    expect(bundled).not.toContain("from './helper'")
  })
})
