import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { useMetricsRange } from "@/features/analytics/hooks/use-metrics-range";

/**
 * @module tests/unit/features/analytics/use-metrics-range
 * @description useMetricsRange: estado del rango de fechas. Default = ultimos
 *   30 dias (from/to en YYYY-MM-DD). setRange reemplaza el rango.
 */

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

describe("useMetricsRange", () => {
	it("Given el render inicial When se monta Then el default cubre 30 dias en formato ISO", () => {
		// Arrange + Act
		const { result } = renderHook(() => useMetricsRange());
		const { from, to } = result.current.range;

		// Assert: ambos son YYYY-MM-DD
		expect(from).toMatch(ISO_DATE);
		expect(to).toMatch(ISO_DATE);

		// Assert: la diferencia entre from y to es ~30 dias. El hook calcula from
		// en hora LOCAL (setDate(-30)) y luego corta a fecha UTC; un cambio de DST
		// dentro de la ventana puede desplazar la fecha UTC en 1 dia, por eso se
		// acepta el conjunto exacto {29,30,31} en vez de un valor unico fragil.
		const fromMs = new Date(`${from}T00:00:00Z`).getTime();
		const toMs = new Date(`${to}T00:00:00Z`).getTime();
		const days = (toMs - fromMs) / (1000 * 60 * 60 * 24);
		expect([29, 30, 31]).toContain(days);
	});

	it("Given un rango nuevo When se llama setRange Then el range se reemplaza", () => {
		// Arrange
		const { result } = renderHook(() => useMetricsRange());

		// Act
		act(() => {
			result.current.setRange({ from: "2026-01-01", to: "2026-01-31" });
		});

		// Assert
		expect(result.current.range).toEqual({
			from: "2026-01-01",
			to: "2026-01-31",
		});
	});
});
