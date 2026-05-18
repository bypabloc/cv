/**
 * @function loadI18nFile
 * @description Valida un UNICO documento YAML i18n (1 archivo = 1 idioma)
 *   contra un schema Zod y retorna el objeto tipado. A diferencia de
 *   `loadYamlEntries`, no hace glob de N entries ni slug-match: los archivos
 *   i18n son documentos completos (`elements.es.yaml`, `vibe.en.yaml`).
 *
 *   El YAML se obtiene del resultado de `import.meta.glob('./*.yaml', {
 *   eager: true })`, igual que el resto de la data — asi `vite-plugin-yaml`
 *   lo procesa y expone como `default` export.
 *
 *   Si el modulo no expone `default`, o si el contenido no cumple el schema,
 *   se lanza un Error que incluye la clave del archivo (para diagnostico).
 *
 * @example
 *   const modules = import.meta.glob<{ default: unknown }>('./*.yaml', {
 *     eager: true,
 *   })
 *   const es = loadI18nFile('./elements.es.yaml', modules, ElementsStringsSchema)
 *
 * @see lib/load-yaml-entries.ts - El loader para colecciones (N entries)
 */
import type { ZodTypeAny, z } from 'zod'

type GlobModules = Record<
  string,
  { default: unknown } | Record<string, unknown>
>

/**
 * Resuelve la clave real dentro de `modules` para un path dado. `import.meta
 * .glob` indexa con la ruta relativa exacta (`./elements.es.yaml`); este
 * helper tolera que el caller pase la ruta con o sin el prefijo `./`.
 */
function resolveKey(path: string, modules: GlobModules): string {
  if (path in modules) return path
  const withDot = path.startsWith('./') ? path : `./${path}`
  if (withDot in modules) return withDot
  const bare = path.replace(/^\.\//, '')
  const match = Object.keys(modules).find(
    (k) => k === bare || k.endsWith(`/${bare}`),
  )
  if (match) return match
  throw new Error(
    `loadI18nFile: no se encontro "${path}" en el glob. ` +
      `Claves disponibles: ${Object.keys(modules).join(', ')}`,
  )
}

export function loadI18nFile<TSchema extends ZodTypeAny>(
  path: string,
  modules: GlobModules,
  schema: TSchema,
): z.infer<TSchema> {
  const key = resolveKey(path, modules)
  const mod = modules[key]

  if (!mod || typeof mod !== 'object' || !('default' in mod)) {
    throw new Error(
      `loadI18nFile: el YAML "${key}" no expone default export. ` +
        'Verifica que vite-plugin-yaml este registrado en el bundler/vitest.',
    )
  }

  const raw = (mod as { default: unknown }).default
  try {
    return schema.parse(raw)
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err)
    throw new Error(`loadI18nFile: ${key} fallo validacion Zod: ${msg}`)
  }
}
