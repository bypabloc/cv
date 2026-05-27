/**
 * @module snapshot-provider
 * @description Factory que crea un `MCPDataProvider` a partir de un
 *   `CvSnapshot` JSON estatico. Los 6 niches lo invocan en su Pages
 *   Function (`apps/<niche>/functions/mcp.ts`) pasando el snapshot
 *   pre-buildeado por el postbuild.
 *
 *   Razon: el bundle de Workers NO puede importar `@portfolio/content`
 *   porque ese paquete usa `import.meta.glob` (Vite-only). El snapshot
 *   se genera en build-time (con Node) y se inlinea como JSON estatico.
 */
import type { CvSnapshot, MCPDataProvider } from './types'

/**
 * @function createSnapshotProvider
 * @description Devuelve un provider read-only que sirve los datos del
 *   snapshot. No clona ni valida (eso sucede en build-time).
 *
 * @param {CvSnapshot} snapshot - JSON pre-buildeado con perfil, experiencias, proyectos, skills, education.
 * @returns {MCPDataProvider} provider con 5 getters tipados.
 *
 * @example
 *   import snapshot from './_data/cv-snapshot.json'
 *   const data = createSnapshotProvider(snapshot as unknown as CvSnapshot)
 *   await handleRequest(body, data)
 */
export function createSnapshotProvider(snapshot: CvSnapshot): MCPDataProvider {
  return {
    getProfile: () => snapshot.profile,
    getExperiences: () => snapshot.experiences,
    getProjects: () => snapshot.projects,
    getSkills: () => snapshot.skills,
    getEducation: () => snapshot.education,
  }
}
