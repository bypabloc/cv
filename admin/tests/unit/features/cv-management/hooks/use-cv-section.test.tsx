import { renderHook, waitFor } from "@testing-library/react";
import { server } from "@tests/mocks/server";
import { makeHookWrapper } from "@tests/utils/hook-wrapper";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";
import { useCvSection } from "@/features/cv-management/hooks/use-cv-section";
import type {
	CvExperience,
	CvPublication,
} from "@/features/cv-management/types";

/**
 * @module tests/unit/features/cv-management/hooks/use-cv-section
 * @description Verifica la query de seccion: datos del GET /cv via MSW,
 *   variante con niche (key distinta + filtro) y publications, que se lee
 *   del content.get-all admin (POST /cv) con filtro/orden client-side.
 */

describe("useCvSection", () => {
	it("Given la seccion experiences When la query resuelve Then expone las 2 fixtures", async () => {
		// Arrange
		const { wrapper } = makeHookWrapper();

		// Act
		const { result } = renderHook(
			() => useCvSection<CvExperience[]>("experiences"),
			{ wrapper },
		);

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data).toHaveLength(2);
		expect(result.current.data?.[0]?.slug).toBe("destacame-architect");
	});

	it("Given un niche When la query resuelve Then trae solo las entidades del niche", async () => {
		// Arrange
		const { wrapper } = makeHookWrapper();

		// Act
		const { result } = renderHook(
			() => useCvSection<CvExperience[]>("experiences", "vibe"),
			{ wrapper },
		);

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data?.map((exp) => exp.slug)).toEqual([
			"destacame-architect",
		]);
	});

	it("Given publications (sin lectura publica) When la query resuelve Then trae las 2 fixtures del get-all", async () => {
		// Arrange
		const { wrapper } = makeHookWrapper();

		// Act
		const { result } = renderHook(
			() => useCvSection<CvPublication[]>("publications"),
			{
				wrapper,
			},
		);

		// Assert: sin niche llega la lista completa en el orden del get-all.
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data?.map((pub) => pub.slug)).toEqual([
			"post-astro-portfolio",
			"post-lambda-coldstart",
		]);
	});

	it("Given publications con niche When la query resuelve Then filtra y ordena por priority desc", async () => {
		// Arrange
		const { wrapper } = makeHookWrapper();

		// Act: ambas fixtures declaran vibe (priority 5 y 9) -> orden desc.
		const { result } = renderHook(
			() => useCvSection<CvPublication[]>("publications", "vibe"),
			{ wrapper },
		);

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data?.map((pub) => pub.slug)).toEqual([
			"post-lambda-coldstart",
			"post-astro-portfolio",
		]);
	});

	it("Given publications sin niches/priority When se filtra por niche Then excluye sin niches y trata priority ausente como 0", async () => {
		// Arrange: get-all con items degradados (niches/priority opcionales).
		server.use(
			http.post("https://api.test.the-full-stack.com/cv", () =>
				HttpResponse.json({
					is_valid: true,
					code: 0,
					data: {
						profile: {},
						experiences: [],
						projects: [],
						skills: [],
						education: [],
						certificates: [],
						awards: [],
						languages: [],
						endorsements: [],
						publications: [
							{ slug: "pub-sin-niches" },
							{ slug: "pub-sin-priority", niches: ["vibe"] },
							{
								slug: "pub-con-priority",
								niches: ["vibe"],
								priority: { vibe: 7 },
							},
						],
					},
				}),
			),
		);
		const { wrapper } = makeHookWrapper();

		// Act
		const { result } = renderHook(
			() => useCvSection<CvPublication[]>("publications", "vibe"),
			{ wrapper },
		);

		// Assert: sin niches -> fuera; sin priority -> peso 0 (va al final).
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data?.map((pub) => pub.slug)).toEqual([
			"pub-con-priority",
			"pub-sin-priority",
		]);
	});

	it("Given publications con un niche sin items When la query resuelve Then lista vacia", async () => {
		// Arrange
		const { wrapper } = makeHookWrapper();

		// Act: ninguna fixture declara el niche fintech.
		const { result } = renderHook(
			() => useCvSection<CvPublication[]>("publications", "fintech"),
			{ wrapper },
		);

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data).toEqual([]);
	});
});
