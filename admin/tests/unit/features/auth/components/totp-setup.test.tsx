import { render, screen, userEvent, waitFor } from "@tests/utils/render";
import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";
import { TotpSetup } from "@/features/auth/components/totp-setup";

/**
 * @module tests/unit/features/auth/components/totp-setup
 * @description Verifica que el QR se renderice DESDE el otpauth_url del backend
 *   y que el secret_b32 se muestre como fallback.
 */

const { qrSpy } = vi.hoisted(() => ({ qrSpy: vi.fn() }));
vi.mock("qrcode.react", () => ({
	QRCodeSVG: (props: { value: string }) => {
		qrSpy(props.value);
		return <svg aria-label="qr" data-value={props.value} />;
	},
}));

const OTPAUTH =
	"otpauth://totp/the-full-stack:user@test.com?secret=JBSWY3DPEHPK3PXP&issuer=the-full-stack";

describe("TotpSetup", () => {
	it("Given el setup devuelve otpauth_url When monta Then QRCodeSVG recibe value=otpauth_url", async () => {
		// Act
		render((<TotpSetup />) as ReactElement);

		// Assert
		await waitFor(() => {
			expect(qrSpy).toHaveBeenCalledWith(OTPAUTH);
		});
		expect(screen.getByLabelText("qr")).toHaveAttribute("data-value", OTPAUTH);
		expect(screen.getByText("JBSWY3DPEHPK3PXP")).toBeInTheDocument();
	});

	it("Given el QR visible When se ingresan 6 digitos y se confirma Then no lanza", async () => {
		// Arrange
		const user = userEvent.setup();
		render((<TotpSetup />) as ReactElement);
		await waitFor(() => {
			expect(
				screen.getByLabelText(/codigo totp de confirmacion/i),
			).toBeInTheDocument();
		});

		// Act
		await user.type(
			screen.getByLabelText(/codigo totp de confirmacion/i),
			"123456",
		);
		await user.click(screen.getByRole("button", { name: /confirmar/i }));

		// Assert: el handler corrio (mfa.confirm-totp 200), el boton vuelve a habilitarse
		await waitFor(() => {
			expect(
				screen.getByRole("button", { name: /confirmar/i }),
			).not.toBeDisabled();
		});
	});
});
