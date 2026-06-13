import { renderHook, waitFor } from "@testing-library/react";
import { CV_FULL_ADMIN_FIXTURE } from "@tests/mocks/handlers/cv-admin";
import { server } from "@tests/mocks/server";
import { makeHookWrapper } from "@tests/utils/hook-wrapper";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";
import { cvKeys } from "@/features/cv-management/api/query-keys";
import { useFullCv } from "@/features/cv-management/hooks/use-full-cv";

/**
 * @module tests/unit/features/cv-management/hooks/use-full-cv
 * @description Verifica la query del CV completo: fetch del content.get-all
 *   (POST /cv) con el fixture de las 10 claves, cacheada bajo la key
 *   ['cv-management', 'full-cv'] (cuelga del prefix del dominio).
 */

const API = "https://api.test.the-full-stack.com";

describe("useFullCv", () => {
	it("Given el fixture del get-all When la query resuelve Then expone el CV completo", async () => {
		// Arrange
		const { wrapper } = makeHookWrapper();

		// Act
		const { result } = renderHook(() => useFullCv(), { wrapper });

		// Assert: la data ES el fixture completo (las 10 claves).
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data).toEqual(CV_FULL_ADMIN_FIXTURE);
	});

	it("Given la query resuelta When se inspecciona el cache Then vive bajo cvKeys.fullCv", async () => {
		// Arrange
		const { client, wrapper } = makeHookWrapper();

		// Act
		const { result } = renderHook(() => useFullCv(), { wrapper });
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});

		// Assert: key exacta colgada del prefix del dominio cv-management.
		expect(cvKeys.fullCv()).toEqual(["cv-management", "full-cv"]);
		expect(client.getQueryData(cvKeys.fullCv())).toEqual(CV_FULL_ADMIN_FIXTURE);
	});

	it("Given un backend en error When la query falla Then expone isError sin data", async () => {
		// Arrange
		server.use(
			http.post(`${API}/cv`, () =>
				HttpResponse.json(
					{ error: "FORBIDDEN", code: 4030, message: "No autorizado" },
					{ status: 403 },
				),
			),
		);
		const { wrapper } = makeHookWrapper();

		// Act
		const { result } = renderHook(() => useFullCv(), { wrapper });

		// Assert
		await waitFor(() => {
			expect(result.current.isError).toBe(true);
		});
		expect(result.current.data).toBeUndefined();
	});
});
