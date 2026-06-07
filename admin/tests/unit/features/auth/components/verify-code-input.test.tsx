import { render, screen, userEvent, waitFor } from "@tests/utils/render";
import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";
import { VerifyCodeInput } from "@/features/auth/components/verify-code-input";
import { useAuthStore } from "@/features/auth/store/use-auth-store";

/**
 * @module tests/unit/features/auth/components/verify-code-input
 * @description Verifica el InputOTP de 8 chars y que el submit con un code de 8
 *   chars (login.verify-code) cierre la sesion.
 */

vi.mock("next/navigation", () => ({
	useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

describe("VerifyCodeInput", () => {
	it("Given un InputOTP de 8 chars When se monta Then el boton arranca deshabilitado", () => {
		// Arrange
		useAuthStore.setState({ tempToken: "mock-temp" });

		// Act
		render((<VerifyCodeInput />) as ReactElement);

		// Assert
		expect(screen.getByRole("button", { name: /verificar/i })).toBeDisabled();
	});

	it("Given code valido When submit Then setea la sesion (login.verify-code)", async () => {
		// Arrange
		useAuthStore.setState({ tempToken: "mock-temp" });
		const user = userEvent.setup();
		render((<VerifyCodeInput />) as ReactElement);

		// Act
		await user.type(
			screen.getByLabelText(/codigo de verificacion/i),
			"12345678",
		);
		await user.click(screen.getByRole("button", { name: /verificar/i }));

		// Assert
		await waitFor(() => {
			expect(useAuthStore.getState().accessToken).not.toBe(null);
		});
		expect(useAuthStore.getState().user?.email).toBe("user@test.com");
	});
});
