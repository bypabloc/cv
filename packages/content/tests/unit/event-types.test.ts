/**
 * @description Tests del catalogo de tipos de evento.
 *
 *   Cubre tres cosas:
 *   1. Formato: cada valor de `EVENT_TYPES` es un UUID string valido.
 *   2. Paridad SQL <-> TS: los seeds de `serverless/migrations/` (006 +
 *      008) y `EVENT_TYPES` deben usar exactamente los mismos UUID. Si
 *      alguien edita uno sin el otro, este test falla y atrapa el drift.
 *   3. Mapa por code_name: `EVENT_TYPE_BY_CODE` mapea el snake_case del
 *      catalogo SQL al UUID; `eventTypeIdFromCode` resuelve un code.
 *
 *   El test parsea el INSERT de cada .sql con un regex, extrae los pares
 *   (code_name, uuid) y verifica contra las constantes TS.
 */
import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  EVENT_TYPE_BY_CODE,
  EVENT_TYPES,
  type EventTypeCode,
  eventTypeIdFromCode,
} from '../../src/lib/event-types'

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

const MIGRATIONS_DIR = resolve(__dirname, '../../../../serverless/migrations')

/**
 * Catalogo esperado: code_name del seed SQL -> clave de `EVENT_TYPES`.
 * Es la lista canonica de SPEC-200 (migration 008) + page_load (006).
 * Si crece el catalogo, esta tabla y `EVENT_TYPES` deben crecer juntas.
 */
const EXPECTED_CATALOG: Record<string, EventTypeCode> = {
  page_load: 'PAGE_LOAD',
  spa_navigation: 'SPA_NAVIGATION',
  cta_click: 'CTA_CLICK',
  nav_click: 'NAV_CLICK',
  project_link_click: 'PROJECT_LINK_CLICK',
  experience_link_click: 'EXPERIENCE_LINK_CLICK',
  cv_download: 'CV_DOWNLOAD',
  theme_toggle: 'THEME_TOGGLE',
  external_link_click: 'EXTERNAL_LINK_CLICK',
  contact_view: 'CONTACT_VIEW',
  contact_form_start: 'CONTACT_FORM_START',
  contact_form_submit: 'CONTACT_FORM_SUBMIT',
  contact_form_success: 'CONTACT_FORM_SUCCESS',
  contact_form_error: 'CONTACT_FORM_ERROR',
  scroll_depth: 'SCROLL_DEPTH',
  page_exit: 'PAGE_EXIT',
}

/**
 * Parsea los pares (code_name, uuid) del INSERT de una migration de seed.
 *
 * Las filas del seed tienen la forma:
 *   ('<uuid>', '<code_name>', '<description>')
 * Se extrae uuid + code_name (los dos primeros literales de cada tupla).
 */
