import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { makeJwt } from "@tests/mocks/jwt";
import { renderHook, waitFor } from "@tests/utils/render";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import { sessionsKeys } from "@/features/sessions-mgmt/api/query-keys";
import { useRevokeSession } from "@/features/sessions-mgmt/hooks/use-revoke-session";
import { ApiError } from "@/lib/api-client";
import type { User } from "@/types/models";

/**
 * @module tests/unit/features/sessions-mgmt/use-revoke-session
 * @description useRevokeSession: revocar otra sesion invalida la lista; revocar
 *   la actual rechaza con 400 CANNOT_REVOKE_CURRENT_SESSION y NO invalida.
 */

const USER: User = {
	id: "usr_01",
	email: "user@test.com",
	status: "active",
	display_name: "Pablo",
	has_password: true,
	mfa_methods: ["totp"],
};

function makeWrapper(client: QueryClient) {
	return function Wrapper({ children }: { children: ReactNode }) {
		return (
			<QueryClientProvider client={client}>{children}</QueryClientProvider>
		);
	};
}

beforeEach(() => {
	useAuthStore.setState({
		accessToken: makeJwt({ sub: "usr_01" }),
		user: USER,
	});
});

describe("useRevokeSession", () => {
	it("Given otra sesion When la revocacion tiene exito Then invalida la lista de sesiones", async () => {
		// Arrange
		const client = new QueryClient({
			defaultOptions: {
				queries: { retry: false, gcTime: 0 },
				mutations: { retry: false },
			},
		});
		const invalidateSpy = vi.spyOn(client, "invalidateQueries");
		const { result } = renderHook(() => useRevokeSession(), {
			wrapper: makeWrapper(client),
		});

		// Act
		result.current.mutate({ session_id: "sess_other" });

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(invalidateSpy).toHaveBeenCalledWith({
			queryKey: sessionsKeys.sessions(),
		});
	});

	it("Given la sesion actual When la revocacion falla (400) Then la mutacion queda en error y no invalida", async () => {
		// Arrange
		const client = new QueryClient({
			defaultOptions: {
				queries: { retry: false, gcTime: 0 },
				mutations: { retry: false },
			},
		});
		const invalidateSpy = vi.spyOn(client, "invalidateQueries");
		const { result } = renderHook(() => useRevokeSession(), {
			wrapper: makeWrapper(client),
		});

		// Act
		result.current.mutate({ session_id: "sess_current" });

		// Assert
		await waitFor(() => {
			expect(result.current.isError).toBe(true);
		});
		expect(result.current.error).toBeInstanceOf(ApiError);
		expect((result.current.error as ApiError).status).toBe(400);
		expect(invalidateSpy).not.toHaveBeenCalled();
	});
});
