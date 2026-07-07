/**
 * @module rooms
 * @description Mapeo data-driven de las experiences reales de
 *   `@portfolio/content` a las 10 salas del journey 3D (plan
 *   journey-salas-estandar). Deriva los textos: RETOS <- summary +
 *   responsibilities; APRENDIZAJES <- achievements + linea de skills.
 *   Las salas son UNIFORMES en tamaño/luz/densidad. Las salas `aula` y
 *   `futuro` son SINTETICAS (sin slug): sus textos son literales del spec
 *   (el aula deriva de `education`: UPTYAB 2011-2016).
 *
 * @see docs/specs/journey-salas-estandar/README.md
 */
import { type Experience, experiences } from '@portfolio/content'

export type RoomId =
  | 'aula'
  | 'corpoelec'
  | 'ipasme'
  | 'iai'
  | 'asesoria'
  | 'cofasa'
  | 'dibal'
  | 'goodmeal'
  | 'destacame'
  | 'futuro'
export type Locale = 'es' | 'en'

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

export interface RoomSpec {
  id: RoomId
  /** Experiences (por slug) que alimentan la sala; vacio = sala sintetica. */
  slugs: readonly string[]
  title: Record<Locale, string>
  represents: Record<Locale, string>
  /** Sala sintetica (sin slug): año + textos literales (ej. `futuro`). */
  synthetic?: { year: string; texts: Record<Locale, RoomTexts> }
}

/** Reseña de la sala `aula` (universidad como CIMIENTO, sin narrar 2015). */
const AULA_REPRESENTS: Record<Locale, string> = {
  es:
    'Esta sala representa los años de universidad: liderar equipos ' +
    'academicos, montar redes cliente-servidor y sentar la base de la ' +
    'arquitectura de software.',
  en:
    'This room represents the university years: leading academic ' +
    'teams, building client-server networks and laying the foundations ' +
    'of software architecture.',
}

/**
 * Textos literales de la sala `aula` (sintetica, sin slug): derivados de
 * `education` (UPTYAB, Ingenieria Informatica 2011-2016 + el hilo
 * autodidacta desde 2012). Las historias de 2015 (IAI y la tesis de
 * PROSALUD) viven en sus propias salas: aqui solo el cimiento.
 */
const AULA_TEXTS: Record<Locale, RoomTexts> = {
  es: {
    title: 'Aula — Universidad',
    role: 'Estudiante de Ingenieria Informatica',
    period: '2011 — 2016',
    company: 'UPTYAB — Universidad Politecnica Territorial de Yaracuy',
    country: 'Venezuela',
    retos: [
      'Pagarme la carrera trabajando como tecnico mientras estudiaba.',
      'Aprender a programar de verdad: POO, bases de datos, redes y ' +
        'sistemas operativos.',
      'Asumir los primeros liderazgos academicos en laboratorios y ' +
        'proyectos de catedra.',
      'Sostener la disciplina de estudiar, trabajar y aprender por mi ' +
        'cuenta a la vez.',
    ],
    aprendizajes: [
      'La base de la ingenieria de software: analisis, diseño y ' +
        'documentacion.',
      'Redes cliente-servidor montadas y depuradas en el laboratorio.',
      'El habito autodidacta: material online desde 2012, sin parar de ' +
        'aprender.',
      'Liderar equipos academicos y justificar cada decision tecnica.',
    ],
    resena: [
      AULA_REPRESENTS.es,
      'Ingenieria Informatica — Universidad Politecnica Territorial de ' +
        'Yaracuy "Aristides Bastidas" (UPTYAB), 2011 — 2016.',
      'Programacion, bases de datos, redes, sistemas operativos y ' +
        'arquitectura de software: el cimiento de todo lo que sigue en ' +
        'el recorrido.',
    ],
    notebook: ['UPTYAB', 'Venezuela', '2011 — 2016', 'Ingenieria Informatica'],
  },
  en: {
    title: 'Classroom — University',
    role: 'Informatics Engineering student',
    period: '2011 — 2016',
    company: 'UPTYAB — Yaracuy Territorial Polytechnic University',
    country: 'Venezuela',
    retos: [
      'Paying my way through university working as a technician while ' +
        'studying.',
      'Learning to really program: OOP, databases, networks and ' +
        'operating systems.',
      'Taking on the first academic leaderships in labs and course ' +
        'projects.',
      'Sustaining the discipline of studying, working and self-learning ' +
        'at once.',
    ],
    aprendizajes: [
      'The foundations of software engineering: analysis, design and ' +
        'documentation.',
      'Client-server networks built and debugged in the lab.',
      'The self-taught habit: online material since 2012, never ' + 'stopping.',
      'Leading academic teams and justifying every technical decision.',
    ],
    resena: [
      AULA_REPRESENTS.en,
      'Informatics Engineering — Yaracuy Territorial Polytechnic ' +
        'University "Aristides Bastidas" (UPTYAB), 2011 — 2016.',
      'Programming, databases, networks, operating systems and software ' +
        'architecture: the foundation of everything that follows in ' +
        'this journey.',
    ],
    notebook: ['UPTYAB', 'Venezuela', '2011 — 2016', 'Informatics Engineering'],
  },
}

