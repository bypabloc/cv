/**
 * @function renderCvHtml
 * @description Renderiza el CV a HTML standalone (sin frameworks). El mismo
 *   HTML se sirve descargable y opcionalmente se convierte a PDF via Puppeteer.
 *
 *   El layout es ATS-friendly: una columna, headings semanticos H1-H3, fuentes
 *   del sistema (no requiere fonts custom para que copy-paste a Word funcione),
 *   sin tablas anidadas.
 *
 * @example
 *   const html = renderCvHtml({ locale: 'en' })
 *   await fs.writeFile('dist/cv-en.html', html)
 */
import {
  awards,
  certificates,
  education,
  experiences,
  filterByNiche,
  formatRange,
  type Niche,
  profile,
  projects,
  publications,
  references,
  skills,
  sortByPriority,
} from '@portfolio/content'

interface RenderInput {
  locale: 'es' | 'en'
  niche?: Niche
}

const LABELS = {
  es: {
    summary: 'Resumen',
    experience: 'Experiencia',
    projects: 'Proyectos destacados',
    education: 'Educación',
    certificates: 'Certificaciones',
    publications: 'Publicaciones',
    awards: 'Premios',
    skills: 'Habilidades técnicas',
    references: 'Referencias',
    contact: 'Contacto',
    present: 'Presente',
    role: 'Cargo',
    stack: 'Stack',
  },
  en: {
    summary: 'Summary',
    experience: 'Experience',
    projects: 'Featured projects',
    education: 'Education',
    certificates: 'Certifications',
    publications: 'Publications',
    awards: 'Awards',
    skills: 'Technical skills',
    references: 'References',
    contact: 'Contact',
    present: 'Present',
    role: 'Role',
    stack: 'Stack',
  },
} as const

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function renderList(items: string[]): string {
  return `<ul>${items.map((i) => `<li>${escapeHtml(i)}</li>`).join('')}</ul>`
}

