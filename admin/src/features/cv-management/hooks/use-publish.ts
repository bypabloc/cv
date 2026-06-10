"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { cvAdminClient } from "../api/cv-admin-client";
import { cvKeys } from "../api/query-keys";
import type { PublishStatusResponse } from "../types";

/**
 * @function usePublishStatus
 * @description Estado del ultimo run de deploy-apps.yml para el ref del
 *   stage (publish.status). El refetch tras un dispatch lo dispara la
 *   invalidacion de `usePublish`.
 */
export function usePublishStatus() {
	return useQuery({
		queryKey: cvKeys.publishStatus(),
		queryFn: async (): Promise<PublishStatusResponse> =>
			(await cvAdminClient.publishStatus()).data,
		staleTime: 30_000,
		refetchOnWindowFocus: false,
	});
}

/**
 * @function usePublish
 * @description Mutation publish.dispatch (workflow_dispatch del deploy de
 *   las 6 apps). En exito invalida publish-status; el toast con el link a
 *   GitHub Actions lo renderiza `PublishCard` (necesita JSX).
 */
export function usePublish() {
	const queryClient = useQueryClient();

	return useMutation({
		mutationFn: () => cvAdminClient.publishDispatch(),
		onSuccess: () => {
			void queryClient.invalidateQueries({
				queryKey: cvKeys.publishStatus(),
			});
		},
		onError: (error) => {
			toast.error(error.message);
		},
	});
}
