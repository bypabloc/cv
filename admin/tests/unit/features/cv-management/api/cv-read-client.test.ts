import { server } from "@tests/mocks/server";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";
import {
	CvReadError,
	fetchCvSection,
} from "@/features/cv-management/api/cv-read-client";
import type { CvExperience } from "@/features/cv-management/types";

/**
 * @module tests/unit/features/cv-management/api/cv-read-client
 * @description Verifica el GET /cv publico: respuesta FLAT por seccion,
 *   filtro por niche via querystring, publications sin red (lista vacia) y
 *   el error CvReadError ante HTTP !ok.
 */

const API = "https://api.test.the-full-stack.com";

describe("fetchCvSection", () => {
	it("Given la seccion experiences When se fetchea Then devuelve las 2 fixtures", async () => {
		// Arrange + Act
		const data = await fetchCvSection<CvExperience[]>("experiences");

		// Assert
		expect(data).toHaveLength(2);
		expect(data[0]?.slug).toBe("destacame-architect");
		expect(data[1]?.slug).toBe("acme-fullstack");
	});

	it("Given un niche When se fetchea experiences Then filtra por niche via querystring", async () => {
		// Arrange + Act
		const data = await fetchCvSection<CvExperience[]>("experiences", {
			niche: "vibe",
		});

		// Assert: solo destacame-architect declara el niche vibe.
		expect(data).toHaveLength(1);
		expect(data[0]?.slug).toBe("destacame-architect");
	});

	it("Given la seccion endorsements When se fetchea Then usa la action legacy references", async () => {
		// Arrange: capturar la action del request real.
		let capturedAction: string | null = null;
		server.use(
			http.get(`${API}/cv`, ({ request }) => {
				capturedAction = new URL(request.url).searchParams.get("action");
				return HttpResponse.json([]);
			}),
		);

		// Act
		const data = await fetchCvSection<unknown[]>("endorsements");

		// Assert
		expect(capturedAction).toBe("references");
		expect(data).toEqual([]);
	});

	it("Given la seccion publications When se fetchea Then resuelve [] sin tocar la red", async () => {
		// Arrange: cualquier GET /cv fallaria el test (handler 500).
		server.use(
			http.get(`${API}/cv`, () =>
				HttpResponse.json({ error: "NO_NETWORK_EXPECTED" }, { status: 500 }),
			),
		);

		// Act
		const data = await fetchCvSection<unknown[]>("publications");

		// Assert
		expect(data).toEqual([]);
	});

	it("Given un backend caido When se fetchea Then lanza CvReadError con el HTTP status", async () => {
		// Arrange
		server.use(
			http.get(`${API}/cv`, () =>
				HttpResponse.json({ error: "BOOM" }, { status: 502 }),
			),
		);

		// Act + Assert
		await expect(fetchCvSection("experiences")).rejects.toThrowError(
			new CvReadError(502, "GET /cv action=experiences fallo con HTTP 502"),
		);
	});
});
