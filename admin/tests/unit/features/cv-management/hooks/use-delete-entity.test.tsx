import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import { server } from "@tests/mocks/server";
import { HttpResponse, http } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { useDeleteEntity } from "@/features/cv-management/hooks/use-delete-entity";

/**
 * @module tests/unit/features/cv-management/hooks/use-delete-entity
 * @description Verifica la mutation de delete: invalida el prefix de la
 *   seccion y toastea la eliminacion.
 */

const { toastSuccess, toastError } = vi.hoisted(() => ({
	toastSuccess: vi.fn(),
	toastError: vi.fn(),
}));
vi.mock("sonner", () => ({
	toast: { success: toastSuccess, error: toastError },
}));

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

describe("useDeleteEntity", () => {
	it("Given un delete exitoso When muta Then invalida la seccion y toastea Entrada eliminada", async () => {
		// Arrange
		const { Wrapper, invalidateSpy } = createWrapper();
		const { result } = renderHook(() => useDeleteEntity("certificates"), {
			wrapper: Wrapper,
		});

		// Act
		await act(async () => {
			await result.current.mutateAsync({ slug: "cert-1" });
		});

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(invalidateSpy).toHaveBeenCalledWith({
			queryKey: ["cv-management", "section", "certificates"],
		});
		expect(toastSuccess).toHaveBeenCalledWith("Entrada eliminada");
	});

	it("Given un slug inexistente When muta Then toastea el error del backend", async () => {
		// Arrange
		server.use(
			http.post("https://api.test.the-full-stack.com/cv-admin", () =>
				HttpResponse.json(
					{ error: "NOT_FOUND", code: 4040, message: "Slug inexistente" },
					{ status: 404 },
				),
			),
		);
		const { Wrapper, invalidateSpy } = createWrapper();
		const { result } = renderHook(() => useDeleteEntity("certificates"), {
			wrapper: Wrapper,
		});

		// Act
		await act(async () => {
			await result.current
				.mutateAsync({ slug: "no-existe" })
				.catch(() => undefined);
		});

		// Assert
		await waitFor(() => {
			expect(result.current.isError).toBe(true);
		});
		expect(toastError).toHaveBeenCalledWith("Slug inexistente");
		expect(invalidateSpy).not.toHaveBeenCalled();
	});
});
