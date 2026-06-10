import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import { server } from "@tests/mocks/server";
import { HttpResponse, http } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import {
	usePublish,
	usePublishStatus,
} from "@/features/cv-management/hooks/use-publish";

/**
 * @module tests/unit/features/cv-management/hooks/use-publish
 * @description Verifica publish.status (query) y publish.dispatch
 *   (mutation): respuesta del run, invalidacion del status en exito y
 *   toast.error en fallo de GitHub.
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

describe("usePublishStatus", () => {
	it("Given un run queued When la query resuelve Then expone status/url/ref", async () => {
		// Arrange
		const { Wrapper } = createWrapper();

		// Act
		const { result } = renderHook(() => usePublishStatus(), {
			wrapper: Wrapper,
		});

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data).toEqual({
			status: "queued",
			conclusion: null,
			url: "https://github.com/bypabloc/cv/actions/runs/123",
			created_at: "2026-06-01T10:00:00Z",
			ref: "dev",
		});
	});
});

describe("usePublish", () => {
	it("Given un dispatch exitoso When muta Then devuelve actions_url e invalida publish-status", async () => {
		// Arrange
		const { Wrapper, invalidateSpy } = createWrapper();
		const { result } = renderHook(() => usePublish(), { wrapper: Wrapper });

		// Act
		let actionsUrl = "";
		await act(async () => {
			const envelope = await result.current.mutateAsync(undefined);
			actionsUrl = envelope.data.actions_url;
		});

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(actionsUrl).toBe(
			"https://github.com/bypabloc/cv/actions/workflows/deploy-apps.yml",
		);
		expect(invalidateSpy).toHaveBeenCalledWith({
			queryKey: ["cv-management", "publish-status"],
		});
	});

	it("Given GitHub caido When muta Then toastea el error", async () => {
		// Arrange
		server.use(
			http.post(`${API}/cv-admin`, () =>
				HttpResponse.json(
					{
						error: "GITHUB_API_ERROR",
						code: 5200,
						message: "GitHub rechazo el dispatch",
					},
					{ status: 502 },
				),
			),
		);
		const { Wrapper } = createWrapper();
		const { result } = renderHook(() => usePublish(), { wrapper: Wrapper });

		// Act
		await act(async () => {
			await result.current.mutateAsync(undefined).catch(() => undefined);
		});

		// Assert
		await waitFor(() => {
			expect(result.current.isError).toBe(true);
		});
		expect(toastError).toHaveBeenCalledWith("GitHub rechazo el dispatch");
	});
});
