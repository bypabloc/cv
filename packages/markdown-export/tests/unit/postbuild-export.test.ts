/**
 * @description Tests para postbuildExport — itera dist/ y escribe .md por
 *   cada index.html. Usa un tmp dir + fs real (no mock-fs) para coverage
 *   real del walk recursivo.
 */
import { mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { postbuildExport } from '../../src/lib/postbuild-export'

describe('postbuildExport', () => {
  let workDir: string

  beforeEach(async () => {
    workDir = await mkdtemp(join(tmpdir(), 'mdx-test-'))
  })

  afterEach(async () => {
    await rm(workDir, { recursive: true, force: true })
  })

  it('Given dist con 1 index.html When export Then crea 1 .md gemelo', async () => {
    await writeFile(
      join(workDir, 'index.html'),
      '<body><main><h1>Home</h1></main></body>',
    )

    const result = await postbuildExport({ distDir: workDir })

    expect(result.count).toBe(1)
    const md = await readFile(join(workDir, 'index.md'), 'utf8')
    expect(md).toBe('# Home\n')
  })

  it('Given dist con index.html anidados When export Then crea .md gemelo por cada uno', async () => {
    await writeFile(
      join(workDir, 'index.html'),
      '<body><main><h1>Home</h1></main></body>',
    )
    await mkdir(join(workDir, 'about'))
    await writeFile(
      join(workDir, 'about', 'index.html'),
      '<body><main><h1>About</h1></main></body>',
    )
    await mkdir(join(workDir, 'projects', 'x'), { recursive: true })
    await writeFile(
      join(workDir, 'projects', 'x', 'index.html'),
      '<body><main><h1>X</h1></main></body>',
    )

    const result = await postbuildExport({ distDir: workDir })

    expect(result.count).toBe(3)
    expect(result.paths).toEqual([
      join(workDir, 'about', 'index.md'),
      join(workDir, 'index.md'),
      join(workDir, 'projects', 'x', 'index.md'),
    ])
  })

  it('Given dist con cv.html suelto When export Then crea cv.md gemelo', async () => {
    await writeFile(join(workDir, 'cv.html'), '<body><main>CV</main></body>')

    const result = await postbuildExport({ distDir: workDir })

    expect(result.paths).toEqual([join(workDir, 'cv.md')])
    expect(await readFile(join(workDir, 'cv.md'), 'utf8')).toContain('CV')
  })

  it('Given dist con 2 paginas When export Then llms-full.txt las concatena con su origen', async () => {
    await writeFile(join(workDir, 'index.html'), '<main><p>Home</p></main>')
    await mkdir(join(workDir, 'about'), { recursive: true })
    await writeFile(
      join(workDir, 'about', 'index.html'),
      '<main><p>About</p></main>',
    )

    await postbuildExport({ distDir: workDir })

    expect(await readFile(join(workDir, 'llms-full.txt'), 'utf8')).toBe(
      'Source: /about/index.md\n\nAbout\n\n---\n\nSource: /index.md\n\nHome\n',
    )
  })

  it('Given dist sin index.html When export Then count es 0', async () => {
    await writeFile(join(workDir, '404.html'), '<body><main>404</main></body>')

    const result = await postbuildExport({ distDir: workDir })

    expect(result.count).toBe(0)
    expect(result.paths).toEqual([])
  })

  it('Given index.html con nav+main+footer When export Then el .md solo tiene el main', async () => {
    await writeFile(
      join(workDir, 'index.html'),
      '<body><nav>NAV</nav><main><h1>X</h1></main><footer>F</footer></body>',
    )

    await postbuildExport({ distDir: workDir })

    const md = await readFile(join(workDir, 'index.md'), 'utf8')
    expect(md).toBe('# X\n')
  })
})
