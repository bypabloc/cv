import { describe, expect, it, vi } from "vitest";
import {
	bucketForSpan,
	combineDateTime,
	formatRangeLabel,
	handleDayPick,
	resolveAbsolute,
	resolveRelative,
	toDateInput,
	toTimeInput,
} from "@/features/analytics/lib/range-presets";

/**
 * @module tests/unit/features/analytics/range-presets
 * @description Verifica la resolucion de presets del selector CloudWatch:
 *   relative (ultimos N) y absolute (from/to), con bucket derivado del span.
 */

describe("bucketForSpan", () => {
	it("Given <=2h When deriva bucket Then minute", () => {
		expect(bucketForSpan(60 * 60_000)).toBe("minute");
	});

	it("Given <=2d When deriva bucket Then hour", () => {
		expect(bucketForSpan(24 * 3_600_000)).toBe("hour");
	});

	it("Given <=60d When deriva bucket Then day", () => {
		expect(bucketForSpan(30 * 86_400_000)).toBe("day");
	});

	it("Given >60d When deriva bucket Then week", () => {
		expect(bucketForSpan(90 * 86_400_000)).toBe("week");
	});
});

describe("resolveRelative", () => {
	it("Given 1h relativo When resuelve Then from=now-1h, to=now, bucket minute", () => {
		// Arrange
		const now = new Date("2026-06-03T21:00:00.000Z");

		// Act
		const range = resolveRelative(1, "hours", now);

		// Assert
		expect(range.to).toBe("2026-06-03T21:00:00.000Z");
		expect(range.from).toBe("2026-06-03T20:00:00.000Z");
		expect(range.bucket).toBe("minute");
	});

	it("Given 30d relativo When resuelve Then bucket day", () => {
		// Arrange
		const now = new Date("2026-06-03T00:00:00.000Z");

		// Act
		const range = resolveRelative(30, "days", now);

		// Assert
		expect(range.from).toBe("2026-05-04T00:00:00.000Z");
		expect(range.bucket).toBe("day");
	});
});

describe("resolveAbsolute", () => {
	it("Given un span de 90min When resuelve Then respeta la hora + bucket minute", () => {
		// Arrange (90 min <= 2h -> bucket minute)
		const from = new Date("2026-06-03T18:00:00.000Z");
		const to = new Date("2026-06-03T19:30:00.000Z");

		// Act
		const range = resolveAbsolute(from, to);

		// Assert
		expect(range.from).toBe("2026-06-03T18:00:00.000Z");
		expect(range.to).toBe("2026-06-03T19:30:00.000Z");
		expect(range.bucket).toBe("minute");
	});

	it("Given un span de 3h When resuelve Then bucket hour (excede minute)", () => {
		// Arrange (3h > 2h -> bucket hour)
		const from = new Date("2026-06-03T18:00:00.000Z");
		const to = new Date("2026-06-03T21:00:00.000Z");

		// Act
		const range = resolveAbsolute(from, to);

		// Assert
		expect(range.bucket).toBe("hour");
	});

	it("Given from>to When resuelve Then los intercambia", () => {
		// Arrange
		const from = new Date("2026-06-03T21:00:00.000Z");
		const to = new Date("2026-06-03T18:00:00.000Z");

		// Act
		const range = resolveAbsolute(from, to);

		// Assert
		expect(range.from).toBe("2026-06-03T18:00:00.000Z");
		expect(range.to).toBe("2026-06-03T21:00:00.000Z");
	});
});

describe("helpers de formato del picker", () => {
	it("Given un Date When toDateInput Then YYYY-MM-DD UTC", () => {
		expect(toDateInput(new Date("2026-06-03T18:30:45.000Z"))).toBe(
			"2026-06-03",
		);
	});

	it("Given un Date When toTimeInput Then hh:mm:ss UTC", () => {
		expect(toTimeInput(new Date("2026-06-03T18:30:45.000Z"))).toBe("18:30:45");
	});

	it("Given date+time When combineDateTime Then Date UTC", () => {
		const d = combineDateTime("2026-06-03", "18:30:00");
		expect(d?.toISOString()).toBe("2026-06-03T18:30:00.000Z");
	});

	it("Given date+time vacio When combineDateTime Then medianoche", () => {
		const d = combineDateTime("2026-06-03", "");
		expect(d?.toISOString()).toBe("2026-06-03T00:00:00.000Z");
	});

	it("Given date vacia When combineDateTime Then null", () => {
		expect(combineDateTime("", "18:00:00")).toBeNull();
	});

	it("Given fecha invalida When combineDateTime Then null", () => {
		expect(combineDateTime("no-es-fecha", "00:00:00")).toBeNull();
	});

	it("Given un rango When formatRangeLabel Then 'desde - hasta'", () => {
		const label = formatRangeLabel({
			from: "2026-06-03T18:00:00.000Z",
			to: "2026-06-03T21:00:00.000Z",
			bucket: "minute",
		});
		expect(label).toContain(" - ");
	});

	it("Given un dia When handleDayPick Then setea YYYY-MM-DD", () => {
		const setDate = vi.fn();
		handleDayPick(new Date("2026-06-15T00:00:00Z"), setDate);
		expect(setDate).toHaveBeenCalledWith("2026-06-15");
	});

	it("Given undefined When handleDayPick Then NO setea (deseleccion)", () => {
		const setDate = vi.fn();
		handleDayPick(undefined, setDate);
		expect(setDate).not.toHaveBeenCalled();
	});
});
