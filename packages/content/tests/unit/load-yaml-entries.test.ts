/**
 * @description Tests para loadYamlEntries. Cubre AC-2 (Zod error con filename),
 *   AC-3 (filename slug === YAML.slug enforced).
 */
import { describe, expect, it } from 'vitest'
import { z } from 'zod'
import { loadYamlEntries } from '../../src/lib/load-yaml-entries'

const TestSchema = z.object({
  slug: z.string().min(1),
  name: z.string().min(1),
  value: z.number().int(),
})
type TestEntry = z.infer<typeof TestSchema>

describe('loadYamlEntries', () => {
  it('Given valid modules When load Then returns parsed entries sorted by slug', () => {
    const modules: Record<string, { default: unknown }> = {
      '/abs/path/to/data/foo/zebra.yaml': {
        default: { slug: 'zebra', name: 'Zebra', value: 3 },
      },
      '/abs/path/to/data/foo/alpha.yaml': {
        default: { slug: 'alpha', name: 'Alpha', value: 1 },
      },
      '/abs/path/to/data/foo/beta.yaml': {
        default: { slug: 'beta', name: 'Beta', value: 2 },
      },
    }
    const result = loadYamlEntries<TestEntry>(modules, TestSchema)
    expect(result.map((e) => e.slug)).toEqual(['alpha', 'beta', 'zebra'])
  })

  it('Given filename slug mismatch When load Then throws error with both slugs and path', () => {
    const modules: Record<string, { default: unknown }> = {
      '/abs/path/to/data/foo/destacame-architect.yaml': {
        default: { slug: 'wrong-slug', name: 'X', value: 1 },
      },
    }
    expect(() => loadYamlEntries<TestEntry>(modules, TestSchema)).toThrowError(
      /destacame-architect\.yaml.*wrong-slug/s,
    )
  })

  it('Given invalid YAML (Zod fails) When load Then throws error including filename', () => {
    const modules: Record<string, { default: unknown }> = {
      '/abs/path/to/data/foo/broken.yaml': {
        default: { slug: 'broken', name: 'X', value: 'not-a-number' },
      },
    }
    expect(() => loadYamlEntries<TestEntry>(modules, TestSchema)).toThrowError(
      /broken\.yaml/,
    )
  })

  it('Given empty modules When load Then returns empty array', () => {
    const result = loadYamlEntries<TestEntry>({}, TestSchema)
    expect(result).toEqual([])
  })

  it('Given module without default export When load Then throws error citing the path', () => {
    const modules = {
      '/abs/path/to/data/foo/orphan.yaml': {},
    } as unknown as Record<string, { default: unknown }>
    expect(() => loadYamlEntries<TestEntry>(modules, TestSchema)).toThrowError(
      /orphan\.yaml/,
    )
  })

  it('Given schema without slug field When load Then skips slug-match assertion', () => {
    const NoSlugSchema = z.object({ name: z.string().min(1) })
    type NoSlugEntry = z.infer<typeof NoSlugSchema>
    const modules: Record<string, { default: unknown }> = {
      '/abs/path/to/data/langs/spanish.yaml': { default: { name: 'Spanish' } },
      '/abs/path/to/data/langs/english.yaml': { default: { name: 'English' } },
    }
    const result = loadYamlEntries<NoSlugEntry>(modules, NoSlugSchema)
    expect(result).toEqual([{ name: 'English' }, { name: 'Spanish' }])
  })

  it('Given path without .yaml extension When load Then throws error citing the path', () => {
    const modules: Record<string, { default: unknown }> = {
      '/abs/path/to/data/foo/no-extension': {
        default: { slug: 'no-extension', name: 'X', value: 1 },
      },
    }
    expect(() => loadYamlEntries<TestEntry>(modules, TestSchema)).toThrowError(
      /no-extension/,
    )
  })

  it('Given filename slug matches YAML slug When load Then succeeds and preserves field', () => {
    const modules: Record<string, { default: unknown }> = {
      '/abs/path/to/data/foo/destacame-architect.yaml': {
        default: {
          slug: 'destacame-architect',
          name: 'Destacame',
          value: 100,
        },
      },
    }
    const result = loadYamlEntries<TestEntry>(modules, TestSchema)
    expect(result).toEqual([
      { slug: 'destacame-architect', name: 'Destacame', value: 100 },
    ])
  })
})
