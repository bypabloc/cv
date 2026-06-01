import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { makeJwt } from "@tests/mocks/jwt";
import { renderHook, waitFor } from "@tests/utils/render";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it } from "vitest";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import { useAccountSessions } from "@/features/sessions-mgmt/hooks/use-account-sessions";
import { useAccountStatus } from "@/features/sessions-mgmt/hooks/use-account-status";
import type { User } from "@/types/models";

/**
 * @module tests/unit/features/sessions-mgmt/use-account-queries
 * @description useAccountStatus y useAccountSessions: desempaquetan el envelope
 *   del Lambda `users` operation `status` y devuelven status / sessions.
 */

const USER: User = {
	id: "usr_01",
	email: "user@test.com",
	status: "active",
	display_name: "Pablo",
	has_password: true,
	mfa_methods: ["totp"],
};

function makeWrapper() {
	const client = new QueryClient({
		defaultOptions: { queries: { retry: false, gcTime: 0 } },
	});
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

describe("useAccountStatus", () => {
	it("Given una cuenta activa When la query resuelve Then devuelve el status desempaquetado", async () => {
		// Arrange + Act
		const { result } = renderHook(() => useAccountStatus(), {
			wrapper: makeWrapper(),
		});

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data).toEqual({
			user_id: "usr_01",
			status: "active",
			current_session_id: "sess_current",
		});
	});
});

describe("useAccountSessions", () => {
	it("Given una cuenta con 2 sesiones When la query resuelve Then devuelve el array de sesiones", async () => {
		// Arrange + Act
		const { result } = renderHook(() => useAccountSessions(), {
			wrapper: makeWrapper(),
		});

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data).toHaveLength(2);
		expect(result.current.data?.[0]?.session_id).toBe("sess_current");
		expect(result.current.data?.[1]?.session_id).toBe("sess_other");
	});
});
