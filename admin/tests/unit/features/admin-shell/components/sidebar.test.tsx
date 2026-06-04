import { render, screen } from "@tests/utils/render";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { Sidebar } from "@/features/admin-shell/components/sidebar";
import { NAV_ITEMS } from "@/features/admin-shell/lib/nav-items";

vi.mock("next/navigation", () => ({
	usePathname: () => "/settings",
}));

const useVisibleNavItemsMock = vi.fn();
vi.mock("@/features/admin-shell/hooks/use-nav-items", () => ({
	useVisibleNavItems: () => useVisibleNavItemsMock(),
}));

const ADMIN_ITEMS = NAV_ITEMS; // los 4 (incluye Usuarios adminOnly)
const NON_ADMIN_ITEMS = NAV_ITEMS.filter((i) => !i.adminOnly); // 3 (sin Usuarios)

describe("Sidebar", () => {
	beforeEach(() => {
		useVisibleNavItemsMock.mockReset();
		useVisibleNavItemsMock.mockReturnValue(ADMIN_ITEMS);
	});

	it("Given pathname /settings When render Then el item Configuracion esta activo", () => {
		// Arrange + Act
		render(<Sidebar />);

		// Assert
		const link = screen.getByRole("link", { name: /configuracion/i });
		expect(link.className).toContain("bg-accent");
	});

	it("Given el sidebar When render Then NO hay un item separado de Mis sesiones", () => {
		// Arrange + Act: Seguridad y Sesiones viven como tabs dentro de /settings.
		render(<Sidebar />);

		// Assert
		expect(screen.queryByRole("link", { name: /mis sesiones/i })).toBe(null);
		expect(screen.queryByRole("link", { name: /^seguridad$/i })).toBe(null);
	});

	it("Given un admin When render Then muestra los 4 items (incluye Usuarios)", () => {
		// Arrange: useVisibleNavItems devuelve los 4 (default del beforeEach)
		// Act
		render(<Sidebar />);

		// Assert
		expect(screen.getAllByRole("link")).toHaveLength(4);
		expect(screen.getByRole("link", { name: /usuarios/i })).toBeInTheDocument();
	});

	it("Given un NO-admin When render Then oculta el item Usuarios (3 items)", () => {
		// Arrange
		useVisibleNavItemsMock.mockReturnValue(NON_ADMIN_ITEMS);

		// Act
		render(<Sidebar />);

		// Assert
		expect(screen.getAllByRole("link")).toHaveLength(3);
		expect(screen.queryByRole("link", { name: /usuarios/i })).toBe(null);
	});

	it("Given el sidebar When render Then muestra el item Metricas", () => {
		// Arrange + Act
		render(<Sidebar />);

		// Assert
		expect(screen.getByRole("link", { name: /metricas/i })).toBeInTheDocument();
	});
});
