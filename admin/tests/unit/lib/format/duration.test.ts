import { describe, expect, it } from "vitest";
import { formatDurationMs } from "@/lib/format/duration";

/**
 * @module tests/unit/lib/format/duration
 * @description Verifica formatDurationMs: MM:SS (<1h), HH:MM:SS (>=1h),
 *   nulos/negativos/NaN.
 */

describe("formatDurationMs", () => {
	it("Given ms < 1h When format Then devuelve MM:SS", () => {
		// Arrange + Act
		const result = formatDurationMs(83000);

		// Assert
		expect(result).toBe("01:23");
	});

	it("Given ms >= 1h When format Then devuelve HH:MM:SS", () => {
		// Arrange + Act
		const result = formatDurationMs(3723000);

		// Assert
		expect(result).toBe("01:02:03");
	});

	it("Given 0 ms When format Then devuelve 00:00", () => {
		// Arrange + Act
		const result = formatDurationMs(0);

		// Assert
		expect(result).toBe("00:00");
	});

	it("Given ms negativo When format Then devuelve 00:00", () => {
		// Arrange + Act
		const result = formatDurationMs(-5000);

		// Assert
		expect(result).toBe("00:00");
	});

	it("Given null When format Then devuelve 00:00", () => {
		// Arrange + Act
		const result = formatDurationMs(null);

		// Assert
		expect(result).toBe("00:00");
	});

	it("Given undefined When format Then devuelve 00:00", () => {
		// Arrange + Act
		const result = formatDurationMs(undefined);

		// Assert
		expect(result).toBe("00:00");
	});

	it("Given NaN When format Then devuelve 00:00", () => {
		// Arrange + Act
		const result = formatDurationMs(Number.NaN);

		// Assert
		expect(result).toBe("00:00");
	});
});
