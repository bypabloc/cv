import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { formatDate, relativeTime } from "@/lib/format/date";

/**
 * @module tests/unit/lib/format/date
 * @description Verifica formatDate (ISO string, Date, nulo, invalido) y
 *   relativeTime (todas las divisiones del loop + nulos/invalidos), con un
 *   reloj fijo via fake timers para asserts deterministas.
 */

describe("formatDate", () => {
	it("Given un ISO string When format en Then devuelve fecha legible", () => {
		// Arrange + Act
		const result = formatDate("2026-05-27T10:30:00Z", "en");

		// Assert: el dia/anio son estables aunque la hora dependa de la TZ
		expect(result.includes("2026")).toBe(true);
		expect(result.includes("May")).toBe(true);
	});

	it("Given un Date When format Then acepta el objeto Date", () => {
		// Arrange
		const date = new Date("2026-05-27T10:30:00Z");

		// Act
		const result = formatDate(date, "en");

		// Assert
		expect(result.includes("2026")).toBe(true);
	});

	it("Given null When format Then devuelve guion", () => {
		// Arrange + Act
		const result = formatDate(null);

		// Assert
		expect(result).toBe("-");
	});

	it("Given undefined When format Then devuelve guion", () => {
		// Arrange + Act
		const result = formatDate(undefined);

		// Assert
		expect(result).toBe("-");
	});

	it("Given string vacio When format Then devuelve guion", () => {
		// Arrange + Act
		const result = formatDate("");

		// Assert
		expect(result).toBe("-");
	});

	it("Given string invalido When format Then devuelve guion", () => {
		// Arrange + Act
		const result = formatDate("no-es-fecha");

		// Assert
		expect(result).toBe("-");
	});

	it("Given un Date invalido When format Then devuelve guion", () => {
		// Arrange
		const invalid = new Date("no-es-fecha");

		// Act
		const result = formatDate(invalid, "en");

		// Assert
		expect(result).toBe("-");
	});
});

describe("relativeTime", () => {
	beforeEach(() => {
		// Reloj fijo: 2026-06-01T12:00:00Z
		vi.useFakeTimers();
		vi.setSystemTime(new Date("2026-06-01T12:00:00Z"));
	});

	afterEach(() => {
		vi.useRealTimers();
	});

	it("Given diferencia < 1 min When relativeTime Then expresa segundos", () => {
		// Arrange: 30s cae en la division second
		const date = new Date(Date.now() - 30_000);

		// Act
		const result = relativeTime(date, "en");

		// Assert
		expect(result).toBe("30 seconds ago");
	});

	it("Given 5 min When relativeTime Then expresa minutos", () => {
		// Arrange
		const date = new Date(Date.now() - 5 * 60_000);

		// Act
		const result = relativeTime(date, "en");

		// Assert
		expect(result).toBe("5 minutes ago");
	});

	it("Given 3 h When relativeTime Then expresa horas", () => {
		// Arrange
		const date = new Date(Date.now() - 3 * 3_600_000);

		// Act
		const result = relativeTime(date, "en");

		// Assert
		expect(result).toBe("3 hours ago");
	});

	it("Given 2 d When relativeTime Then expresa dias", () => {
		// Arrange
		const date = new Date(Date.now() - 2 * 86_400_000);

		// Act
		const result = relativeTime(date, "en");

		// Assert
		expect(result).toBe("2 days ago");
	});

	it("Given 2 semanas When relativeTime Then expresa semanas", () => {
		// Arrange
		const date = new Date(Date.now() - 2 * 604_800_000);

		// Act
		const result = relativeTime(date, "en");

		// Assert
		expect(result).toBe("2 weeks ago");
	});

	it("Given 3 meses When relativeTime Then expresa meses", () => {
		// Arrange: ~3 meses (en ms con el divisor month 2629.8M)
		const date = new Date(Date.now() - 3 * 2_629_800_000);

		// Act
		const result = relativeTime(date, "en");

		// Assert
		expect(result).toBe("3 months ago");
	});

	it("Given mas de un ano When relativeTime Then expresa anos", () => {
		// Arrange: 2 anos (divisor year 31.5576e9)
		const date = new Date(Date.now() - 2 * 31_557_600_000);

		// Act
		const result = relativeTime(date, "en");

		// Assert
		expect(result).toBe("2 years ago");
	});

	it("Given un futuro proximo When relativeTime Then expresa adelante", () => {
		// Arrange: en 5 minutos
		const date = new Date(Date.now() + 5 * 60_000);

		// Act
		const result = relativeTime(date, "en");

		// Assert
		expect(result).toBe("in 5 minutes");
	});

	it("Given null When relativeTime Then devuelve guion", () => {
		// Arrange + Act
		const result = relativeTime(null);

		// Assert
		expect(result).toBe("-");
	});

	it("Given string invalido When relativeTime Then devuelve guion", () => {
		// Arrange + Act
		const result = relativeTime("no-es-fecha");

		// Assert
		expect(result).toBe("-");
	});
});
