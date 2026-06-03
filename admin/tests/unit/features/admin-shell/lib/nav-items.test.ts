import { describe, expect, it } from "vitest";
import { NAV_ITEMS } from "@/features/admin-shell/lib/nav-items";

/**
 * @module tests/unit/features/admin-shell/lib/nav-items
 * @description Verifica los items del sidebar. Regresion del bug 4: el slot
 *   `metrics` NO se lista hasta que el plan b-analytics-api monte la page
 *   /metrics (un link rompe la navegacion con un 404 del SPA fallback).
 */

describe("NAV_ITEMS", () => {
	it("Given los items When se inspeccionan Then ninguno apunta a /metrics", () => {
		// Arrange + Act
		const hrefs = NAV_ITEMS.map((item) => item.href);

		// Assert
		expect(hrefs).not.toContain("/metrics");
	});

	it("Given los items When se cuentan Then hay 4 (sin Metricas)", () => {
		// Arrange + Act + Assert
		expect(NAV_ITEMS).toHaveLength(4);
	});

	it("Given los items When se listan Then son settings, sessions, users, cv", () => {
		// Arrange + Act
		const hrefs = NAV_ITEMS.map((item) => item.href);

		// Assert
		expect(hrefs).toEqual(["/settings", "/sessions", "/users", "/cv"]);
	});
});
