import { renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { useMounted } from "@/hooks/use-mounted";

/**
 * @module tests/unit/hooks/use-mounted
 * @description Verifica que useMounted es true tras el primer mount en cliente.
 */

describe("useMounted", () => {
	it("Given el hook montado When render Then devuelve true tras el effect", () => {
		// Arrange + Act
		const { result } = renderHook(() => useMounted());

		// Assert: en RTL el effect ya corrio al terminar render
		expect(result.current).toBe(true);
	});
});