/** Reseña de la sala `futuro` (spec.represents + resena del cuaderno). */
const FUTURO_REPRESENTS: Record<Locale, string> = {
  es:
    'Esta sala representa hacia donde voy: el siguiente escalon tecnico, ' +
    'la IA a escala y la mentoria. El recorrido termina mirando adelante ' +
    '— hablemos.',
  en:
    "This room represents where I'm heading: the next technical step, " +
    "AI at scale, and mentorship. The journey ends looking forward — let's " +
    'talk.',
}

/** Textos literales de la sala `futuro` (vision profesional, sin slug). */
const FUTURO_TEXTS: Record<Locale, RoomTexts> = {
  es: {
    title: 'Futuro — Vision',
    role: 'Rumbo a Staff / Principal Engineer',
    period: 'proximamente',
    company: 'Pablo Contreras',
    country: 'donde el reto valga la pena',
    retos: [
      'Crecer a Staff / Principal Engineer sin dejar de construir.',
      'Llevar la IA (vibe coding, AI workflows) a la escala de un equipo.',
      'Multiplicar impacto via mentoria y liderazgo tecnico.',
      'Lanzar productos propios: IA, indie/SaaS y problemas LATAM.',
      'Abrir nuevos rubros: cada reto nuevo es una sala nueva.',
    ],
    aprendizajes: [
      'Arquitectura de sistemas distribuidos robustos y observables.',
      'Equipos que shippean con estandares y sin acoplamiento.',
      'Adopcion de IA productiva y segura como norma del equipo.',
      'Open source, contenido tecnico publico y comunidad.',
      'Siempre estudiante: datos, seguridad, cloud avanzado.',
    ],
    resena: [FUTURO_REPRESENTS.es],
    notebook: [
      'Pablo Contreras',
      'lo que viene',
      'proximamente',
      'Staff / Principal',
    ],
  },
  en: {
    title: 'Future — Vision',
    role: 'Toward Staff / Principal Engineer',
    period: 'coming soon',
    company: 'Pablo Contreras',
    country: 'wherever the challenge is worth it',
    retos: [
      'Grow into Staff / Principal Engineer while still building.',
      'Bring AI (vibe coding, AI workflows) to team scale.',
      'Multiply impact through mentorship and technical leadership.',
      'Launch products of my own: AI, indie/SaaS and LATAM problems.',
      'Open new sectors: every new challenge is a new room.',
    ],
    aprendizajes: [
      'Architecture of robust, observable distributed systems.',
      'Teams that ship with standards and without coupling.',
      'Productive, safe AI adoption as a team norm.',
      'Open source, public technical content and community.',
      'Always a student: data, security, advanced cloud.',
    ],
    resena: [FUTURO_REPRESENTS.en],
    notebook: [
      'Pablo Contreras',
      "what's next",
      'coming soon',
      'Staff / Principal',
    ],
  },
}

/**
 * Specs de las 10 salas. Agregar una sala = agregar un spec (+ su escena).
 * El orden del array ES el orden narrativo del recorrido (cronologico +
 * futuro; plan journey-salas-estandar, Mapa de salas).
 */
