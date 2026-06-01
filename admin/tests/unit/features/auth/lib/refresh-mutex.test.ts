import { describe, expect, it, vi } from "vitest";
import { withRefreshMutex } from "@/features/auth/lib/refresh-mutex";

/**
 * @module tests/unit/features/auth/lib/refresh-mutex
 * @description Verifica que el mutex garantice un solo refresh in-flight.
 */
describe("withRefreshMutex", () => {
	it("Given una sola llamada When se ejecuta Then corre refreshFn una vez", async () => {
		// Arrange
		const refreshFn = vi.fn().mockResolvedValue(true);

		// Act
		const result = await withRefreshMutex(refreshFn);

		// Assert
		expect(refreshFn).toHaveBeenCalledTimes(1);
		expect(result).toBe(true);
	});

	it("Given 5 llamadas concurrentes When se procesan Then corre refreshFn una sola vez", async () => {
		// Arrange
		let calls = 0;
		const refreshFn = vi.fn(async () => {
			calls += 1;
			await new Promise((resolve) => setTimeout(resolve, 20));
			return true;
		});

		// Act
		const results = await Promise.all([
			withRefreshMutex(refreshFn),
			withRefreshMutex(refreshFn),
			withRefreshMutex(refreshFn),
			withRefreshMutex(refreshFn),
			withRefreshMutex(refreshFn),
		]);

		// Assert
		expect(calls).toBe(1);
		expect(results).toEqual([true, true, true, true, true]);
	});

	it("Given el refresh termino When se llama de nuevo Then ejecuta refreshFn otra vez", async () => {
		// Arrange
		const refreshFn = vi.fn().mockResolvedValue(true);

		// Act
		await withRefreshMutex(refreshFn);
		await withRefreshMutex(refreshFn);

		// Assert
		expect(refreshFn).toHaveBeenCalledTimes(2);
	});

	it("Given refreshFn lanza When se llama de nuevo Then el mutex se limpio", async () => {
		// Arrange
		const failing = vi.fn().mockRejectedValue(new Error("boom"));
		const ok = vi.fn().mockResolvedValue(true);

		// Act
		await expect(withRefreshMutex(failing)).rejects.toThrow("boom");
		const result = await withRefreshMutex(ok);

		// Assert
		expect(ok).toHaveBeenCalledTimes(1);
		expect(result).toBe(true);
	});
});
