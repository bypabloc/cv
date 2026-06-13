import { describe, expect, it } from "vitest";
import { NAV_ITEMS } from "@/features/admin-shell/lib/nav-items";

/**
 * @module tests/unit/features/admin-shell/lib/nav-items
 * @description Verifica los items del sidebar. Configuracion agrupa
 *   Perfil/Seguridad/Sesiones en tabs dentro de /settings, por eso el sidebar
 *   NO tiene items separados para Seguridad ni Mis sesiones.
 */

describe("NAV_ITEMS", () => {
	it("Given los items When se inspeccionan Then incluye /metrics como raiz", () => {
		// Arrange + Act
		const hrefs = NAV_ITEMS.map((item) => item.href);

		// Assert
		expect(hrefs).toContain("/metrics");
	});

	it("Given los items When se cuentan Then hay 4 (metrics, settings, users, cv)", () => {
		// Arrange + Act + Assert
		expect(NAV_ITEMS).toHaveLength(4);
	});

	it("Given los items When se listan Then son metrics, settings, users, cv", () => {
		// Arrange + Act
		const hrefs = NAV_ITEMS.map((item) => item.href);

		// Assert
		expect(hrefs).toEqual(["/metrics", "/settings", "/users", "/cv"]);
	});

	it("Given los items When se inspeccionan Then users y cv son adminOnly", () => {
		// Arrange + Act
		const adminOnly = NAV_ITEMS.filter((item) => item.adminOnly === true).map(
			(item) => item.href,
		);

		// Assert: Gestion CV es adminOnly (AC-13 del plan c-cv-management).
		expect(adminOnly).toEqual(["/users", "/cv"]);
	});

	it("Given los items When se busca Then NO hay item separado de Seguridad ni Sesiones", () => {
		// Arrange + Act
		const hrefs = NAV_ITEMS.map((item) => item.href);

		// Assert: ambos viven como tabs dentro de /settings.
		expect(hrefs).not.toContain("/settings/security");
		expect(hrefs).not.toContain("/settings/sessions");
		expect(hrefs).not.toContain("/sessions");
	});
});
