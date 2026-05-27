/**
 * @script build-snapshot
 * @description Genera un `cv-snapshot.json` listo para ser inlineado en
 *   la Pages Function `apps/<niche>/functions/mcp.ts`. Lee los caches
 *   JSON del CV (`packages/content/src/data-cache/*.json`) y los mapea
 *   a la shape minima `CvSnapshot` que esperan los 3 tools del MCP
 *   server.
 *
 *   Razon: el bundle del Worker NO puede importar `@portfolio/content`
 *   en runtime (usa `import.meta.glob` de Vite). El snapshot se inyecta
 *   como JSON estatico via `import` directo en `mcp.ts`.
 *
 *   Uso: invocado desde `apps/<niche>/scripts/postbuild-functions.mjs`.
 *
 * @example
 *   node packages/mcp/scripts/build-snapshot.mjs apps/generic/functions/_data/cv-snapshot.json
 */
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const REPO_ROOT = resolve(__dirname, '../../..')
const CACHE_DIR = resolve(REPO_ROOT, 'packages/content/src/data-cache')

async function readJson(name) {
  const txt = await readFile(resolve(CACHE_DIR, name), 'utf8')
  return JSON.parse(txt)
}

function pickProfile(p) {
  return {
    summary: { en: p.summary.en },
    location: p.location,
    availability: p.availability ? { en: p.availability.en } : undefined,
    contacts: {
      email: p.contacts.email,
      linkedin: p.contacts.linkedin,
      github: p.contacts.github,
      website: p.contacts.website,
    },
  }
}

function pickExperience(e) {
  return {
    slug: e.slug,
    role: { en: e.role.en },
    company: e.company,
    start: e.start,
    end: e.end ?? null,
    summary: e.summary ? { en: e.summary.en } : undefined,
    achievements: { en: e.achievements?.en ?? [] },
    skillsTechnical: e.skillsTechnical ?? [],
  }
}

function pickProject(p) {
  return {
    slug: p.slug,
    name: p.name,
    summary: { en: p.summary.en },
    stack: p.stack ?? [],
    url: p.url ?? null,
  }
}

function pickSkill(s) {
  return {
    name: { en: s.name.en },
    skills: s.skills ?? [],
  }
}

function pickEducation(ed) {
  return {
    institution: ed.institution,
    degree: ed.degree ? { en: ed.degree.en } : undefined,
    start: ed.start ?? null,
    end: ed.end ?? null,
  }
}

export async function buildSnapshot() {
  const [profile, experiences, projects, skills, education] = await Promise.all(
    [
      readJson('profile.json'),
      readJson('experiences.json'),
      readJson('projects.json'),
      readJson('skills.json'),
      readJson('education.json'),
    ],
  )
  return {
    profile: pickProfile(profile),
    experiences: experiences.map(pickExperience),
    projects: projects.map(pickProject),
    skills: skills.map(pickSkill),
    education: education.map(pickEducation),
  }
}

export async function writeSnapshot(outFile) {
  const snapshot = await buildSnapshot()
  await mkdir(dirname(outFile), { recursive: true })
  await writeFile(outFile, JSON.stringify(snapshot, null, 2), 'utf8')
  return snapshot
}

// CLI entry point
if (import.meta.url === `file://${process.argv[1]}`) {
  const outFile = process.argv[2]
  if (!outFile) {
    console.error('Usage: build-snapshot.mjs <output-file>')
    process.exit(1)
  }
  writeSnapshot(resolve(process.cwd(), outFile))
    .then((s) => {
      console.info(
        `[build-snapshot] ${outFile} (profile + ${s.experiences.length} experiences + ${s.projects.length} projects + ${s.skills.length} skills + ${s.education.length} education)`,
      )
    })
    .catch((e) => {
      console.error('[build-snapshot] FAILED:', e.message)
      process.exit(2)
    })
}
