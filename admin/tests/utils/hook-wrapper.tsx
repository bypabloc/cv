import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";

/**
 * @module tests/utils/hook-wrapper
 * @description Wrapper de renderHook con un QueryClient de test (sin retry,
 *   sin cache). Reutilizado por los tests de hooks de Tanstack Query.
 */
export function makeHookWrapper() {
	const client = new QueryClient({
		defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
	});
	return {
		client,
		wrapper: ({ children }: { children: ReactNode }) => (
			<QueryClientProvider client={client}>{children}</QueryClientProvider>
		),
	};
}
