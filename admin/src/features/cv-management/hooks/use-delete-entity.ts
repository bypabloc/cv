"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { deleteEntity } from "../api/cv-admin-client";
import { cvKeys } from "../api/query-keys";
import type { CvEntitySectionKind, DeletePayload } from "../types";

/**
 * @function useDeleteEntity
 * @description Mutation de delete-<entidad> por slug: invalida el prefix de
 *   la seccion y notifica con toast.
 */
export function useDeleteEntity(section: CvEntitySectionKind) {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: (payload: DeletePayload) => deleteEntity(section, payload),
		onSuccess: () => {
			void queryClient.invalidateQueries({
				queryKey: cvKeys.sectionAll(section),
			});
			toast.success("Entrada eliminada");
		},
		onError: (error) => {
			toast.error(error.message);
		},
	});
}
