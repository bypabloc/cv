import { render, screen, userEvent, waitFor } from "@tests/utils/render";
import type { ReactElement } from "react";
import { describe, expect, it } from "vitest";
import { RecoveryCodesSection } from "@/features/settings/components/recovery-codes-section";

/**
 * @module tests/unit/features/settings/components/security-sections
 * @description Cubre la seccion recovery-codes (genera + modal con los 10
 *   codes) que compone el panel unificado de seguridad.
 */

describe("RecoveryCodesSection", () => {
	it("Given el boton Generar When click Then muestra los 10 codes en el modal", async () => {
		// Arrange
		const user = userEvent.setup();
		render((<RecoveryCodesSection />) as ReactElement);

		// Act
		await user.click(screen.getByRole("button", { name: /generar codigos/i }));

		// Assert: el modal abre con el primer code del MSW (RECOV00000)
		await waitFor(() => {
			expect(screen.getByText("RECOV00000")).toBeInTheDocument();
		});
		expect(screen.getByText("RECOV00009")).toBeInTheDocument();
	});
});
