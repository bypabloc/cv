import { render, screen, userEvent, waitFor } from "@tests/utils/render";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MobileSidebar } from "@/features/admin-shell/components/mobile-sidebar";
import { NAV_ITEMS } from "@/features/admin-shell/lib/nav-items";

/**
 * @module tests/unit/features/admin-shell/components/mobile-sidebar
 * @description Verifica el Sheet de navegacion mobile: abre con el trigger,
 *   lista los items visibles (filtrados por rol admin), marca el activo segun
 *   pathname y cierra al click en un item.
 */

vi.mock("next/navigation", () => ({
	usePathname: () => "/settings",
}));

const useVisibleNavItemsMock = vi.fn();
vi.mock("@/features/admin-shell/hooks/use-nav-items", () => ({
	useVisibleNavItems: () => useVisibleNavItemsMock(),
}));

const ADMIN_ITEMS = NAV_ITEMS; // los 4 (incluye Usuarios adminOnly)
const NON_ADMIN_ITEMS = NAV_ITEMS.filter((i) => !i.adminOnly); // 3 (sin Usuarios)

describe("MobileSidebar", () => {
	beforeEach(() => {
		useVisibleNavItemsMock.mockReset();
		useVisibleNavItemsMock.mockReturnValue(ADMIN_ITEMS);
	});

	it("Given un admin When abre el Sheet Then muestra los 6 items", async () => {
		// Arrange
		const user = userEvent.setup();
		render(<MobileSidebar />);

		// Act
		await user.click(screen.getByRole("button", { name: /abrir menu/i }));

		// Assert
		const links = await screen.findAllByRole("link");
		expect(links).toHaveLength(6);
	});

	it("Given un NO-admin When abre el Sheet Then oculta el item Usuarios (5 items)", async () => {
		// Arrange
		useVisibleNavItemsMock.mockReturnValue(NON_ADMIN_ITEMS);
		const user = userEvent.setup();
		render(<MobileSidebar />);

		// Act
		await user.click(screen.getByRole("button", { name: /abrir menu/i }));

		// Assert
		const links = await screen.findAllByRole("link");
		expect(links).toHaveLength(5);
		expect(screen.queryByRole("link", { name: /usuarios/i })).toBe(null);
	});

	it("Given pathname /settings When abierto Then el item Configuracion esta activo", async () => {
		// Arrange
		const user = userEvent.setup();
		render(<MobileSidebar />);

		// Act
		await user.click(screen.getByRole("button", { name: /abrir menu/i }));

		// Assert
		const link = await screen.findByRole("link", { name: /configuracion/i });
		expect(link.className).toContain("bg-accent");
	});

	it("Given pathname /settings When abierto Then el item Mis sesiones NO esta activo", async () => {
		// Arrange
		const user = userEvent.setup();
		render(<MobileSidebar />);

		// Act
		await user.click(screen.getByRole("button", { name: /abrir menu/i }));

		// Assert
		const link = await screen.findByRole("link", { name: /mis sesiones/i });
		expect(link.className).toContain("text-muted-foreground");
	});

	it("Given el Sheet abierto Then muestra el item Metricas", async () => {
		// Arrange
		const user = userEvent.setup();
		render(<MobileSidebar />);

		// Act
		await user.click(screen.getByRole("button", { name: /abrir menu/i }));

		// Assert
		expect(
			await screen.findByRole("link", { name: /metricas/i }),
		).toBeInTheDocument();
	});

	it("Given el Sheet abierto When click en un item Then cierra el Sheet", async () => {
		// Arrange
		const user = userEvent.setup();
		render(<MobileSidebar />);
		await user.click(screen.getByRole("button", { name: /abrir menu/i }));
		const link = await screen.findByRole("link", { name: /configuracion/i });

		// Act
		await user.click(link);

		// Assert: tras click el contenido del Sheet se desmonta (cierra)
		await waitFor(() => {
			expect(screen.queryByRole("link", { name: /configuracion/i })).toBe(null);
		});
	});
});
