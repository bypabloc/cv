import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook } from "@testing-library/react";
import { server } from "@tests/mocks/server";
import { HttpResponse, http } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import {
	useChangeEmailInitiate,
	useConfirmEmailChange,
} from "@/features/settings/hooks/use-change-email";
import { useChangePassword } from "@/features/settings/hooks/use-change-password";
import { useDeleteAccount } from "@/features/settings/hooks/use-delete-account";
import { useUpdateProfile } from "@/features/settings/hooks/use-update-profile";
import { useDeleteUser } from "@/features/users-admin/hooks/use-delete-user";
import { useEnableUser } from "@/features/users-admin/hooks/use-enable-user";
import { useForceLogout } from "@/features/users-admin/hooks/use-force-logout";
import type { ApiError } from "@/lib/api-client";

/**
 * @module tests/unit/features/settings/hooks/settings-admin-hooks-error
 * @description Cubre las ramas onError de los hooks de settings (change-email
 *   initiate + confirm, change-password fallback no-401, delete-account
 *   fallback no-409, update-profile) y los onError de los hooks admin
 *   (delete/enable/force-logout) que solo tenian el onSuccess cubierto.
 */

vi.mock("next/navigation", () => ({
	useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

const API = "https://api.test.the-full-stack.com";

function wrapper({ children }: { children: ReactNode }) {
	const client = new QueryClient({
		defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
	});
	return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

function force500(path: "users") {
	server.use(
		http.post(`${API}/${path}`, () =>
			HttpResponse.json(
				{ error: "SERVER_ERROR", code: 5000, message: "Boom" },
				{ status: 500 },
			),
		),
	);
}

describe("useChangeEmailInitiate", () => {
	it("Given un email valido When mutate Then resuelve (onSuccess)", async () => {
		// Arrange
		const { result } = renderHook(() => useChangeEmailInitiate(), { wrapper });

		// Act
		const data = await act(async () =>
			result.current.mutateAsync({ new_email: "nuevo@test.com" }),
		);

		// Assert
		expect(data.data.request_id).toBe("req_01");
	});

	it("Given un 500 When mutate Then propaga ApiError (onError)", async () => {
		// Arrange
		force500("users");
		const { result } = renderHook(() => useChangeEmailInitiate(), { wrapper });

		// Act
		const error = await act(async () =>
			result.current
				.mutateAsync({ new_email: "nuevo@test.com" })
				.catch((e: unknown) => e),
		);

		// Assert
		expect((error as ApiError).status).toBe(500);
	});
});

describe("useConfirmEmailChange", () => {
	it("Given un token valido When mutate Then resuelve (onSuccess invalida)", async () => {
		// Arrange
		const { result } = renderHook(() => useConfirmEmailChange(), { wrapper });

		// Act
		const data = await act(async () =>
			result.current.mutateAsync({ token: "tok_01" }),
		);

		// Assert
		expect(data.data.ok).toBe(true);
	});

	it("Given un 500 When mutate Then propaga ApiError (onError)", async () => {
		// Arrange
		force500("users");
		const { result } = renderHook(() => useConfirmEmailChange(), { wrapper });

		// Act
		const error = await act(async () =>
			result.current.mutateAsync({ token: "tok_01" }).catch((e: unknown) => e),
		);

		// Assert
		expect((error as ApiError).status).toBe(500);
	});
});

describe("useChangePassword onError fallback", () => {
	it("Given un 500 (no 401) When mutate Then propaga ApiError (rama else)", async () => {
		// Arrange
		force500("users");
		const { result } = renderHook(() => useChangePassword(), { wrapper });

		// Act
		const error = await act(async () =>
			result.current
				.mutateAsync({ current_password: "old", new_password: "nueva-larga-1" })
				.catch((e: unknown) => e),
		);

		// Assert
		expect((error as ApiError).status).toBe(500);
	});
});

describe("useDeleteAccount onError fallback", () => {
	it("Given un 500 (no 409) When mutate Then propaga ApiError (rama else)", async () => {
		// Arrange
		force500("users");
		const { result } = renderHook(() => useDeleteAccount(), { wrapper });

		// Act
		const error = await act(async () =>
			result.current.mutateAsync().catch((e: unknown) => e),
		);

		// Assert
		expect((error as ApiError).status).toBe(500);
	});

	it("Given un 409 CANNOT_DELETE_ADMIN When mutate Then propaga ApiError 409", async () => {
		// Arrange
		server.use(
			http.post(`${API}/users`, () =>
				HttpResponse.json(
					{ error: "CANNOT_DELETE_ADMIN_ACCOUNT", code: 4090, message: "No" },
					{ status: 409 },
				),
			),
		);
		const { result } = renderHook(() => useDeleteAccount(), { wrapper });

		// Act
		const error = await act(async () =>
			result.current.mutateAsync().catch((e: unknown) => e),
		);

		// Assert
		expect((error as ApiError).status).toBe(409);
	});
});

describe("useUpdateProfile onError", () => {
	it("Given un 500 When mutate Then propaga ApiError (onError)", async () => {
		// Arrange
		force500("users");
		const { result } = renderHook(() => useUpdateProfile(), { wrapper });

		// Act
		const error = await act(async () =>
			result.current
				.mutateAsync({ display_name: "X" })
				.catch((e: unknown) => e),
		);

		// Assert
		expect((error as ApiError).status).toBe(500);
	});
});

describe("admin mutations onError", () => {
	it("Given un 500 When deleteUser Then propaga ApiError (onError)", async () => {
		// Arrange
		force500("users");
		const { result } = renderHook(() => useDeleteUser(), { wrapper });

		// Act
		const error = await act(async () =>
			result.current
				.mutateAsync({ user_id: "usr_02" })
				.catch((e: unknown) => e),
		);

		// Assert
		expect((error as ApiError).status).toBe(500);
	});

	it("Given un 500 When enableUser Then propaga ApiError (onError)", async () => {
		// Arrange
		force500("users");
		const { result } = renderHook(() => useEnableUser(), { wrapper });

		// Act
		const error = await act(async () =>
			result.current
				.mutateAsync({ user_id: "usr_02" })
				.catch((e: unknown) => e),
		);

		// Assert
		expect((error as ApiError).status).toBe(500);
	});

	it("Given un 500 When forceLogout Then propaga ApiError (onError)", async () => {
		// Arrange
		force500("users");
		const { result } = renderHook(() => useForceLogout(), { wrapper });

		// Act
		const error = await act(async () =>
			result.current
				.mutateAsync({ user_id: "usr_02" })
				.catch((e: unknown) => e),
		);

		// Assert
		expect((error as ApiError).status).toBe(500);
	});
});
