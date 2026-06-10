import { renderHook, waitFor } from "@testing-library/react";
import { makeHookWrapper } from "@tests/utils/hook-wrapper";
import { describe, expect, it } from "vitest";
import { useCvSection } from "@/features/cv-management/hooks/use-cv-section";
import type { CvExperience } from "@/features/cv-management/types";

/**
 * @module tests/unit/features/cv-management/hooks/use-cv-section
 * @description Verifica la query de seccion: datos del GET /cv via MSW,
 *   variante con niche (key distinta + filtro) y publications sin lectura.
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

	it("Given publications (sin lectura publica) When la query resuelve Then lista vacia", async () => {
		// Arrange
		const { wrapper } = makeHookWrapper();

		// Act
		const { result } = renderHook(
			() => useCvSection<unknown[]>("publications"),
			{
				wrapper,
			},
		);

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data).toEqual([]);
	});
});
