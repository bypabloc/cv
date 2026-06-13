"use client";

import { createSyncStoragePersister } from "@tanstack/query-sync-storage-persister";
import { QueryClient } from "@tanstack/react-query";
import { PersistQueryClientProvider } from "@tanstack/react-query-persist-client";
import { compress, decompress } from "lz-string";
import { type ReactNode, useState } from "react";
import { ApiError } from "@/lib/api-client";
import { METRICS_PII_FEATURES } from "@/lib/metrics-query-keys";

/**
 * @component QueryProvider
 * @description Tanstack Query con defaults seguros + persister localStorage
 *   (lz-string). No retry en 401/403/422. No persiste data sensible.
 *
 * @props {ReactNode} children - Arbol de la app
 */
export function QueryProvider({ children }: { children: ReactNode }) {
	const [client] = useState(
		() =>
			new QueryClient({
				defaultOptions: {
					queries: {
						staleTime: 30_000,
						gcTime: 5 * 60_000,
						refetchOnWindowFocus: false,
						retry: (failureCount, error) => {
							if (
								error instanceof ApiError &&
								[401, 403, 422].includes(error.status)
							) {
								return false;
							}
							return failureCount < 1;
						},
					},
					mutations: { retry: 0 },
				},
			}),
	);

	const [persister] = useState(() =>
		createSyncStoragePersister({
			storage: typeof window === "undefined" ? undefined : window.localStorage,
			key: "portfolio-admin-query",
			serialize: (data) => compress(JSON.stringify(data)),
			deserialize: (data) => JSON.parse(decompress(data) || "{}"),
		}),
	);

	return (
		<PersistQueryClientProvider
			client={client}
			persistOptions={{
				persister,
				maxAge: 24 * 60 * 60 * 1000,
				dehydrateOptions: {
					shouldDehydrateQuery: (query) => {
						if (query.state.status !== "success") return false;
						const key = query.queryKey[0];
						// No persistir datos sensibles (usuarios admin, sesiones)
						if (key === "admin") return false;
						// No persistir el contenido del editor CV: rehidratar
						// del localStorage muestra datos viejos tras un reload
						// (los forms capturan defaultValues UNA vez) y el
						// staleTime 0 del editor ya garantiza fetch fresco.
						if (key === "cv-management") return false;
						// Metricas con PII (contacts, sessions de tracking): no
						// persistir. Las agregadas si (UX rapida al recargar).
						if (
							key === "metrics" &&
							METRICS_PII_FEATURES.includes(query.queryKey[1] as string)
						) {
							return false;
						}
						return true;
					},
				},
			}}
		>
			{children}
		</PersistQueryClientProvider>
	);
}
