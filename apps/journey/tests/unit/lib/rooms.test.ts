import type { Experience } from '@portfolio/content'
import { describe, expect, it } from 'vitest'
import { buildRooms, MVP_ROOM_SPECS } from '../../../src/lib/rooms'

/**
 * Fixture minima de Experience valida contra el schema de content.
 */
function makeExperience(overrides: Partial<Experience>): Experience {
  return {
    slug: 'fixture',
    role: { es: 'Rol ES', en: 'Role EN' },
    company: 'Fixture Co',
    country: 'Venezuela',
    start: '2013-01',
    end: '2013-12',
    niches: ['generic'],
    priority: {},
    summary: { es: 'Resumen ES', en: 'Summary EN' },
    responsibilities: { es: ['Resp ES 1'], en: ['Resp EN 1'] },
    achievements: { es: ['Logro ES 1'], en: ['Achievement EN 1'] },
    skillsTechnical: ['PHP'],
    skillsSoft: ['Comunicacion'],
    seniority: 'intern',
    metricsEstimated: false,
    ...overrides,
  }
}

const FIXTURES: readonly Experience[] = [
  makeExperience({
    slug: 'iai',
    company: 'Proyecto academico',
    start: '2015-01',
    end: '2015-12',
    summary: { es: 'Sistema IAI', en: 'IAI system' },
    responsibilities: { es: ['Disenar IAI'], en: ['Design IAI'] },
    achievements: { es: ['Entregue IAI'], en: ['Delivered IAI'] },
    skillsTechnical: ['Java'],
    skillsSoft: ['Liderazgo'],
  }),
  makeExperience({
    slug: 'projects-degrees',
    company: 'Asesoria de grado',
    start: '2015-01',
    end: '2015-12',
    summary: { es: 'Rescate de tesis', en: 'Thesis rescue' },
    responsibilities: {
      es: ['Reencaminar proyectos'],
      en: ['Redirect projects'],
    },
    achievements: {
      es: ['Capacite 6 estudiantes'],
      en: ['Trained 6 students'],
    },
    skillsTechnical: ['Java', 'SQL'],
    skillsSoft: ['Liderazgo'],
  }),
  makeExperience({
    slug: 'corpoelec',
    company: 'CORPOELEC',
    start: '2013-01',
    end: '2013-12',
    summary: { es: 'Inventario offline', en: 'Offline inventory' },
    responsibilities: {
      es: ['Levantar requerimientos'],
      en: ['Gather requirements'],
    },
    achievements: { es: ['Centralice 3 sedes'], en: ['Centralized 3 sites'] },
    skillsTechnical: ['PHP', 'jQuery'],
    skillsSoft: ['Comunicacion'],
  }),
  makeExperience({
    slug: 'destacame-architect',
    company: 'Destacame',
    country: 'Chile',
    start: '2022-08',
    end: undefined,
    seniority: 'lead',
    summary: { es: 'Arquitectura fintech', en: 'Fintech architecture' },
    responsibilities: { es: ['Orquestar CL+MX'], en: ['Orchestrate CL+MX'] },
    achievements: { es: ['Lidere equipos 4-6'], en: ['Led teams of 4-6'] },
    skillsTechnical: ['Django', 'Vue'],
    skillsSoft: ['Liderazgo'],
  }),
]

describe('MVP_ROOM_SPECS', () => {
  it('Given el plan MVP When se leen los specs Then define aula, corpoelec y cima en ese orden', () => {
    expect(MVP_ROOM_SPECS.map((s) => s.id)).toEqual([
      'aula',
      'corpoelec',
      'cima',
    ])
    expect(MVP_ROOM_SPECS.map((s) => [...s.slugs])).toEqual([
      ['iai', 'projects-degrees'],
      ['corpoelec'],
      ['destacame-architect'],
    ])
  })
})

