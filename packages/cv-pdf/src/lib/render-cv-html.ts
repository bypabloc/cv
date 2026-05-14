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
  /**
   * Si true, inyecta el script `/cv-filters.js` + chips de UI + `data-*`
   * attrs en cada item filtrable. Por default `false` para mantener
   * compatibilidad con consumers que esperan HTML ATS plano.
   *
   * Cuando el CV se sirve en una app cuya `public/` contiene
   * `cv-filters.js`, pasar `enableFilters: true` para activar la capa
   * interactiva.
   */
  enableFilters?: boolean
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
    filterBar: 'Filtros',
    filterClear: 'Limpiar filtros',
    filterEmpty: 'No hay items con estos filtros',
    filterTechLabel: 'Tecnologías',
    filterSeniorityLabel: 'Seniority',
    filterTypeLabel: 'Tipo de proyecto',
    filterConfidentialLabel: 'Ocultar confidenciales',
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
    filterBar: 'Filters',
    filterClear: 'Clear filters',
    filterEmpty: 'No items match these filters',
    filterTechLabel: 'Technologies',
    filterSeniorityLabel: 'Seniority',
    filterTypeLabel: 'Project type',
    filterConfidentialLabel: 'Hide confidential',
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

/** Recopila tecnologias unicas de experiences + projects para chips. */
function collectTechs(
  exps: readonly { skillsTechnical: readonly string[] }[],
  projs: readonly { stack: readonly string[] }[],
): string[] {
  const set = new Set<string>()
  for (const e of exps) {
    for (const s of e.skillsTechnical) {
      set.add(s)
    }
  }
  for (const p of projs) {
    for (const s of p.stack) {
      set.add(s)
    }
  }
  return Array.from(set).sort((a, b) => a.localeCompare(b))
}

/** Recopila seniorities y projectTypes unicos para chips. */
function collectUnique<T extends string>(values: readonly T[]): T[] {
  return Array.from(new Set(values)).sort((a, b) => a.localeCompare(b))
}

/** Subset de LABELS usado por la filter bar. */
type FilterBarLabels = {
  readonly filterBar: string
  readonly filterClear: string
  readonly filterTechLabel: string
  readonly filterSeniorityLabel: string
  readonly filterTypeLabel: string
  readonly filterConfidentialLabel: string
}

/**
 * Renderiza el filter shell (toggle FAB + panel colapsado) cuando
 * `enableFilters` es true. Default `hidden` (cv-filters.js lo revela). Sin
 * JS = invisible (ATS-safe).
 *
 * Mismo contrato de markup que `packages/app-shared/src/components/FilterChips.astro`
 * para que el bundle vanilla los maneje identicos.
 */
function renderFilterBar(
  t: FilterBarLabels,
  techs: string[],
  seniorities: string[],
  projectTypes: string[],
): string {
  const techChips = techs
    .map(
      (tech) =>
        `<button type="button" class="filter-chip" data-filter-chip="tech" data-filter-value="${escapeHtml(tech)}" aria-pressed="false">${escapeHtml(tech)}</button>`,
    )
    .join('')
  const seniorityChips = seniorities
    .map(
      (s) =>
        `<button type="button" class="filter-chip" data-filter-chip="seniority" data-filter-value="${escapeHtml(s)}" aria-pressed="false">${escapeHtml(s)}</button>`,
    )
    .join('')
  const typeChips = projectTypes
    .map(
      (s) =>
        `<button type="button" class="filter-chip" data-filter-chip="projectType" data-filter-value="${escapeHtml(s)}" aria-pressed="false">${escapeHtml(s)}</button>`,
    )
    .join('')
  return `
<aside class="filter-shell" data-filter-bar hidden aria-label="${escapeHtml(t.filterBar)}">
  <button type="button" class="filter-toggle" data-filter-toggle aria-expanded="false" aria-controls="filter-panel">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <line x1="4" y1="6" x2="20" y2="6"></line>
      <line x1="7" y1="12" x2="17" y2="12"></line>
      <line x1="10" y1="18" x2="14" y2="18"></line>
    </svg>
    <span>${escapeHtml(t.filterBar)}</span>
    <span class="filter-toggle__badge" data-filter-count hidden>0</span>
  </button>

  <div class="filter-panel" id="filter-panel" data-filter-panel role="dialog" aria-modal="false" aria-label="${escapeHtml(t.filterBar)}" hidden>
    <header class="filter-panel__header">
      <strong>${escapeHtml(t.filterBar)}</strong>
      <button type="button" class="filter-panel__close" data-filter-toggle aria-label="Close">×</button>
    </header>
    <div class="filter-panel__body">
      <div class="filter-group">
        <span class="filter-group-label">${escapeHtml(t.filterTechLabel)}</span>
        <div class="filter-group__chips">${techChips}</div>
      </div>
      <div class="filter-group">
        <span class="filter-group-label">${escapeHtml(t.filterSeniorityLabel)}</span>
        <div class="filter-group__chips">${seniorityChips}</div>
      </div>
      <div class="filter-group">
        <span class="filter-group-label">${escapeHtml(t.filterTypeLabel)}</span>
        <div class="filter-group__chips">${typeChips}</div>
      </div>
      <div class="filter-group">
        <button type="button" class="filter-chip" data-filter-chip="hideConfidential" data-filter-value="1" aria-pressed="false">${escapeHtml(t.filterConfidentialLabel)}</button>
      </div>
    </div>
    <footer class="filter-panel__footer">
      <button type="button" class="filter-clear" data-filter-clear="all">${escapeHtml(t.filterClear)}</button>
    </footer>
  </div>

  <button type="button" class="filter-backdrop" data-filter-backdrop data-filter-toggle aria-hidden="true" tabindex="-1" hidden></button>
</aside>
`
}

