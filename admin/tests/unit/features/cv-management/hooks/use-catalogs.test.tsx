import { renderHook, waitFor } from "@testing-library/react";
import { makeHookWrapper } from "@tests/utils/hook-wrapper";
import { describe, expect, it } from "vitest";
import { useCatalogs } from "@/features/cv-management/hooks/use-catalogs";

/**
 * @module tests/unit/features/cv-management/hooks/use-catalogs
 * @description Verifica que la query de catalogos desenvuelve el Envelope y
 *   expone niches/skills/techTags para los selects.
 */

describe("useCatalogs", () => {
	it("Given el catalogo del backend When la query resuelve Then expone los 3 vocabularios", async () => {
		// Arrange
		const { wrapper } = makeHookWrapper();

		// Act
		const { result } = renderHook(() => useCatalogs(), { wrapper });

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data).toEqual({
			niches: ["generic", "vibe", "fintech"],
			skills: [
				{ slug: "python", name: "Python" },
				{ slug: "react", name: "React" },
				{ slug: "vue", name: "Vue" },
			],
			techTags: [
				{ slug: "astro", name: "Astro" },
				{ slug: "nextjs", name: "Next.js" },
			],
		});
	});
});
