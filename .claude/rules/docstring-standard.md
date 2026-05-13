# Estandar de Docstring (agnostico al lenguaje)

> Guia para documentar cualquier unidad de codigo del portfolio:
> componentes Astro, layouts, utilities, validators, content collection
> schemas, configuraciones. Pensado para usarse en `.astro`, `.ts`, `.md`,
> `.css`, `.yaml`.
>
> Stack: Astro 6 + TypeScript 6 + Biome v2 + Vitest + Playwright.

## Filosofia

El docstring **no es decoracion**. Es el **contrato** del bloque que documenta.
Permite a quien lee (humano o IA) entender:

1. **Que** hace (proposito).
2. **Por que** existe (razon tecnica o de diseno).
3. **Como** se usa (ejemplo).
4. **Que entra y sale** (props, params, retorno).
5. **Quien** lo creo (auditoria — opcional, ver politica abajo).

Si quien lee tiene que **leer la implementacion** para entender estas 5 cosas, el docstring fallo.

## Anatomia universal

```text
1. NOMBRE        — que es esta unidad
2. DESCRIPCION   — que hace en una linea
3. CONTEXTO      — por que existe (opcional, recomendado)
4. ENTRADA       — props, params
5. SALIDA        — return, throws, side effects
6. EJEMPLO       — uso tipico
7. NOTAS         — gotchas, deprecation, refs (opcional)
```

## Politica de `@author` y `@since`

- **`@author`** — opcional. `git blame` ya provee esta info. Usar **solo** cuando agrega contexto no obvio (autor externo, donacion de codigo).
- **`@since YYYY/MM/DD`** — opcional. La fecha del primer commit ya esta en `git log --follow`. Solo si el codigo precede al primer commit local.
- **NUNCA** atribuir a IA (`@author Claude`, `@author Cursor`, etc.). Politica de empresa.

Set obligatorio: `@<tipo>`, `@description`, `@example` (cuando aporte). El resto es condicional.

## Tags estandar

### Tags obligatorios

| Tag | Proposito | Cuando usar |
|-----|-----------|-------------|
| `@<tipo>` | Identifica el tipo + nombre. Ver tabla de tipos abajo. | Siempre |
| `@description` | Una linea explicando que hace | Siempre |
| `@example` | Como usarlo | Casi siempre (salvo trivial) |

### Tags condicionales

| Tag | Cuando usar |
|-----|-------------|
| `@props` / `@param` | Si recibe entrada |
| `@returns` | Si retorna valor no-void |
| `@throws` | Si puede lanzar excepciones |
| `@deprecated` | Si esta obsoleto (incluir alternativa) |
| `@see` | Para referencias cruzadas (otros archivos, issues) |
| `@todo` | Trabajo pendiente conocido |
| `@note` | Informacion importante adicional |
| `@author` | Solo cuando agrega contexto no obvio |
| `@since` | Solo cuando precede al primer commit local |

### Tipos (`@<tipo>`) por contexto

| Tipo | Uso |
|------|-----|
| `@component` | Componente Astro (`.astro`) |
| `@layout` | Layout Astro (`src/layouts/<X>.astro`) |
| `@page` | Pagina Astro (`src/pages/<X>.astro`) |
| `@module` | Archivo barrel o agrupador (`src/lib/index.ts`) |
| `@function` | Funcion utilitaria pura (en `src/lib/`) |
| `@class` | Clase (raro en este proyecto) |
| `@schema` | Zod schema (ej. content collections en `src/content/config.ts`) |
| `@type` | TypeScript type/interface compartido |
| `@config` | Archivo de configuracion (`astro.config.ts`, `biome.json`, etc.) |
| `@validator` | Funcion de validacion (`src/lib/validators/<X>.ts`) |
| `@formatter` | Funcion de formato (`src/lib/format-<X>.ts`) |

## Formato por contexto

La sintaxis del bloque de comentario depende del lenguaje. El contenido es el mismo.

### TSDoc / JSDoc (TS)

```ts
/**
 * @function formatDate
 * @description Formatea YYYY-MM al nombre del mes + ano segun locale (es/en)
 *
 * @param {string} input - Fecha en formato YYYY-MM (ej. "2024-01")
 * @param {'es' | 'en'} locale - Codigo de idioma
 *
 * @returns {string} Mes + ano legible (ej. "enero 2024" / "January 2024")
 *
 * @throws {Error} Si input no matchea YYYY-MM o el mes es 1-12 invalido
 *
 * @example
 *   formatDate('2024-01', 'es')  // "enero 2024"
 *   formatDate('2024-12', 'en')  // "December 2024"
 *
 * @see src/content/config.ts - Schema que usa este formatter al renderizar
 */
export function formatDate(input: string, locale: 'es' | 'en'): string
```

### Astro (frontmatter `---` con JSDoc en script)

