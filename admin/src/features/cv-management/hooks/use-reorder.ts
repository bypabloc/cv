"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { cvAdminClient } from "../api/cv-admin-client";
import { cvKeys } from "../api/query-keys";
import type { CvSection, ReorderPayload } from "../types";

/**
 * @function useReorder
 * @description Mutation content.reorder: reescribe las prioridades del niche
 *   con la lista COMPLETA de slugs en el orden nuevo (el backend exige que
 *   `ordered_slugs` coincida con todas las entidades del niche). Invalida el
 *   prefix de la seccion.
 */
export function useReorder(section: CvSection) {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: (payload: ReorderPayload) => cvAdminClient.reorder(payload),
		onSuccess: () => {
			void queryClient.invalidateQueries({
				queryKey: cvKeys.sectionAll(section),
			});
			toast.success("Orden actualizado");
		},
		onError: (error) => {
			toast.error(error.message);
		},
	});
}