function parseSeedUuids(sqlPath: string): Map<string, string> {
  const pairs = new Map<string, string>()
  if (!existsSync(sqlPath)) return pairs
  const sql = readFileSync(sqlPath, 'utf-8')
  const rowRe = /\(\s*'([0-9a-f-]{36})'\s*,\s*'([a-z_]+)'/gi
  for (const match of sql.matchAll(rowRe)) {
    const uuid = match[1]
    const codeName = match[2]
    if (uuid && codeName) {
      pairs.set(codeName, uuid)
    }
  }
  return pairs
}

const seed006 = parseSeedUuids(resolve(MIGRATIONS_DIR, '006_event_types.sql'))
const seed008 = parseSeedUuids(
  resolve(MIGRATIONS_DIR, '008_event_types_seed.sql'),
)

/**
 * Catalogo SQL combinado: 006 (page_load) + 008 (el resto). Si 008 todavia
 * no existe en este worktree, el test de paridad de 008 se salta con guarda.
 */
const seededCatalog = new Map<string, string>([...seed006, ...seed008])

describe('EVENT_TYPES', () => {
  it('Given EVENT_TYPES.PAGE_LOAD When inspect Then is a valid UUID string', () => {
    expect(EVENT_TYPES.PAGE_LOAD).toMatch(UUID_RE)
  })

  it('Given every EVENT_TYPES value When inspect Then all are valid UUID strings', () => {
    const invalid = Object.entries(EVENT_TYPES).filter(
      ([, uuid]) => !UUID_RE.test(uuid),
    )
    expect(invalid).toEqual([])
  })

  it('Given EVENT_TYPES When count keys Then exposes the full 16-event catalog', () => {
    expect(Object.keys(EVENT_TYPES).length).toBe(16)
  })

  it('Given every EVENT_TYPES value When collected Then all UUIDs are unique', () => {
    const values = Object.values(EVENT_TYPES)
    expect(new Set(values).size).toBe(values.length)
  })

  it('Given the barrel @portfolio/content When import EVENT_TYPES Then it is exported and typed', () => {
    const code: EventTypeCode = 'PAGE_LOAD'
    expect(EVENT_TYPES[code]).toBe('019e372b-e0a7-7154-8279-8829bcf6a08c')
  })
})

describe('EVENT_TYPE_BY_CODE / eventTypeIdFromCode', () => {
  it('Given code_name cta_click When eventTypeIdFromCode Then returns CTA_CLICK UUID', () => {
    expect(eventTypeIdFromCode('cta_click')).toBe(EVENT_TYPES.CTA_CLICK)
  })

  it('Given an unknown code When eventTypeIdFromCode Then returns undefined', () => {
    expect(eventTypeIdFromCode('not_a_real_event')).toBe(undefined)
  })

  it('Given EVENT_TYPE_BY_CODE When inspect page_load Then maps to PAGE_LOAD UUID', () => {
    expect(EVENT_TYPE_BY_CODE.page_load).toBe(EVENT_TYPES.PAGE_LOAD)
  })

  it('Given EVENT_TYPE_BY_CODE When count entries Then has one per EVENT_TYPES key', () => {
    expect(Object.keys(EVENT_TYPE_BY_CODE).length).toBe(
      Object.keys(EVENT_TYPES).length,
    )
  })
})

describe('event_types catalog parity (SQL <-> TS) [AC-2]', () => {
  it('Given the expected catalog When checked Then every code maps to an EVENT_TYPES key', () => {
    for (const [, tsCode] of Object.entries(EXPECTED_CATALOG)) {
      expect(EVENT_TYPES[tsCode]).toMatch(UUID_RE)
    }
  })

  it('Given EVENT_TYPES When compared Then every key appears in the expected catalog', () => {
    const expectedCodes = new Set(Object.values(EXPECTED_CATALOG))
    const tsCodes = Object.keys(EVENT_TYPES) as EventTypeCode[]
    const missing = tsCodes.filter((code) => !expectedCodes.has(code))
    expect(missing).toEqual([])
  })

  it('Given migration 006 seed When parse Then page_load UUID matches EVENT_TYPES.PAGE_LOAD', () => {
    expect(seed006.get('page_load')).toBe(EVENT_TYPES.PAGE_LOAD)
  })

  it('Given the seeded SQL catalog When compared Then every seeded code_name matches its TS constant', () => {
    for (const [codeName, uuid] of seededCatalog) {
      const tsCode = EXPECTED_CATALOG[codeName]
      expect(tsCode).not.toBe(undefined)
      expect(EVENT_TYPES[tsCode as EventTypeCode]).toBe(uuid)
    }
  })

  it('Given migration 008 seed When it exists Then it seeds every non-page_load event', () => {
    // Guarda: 008 lo crea el backend en Fase 2; si todavia no esta en este
    // worktree el test no falla, solo se salta la comprobacion de 008.
    if (seed008.size === 0) return
    for (const [codeName, tsCode] of Object.entries(EXPECTED_CATALOG)) {
      if (codeName === 'page_load') continue
      expect(seed008.get(codeName)).toBe(EVENT_TYPES[tsCode])
    }
  })
})
