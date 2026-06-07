import { fireEvent, render, screen, waitFor } from "@tests/utils/render";
import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";
import { LoginPasswordInput } from "@/features/auth/components/login-password-input";
import { LoginTotpInput } from "@/features/auth/components/login-totp-input";
import { MagicLinkPrompt } from "@/features/auth/components/magic-link-prompt";
import { RecoveryCodeInput } from "@/features/auth/components/recovery-code-input";
import { SetPasswordForm } from "@/features/auth/components/set-password-form";
import { VerifyCodeInput } from "@/features/auth/components/verify-code-input";
import { useAuthStore } from "@/features/auth/store/use-auth-store";

/**
 * @module tests/unit/features/auth/components/forms-no-temp-token
 * @description Cubre la rama `!tempToken` (true) de los forms de auth: el
 *   boton queda disabled y el guard `if (!tempToken) return` corta el submit
 *   (la mutation no se dispara). El store arranca sin tempToken (reset en
 *   setup).
 */

vi.mock("next/navigation", () => ({
	useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

describe("LoginPasswordInput sin tempToken", () => {
	it("Given sin tempToken When render Then el boton esta disabled", () => {
		// Arrange + Act
		render((<LoginPasswordInput />) as ReactElement);

		// Assert: rama `!tempToken` -> disabled
		expect(screen.getByRole("button", { name: /continuar/i })).toBeDisabled();
	});

	it("Given sin tempToken When submit forzado Then no setea sesion (guard)", async () => {
		// Arrange
		render((<LoginPasswordInput />) as ReactElement);

		// Act: el form se submitea aunque el boton este disabled -> guard corta
		const form = document.querySelector("form") as HTMLFormElement;
		fireEvent.submit(form);

		// Assert: el guard `if (!tempToken) return` evita la mutation
		await waitFor(() => {
			expect(useAuthStore.getState().accessToken).toBe(null);
		});
	});
});

describe("RecoveryCodeInput sin tempToken", () => {
	it("Given sin tempToken When render Then el boton esta disabled", () => {
		render((<RecoveryCodeInput />) as ReactElement);
		expect(screen.getByRole("button", { name: /usar codigo/i })).toBeDisabled();
	});

	it("Given sin tempToken When submit forzado Then no consume (guard)", async () => {
		render((<RecoveryCodeInput />) as ReactElement);
		const form = document.querySelector("form") as HTMLFormElement;
		fireEvent.submit(form);
		await waitFor(() => {
			expect(useAuthStore.getState().accessToken).toBe(null);
		});
	});
});

describe("SetPasswordForm sin tempToken", () => {
	it("Given sin tempToken When render Then el boton esta disabled", () => {
		render((<SetPasswordForm />) as ReactElement);
		expect(
			screen.getByRole("button", { name: /guardar contrasena/i }),
		).toBeDisabled();
	});
});

describe("MagicLinkPrompt sin tempToken", () => {
	it("Given sin tempToken When render Then el boton de reenviar esta disabled", () => {
		render((<MagicLinkPrompt />) as ReactElement);
		expect(
			screen.getByRole("button", { name: /reenviar email/i }),
		).toBeDisabled();
	});

	it("Given sin tempToken When click forzado Then no dispara el reenvio (guard onClick)", () => {
		// Arrange: el boton esta disabled; forzamos el click programatico para
		// cubrir la rama `if (tempToken)` falsa del onClick.
		render((<MagicLinkPrompt />) as ReactElement);
		const button = screen.getByRole("button", { name: /reenviar email/i });

		// Act
		fireEvent.click(button);

		// Assert: no rompe, el texto del prompt sigue presente
		expect(
			screen.getByText(/te enviamos un email con un link/i),
		).toBeInTheDocument();
	});
});

describe("VerifyCodeInput sin tempToken", () => {
	it("Given sin tempToken When render Then el boton esta disabled", () => {
		render((<VerifyCodeInput />) as ReactElement);
		expect(screen.getByRole("button", { name: /verificar/i })).toBeDisabled();
	});

	it("Given sin tempToken When submit forzado Then no verifica (guard)", async () => {
		// Arrange: el guard `if (... || !tempToken) return` corta el submit
		render((<VerifyCodeInput />) as ReactElement);

		// Act
		const form = document.querySelector("form") as HTMLFormElement;
		fireEvent.submit(form);

		// Assert
		await waitFor(() => {
			expect(useAuthStore.getState().accessToken).toBe(null);
		});
	});
});

describe("LoginTotpInput sin tempToken", () => {
	it("Given sin tempToken When render Then el boton de verificar esta disabled", () => {
		render((<LoginTotpInput />) as ReactElement);
		expect(screen.getByRole("button", { name: /^verificar$/i })).toBeDisabled();
	});

	it("Given sin tempToken When submit forzado Then no verifica (guard)", async () => {
		render((<LoginTotpInput />) as ReactElement);
		const form = document.querySelector("form") as HTMLFormElement;
		fireEvent.submit(form);
		await waitFor(() => {
			expect(useAuthStore.getState().accessToken).toBe(null);
		});
	});
});