```astro
---
/**
 * @component Hero
 * @description Hero del home con titulo, subtitulo y CTA principal
 *
 * @props {string} title - Titulo H1 (max 60 caracteres)
 * @props {string} subtitle - Subtitulo descriptivo
 * @props {string} ctaHref - URL del CTA (default: '#contact')
 * @props {string} [ctaLabel] - Texto del CTA (default: 'Contactar')
 *
 * @example
 *   <Hero
 *     title="Pablo Contreras"
 *     subtitle="Frontend Engineer & Tech Lead"
 *   />
 */
interface Props {
  title: string
  subtitle: string
  ctaHref?: string
  ctaLabel?: string
}
const { title, subtitle, ctaHref = '#contact', ctaLabel = 'Contactar' } = Astro.props
---

<section class="hero">
  <h1>{title}</h1>
  <p>{subtitle}</p>
  <a href={ctaHref}>{ctaLabel}</a>
</section>
```

### Markdown (rules, READMEs)

Frontmatter YAML al inicio del archivo:

```yaml
---
title: Convenciones Astro del portfolio
description: Stack, estructura, naming, Biome strict, testing con Vitest
related:
  - .claude/rules/astro-landing.md
  - .claude/rules/design-system.md
status: stable
---
```

### YAML (configs)

YAML soporta comentarios `#`:

```yaml
# @config: ci.yml
# @description: Pipeline CI - lint + typecheck + build sobre PRs a main
# @triggers: pull_request a main | master
```

JSON no soporta comentarios. Documentar en archivo `.md` adyacente.

### Bash / Shell

```bash
#!/usr/bin/env bash
# @file: deploy.sh
# @description: Despliega dist/ a Vercel desde local
# @param: $1 - target (preview|production)
# @returns: 0 si exito, 1 si falla auth, 2 si falla upload
#
# @example:
#   ./scripts/deploy.sh production
```

## Plantillas reutilizables

### Componente Astro (presentacional)

```astro
---
/**
 * @component ExperienceCard
 * @description Tarjeta de experiencia laboral del CV
 *
 * @props {string} role - Cargo
 * @props {string} company - Empresa
 * @props {string} startDate - YYYY-MM
 * @props {string} [endDate] - YYYY-MM, omitir para "Presente"
 *
 * @example
 *   <ExperienceCard
 *     role="Senior Frontend"
 *     company="Acme"
 *     startDate="2024-01"
 *   >
 *     Liderazgo tecnico del equipo de frontend (5 personas).
 *   </ExperienceCard>
 */
interface Props {
  role: string
  company: string
  startDate: string
  endDate?: string
}
const { role, company, startDate, endDate } = Astro.props
---
```

### Funcion utility (pura)

```ts
/**
 * @function slugify
 * @description Convierte titulo a slug URL-safe (kebab-case sin acentos)
 *
 * @param {string} title - Titulo original (puede tener acentos, espacios, mayusculas)
 *
 * @returns {string} Slug kebab-case ASCII-only
 *
 * @example
 *   slugify('Mi Proyecto Genial')      // "mi-proyecto-genial"
 *   slugify('Café & Té')               // "cafe-y-te"
 *   slugify('  con  espacios  ')       // "con-espacios"
 */
export function slugify(title: string): string
```

### Validator

```ts
/**
 * @validator validateEmail
 * @description Valida formato de email basico (no garantiza deliverability)
 *
 * @param {string} input - String a validar
 *
 * @returns {{ valid: true } | { valid: false, error: 'REQUIRED' | 'INVALID_FORMAT' }} Resultado discriminado
 *
 * @example
 *   validateEmail('user@example.com')  // { valid: true }
 *   validateEmail('user@')              // { valid: false, error: 'INVALID_FORMAT' }
 *   validateEmail('')                   // { valid: false, error: 'REQUIRED' }
 */
export function validateEmail(input: string): ValidationResult
```

### Zod schema (content collection)

```ts
/**
 * @schema experienceSchema
 * @description Schema de entry de experiencia laboral en content collection
 *
 * @example
 *   // src/content/experience/2024-acme.md
 *   ---
 *   role: Senior Frontend
 *   company: Acme
 *   startDate: 2024-01
 *   endDate: 2026-05
 *   highlights:
 *     - Lidere migracion a Astro 6
 *     - Reduje LCP de 3.2s a 1.4s
 *   ---
 *
 * @see src/content/config.ts - Definicion completa
 */
export const experienceSchema = z.object({ /* ... */ })
```

## Reglas de estilo

### 1. Una linea para `@description`

MAL:

```ts
/**
 * @function formatDate
 * @description Esta funcion recibe una fecha YYYY-MM y un locale.
 *   La formatea segun el idioma. Tambien valida que el mes sea valido.
 */
```

BIEN:

```ts
/**
 * @function formatDate
 * @description Formatea YYYY-MM al nombre del mes + ano segun locale (es/en)
 */
```

