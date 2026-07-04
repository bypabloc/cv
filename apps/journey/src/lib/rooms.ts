/**
 * @module rooms
 * @description Mapeo data-driven de las experiences reales de
 *   `@portfolio/content` a las salas del journey 3D (Propuesta A).
 *   Deriva los textos del plan: RETOS <- summary + responsibilities;
 *   APRENDIZAJES <- achievements + linea de skills. Los params visuales
 *   (escala/luz/densidad) materializan el eje seniority (AC-12).
 *
 * @see docs/specs/journey-3d-cv/07-implementacion-mvp.md
 */
import {
  type Experience,
  experiences,
  SENIORITIES,
  type SeniorityValue,
} from '@portfolio/content'

export type RoomId = 'aula' | 'corpoelec' | 'cima'
export type Locale = 'es' | 'en'

export interface RoomSpec {
  id: RoomId
  /** Experiences (por slug) que alimentan la sala, en orden narrativo. */
  slugs: readonly string[]
  title: Record<Locale, string>
  /** Que representa la sala (la reseña del cuaderno-atril). */
  represents: Record<Locale, string>
}

/**
 * Specs del MVP (3 salas). Agregar una sala = agregar un spec (+ su escena).
 * El orden del array ES el orden narrativo del recorrido (plan, Mapa de salas).
 */
export const MVP_ROOM_SPECS: readonly RoomSpec[] = [
  {
    id: 'aula',
    slugs: ['iai', 'projects-degrees'],
    title: { es: 'Aula — Universidad', en: 'Classroom — University' },
    represents: {
      es:
        'Esta sala representa los años de universidad: liderar equipos ' +
        'academicos, montar redes cliente-servidor y sentar la base de la ' +
        'arquitectura de software.',
      en:
        'This room represents the university years: leading academic ' +
        'teams, building client-server networks and laying the foundations ' +
        'of software architecture.',
    },
  },
  {
    id: 'corpoelec',
    slugs: ['corpoelec'],
    title: {
      es: 'CORPOELEC — Central electrica',
      en: 'CORPOELEC — Power utility',
    },
    represents: {
      es:
        'Esta sala representa la primera experiencia profesional: ' +
        'digitalizar el inventario de una central electrica estatal que ' +
        'vivia en planillas de papel.',
      en:
        'This room represents the first professional experience: ' +
        'digitising the inventory of a state power utility that lived on ' +
        'paper records.',
    },
  },
  {
    id: 'cima',
    slugs: ['destacame-architect'],
    title: { es: 'La Cima — Destacame', en: 'The Summit — Destacame' },
    represents: {
      es:
        'Esta sala representa la cima actual: arquitectura frontend y ' +
        'microservicios para fintech, orquestando operaciones en Chile y ' +
        'Mexico.',
      en:
        'This room represents the current summit: frontend architecture ' +
        'and microservices for fintech, orchestrating operations across ' +
        'Chile and Mexico.',
    },
  },
]

interface SeniorityParams {
  scale: number
  lightIntensity: number
  propDensity: number
}

/** El eje seniority en numeros: la sala crece en tamaño, luz y densidad. */
const SENIORITY_PARAMS: Record<SeniorityValue, SeniorityParams> = {
  intern: { scale: 1, lightIntensity: 0.55, propDensity: 0.4 },
  junior: { scale: 1.15, lightIntensity: 0.65, propDensity: 0.55 },
  mid: { scale: 1.3, lightIntensity: 0.75, propDensity: 0.7 },
  senior: { scale: 1.45, lightIntensity: 0.85, propDensity: 0.85 },
  lead: { scale: 1.65, lightIntensity: 1, propDensity: 1 },
}

export interface RoomTexts {
  title: string
  role: string
  period: string
  /** Empresas de la etapa (unidas con ' · ' si son varias). */
  company: string
  /** Pais(es) del cliente/empleador de la etapa. */
  country: string
  retos: string[]
  aprendizajes: string[]
  /** Reseña completa del cuaderno-atril (parrafos para el panel DOM). */
  resena: string[]
  /** Lineas cortas del cuaderno 3D (empresa, lugar, periodo, rol). */
  notebook: string[]
}

export interface RoomDef extends SeniorityParams {
  id: RoomId
  order: number
  slugs: readonly string[]
  seniority: SeniorityValue
  /** Año de inicio de la etapa (mini-timeline del pasillo). */
  year: string
  texts: Record<Locale, RoomTexts>
}

