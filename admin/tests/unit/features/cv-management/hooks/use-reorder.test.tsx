import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import { server } from "@tests/mocks/server";
import { HttpResponse, http } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { useReorder } from "@/features/cv-management/hooks/use-reorder";

/**
 * @module tests/unit/features/cv-management/hooks/use-reorder
 * @description Verifica la mutation reorder: payload completo
 *   {entity_type, niche, ordered_slugs}, invalidacion del prefix de la
 *   seccion y toast de orden actualizado.
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

describe("useReorder", () => {
	it("Given un reorder exitoso When muta Then responde reordered, invalida y toastea", async () => {
		// Arrange
		const { Wrapper, invalidateSpy } = createWrapper();
		const { result } = renderHook(() => useReorder("experiences"), {
			wrapper: Wrapper,
		});

		// Act
		let reordered = 0;
		await act(async () => {
			const envelope = await result.current.mutateAsync({
				entity_type: "experience",
				niche: "generic",
				ordered_slugs: ["b", "a"],
			});
			reordered = envelope.data.reordered;
		});

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(reordered).toBe(2);
		expect(invalidateSpy).toHaveBeenCalledWith({
			queryKey: ["cv-management", "section", "experiences"],
		});
		expect(toastSuccess).toHaveBeenCalledWith("Orden actualizado");
	});

	it("Given slugs que no matchean el niche When muta Then toastea el error 1101", async () => {
		// Arrange
		server.use(
			http.post("https://api.test.the-full-stack.com/cv-admin", () =>
				HttpResponse.json(
					{
						error: "REORDER_SLUGS_MISMATCH",
						code: 1101,
						message: "ordered_slugs no coincide con las entidades del niche",
					},
					{ status: 422 },
				),
			),
		);
		const { Wrapper, invalidateSpy } = createWrapper();
		const { result } = renderHook(() => useReorder("experiences"), {
			wrapper: Wrapper,
		});

		// Act
		await act(async () => {
			await result.current
				.mutateAsync({
					entity_type: "experience",
					niche: "generic",
					ordered_slugs: ["a"],
				})
				.catch(() => undefined);
		});

		// Assert
		await waitFor(() => {
			expect(result.current.isError).toBe(true);
		});
		expect(toastError).toHaveBeenCalledWith(
			"ordered_slugs no coincide con las entidades del niche",
		);
		expect(invalidateSpy).not.toHaveBeenCalled();
	});
});
