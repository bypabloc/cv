import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { useLocalStorage } from "@/hooks/use-local-storage";

/**
 * @module tests/unit/hooks/use-local-storage
 * @description Verifica useLocalStorage: valor inicial, lectura de un valor
 *   persistido, set que persiste, y JSON corrupto que cae al default.
 */

describe("useLocalStorage", () => {
	it("Given sin valor previo When render Then usa el initialValue", () => {
		// Arrange + Act
		const { result } = renderHook(() => useLocalStorage("k-default", "def"));

		// Assert
		expect(result.current[0]).toBe("def");
	});

	it("Given un valor persistido When render Then lo hidrata de localStorage", () => {
		// Arrange
		localStorage.setItem("k-hydrate", JSON.stringify("persisted"));

		// Act
		const { result } = renderHook(() => useLocalStorage("k-hydrate", "def"));

		// Assert
		expect(result.current[0]).toBe("persisted");
	});

	it("Given un setter When se llama Then actualiza estado y localStorage", () => {
		// Arrange
		const { result } = renderHook(() =>
			useLocalStorage<{ n: number }>("k-set", { n: 0 }),
		);

		// Act
		act(() => {
			result.current[1]({ n: 5 });
		});

		// Assert
		expect(result.current[0]).toEqual({ n: 5 });
		expect(localStorage.getItem("k-set")).toBe(JSON.stringify({ n: 5 }));
	});

	it("Given JSON corrupto When render Then cae al initialValue (catch)", () => {
		// Arrange
		localStorage.setItem("k-corrupt", "{no-es-json");

		// Act
		const { result } = renderHook(() =>
			useLocalStorage("k-corrupt", "fallback"),
		);

		// Assert
		expect(result.current[0]).toBe("fallback");
	});
});
