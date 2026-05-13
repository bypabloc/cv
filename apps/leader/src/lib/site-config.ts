/**
 * @module site-config (leader)
 * @description Config especifica del sitio leader. Delega a `defineSiteConfig`
 *   del paquete compartido — solo declara los overrides unicos del sitio.
 */
import { defineSiteConfig } from '@portfolio/app-shared'

export const { NICHE, SITE_URL, OG_IMAGE, STRINGS } = defineSiteConfig({
  niche: 'leader',
  siteUrl: import.meta.env.SITE_URL ?? undefined,
  overrides: {
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
  },
})
