import { render, screen } from "@tests/utils/render";
import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";
import SettingsLayout from "@/app/(admin)/settings/layout";

/**
 * @module tests/unit/app/settings-layout
 * @description Verifica los 3 tabs (rutas reales) del layout de /settings:
 *   Perfil y cuenta, Seguridad, Sesiones; y que el activo se deriva del
 *   pathname (AC-8).
 */

const pathnameMock = vi.fn(() => "/settings");
vi.mock("next/navigation", () => ({
	usePathname: () => pathnameMock(),
}));

describe("SettingsLayout", () => {
	it("Given el layout When render Then muestra los 3 tabs como links", () => {
		// Arrange + Act
		render(
			(
				<SettingsLayout>
					<div>child</div>
				</SettingsLayout>
			) as ReactElement,
		);

		// Assert
		expect(
			screen.getByRole("link", { name: /perfil y cuenta/i }),
		).toHaveAttribute("href", "/settings");
		expect(screen.getByRole("link", { name: /seguridad/i })).toHaveAttribute(
			"href",
			"/settings/security",
		);
		expect(screen.getByRole("link", { name: /sesiones/i })).toHaveAttribute(
			"href",
			"/settings/sessions",
		);
	});

	it("Given pathname /settings/security When render Then el tab Seguridad esta activo", () => {
		// Arrange
		pathnameMock.mockReturnValue("/settings/security");

		// Act
		render(
			(
				<SettingsLayout>
					<div>child</div>
				</SettingsLayout>
			) as ReactElement,
		);

		// Assert
		expect(screen.getByRole("link", { name: /seguridad/i })).toHaveAttribute(
			"aria-current",
			"page",
		);
		expect(
			screen.getByRole("link", { name: /perfil y cuenta/i }),
		).not.toHaveAttribute("aria-current");
	});

	it("Given el layout When render Then renderiza children", () => {
		// Arrange
		pathnameMock.mockReturnValue("/settings");

		// Act
		render(
			(
				<SettingsLayout>
					<div data-testid="child">contenido</div>
				</SettingsLayout>
			) as ReactElement,
		);

		// Assert
		expect(screen.getByTestId("child")).toBeInTheDocument();
	});
});