describe('buildRooms', () => {
  it('Given los fixtures When se construyen las salas Then retorna 3 salas ordenadas segun el plan', () => {
    const rooms = buildRooms(FIXTURES)

    expect(rooms.map((r) => r.id)).toEqual(['aula', 'corpoelec', 'cima'])
    expect(rooms.map((r) => r.order)).toEqual([0, 1, 2])
  })

  it('Given una sala de un solo slug When se derivan los textos Then retos = summary + responsibilities y aprendizajes = achievements + linea de skills', () => {
    const rooms = buildRooms(FIXTURES)
    const corpoelec = rooms[1]

    expect(corpoelec?.texts.es.retos).toEqual([
      'Inventario offline',
      'Levantar requerimientos',
    ])
    expect(corpoelec?.texts.es.aprendizajes).toEqual([
      'Centralice 3 sedes',
      'Skills: PHP · jQuery · Comunicacion',
    ])
    expect(corpoelec?.texts.en.retos).toEqual([
      'Offline inventory',
      'Gather requirements',
    ])
    expect(corpoelec?.texts.en.aprendizajes).toEqual([
      'Centralized 3 sites',
      'Skills: PHP · jQuery · Comunicacion',
    ])
  })

  it('Given la sala aula con 2 slugs When se derivan los textos Then fusiona ambos y deduplica skills preservando el orden', () => {
    const rooms = buildRooms(FIXTURES)
    const aula = rooms[0]

    expect(aula?.texts.es.retos).toEqual([
      'Sistema IAI',
      'Disenar IAI',
      'Rescate de tesis',
      'Reencaminar proyectos',
    ])
    expect(aula?.texts.es.aprendizajes).toEqual([
      'Entregue IAI',
      'Capacite 6 estudiantes',
      'Skills: Java · SQL · Liderazgo',
    ])
  })

  it('Given los seniorities When se derivan los params visuales Then la cima supera al aula en escala, luz y densidad (eje seniority)', () => {
    const rooms = buildRooms(FIXTURES)
    const aula = rooms[0]
    const cima = rooms[2]

    expect(aula?.seniority).toBe('intern')
    expect(cima?.seniority).toBe('lead')
    expect(aula?.scale).toBe(1)
    expect(cima?.scale).toBe(1.65)
    expect(aula?.lightIntensity).toBe(0.55)
    expect(cima?.lightIntensity).toBe(1)
    expect(aula?.propDensity).toBe(0.4)
    expect(cima?.propDensity).toBe(1)
  })

  it('Given los rangos de fechas When se formatea el periodo Then usa el año unico, el rango o "hoy"/"today"', () => {
    const rooms = buildRooms(FIXTURES)

    expect(rooms[0]?.texts.es.period).toBe('2015')
    expect(rooms[1]?.texts.es.period).toBe('2013')
    expect(rooms[2]?.texts.es.period).toBe('2022 — hoy')
    expect(rooms[2]?.texts.en.period).toBe('2022 — today')
    expect(rooms.map((r) => r.year)).toEqual(['2015', '2013', '2022'])
  })

  it('Given un slug del spec ausente en las experiences When se construyen las salas Then lanza un error que nombra el slug', () => {
    const sinCorpoelec = FIXTURES.filter((e) => e.slug !== 'corpoelec')

    expect(() => buildRooms(sinCorpoelec)).toThrowError(
      'buildRooms: experience "corpoelec" no encontrada en @portfolio/content',
    )
  })

  it('Given los datos reales de @portfolio/content When se construyen las salas Then las 3 salas del MVP existen con el seniority real', () => {
    const rooms = buildRooms()

    expect(rooms.map((r) => r.id)).toEqual(['aula', 'corpoelec', 'cima'])
    expect(rooms[1]?.seniority).toBe('intern')
    expect(rooms[2]?.seniority).toBe('lead')
    expect(rooms[2]?.texts.es.period).toBe('2022 — hoy')
  })
})
