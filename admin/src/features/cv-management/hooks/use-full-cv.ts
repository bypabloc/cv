"use client";

import { useQuery } from "@tanstack/react-query";
import { cvAdminClient } from "../api/cv-admin-client";
import { cvKeys } from "../api/query-keys";
import type { CvFullAdmin } from "../types";

/**
 * @function useFullCv
 * @description Query del CV completo en shape de edicion (content.get-all,
 *   POST /cv con Bearer admin): UN solo request para el overview en vez de
 *   un fetch por seccion. staleTime 0: el overview SIEMPRE refetchea al
 *   montar (mismo criterio que useCvSection — los conteos deben reflejar la
 *   ultima mutacion; la key cuelga de cvKeys.all, que no se persiste).
 */
export function useFullCv() {
	return useQuery({
		queryKey: cvKeys.fullCv(),
		queryFn: async (): Promise<CvFullAdmin> =>
			(await cvAdminClient.getAll()).data,
		staleTime: 0,
	});
}
