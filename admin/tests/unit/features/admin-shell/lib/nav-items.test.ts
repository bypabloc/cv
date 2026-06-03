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

	it("Given los items When se cuentan Then hay 6 (con Metricas y Seguridad)", () => {
		// Arrange + Act + Assert
		expect(NAV_ITEMS).toHaveLength(6);
	});

	it("Given los items When se listan Then son metrics, settings, security, sessions, users, cv", () => {
		// Arrange + Act
		const hrefs = NAV_ITEMS.map((item) => item.href);

		// Assert
		expect(hrefs).toEqual([
			"/metrics",
			"/settings",
			"/settings/security",
			"/sessions",
			"/users",
			"/cv",
		]);
	});

	it("Given los items When se busca Seguridad Then existe con href /settings/security y label Seguridad", () => {
		// Arrange + Act
		const security = NAV_ITEMS.find(
			(item) => item.href === "/settings/security",
		);

		// Assert
		expect(security?.label).toBe("Seguridad");
	});
});
