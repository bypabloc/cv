import { describe, expect, it } from "vitest";
import { NAV_ITEMS } from "@/features/admin-shell/lib/nav-items";

/**
 * @module tests/unit/features/admin-shell/lib/nav-items
 * @description Verifica los items del sidebar. Tras el plan b-analytics-api la
 *   raiz del area de metricas (`/metrics`) ES un item del sidebar (la page ya
 *   existe); las sub-secciones de /metrics/* se navegan desde esa page.
 */

describe("NAV_ITEMS", () => {
	it("Given los items When se inspeccionan Then incluye /metrics como raiz", () => {
		// Arrange + Act
		const hrefs = NAV_ITEMS.map((item) => item.href);

		// Assert
		expect(hrefs).toContain("/metrics");
	});

	it("Given los items When se cuentan Then hay 5 (con Metricas)", () => {
		// Arrange + Act + Assert
		expect(NAV_ITEMS).toHaveLength(5);
	});

	it("Given los items When se listan Then son metrics, settings, sessions, users, cv", () => {
		// Arrange + Act
		const hrefs = NAV_ITEMS.map((item) => item.href);

		// Assert
		expect(hrefs).toEqual([
			"/metrics",
			"/settings",
			"/sessions",
			"/users",
			"/cv",
		]);
	});
});
