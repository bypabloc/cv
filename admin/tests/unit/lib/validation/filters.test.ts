import { describe, expect, it } from "vitest";
import { dateRangeSchema, paginationSchema } from "@/lib/validation/filters";

/**
 * @module tests/unit/lib/validation/filters
 * @description Verifica los Zod schemas de filtros: dateRange (regex
 *   YYYY-MM-DD) y pagination (coerce + defaults + bounds).
 */

describe("dateRangeSchema", () => {
	it("Given un rango valido When parse Then devuelve from/to", () => {
		// Arrange + Act
		const result = dateRangeSchema.parse({
			from: "2026-01-01",
			to: "2026-12-31",
		});

		// Assert
		expect(result).toEqual({ from: "2026-01-01", to: "2026-12-31" });
	});

	it("Given una fecha invalida When safeParse Then falla", () => {
		// Arrange + Act
		const result = dateRangeSchema.safeParse({
			from: "01/01/2026",
			to: "2026-12-31",
		});

		// Assert
		expect(result.success).toBe(false);
	});
});

describe("paginationSchema", () => {
	it("Given objeto vacio When parse Then aplica defaults", () => {
		// Arrange + Act
		const result = paginationSchema.parse({});

		// Assert
		expect(result).toEqual({ page: 1, page_size: 50 });
	});

	it("Given strings numericas When parse Then coacciona a number", () => {
		// Arrange + Act
		const result = paginationSchema.parse({ page: "3", page_size: "20" });

		// Assert
		expect(result).toEqual({ page: 3, page_size: 20 });
	});

	it("Given page_size > 200 When safeParse Then falla por el max", () => {
		// Arrange + Act
		const result = paginationSchema.safeParse({ page: 1, page_size: 500 });

		// Assert
		expect(result.success).toBe(false);
	});
});
