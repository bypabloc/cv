/**
 * @function loadYamlEntries
 * @description Helper generico que toma el resultado de `import.meta.glob('./*.yaml',
 *   { eager: true })`, valida cada entry con un schema Zod y retorna un array
 *   tipado readonly. Aplica dos invariantes:
 *
 *   1. Si el schema declara un campo `slug` string, el valor del campo debe
 *      coincidir con el slug derivado del filename (`destacame-architect.yaml`
 *      -> slug `'destacame-architect'`). Esto previene drift entre filename y
 *      contenido.
 *   2. El array resultante se ordena ascendentemente por slug (cuando aplica) o
 *      por basename del filename, para que los snapshots sean estables entre
 *      OS y entre filesystems con orden de glob no determinista.
 *
 *   Si una entry falla Zod, o si la entry no tiene `default`, o si el slug
 *   no matchea, se lanza un Error con el path absoluto del YAML.
 *
 * @example
 *   const modules = import.meta.glob<{ default: unknown }>('./*.yaml', { eager: true })
 *   export const experiences = loadYamlEntries<Experience>(modules, ExperienceSchema)
 */
import type { ZodTypeAny, z } from 'zod'

type GlobModules = Record<
  string,
  { default: unknown } | Record<string, unknown>
>

/** Extrae el slug del filename: `/abs/.../destacame-architect.yaml` -> `destacame-architect`. */
function slugFromPath(path: string): string {
  const match = path.match(/([^/\\]+)\.ya?ml$/)
  if (!match) {
    throw new Error(`loadYamlEntries: path no termina en .yaml: ${path}`)
  }
  return match[1] as string
}

export function loadYamlEntries<T>(
  modules: GlobModules,
  schema: ZodTypeAny,
): readonly T[] {
  const entries: { slug: string; data: T }[] = []

  for (const [path, mod] of Object.entries(modules)) {
    if (!mod || typeof mod !== 'object' || !('default' in mod)) {
      throw new Error(
        `loadYamlEntries: el YAML "${path}" no expone default export. Verifica que vite-plugin-yaml este registrado en el bundler/vitest.`,
      )
    }

    const raw = (mod as { default: unknown }).default
    const fileSlug = slugFromPath(path)

    let parsed: z.infer<typeof schema>
    try {
      parsed = schema.parse(raw)
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      throw new Error(`loadYamlEntries: ${path} fallo validacion Zod: ${msg}`)
    }

    if (
      parsed &&
      typeof parsed === 'object' &&
      'slug' in parsed &&
      typeof (parsed as { slug: unknown }).slug === 'string'
    ) {
      const yamlSlug = (parsed as { slug: string }).slug
      if (yamlSlug !== fileSlug) {
        throw new Error(
          `loadYamlEntries: slug mismatch en ${path}: filename="${fileSlug}" pero YAML.slug="${yamlSlug}". Renombra el archivo o ajusta el campo slug.`,
        )
      }
    }

    entries.push({ slug: fileSlug, data: parsed as T })
  }

  entries.sort((a, b) => a.slug.localeCompare(b.slug))
  return entries.map((e) => e.data)
}
