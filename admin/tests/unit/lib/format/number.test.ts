import { describe, expect, it } from "vitest";
import { formatNumber, formatPercent } from "@/lib/format/number";

/**
 * @module tests/unit/lib/format/number
 * @description Verifica formatNumber y formatPercent: locale, nulos, NaN.
 */

describe("formatNumber", () => {
	it("Given un numero When format con locale es Then usa separador de miles", () => {
		// Arrange + Act
		const result = formatNumber(12345);

		// Assert
		expect(result).toBe("12.345");
	});

	it("Given un numero When format con locale en Then usa coma de miles", () => {
		// Arrange + Act
		const result = formatNumber(12345, "en");

		// Assert
		expect(result).toBe("12,345");
	});

	it("Given null When format Then devuelve 0", () => {
		// Arrange + Act
		const result = formatNumber(null);

		// Assert
		expect(result).toBe("0");
	});

	it("Given undefined When format Then devuelve 0", () => {
		// Arrange + Act
		const result = formatNumber(undefined);

		// Assert
		expect(result).toBe("0");
	});

	it("Given NaN When format Then devuelve 0", () => {
		// Arrange + Act
		const result = formatNumber(Number.NaN);

		// Assert
		expect(result).toBe("0");
	});
});

describe("formatPercent", () => {
	it("Given una fraccion When format con 0 decimales Then redondea a entero", () => {
		// Arrange + Act
		const result = formatPercent(0.42, 0, "en");

		// Assert
		expect(result).toBe("42%");
	});

	it("Given una fraccion When format con 1 decimal Then muestra el decimal", () => {
		// Arrange + Act
		const result = formatPercent(0.4235, 1, "en");

		// Assert
		expect(result).toBe("42.4%");
	});

	it("Given null When format Then devuelve 0%", () => {
		// Arrange + Act
		const result = formatPercent(null);

		// Assert
		expect(result).toBe("0%");
	});

	it("Given undefined When format Then devuelve 0%", () => {
		// Arrange + Act
		const result = formatPercent(undefined);

		// Assert
		expect(result).toBe("0%");
	});

	it("Given NaN When format Then devuelve 0%", () => {
		// Arrange + Act
		const result = formatPercent(Number.NaN);

		// Assert
		expect(result).toBe("0%");
	});
});
