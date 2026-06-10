"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchCvSection } from "../api/cv-read-client";
import { cvKeys } from "../api/query-keys";
import type { CvSection } from "../types";

/**
 * @function useCvSection
 * @description Query de una seccion del CV publico (GET /cv) tipada por el
 *   caller, opcionalmente filtrada/ordenada por niche. staleTime 0: el
 *   editor SIEMPRE refetchea al montar — los forms capturan defaultValues
 *   una sola vez, asi que montar sobre data stale congela valores viejos
 *   (estas queries tampoco se persisten en localStorage).
 */
export function useCvSection<T = unknown>(section: CvSection, niche?: string) {
	return useQuery({
		queryKey: cvKeys.section(section, niche),
		queryFn: () => fetchCvSection<T>(section, { niche }),
		staleTime: 0,
	});
}