export const ROOM_SPECS: readonly RoomSpec[] = [
  {
    id: 'aula',
    slugs: [],
    title: { es: 'Aula — Universidad', en: 'Classroom — University' },
    represents: AULA_REPRESENTS,
    synthetic: { year: '2011 — 2016', texts: AULA_TEXTS },
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
    id: 'ipasme',
    slugs: ['ipasme'],
    title: { es: 'IPASME — Salud', en: 'IPASME — Healthcare' },
    represents: {
      es:
        'Esta sala representa el salto a los datos sensibles: historias ' +
        'medicas digitales que reemplazaron las carpetas de papel de un ' +
        'servicio de salud.',
      en:
        'This room represents the leap into sensitive data: digital ' +
        'medical records replacing the paper folders of a healthcare ' +
        'service.',
    },
  },
  {
    id: 'iai',
    slugs: ['iai'],
    title: { es: 'IAI — Obras publicas', en: 'IAI — Public works' },
    represents: {
      es:
        'Esta sala representa mi proyecto de grado hecho realidad: el ' +
        'sistema de presupuestos y seguimiento de obras del Instituto ' +
        'Autonomo de Infraestructura del Estado Yaracuy, con un equipo ' +
        'de tres y una PC como servidor central.',
      en:
        'This room represents my thesis project made real: the budgeting ' +
        'and construction-site tracking system of the Yaracuy State ' +
        'Infrastructure Institute, with a team of three and one PC as ' +
        'the central server.',
    },
  },
  {
    id: 'asesoria',
    slugs: ['projects-degrees'],
    title: { es: 'Asesoria — PROSALUD', en: 'Advisory — PROSALUD' },
    represents: {
      es:
        'Esta sala representa mi primer trabajo pagado como consultor: ' +
        'rescatar en una semana una tesis bloqueada, desarrollar yo solo ' +
        'el sistema de PROSALUD y enseñar al equipo a defenderlo.',
      en:
        'This room represents my first paid consulting job: rescuing a ' +
        'stalled thesis in one week, single-handedly building the ' +
        'PROSALUD system and teaching the team to defend it.',
    },
  },
  {
    id: 'cofasa',
    slugs: ['cofasa'],
    title: {
      es: 'Cofasa — Laboratorio farmaceutico',
      en: 'Cofasa — Pharma lab',
    },
    represents: {
      es:
        'Esta sala representa la industria: monitorear la produccion ' +
        'farmaceutica y convertir las paradas de maquina en indicadores ' +
        'accionables.',
      en:
        'This room represents industry: monitoring pharma production and ' +
        'turning machine downtime into actionable indicators.',
    },
  },
  {
    id: 'dibal',
    slugs: ['dibal'],
    title: { es: 'Dibal — SaaS POS', en: 'Dibal — POS SaaS' },
    represents: {
      es:
        'Esta sala representa el liderazgo desde cero: primer ' +
        'desarrollador y tech lead de un SaaS POS multi-restaurante con ' +
        'facturacion electronica en Peru.',
      en:
        'This room represents leadership from scratch: first developer ' +
        'and tech lead of a multi-restaurant POS SaaS with e-invoicing ' +
        'in Peru.',
    },
  },
  {
    id: 'goodmeal',
    slugs: ['goodmeal'],
    title: { es: 'GoodMeal — Food-tech', en: 'GoodMeal — Food tech' },
    represents: {
      es:
        'Esta sala representa el food-tech con proposito: liderar la ' +
        'migracion del frontend a Vue 3 y reforzar el flujo de pagos de ' +
        'una app anti-desperdicio en Chile.',
      en:
        'This room represents purposeful food tech: leading the frontend ' +
        'migration to Vue 3 and hardening the payments flow of an ' +
        'anti-waste app in Chile.',
    },
  },
  {
    id: 'destacame',
    slugs: ['destacame-architect', 'destacame-frontend'],
    title: { es: 'Destacame — Fintech', en: 'Destacame — Fintech' },
    represents: {
      es:
        'Esta sala representa la cima actual: interfaces y arquitectura ' +
        'fintech para Destacame — PagaloAqui con la banca y el producto ' +
        'propio — orquestando operaciones en Chile y Mexico.',
      en:
        'This room represents the current summit: fintech interfaces and ' +
        'architecture for Destacame — PagaloAqui with the banks and the ' +
        'core product — orchestrating operations across Chile and Mexico.',
    },
  },
  {
    id: 'futuro',
    slugs: [],
    title: { es: 'Futuro — Vision', en: 'Future — Vision' },
    represents: FUTURO_REPRESENTS,
    synthetic: { year: '∞', texts: FUTURO_TEXTS },
  },
]

export interface RoomDef {
  id: RoomId
  order: number
  slugs: readonly string[]
  /** Año de inicio de la etapa (mini-timeline del pasillo). */
  year: string
  texts: Record<Locale, RoomTexts>
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
 * @description Construye las 10 salas desde las experiences reales.
 *   Falla rapido (build-time) si un slug del spec no existe en el CV.
 *   Las salas sinteticas (slugs vacios: `aula` y `futuro`) usan sus
 *   textos literales del spec.
 *
 * @param {readonly Experience[]} source - experiences (default: las reales)
 * @returns {RoomDef[]} salas en orden narrativo
 * @throws {Error} si un slug del spec no esta en source, o si una sala
 *   sintetica no trae `synthetic`
 *
 * @example
 *   const rooms = buildRooms()
 *   rooms[0].id            // 'aula'
 *   rooms[9].id            // 'futuro'
 */
export function buildRooms(
  source: readonly Experience[] = experiences,
): RoomDef[] {
  return ROOM_SPECS.map((spec, order) => {
    if (spec.slugs.length === 0) {
      if (!spec.synthetic) {
        throw new Error(
          `buildRooms: sala sintetica "${spec.id}" sin textos literales`,
        )
      }
      return {
        id: spec.id,
        order,
        slugs: spec.slugs,
        year: spec.synthetic.year,
        texts: spec.synthetic.texts,
      }
    }
    const exps = spec.slugs.map((slug) => {
      const found = source.find((e) => e.slug === slug)
      if (!found) {
        throw new Error(
          `buildRooms: experience "${slug}" no encontrada en @portfolio/content`,
        )
      }
      return found
    })
    return {
      id: spec.id,
      order,
      slugs: spec.slugs,
      year: yearOf(exps.map((e) => e.start).reduce((a, b) => (a < b ? a : b))),
      texts: {
        es: buildTexts(spec, exps, 'es'),
        en: buildTexts(spec, exps, 'en'),
      },
    }
  })
}
