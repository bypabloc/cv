import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import { server } from "@tests/mocks/server";
import { HttpResponse, http } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { useUpsertEntity } from "@/features/cv-management/hooks/use-upsert-entity";
import type { CvLanguage } from "@/features/cv-management/types";

/**
 * @module tests/unit/features/cv-management/hooks/use-upsert-entity
 * @description Verifica la mutation de upsert: invalida el prefix de la
 *   seccion + toast de exito; en error muestra el mensaje del backend.
 */

const { toastSuccess, toastError } = vi.hoisted(() => ({
	toastSuccess: vi.fn(),
	toastError: vi.fn(),
}));
vi.mock("sonner", () => ({
	toast: { success: toastSuccess, error: toastError },
}));

const API = "https://api.test.the-full-stack.com";

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

const LANGUAGE: CvLanguage = {
	slug: "lang-1",
	name: { es: "Ingles", en: "English" },
	level: { es: "Avanzado", en: "Advanced" },
	niches: ["generic"],
	priority: {},
};

describe("useUpsertEntity", () => {
	it("Given un upsert exitoso When muta Then invalida el prefix de la seccion y toastea", async () => {
		// Arrange
		const { Wrapper, invalidateSpy } = createWrapper();
		const { result } = renderHook(() => useUpsertEntity("languages"), {
			wrapper: Wrapper,
		});

		// Act
		await act(async () => {
			await result.current.mutateAsync(LANGUAGE);
		});

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(invalidateSpy).toHaveBeenCalledWith({
			queryKey: ["cv-management", "section", "languages"],
		});
		expect(toastSuccess).toHaveBeenCalledWith("Cambios guardados");
	});

	it("Given un backend en error When muta Then toastea el mensaje y NO invalida", async () => {
		// Arrange
		server.use(
			http.post(`${API}/cv-admin`, () =>
				HttpResponse.json(
					{ error: "UNKNOWN_NICHE", code: 4004, message: "Niche desconocido" },
					{ status: 422 },
				),
			),
		);
		const { Wrapper, invalidateSpy } = createWrapper();
		const { result } = renderHook(() => useUpsertEntity("languages"), {
			wrapper: Wrapper,
		});

		// Act
		await act(async () => {
			await result.current.mutateAsync(LANGUAGE).catch(() => undefined);
		});

		// Assert
		await waitFor(() => {
			expect(result.current.isError).toBe(true);
		});
		expect(toastError).toHaveBeenCalledWith("Niche desconocido");
		expect(invalidateSpy).not.toHaveBeenCalled();
	});
});