export function renderCvHtml(input: RenderInput): string {
  const { locale, niche = 'generic' } = input
  const t = LABELS[locale]

  const exps = sortByPriority(filterByNiche(experiences, niche), niche)
  const projs = sortByPriority(filterByNiche(projects, niche), niche)
  const certs = filterByNiche(certificates, niche)
  const pubs = filterByNiche(publications, niche)
  const awds = filterByNiche(awards, niche)
  const sks = filterByNiche(skills, niche)

  const head = `<!doctype html>
<html lang="${locale}">
<head>
<meta charset="utf-8" />
<title>${escapeHtml(profile.name)} — CV</title>
<style>
:root { font-family: 'Helvetica Neue', Arial, sans-serif; color: #111; }
body { max-width: 760px; margin: 24px auto; padding: 0 24px; line-height: 1.45; font-size: 11pt; }
h1 { font-size: 22pt; margin: 0 0 4px; }
h2 { font-size: 13pt; margin: 24px 0 8px; padding-bottom: 4px; border-bottom: 1px solid #ddd; text-transform: uppercase; letter-spacing: 0.04em; }
h3 { font-size: 11pt; margin: 12px 0 2px; }
p { margin: 0 0 6px; }
ul { margin: 4px 0 8px 18px; padding: 0; }
li { margin-bottom: 2px; }
a { color: #2046d3; text-decoration: none; }
.contact { color: #555; font-size: 10pt; margin-bottom: 12px; }
.exp-meta, .proj-meta { color: #666; font-size: 10pt; margin-bottom: 4px; }
.tag { display: inline-block; padding: 1px 6px; font-size: 9pt; border: 1px solid #ddd; border-radius: 999px; margin-right: 4px; color: #555; }
@page { size: A4; margin: 16mm 14mm; }
@media print { body { margin: 0; max-width: none; } }
</style>
</head>
<body>`

  const header = `
<h1>${escapeHtml(profile.name)}</h1>
<p class="contact">${escapeHtml(profile.headline[locale])} · ${escapeHtml(profile.location)}</p>
<p class="contact">
  <a href="mailto:${escapeHtml(profile.contacts.email)}">${escapeHtml(profile.contacts.email)}</a>
  · <a href="${escapeHtml(profile.contacts.linkedin)}">LinkedIn</a>
  · <a href="${escapeHtml(profile.contacts.github)}">GitHub</a>
  ${profile.contacts.medium ? `· <a href="${escapeHtml(profile.contacts.medium)}">Medium</a>` : ''}
</p>
<h2>${t.summary}</h2>
<p>${escapeHtml(profile.summary[locale])}</p>
`

  const expsHtml = `<h2>${t.experience}</h2>${exps
    .map((e) => {
      const range = formatRange(e.start, e.end, locale)
      return `
<h3>${escapeHtml(e.role[locale])} — ${escapeHtml(e.company)}</h3>
<p class="exp-meta">${escapeHtml(range)}</p>
${renderList(e.responsibilities[locale])}
${e.achievements[locale].length > 0 ? renderList(e.achievements[locale]) : ''}
<p>${e.skillsTechnical.map((s) => `<span class="tag">${escapeHtml(s)}</span>`).join('')}</p>
`
    })
    .join('')}`

  const projsHtml =
    projs.length > 0
      ? `<h2>${t.projects}</h2>${projs
          .map(
            (p) => `
<h3>${escapeHtml(p.name)}</h3>
<p>${escapeHtml(p.summary[locale])}</p>
<p class="proj-meta">${t.stack}: ${p.stack.map((s) => `<span class="tag">${escapeHtml(s)}</span>`).join('')}</p>
${p.url ? `<p class="proj-meta"><a href="${escapeHtml(p.url)}">${escapeHtml(p.url)}</a></p>` : ''}
${p.repo ? `<p class="proj-meta"><a href="${escapeHtml(p.repo)}">${escapeHtml(p.repo)}</a></p>` : ''}
`,
          )
          .join('')}`
      : ''

  const sksHtml =
    sks.length > 0
      ? `<h2>${t.skills}</h2>${sks
          .map(
            (cat) => `
<h3>${escapeHtml(cat.name[locale])}</h3>
<p>${cat.skills.map((s) => `<span class="tag">${escapeHtml(s)}</span>`).join('')}</p>
`,
          )
          .join('')}`
      : ''

  const eduHtml =
    education.length > 0
      ? `<h2>${t.education}</h2>${education
          .map(
            (e) => `
<h3>${escapeHtml(e.institution)}${e.degree ? ` — ${escapeHtml(e.degree[locale])}` : ''}</h3>
<p class="exp-meta">${escapeHtml(e.start)} — ${escapeHtml(e.end)}</p>
<p>${escapeHtml(e.description[locale])}</p>
`,
          )
          .join('')}`
      : ''

  const certsHtml =
    certs.length > 0
      ? `<h2>${t.certificates}</h2><ul>${certs
          .map(
            (c) =>
              `<li><a href="${escapeHtml(c.url)}">${escapeHtml(c.title)}</a> — ${escapeHtml(c.issuer)} (${escapeHtml(c.date)})</li>`,
          )
          .join('')}</ul>`
      : ''

  const pubsHtml =
    pubs.length > 0
      ? `<h2>${t.publications}</h2><ul>${pubs
          .map(
            (p) =>
              `<li><a href="${escapeHtml(p.url)}">${escapeHtml(p.title)}</a> — ${escapeHtml(p.platform)} (${escapeHtml(p.date)})</li>`,
          )
          .join('')}</ul>`
      : ''

  const awdsHtml =
    awds.length > 0
      ? `<h2>${t.awards}</h2><ul>${awds
          .map(
            (a) =>
              `<li><strong>${escapeHtml(a.title[locale])}</strong> — ${escapeHtml(a.issuer)} (${escapeHtml(a.date)})</li>`,
          )
          .join('')}</ul>`
      : ''

  const refsHtml =
    references.length > 0
      ? `<h2>${t.references}</h2><ul>${references
          .map(
            (r) =>
              `<li><strong>${escapeHtml(r.name)}</strong> — ${escapeHtml(r.role)}${r.company ? ` · ${escapeHtml(r.company)}` : ''} · <a href="${escapeHtml(r.linkedin)}">LinkedIn</a></li>`,
          )
          .join('')}</ul>`
      : ''

  return `${head}${header}${expsHtml}${projsHtml}${sksHtml}${eduHtml}${certsHtml}${pubsHtml}${awdsHtml}${refsHtml}</body></html>`
}
