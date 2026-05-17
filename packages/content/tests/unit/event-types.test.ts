/**
 * @description Tests del catalogo de tipos de evento.
 *
 *   Cubre dos cosas:
 *   1. Formato: cada valor de `EVENT_TYPES` es un UUID string valido.
 *   2. Paridad SQL <-> TS: el seed de `serverless/migrations/006_event_types.sql`
 *      y `EVENT_TYPES` deben usar exactamente los mismos UUID. Si alguien edita
 *      uno sin el otro, este test falla y atrapa el drift.
 *
 *   El test parsea el INSERT del .sql con un regex, extrae los pares
 *   (code_name, uuid) y verifica contra las constantes TS.
 */
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import { EVENT_TYPES, type EventTypeCode } from '../../src/lib/event-types'

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

/**
 * Parsea los pares (code_name, uuid) del INSERT de la migration de seed.
 *
 * Las filas del seed tienen la forma:
 *   ('<uuid>', '<code_name>', '<description>')
 * Se extrae uuid + code_name (los dos primeros literales de cada tupla).
 */
function parseSeedUuids(sqlPath: string): Map<string, string> {
  const sql = readFileSync(sqlPath, 'utf-8')
  const rowRe = /\(\s*'([0-9a-f-]{36})'\s*,\s*'([a-z_]+)'/gi
  const pairs = new Map<string, string>()
  for (const match of sql.matchAll(rowRe)) {
    const uuid = match[1]
    const codeName = match[2]
    if (uuid && codeName) {
      pairs.set(codeName, uuid)
    }
  }
  return pairs
}

const seed006 = parseSeedUuids(
  resolve(__dirname, '../../../../serverless/migrations/006_event_types.sql'),
)

describe('EVENT_TYPES', () => {
  it('Given EVENT_TYPES.PAGE_LOAD When inspect Then is a valid UUID string', () => {
    expect(EVENT_TYPES.PAGE_LOAD).toMatch(UUID_RE)
  })

  it('Given the barrel @portfolio/content When import EVENT_TYPES Then it is exported and typed', () => {
    const code: EventTypeCode = 'PAGE_LOAD'
    expect(EVENT_TYPES[code]).toBe('019e372b-e0a7-7154-8279-8829bcf6a08c')
  })
})

describe('event_types catalog parity (SQL <-> TS)', () => {
  it('Given migration 006 seed When parse Then page_load UUID matches EVENT_TYPES.PAGE_LOAD', () => {
    expect(seed006.get('page_load')).toBe(EVENT_TYPES.PAGE_LOAD)
  })

  it('Given the SQL seed When compared Then every seeded code_name has a matching TS constant', () => {
    // Fase 1: el seed 006 solo trae page_load. SPEC-200 amplia el seed y el
    // mapa; este loop ya cubre el catalogo completo cuando crezca.
    const tsByCode: Record<string, string> = {
      page_load: EVENT_TYPES.PAGE_LOAD,
    }
    for (const [codeName, uuid] of seed006) {
      expect(tsByCode[codeName]).toBe(uuid)
    }
  })
})
