"use client";

import { useQuery } from "@tanstack/react-query";
import { cvAdminClient } from "../api/cv-admin-client";
import { fetchCvSection } from "../api/cv-read-client";
import { cvKeys } from "../api/query-keys";
import { SECTION_CONFIG } from "../lib/sections";
import type { CvPublication, CvSection } from "../types";

/**
 * @function publicationsForNiche
 * @description Filtro + orden client-side de publications (la unica seccion
 *   sin lectura publica: se lee del content.get-all, que llega sin filtrar):
 *   con niche activo deja solo los items del niche ordenados por
 *   `priority[niche]` desc (mismo contrato que el GET publico por seccion).
 */
function publicationsForNiche(
	items: CvPublication[],
	niche?: string,
): CvPublication[] {
	if (!niche) return items;
	return items
		.filter((item) => item.niches?.includes(niche) ?? false)
		.sort((a, b) => (b.priority?.[niche] ?? 0) - (a.priority?.[niche] ?? 0));
}

/**
 * @function useCvSection
 * @description Query de una seccion del CV publico (GET /cv) tipada por el
 *   caller, opcionalmente filtrada/ordenada por niche. La seccion sin
 *   lectura publica (publications) se resuelve del content.get-all admin
 *   (POST /cv) con filtro/orden client-side. staleTime 0: el editor SIEMPRE
 *   refetchea al montar — los forms capturan defaultValues una sola vez,
 *   asi que montar sobre data stale congela valores viejos (estas queries
 *   tampoco se persisten en localStorage).
 */
export function useCvSection<T = unknown>(section: CvSection, niche?: string) {
	return useQuery({
		queryKey: cvKeys.section(section, niche),
		queryFn: async (): Promise<T> => {
			if (SECTION_CONFIG[section].readAction === null) {
				const { data } = await cvAdminClient.getAll();
				return publicationsForNiche(data.publications, niche) as unknown as T;
			}
			return fetchCvSection<T>(section, { niche });
		},
		staleTime: 0,
	});
}
