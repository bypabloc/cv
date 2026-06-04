import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { useMetricsCloudwatchRange } from "@/features/analytics/hooks/use-metrics-cloudwatch-range";
import { resolveRelative } from "@/features/analytics/lib/range-presets";

/**
 * @module tests/unit/features/analytics/use-metrics-cloudwatch-range
 * @description Verifica el estado del rango de /metrics: default 30d (bucket
 *   day) + setRange.
 */

describe("useMetricsCloudwatchRange", () => {
	it("Given el hook When monta Then default es 30d con bucket day", () => {
		// Arrange + Act
		const { result } = renderHook(() => useMetricsCloudwatchRange());

		// Assert
		expect(result.current.range.bucket).toBe("day");
		expect(result.current.range.from).toContain("T");
		expect(result.current.range.to).toContain("T");
	});

	it("Given el hook When setRange Then actualiza el rango", () => {
		// Arrange
		const { result } = renderHook(() => useMetricsCloudwatchRange());
		const next = resolveRelative(1, "hours", new Date("2026-06-03T21:00:00Z"));

		// Act
		act(() => result.current.setRange(next));

		// Assert
		expect(result.current.range.bucket).toBe("minute");
		expect(result.current.range.to).toBe("2026-06-03T21:00:00.000Z");
	});
});
