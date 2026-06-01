import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import { server } from "@tests/mocks/server";
import { HttpResponse, http } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { useAdminActions } from "@/features/users-admin/hooks/use-admin-actions";
import { useDeleteUser } from "@/features/users-admin/hooks/use-delete-user";
import { useDisableUser } from "@/features/users-admin/hooks/use-disable-user";
import { useEnableUser } from "@/features/users-admin/hooks/use-enable-user";
import { useForceLogout } from "@/features/users-admin/hooks/use-force-logout";
import { useUsersList } from "@/features/users-admin/hooks/use-users-list";

const API = "https://api.test.the-full-stack.com";

/**
 * @module tests/unit/features/users-admin/admin-mutations
 * @description Cubre enable/delete/force-logout (invalidacion en exito) +
 *   list-users + list-admin-actions contra MSW. Cierra la cobertura del
 *   cliente y de los hooks de mutacion restantes.
 */

function createWrapper() {
	const client = new QueryClient({
		defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
	});
	const invalidateSpy = vi.spyOn(client, "invalidateQueries");
	function Wrapper({ children }: { children: ReactNode }) {
		return (
			<QueryClientProvider client={client}>{children}</QueryClientProvider>
		);
	}
	return { Wrapper, invalidateSpy };
}

describe("useEnableUser", () => {
	it("Given un user When enable Then invalida users + user + actions en exito", async () => {
		// Arrange
		const { Wrapper, invalidateSpy } = createWrapper();
		const { result } = renderHook(() => useEnableUser(), { wrapper: Wrapper });

		// Act
		await act(async () => {
			await result.current.mutateAsync({ user_id: "usr_02" });
		});

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(invalidateSpy).toHaveBeenCalledWith({
			queryKey: ["admin", "users"],
		});
		expect(invalidateSpy).toHaveBeenCalledWith({
			queryKey: ["admin", "user", "usr_02"],
		});
		expect(invalidateSpy).toHaveBeenCalledWith({
			queryKey: ["admin", "actions"],
		});
	});
});

describe("useDeleteUser", () => {
	it("Given un user When delete Then invalida las queries admin en exito", async () => {
		// Arrange
		const { Wrapper, invalidateSpy } = createWrapper();
		const { result } = renderHook(() => useDeleteUser(), { wrapper: Wrapper });

		// Act
		await act(async () => {
			await result.current.mutateAsync({ user_id: "usr_02" });
		});

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(invalidateSpy).toHaveBeenCalledWith({
			queryKey: ["admin", "users"],
		});
		expect(invalidateSpy).toHaveBeenCalledWith({
			queryKey: ["admin", "user", "usr_02"],
		});
		expect(invalidateSpy).toHaveBeenCalledWith({
			queryKey: ["admin", "actions"],
		});
	});
});

describe("useForceLogout", () => {
	it("Given un user When force-logout Then invalida las queries admin en exito", async () => {
		// Arrange
		const { Wrapper, invalidateSpy } = createWrapper();
		const { result } = renderHook(() => useForceLogout(), { wrapper: Wrapper });

		// Act
		await act(async () => {
			await result.current.mutateAsync({ user_id: "usr_02" });
		});

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(invalidateSpy).toHaveBeenCalledWith({
			queryKey: ["admin", "users"],
		});
		expect(invalidateSpy).toHaveBeenCalledWith({
			queryKey: ["admin", "user", "usr_02"],
		});
		expect(invalidateSpy).toHaveBeenCalledWith({
			queryKey: ["admin", "actions"],
		});
	});
});

describe("useUsersList", () => {
	it("Given el caller admin When query Then devuelve los 2 usuarios paginados", async () => {
		// Arrange
		const { Wrapper } = createWrapper();
		const { result } = renderHook(() => useUsersList(), { wrapper: Wrapper });

		// Act + Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data?.users).toHaveLength(2);
		expect(result.current.data?.total).toBe(2);
	});
});

describe("useAdminActions", () => {
	it("Given el log de acciones When query Then devuelve el array de acciones", async () => {
		// Arrange
		const { Wrapper } = createWrapper();
		const { result } = renderHook(() => useAdminActions(), {
			wrapper: Wrapper,
		});

		// Act + Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data).toHaveLength(1);
		expect(result.current.data?.[0]?.action).toBe("disable-user");
	});
});

describe("useDisableUser onError", () => {
	it("Given un 500 del backend When disable Then la mutation entra en error", async () => {
		// Arrange
		server.use(
			http.post(`${API}/users`, () =>
				HttpResponse.json(
					{ error: "SERVER_ERROR", code: 6000, message: "Error interno" },
					{ status: 500 },
				),
			),
		);
		const { Wrapper, invalidateSpy } = createWrapper();
		const { result } = renderHook(() => useDisableUser(), { wrapper: Wrapper });

		// Act
		await act(async () => {
			await result.current
				.mutateAsync({ user_id: "usr_02" })
				.catch(() => undefined);
		});

		// Assert
		await waitFor(() => {
			expect(result.current.isError).toBe(true);
		});
		expect(invalidateSpy).not.toHaveBeenCalled();
	});
});
