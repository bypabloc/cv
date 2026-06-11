"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { deleteEntity } from "../api/cv-admin-client";
import { cvKeys } from "../api/query-keys";
import type { CvEntitySectionKind, DeletePayload } from "../types";

/**
 * @function useDeleteEntity
 * @description Mutation de delete-<entidad> por slug: ESPERA la invalidacion
 *   del prefix de la seccion + el get-all del overview (refetch incluido) y
 *   recien ahi notifica — la card eliminada ya no esta en la lista cuando
 *   aparece el toast.
 */
export function useDeleteEntity(section: CvEntitySectionKind) {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: (payload: DeletePayload) => deleteEntity(section, payload),
		onSuccess: async () => {
			await Promise.all([
				queryClient.invalidateQueries({
					queryKey: cvKeys.sectionAll(section),
				}),
				queryClient.invalidateQueries({ queryKey: cvKeys.fullCv() }),
			]);
			toast.success("Entrada eliminada");
		},
		onError: (error) => {
			toast.error(error.message);
		},
	});
}
