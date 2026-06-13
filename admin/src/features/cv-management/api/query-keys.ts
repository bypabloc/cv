import type { CvSection } from "../types";

/**
 * @module features/cv-management/api/query-keys
 * @description Query keys del dominio cv-management. Las queries de seccion
 *   incluyen el niche activo; las mutations invalidan por PREFIX
 *   (`sectionAll`) para alcanzar cualquier niche cacheado.
 */
export const cvKeys = {
	all: ["cv-management"] as const,
	/** Prefix de una seccion (sin niche): invalidacion masiva. */
	sectionAll: (section: CvSection) =>
		[...cvKeys.all, "section", section] as const,
	/** Key completa de una seccion + niche activo. */
	section: (section: CvSection, niche?: string) =>
		[...cvKeys.sectionAll(section), { niche: niche ?? null }] as const,
	/**
	 * CV completo de content.get-all (overview). Cuelga de `all` para
	 * heredar la exclusion de persistencia localStorage (query-provider) y
	 * cualquier barrido de invalidaciones por el prefix del dominio.
	 */
	fullCv: () => [...cvKeys.all, "full-cv"] as const,
	catalogs: () => [...cvKeys.all, "catalogs"] as const,
	publishStatus: () => [...cvKeys.all, "publish-status"] as const,
};
