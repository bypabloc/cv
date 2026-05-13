/**
 * @module site-config (leader)
 */
import { buildStrings } from '@portfolio/app-shared'
import type { Niche } from '@portfolio/content'

export const NICHE: Niche = 'leader'
export const SITE_URL =
  import.meta.env.SITE_URL ?? 'https://leader.the-full-stack.com'
export const OG_IMAGE = `${SITE_URL}/og-image.svg`

export const STRINGS = buildStrings({
  metaTitleEs: 'Pablo Contreras — Tech Lead / Engineering Manager',
  metaTitleEn: 'Pablo Contreras — Tech Lead / Engineering Manager',
  metaDescriptionEs:
    'Tech Lead con experiencia liderando equipos multidisciplinarios, mentoring y entrega de producto fintech a escala. Premio Innovador del Año en Destacame.',
  metaDescriptionEn:
    'Tech Lead experienced in leading cross-functional engineering teams, mentoring and shipping fintech products at scale. Innovator of the Year award at Destacame.',
  heroEyebrowEs: 'Pablo Contreras · Tech Lead · Lima, Perú',
  heroEyebrowEn: 'Pablo Contreras · Tech Lead · Lima, Peru',
  heroHeadlineEs: 'Tech Lead & Engineering Manager',
  heroHeadlineEn: 'Tech Lead & Engineering Manager',
  heroSummaryEs:
    'Lidero equipos de ingenieria desde mi primer rol en Dibal (primer dev contratado) hasta plataforma fintech en Destacame. Innovador del Año 2023 por automatizar operaciones internas con impacto medible. Mentoreo + delivery + resiliencia organizacional.',
  heroSummaryEn:
    'I lead engineering teams from my first role at Dibal (first hire) to fintech platform at Destacame. Innovator of the Year 2023 for automating internal operations with measurable impact. Mentoring + delivery + organizational resilience.',
  nicheLabelEs: 'Tech Lead',
  nicheLabelEn: 'Tech Lead',
  experienceSubtitleEs:
    'Roles de liderazgo destacados: Tech Lead en Destacame, primer dev y líder en Dibal.',
  experienceSubtitleEn:
    'Leadership roles first: Tech Lead at Destacame, first developer and lead at Dibal.',
  projectsSubtitleEs:
    'Proyectos donde lideré equipo (Dibal, Destacame) y reconocimientos.',
  projectsSubtitleEn:
    'Projects where I led the team (Dibal, Destacame) and awards.',
  atsKeywords: [
    'Tech Lead',
    'Engineering Manager',
    'Staff Engineer',
    'Team Lead',
    'Mentoring',
    'Hiring',
    'Cross-functional teams',
    'Scrum',
    'Metodologías Ágiles',
    'Innovador del Año 2023',
    'Triple Alianza 2020',
    'Strategic Planning',
    'Stakeholder Management',
  ],
})
