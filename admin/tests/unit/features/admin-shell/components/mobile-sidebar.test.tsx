import { render, screen, userEvent, waitFor } from "@tests/utils/render";
import { describe, expect, it, vi } from "vitest";
import { MobileSidebar } from "@/features/admin-shell/components/mobile-sidebar";

/**
 * @module tests/unit/features/admin-shell/components/mobile-sidebar
 * @description Verifica el Sheet de navegacion mobile: abre con el trigger,
 *   lista los 5 items, marca el activo segun pathname y cierra al click en un
 *   item.
 */

vi.mock("next/navigation", () => ({
	usePathname: () => "/settings",
}));

describe("MobileSidebar", () => {
	it("Given el trigger When click Then abre el Sheet y muestra los 5 items", async () => {
		// Arrange
		const user = userEvent.setup();
		render(<MobileSidebar />);

		// Act
		await user.click(screen.getByRole("button", { name: /abrir menu/i }));

		// Assert
		const links = await screen.findAllByRole("link");
		expect(links).toHaveLength(5);
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

	it("Given pathname /settings When abierto Then el item Metricas NO esta activo", async () => {
		// Arrange
		const user = userEvent.setup();
		render(<MobileSidebar />);

		// Act
		await user.click(screen.getByRole("button", { name: /abrir menu/i }));

		// Assert
		const link = await screen.findByRole("link", { name: /metricas/i });
		expect(link.className).toContain("text-muted-foreground");
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