function seniorityRank(value: SeniorityValue): number {
  return SENIORITIES.indexOf(value)
}

function maxSeniority(exps: readonly Experience[]): SeniorityValue {
  return exps.reduce<SeniorityValue>(
    (acc, exp) =>
      seniorityRank(exp.seniority) > seniorityRank(acc) ? exp.seniority : acc,
    'intern',
  )
}

function yearOf(yearMonth: string): string {
  return yearMonth.slice(0, 4)
}

function formatPeriod(exps: readonly Experience[], locale: Locale): string {
  const startYear = exps
    .map((e) => yearOf(e.start))
    .reduce((a, b) => (a < b ? a : b))
  const isOngoing = exps.some((e) => e.end === undefined)
  if (isOngoing) {
    return `${startYear} — ${locale === 'es' ? 'hoy' : 'today'}`
  }
  const endYear = exps
    .map((e) => yearOf(e.end as string))
    .reduce((a, b) => (a > b ? a : b))
  return startYear === endYear ? startYear : `${startYear} — ${endYear}`
}

function buildRetos(exps: readonly Experience[], locale: Locale): string[] {
  return exps.flatMap((exp) => [
    ...(exp.summary ? [exp.summary[locale]] : []),
    ...exp.responsibilities[locale],
  ])
}

function buildAprendizajes(
  exps: readonly Experience[],
  locale: Locale,
): string[] {
  const achievements = exps.flatMap((exp) => exp.achievements[locale])
  // Tecnicas primero, soft al final (a traves de TODAS las exps de la sala).
  const skills = [
    ...new Set([
      ...exps.flatMap((exp) => exp.skillsTechnical),
      ...exps.flatMap((exp) => exp.skillsSoft),
    ]),
  ]
  return skills.length > 0
    ? [...achievements, `Skills: ${skills.join(' · ')}`]
    : achievements
}

function buildTexts(
  spec: RoomSpec,
  exps: readonly Experience[],
  locale: Locale,
): RoomTexts {
  const role = exps[0]?.role[locale] ?? ''
  const period = formatPeriod(exps, locale)
  const company = [...new Set(exps.map((exp) => exp.company))].join(' · ')
  const country = [...new Set(exps.map((exp) => exp.country))].join(' · ')
  const labels =
    locale === 'es'
      ? { company: 'Empresa', role: 'Rol', period: 'Periodo', where: 'Donde' }
      : { company: 'Company', role: 'Role', period: 'Period', where: 'Where' }
  return {
    title: spec.title[locale],
    role,
    period,
    company,
    country,
    retos: buildRetos(exps, locale),
    aprendizajes: buildAprendizajes(exps, locale),
    resena: [
      spec.represents[locale],
      `${labels.company}: ${company}`,
      `${labels.where}: ${country}`,
      `${labels.role}: ${role}`,
      `${labels.period}: ${period}`,
      ...exps.flatMap((exp) => (exp.summary ? [exp.summary[locale]] : [])),
    ],
    notebook: [company, country, period, role],
  }
}

/**
 * @function buildRooms
 * @description Construye las salas del MVP desde las experiences reales.
 *   Falla rapido (build-time) si un slug del spec no existe en el CV.
 *
 * @param {readonly Experience[]} source - experiences (default: las reales)
 * @returns {RoomDef[]} salas en orden narrativo
 * @throws {Error} si un slug del spec no esta en source
 *
 * @example
 *   const rooms = buildRooms()
 *   rooms[0].id            // 'aula'
 *   rooms[2].texts.es.period  // '2022 — hoy'
 */
export function buildRooms(
  source: readonly Experience[] = experiences,
): RoomDef[] {
  return MVP_ROOM_SPECS.map((spec, order) => {
    const exps = spec.slugs.map((slug) => {
      const found = source.find((e) => e.slug === slug)
      if (!found) {
        throw new Error(
          `buildRooms: experience "${slug}" no encontrada en @portfolio/content`,
        )
      }
      return found
    })
    const seniority = maxSeniority(exps)
    return {
      id: spec.id,
      order,
      slugs: spec.slugs,
      seniority,
      year: yearOf(exps.map((e) => e.start).reduce((a, b) => (a < b ? a : b))),
      ...SENIORITY_PARAMS[seniority],
      texts: {
        es: buildTexts(spec, exps, 'es'),
        en: buildTexts(spec, exps, 'en'),
      },
    }
  })
}
