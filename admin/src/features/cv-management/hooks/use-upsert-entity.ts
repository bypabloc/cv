"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { upsertEntity } from "../api/cv-admin-client";
import { cvKeys } from "../api/query-keys";
import type { CvSection, CvUpsertPayload } from "../types";

/**
 * @function useUpsertEntity
 * @description Mutation de upsert de la seccion: ESPERA la invalidacion del
 *   prefix de la seccion + el get-all del overview (incluye el refetch de
 *   las queries activas) y recien ahi notifica — "Cambios guardados" implica
 *   lista fresca, asi reabrir el dialog hidrata los valores recien guardados.
 */
export function useUpsertEntity(section: CvSection) {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: (payload: CvUpsertPayload) => upsertEntity(section, payload),
		onSuccess: async () => {
			await Promise.all([
				queryClient.invalidateQueries({
					queryKey: cvKeys.sectionAll(section),
				}),
				queryClient.invalidateQueries({ queryKey: cvKeys.fullCv() }),
			]);
			toast.success("Cambios guardados");
		},
		onError: (error) => {
			toast.error(error.message);
		},
	});
}
