import { render, screen } from "@tests/utils/render";
import { describe, expect, it, vi } from "vitest";
import { Sidebar } from "@/features/admin-shell/components/sidebar";

vi.mock("next/navigation", () => ({
	usePathname: () => "/settings",
}));

describe("Sidebar", () => {
	it("Given pathname /settings When render Then el item Configuracion esta activo", () => {
		// Arrange + Act
		render(<Sidebar />);

		// Assert
		const link = screen.getByRole("link", { name: /configuracion/i });
		expect(link.className).toContain("bg-accent");
	});

	it("Given pathname /settings When render Then el item Mis sesiones NO esta activo", () => {
		// Arrange + Act
		render(<Sidebar />);

		// Assert
		const link = screen.getByRole("link", { name: /mis sesiones/i });
		expect(link.className).toContain("text-muted-foreground");
	});

	it("Given el sidebar When render Then muestra los 4 items de navegacion", () => {
		// Arrange + Act
		render(<Sidebar />);

		// Assert
		expect(screen.getAllByRole("link")).toHaveLength(4);
	});

	it("Given el sidebar When render Then NO muestra el item Metricas", () => {
		// Arrange + Act
		render(<Sidebar />);

		// Assert
		expect(screen.queryByRole("link", { name: /metricas/i })).toBe(null);
	});
});