### 2. `@example` con codigo real, no pseudocodigo

MAL:

```ts
/**
 * @example
 *   formatDate('YYYY-MM', 'locale')
 */
```

BIEN:

```ts
/**
 * @example
 *   formatDate('2024-01', 'es')  // "enero 2024"
 *   formatDate('2024-12', 'en')  // "December 2024"
 */
```

### 3. Tipos explicitos en `@props` / `@param`

```ts
/**
 * @props {string} title - Titulo H1 (max 60 caracteres)
 * @props {boolean} [featured] - Destacar la card (default: false)
 */
```

### 4. Defaults documentados

```ts
/**
 * @props {boolean} featured - Destacar la card (default: false)
 * @props {'small' | 'medium' | 'large'} size - Tamano (default: 'medium')
 */
```

### 5. Idioma

- `@description`, `@note`, `@todo` — **espanol**.
- Identificadores (`title`, `variant`, `'astro'`) — **ingles**.

### 6. Sin atribucion a IA

```ts
// PROHIBIDO
/** @author Pablo Contreras (con asistencia de Claude) */
/** @author Generated with AI */
```

### 7. Sin informacion sensible en ejemplos

MAL:

```ts
/**
 * @example
 *   sendContactEmail('mi.email.real@gmail.com', 'mensaje')
 */
```

BIEN — datos sinteticos:

```ts
/**
 * @example
 *   sendContactEmail('user@example.com', 'Hola, me interesa colaborar')
 */
```

### 8. Sin redundancia con tipos TypeScript

MAL — el tipo ya esta en la signature, no repetir:

```ts
/**
 * @function add
 * @description Suma dos numeros
 * @param {number} a - Primer numero
 * @param {number} b - Segundo numero
 * @returns {number} La suma
 */
function add(a: number, b: number): number
```

BIEN — el docstring aporta contexto que el tipo no captura:

```ts
/**
 * @function add
 * @description Suma sin overflow (clamp a Number.MAX_SAFE_INTEGER)
 * @param {number} a - Sumando A
 * @param {number} b - Sumando B
 * @returns {number} Suma clampeada al rango seguro de JS
 */
function add(a: number, b: number): number
```

## Cuando NO documentar

No todo necesita docstring.

### SI documentar

- Componentes Astro con props complejas
- Layouts (`src/layouts/`)
- Hooks o utilities reutilizables en `src/lib/`
- Validators (`src/lib/validators/`)
- Formatters (`src/lib/format-*.ts`)
- Zod schemas con reglas no-triviales
- Configs criticas (`astro.config.ts`, `biome.json` overrides)

### Opcional (recomendado si la logica no es obvia)

- Funciones internas privadas (`_helper`)
- Tipos / interfaces complejos

### NO necesita docstring

- Componentes triviales sin props
- Variables locales triviales
- Loops / condicionales obvios
- Re-exports puros (`export * from './foo'`)
- `*.test.ts` — el nombre del test es el contrato

## Anti-patrones

### Docstring que repite el nombre

MAL:

```ts
/**
 * @function getItems
 * @description Obtiene los items
 */
```

BIEN:

```ts
/**
 * @function getItems
 * @description Lista items del CV agrupados por categoria, ordenados por fecha desc
 */
```

### Docstring desactualizado

```ts
/**
 * @props oldName - ...   ← el codigo ahora tiene `newName`
 */
```

**Peor que no docstring**. Mantener sincronizado con cada cambio.

### Tags inventados

Solo usar tags del vocabulario estandar definido arriba.

### Comentarios que explican lo obvio

```ts
// Aumenta el contador en 1
counter++
```

Eliminar. Comentar **el por que**, no el que:

```ts
// Throttle a 60fps porque el browser no renderea mas rapido
counter++
```

## Checklist mental al escribir un docstring

Antes de commit, verifica:

- [ ] El `@<tipo>` y nombre coinciden con el codigo.
- [ ] `@description` es una linea, sin redundancia, aporta valor.
- [ ] Todos los props/params no-obvios estan documentados con tipos y defaults.
- [ ] Returns y throws documentados (cuando aplica).
- [ ] `@example` tiene codigo real, no pseudocodigo.
- [ ] No hay info sensible (emails reales, contactos, tokens).
- [ ] Sincronizado con el codigo actual.
- [ ] Idioma correcto: descripcion en espanol, identificadores en ingles.
- [ ] Sin atribucion a IA.

## Validacion automatica

Por ahora **no hay enforcement automatico** de docstrings (Biome v2 no soporta plugins custom todavia). El review se hace via:

- `code-reviewer` agent (verifica calidad de docstrings en cambios).
- Code review humano en PRs.
- Esta rule como referencia.

## Referencias

- Naming relacionado: `astro-landing.md`
- Diseno: `design-system.md`
