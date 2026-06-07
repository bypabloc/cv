import { renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useVisibleNavItems } from "@/features/admin-shell/hooks/use-nav-items";

/**
 * @module tests/unit/features/admin-shell/hooks/use-nav-items
 * @description Filtra los items adminOnly del sidebar segun el rol resuelto por
 *   useIsAdmin: admin -> todos; no-admin -> sin los adminOnly.
 */

const useIsAdminMock = vi.fn();
vi.mock("@/features/admin-shell/hooks/use-is-admin", () => ({
	useIsAdmin: () => useIsAdminMock(),
}));

afterEach(() => {
	useIsAdminMock.mockReset();
});

describe("useVisibleNavItems", () => {
	it("Given un admin When resuelve Then incluye el item adminOnly Usuarios", () => {
		// Arrange
		useIsAdminMock.mockReturnValue({ isAdmin: true, isResolved: true });

		// Act
		const { result } = renderHook(() => useVisibleNavItems());

		// Assert
		const hrefs = result.current.map((i) => i.href);
		expect(hrefs).toEqual(["/metrics", "/settings", "/users", "/cv"]);
	});

	it("Given un NO-admin When resuelve Then excluye los items adminOnly", () => {
		// Arrange
		useIsAdminMock.mockReturnValue({ isAdmin: false, isResolved: true });

		// Act
		const { result } = renderHook(() => useVisibleNavItems());

		// Assert
		const hrefs = result.current.map((i) => i.href);
		expect(hrefs).toEqual(["/metrics", "/settings", "/cv"]);
		expect(hrefs).not.toContain("/users");
	});

	it("Given el rol sin resolver When isAdmin false Then oculta los adminOnly (asume no-admin)", () => {
		// Arrange: aun sondeando -> isAdmin false
		useIsAdminMock.mockReturnValue({ isAdmin: false, isResolved: false });

		// Act
		const { result } = renderHook(() => useVisibleNavItems());

		// Assert
		expect(result.current.map((i) => i.href)).not.toContain("/users");
	});
});