export function renderCvHtml(input: RenderInput): string {
  const { locale, niche = 'generic', enableFilters = false } = input
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
/* Filter shell (toggle FAB + panel) — coincide con FilterChips.astro de app-shared */
.filter-shell { position: fixed; inset: 0; pointer-events: none; z-index: 60; font-size: 10pt; }
.filter-toggle { position: fixed; right: 16px; bottom: 16px; display: inline-flex; align-items: center; gap: 6px; padding: 10px 16px; background: #2046d3; color: #fff; border: 1px solid #2046d3; border-radius: 999px; font-family: inherit; font-size: 0.85rem; font-weight: 600; cursor: pointer; pointer-events: auto; box-shadow: 0 4px 16px rgba(0,0,0,0.12); }
.filter-toggle:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(0,0,0,0.18); }
.filter-toggle__badge { display: inline-flex; align-items: center; justify-content: center; min-width: 1.4em; height: 1.4em; padding: 0 6px; border-radius: 999px; background: #fff; color: #2046d3; font-size: 0.75rem; font-weight: 700; line-height: 1; }
.filter-toggle__badge[hidden] { display: none; }
.filter-shell.is-open .filter-toggle { display: none; }
.filter-backdrop { position: fixed; inset: 0; background: rgba(10,10,10,0.5); border: none; cursor: pointer; pointer-events: auto; padding: 0; z-index: 1; }
.filter-backdrop[hidden] { display: none; }
.filter-shell.is-open .filter-backdrop { display: block; }
.filter-panel { position: fixed; right: 16px; bottom: 16px; width: min(420px, calc(100vw - 32px)); max-height: calc(100vh - 32px); background: #fff; border: 1px solid #ddd; border-radius: 12px; box-shadow: 0 16px 48px rgba(0,0,0,0.25); pointer-events: auto; display: flex; flex-direction: column; overflow: hidden; z-index: 2; }
.filter-panel[hidden] { display: none; }
.filter-shell.is-open .filter-panel { display: flex; }
.filter-panel__header { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; border-bottom: 1px solid #ddd; }
.filter-panel__close { background: transparent; border: none; font-size: 18pt; line-height: 1; color: #555; cursor: pointer; padding: 0 6px; }
.filter-panel__body { padding: 12px 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
.filter-panel__footer { padding: 12px 16px; border-top: 1px solid #ddd; display: flex; justify-content: flex-end; }
.filter-group { display: flex; flex-direction: column; gap: 6px; }
.filter-group-label { font-weight: 600; color: #555; text-transform: uppercase; font-size: 9pt; letter-spacing: 0.04em; }
.filter-group__chips { display: flex; flex-wrap: wrap; gap: 4px; }
.filter-chip { background: #f7f7f5; border: 1px solid #ccc; border-radius: 999px; padding: 3px 10px; font-size: 9pt; color: #333; cursor: pointer; font-family: inherit; }
.filter-chip:hover { border-color: #888; }
.filter-chip.is-active { background: #2046d3; color: #fff; border-color: #2046d3; }
.filter-clear { background: transparent; border: 1px solid #c33; color: #c33; border-radius: 999px; padding: 6px 16px; font-size: 9pt; cursor: pointer; font-family: inherit; }
.filter-empty { color: #888; font-style: italic; padding: 8px 0; }
@media (max-width: 640px) {
  .filter-toggle { right: 12px; bottom: 12px; padding: 8px 12px; font-size: 0.8rem; }
  .filter-panel { right: 0; bottom: 0; left: 0; width: 100%; max-height: 80vh; border-radius: 12px 12px 0 0; }
}
@page { size: A4; margin: 16mm 14mm; }
@media print { body { margin: 0; max-width: none; } .filter-shell { display: none; } }
</style>
</head>
<body>`

  const locationLine = profile.availability
    ? `${escapeHtml(profile.location)} · ${escapeHtml(profile.availability[locale])}`
    : escapeHtml(profile.location)
  const header = `
<h1>${escapeHtml(profile.name)}</h1>
<p class="contact">${escapeHtml(profile.headline[locale])} · ${locationLine}</p>
<p class="contact">
  <a href="mailto:${escapeHtml(profile.contacts.email)}">${escapeHtml(profile.contacts.email)}</a>
  · <a href="${escapeHtml(profile.contacts.linkedin)}">LinkedIn</a>
  · <a href="${escapeHtml(profile.contacts.github)}">GitHub</a>
</p>
<h2>${t.summary}</h2>
<p>${escapeHtml(profile.summary[locale])}</p>
`

  const expsHtml = `<section data-filter-section="experience"><h2>${t.experience}</h2>${exps
    .map((e) => {
      const range = formatRange(e.start, e.end, locale)
      const techCsv = e.skillsTechnical.join(',')
      return `
<article data-filterable data-tech="${escapeHtml(techCsv)}" data-seniority="${escapeHtml(e.seniority)}" data-start="${escapeHtml(e.start)}" data-end="${escapeHtml(e.end ?? '')}" data-company="${escapeHtml(e.company)}">
<h3>${escapeHtml(e.role[locale])} — ${escapeHtml(e.company)}</h3>
<p class="exp-meta">${escapeHtml(range)}</p>
${renderList(e.responsibilities[locale])}
${e.achievements[locale].length > 0 ? renderList(e.achievements[locale]) : ''}
<p>${e.skillsTechnical.map((s) => `<span class="tag">${escapeHtml(s)}</span>`).join('')}</p>
</article>
`
    })
    .join(
      '',
    )}<p class="filter-empty" data-filter-empty hidden>${escapeHtml(t.filterEmpty)}</p></section>`

  const projsHtml =
    projs.length > 0
      ? `<section data-filter-section="project"><h2>${t.projects}</h2>${projs
          .map(
            (p) => `
<article data-filterable data-tech="${escapeHtml(p.stack.join(','))}" data-project-type="${escapeHtml(p.projectType)}" data-confidential="${p.isConfidential ? 'true' : 'false'}">
<h3>${escapeHtml(p.name)}</h3>
<p>${escapeHtml(p.summary[locale])}</p>
<p class="proj-meta">${t.stack}: ${p.stack.map((s) => `<span class="tag">${escapeHtml(s)}</span>`).join('')}</p>
${p.url ? `<p class="proj-meta"><a href="${escapeHtml(p.url)}">${escapeHtml(p.url)}</a></p>` : ''}
${p.repo ? `<p class="proj-meta"><a href="${escapeHtml(p.repo)}">${escapeHtml(p.repo)}</a></p>` : ''}
</article>
`,
          )
          .join(
            '',
          )}<p class="filter-empty" data-filter-empty hidden>${escapeHtml(t.filterEmpty)}</p></section>`
      : ''

  const sksHtml =
    sks.length > 0
      ? `<section data-filter-section="skill"><h2>${t.skills}</h2>${sks
          .map(
            (cat) => `
<article data-filterable data-skill-kind="${escapeHtml(cat.kind)}">
<h3>${escapeHtml(cat.name[locale])}</h3>
<p>${cat.skills.map((s) => `<span class="tag">${escapeHtml(s)}</span>`).join('')}</p>
</article>
`,
          )
          .join(
            '',
          )}<p class="filter-empty" data-filter-empty hidden>${escapeHtml(t.filterEmpty)}</p></section>`
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
      ? `<section data-filter-section="certificate"><h2>${t.certificates}</h2><ul>${certs
          .map(
            (c) =>
              `<li data-filterable data-start="${escapeHtml(c.date.slice(0, 7))}" data-end="${escapeHtml(c.date.slice(0, 7))}"><a href="${escapeHtml(c.url)}">${escapeHtml(c.title)}</a> — ${escapeHtml(c.issuer)} (${escapeHtml(c.date)})</li>`,
          )
          .join(
            '',
          )}</ul><p class="filter-empty" data-filter-empty hidden>${escapeHtml(t.filterEmpty)}</p></section>`
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

  // Filter bar + script tag (solo cuando enableFilters=true).
  const filterBar = enableFilters
    ? renderFilterBar(
        t,
        collectTechs(exps, projs),
        collectUnique(exps.map((e) => e.seniority)),
        collectUnique(projs.map((p) => p.projectType)),
      )
    : ''
  const filterScript = enableFilters
    ? '<script src="/cv-filters.js" defer></script>'
    : ''

  return `${head}${filterScript}${header}${filterBar}${expsHtml}${projsHtml}${sksHtml}${eduHtml}${certsHtml}${pubsHtml}${awdsHtml}${refsHtml}</body></html>`
}
