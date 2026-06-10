"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { upsertEntity } from "../api/cv-admin-client";
import { cvKeys } from "../api/query-keys";
import type { CvSection, CvUpsertPayload } from "../types";

/**
 * @function useUpsertEntity
 * @description Mutation de upsert de la seccion: invalida el prefix de la
 *   seccion (todas las variantes de niche) y notifica con toast.
 */
export function useUpsertEntity(section: CvSection) {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: (payload: CvUpsertPayload) => upsertEntity(section, payload),
		onSuccess: () => {
			void queryClient.invalidateQueries({
				queryKey: cvKeys.sectionAll(section),
			});
			toast.success("Cambios guardados");
		},
		onError: (error) => {
			toast.error(error.message);
		},
	});
}
