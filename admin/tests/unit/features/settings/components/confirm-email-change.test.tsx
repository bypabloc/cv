import { render, screen, waitFor } from "@tests/utils/render";
import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";
import { ConfirmEmailChange } from "@/features/settings/components/confirm-email-change";

/**
 * @module tests/unit/features/settings/components/confirm-email-change
 * @description Verifica que sin `?token` no renderiza nada, y que con token
 *   auto-dispara la confirmacion (users.profile.confirm-email-change) y muestra
 *   el estado de exito.
 */

const { searchParamsMock } = vi.hoisted(() => ({
	searchParamsMock: { get: vi.fn() },
}));
vi.mock("next/navigation", () => ({
	useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
	useSearchParams: () => searchParamsMock,
}));

describe("ConfirmEmailChange", () => {
	it("Given sin token When render Then no renderiza el alert de confirmacion", () => {
		// Arrange
		searchParamsMock.get.mockReturnValue(null);

		// Act
		render((<ConfirmEmailChange />) as ReactElement);

		// Assert: el componente retorna null -> no hay titulo de confirmacion
		expect(
			screen.queryByText(/confirmacion de email/i),
		).not.toBeInTheDocument();
	});

	it("Given token en la URL When monta Then confirma y muestra exito", async () => {
		// Arrange
		searchParamsMock.get.mockReturnValue("tok-123");

		// Act
		render((<ConfirmEmailChange />) as ReactElement);

		// Assert: el MSW responde 200 -> estado de exito
		await waitFor(() => {
			expect(
				screen.getByText(/tu email fue actualizado correctamente/i),
			).toBeInTheDocument();
		});
	});
});
