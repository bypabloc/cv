import { describe, expect, it } from "vitest";
import { adminKeys } from "@/features/users-admin/api/query-keys";

/**
 * @module tests/unit/features/users-admin/query-keys
 * @description Verifica las query keys: prefix de listado (usersAll), key con
 *   params (default {} cuando se omite), key de detalle y de acciones.
 */
describe("adminKeys", () => {
	it('Given usersAll When llamado Then es el prefix ["admin", "users"]', () => {
		// Arrange + Act + Assert
		expect(adminKeys.usersAll()).toEqual(["admin", "users"]);
	});

	it("Given users sin params When llamado Then usa el default {}", () => {
		// Arrange + Act + Assert
		expect(adminKeys.users()).toEqual(["admin", "users", {}]);
	});

	it("Given users con params When llamado Then incluye la paginacion", () => {
		// Arrange + Act + Assert
		expect(adminKeys.users({ page: 2, page_size: 10 })).toEqual([
			"admin",
			"users",
			{ page: 2, page_size: 10 },
		]);
	});

	it('Given user(id) When llamado Then es ["admin", "user", id]', () => {
		// Arrange + Act + Assert
		expect(adminKeys.user("usr_01")).toEqual(["admin", "user", "usr_01"]);
	});

	it('Given actions When llamado Then es ["admin", "actions"]', () => {
		// Arrange + Act + Assert
		expect(adminKeys.actions()).toEqual(["admin", "actions"]);
	});
});
