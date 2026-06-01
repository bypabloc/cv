import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";
import { useDisableMfa } from "@/features/auth/hooks/use-disable-mfa";
import { ApiError } from "@/lib/api-client";

/**
 * @module tests/unit/features/auth/hooks/use-disable-mfa
 * @description Verifica que un 409 MUST_KEEP_ONE_MFA_METHOD se propague como
 *   ApiError (el handler MSW siempre devuelve 409 para disable).
 */

function wrapper({ children }: { children: ReactNode }) {
	const client = new QueryClient({
		defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
	});
	return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("useDisableMfa", () => {
	it("Given disable que deja total_mfa 0 When mutate Then propaga ApiError 409", async () => {
		// Arrange
		const { result } = renderHook(() => useDisableMfa(), { wrapper });

		// Act
		const error = await act(async () =>
			result.current.mutateAsync({ kind: "totp" }).catch((e: unknown) => e),
		);

		// Assert
		expect(error).toBeInstanceOf(ApiError);
		expect((error as ApiError).status).toBe(409);
	});
});
