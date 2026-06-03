import { render, screen, userEvent, waitFor } from "@tests/utils/render";
import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";
import { LoginPasswordInput } from "@/features/auth/components/login-password-input";
import { LoginTotpInput } from "@/features/auth/components/login-totp-input";
import { MagicLinkPrompt } from "@/features/auth/components/magic-link-prompt";
import { RecoveryCodeInput } from "@/features/auth/components/recovery-code-input";
import { SetPasswordForm } from "@/features/auth/components/set-password-form";
import { useAuthStore } from "@/features/auth/store/use-auth-store";

/**
 * @module tests/unit/features/auth/components/forms
 * @description Tests de los forms de auth (set-password, magic-link, login
 *   password/totp/recovery).
 */

vi.mock("next/navigation", () => ({
	useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

vi.mock("@marsidev/react-turnstile", () => ({
	Turnstile: ({ onSuccess }: { onSuccess?: (token: string) => void }) => (
		<button type="button" onClick={() => onSuccess?.("tok-ok")}>
			pasar-turnstile
		</button>
	),
}));

describe("SetPasswordForm", () => {
	it("Given passwords que no coinciden When submit Then muestra error de Zod", async () => {
		useAuthStore.setState({ tempToken: "t" });
		const user = userEvent.setup();
		render((<SetPasswordForm />) as ReactElement);

		const inputs = screen.getAllByLabelText(/contrasena/i);
		await user.type(inputs[0] as HTMLElement, "abcdefghijkl");
		await user.type(inputs[1] as HTMLElement, "distinta12345");
		await user.click(screen.getByRole("button", { name: /guardar/i }));

		await waitFor(() => {
			expect(screen.getByText(/no coinciden/i)).toBeInTheDocument();
		});
	});

	it("Given passwords iguales When submit Then setea la sesion", async () => {
		useAuthStore.setState({ tempToken: "t" });
		const user = userEvent.setup();
		render((<SetPasswordForm />) as ReactElement);

		const inputs = screen.getAllByLabelText(/contrasena/i);
		await user.type(inputs[0] as HTMLElement, "abcdefghijkl");
		await user.type(inputs[1] as HTMLElement, "abcdefghijkl");
		await user.click(screen.getByRole("button", { name: /guardar/i }));

		await waitFor(() => {
			expect(useAuthStore.getState().accessToken).not.toBe(null);
		});
	});
});

describe("MagicLinkPrompt", () => {
	it("Given temp_token When click Reenviar Then dispara el reenvio", async () => {
		useAuthStore.setState({ tempToken: "t" });
		const user = userEvent.setup();
		render((<MagicLinkPrompt />) as ReactElement);

		const button = screen.getByRole("button", { name: /reenviar/i });
		expect(button).not.toBeDisabled();
		await user.click(button);
		// Sin throw -> el handler corrio (MSW resend-code 200).
		expect(
			screen.getByText(/te enviamos un email con un link/i),
		).toBeInTheDocument();
	});
});

describe("LoginPasswordInput", () => {
	it("Given password corta When submit Then Zod bloquea (min 12)", async () => {
		useAuthStore.setState({ tempToken: "t" });
		const user = userEvent.setup();
		render((<LoginPasswordInput />) as ReactElement);

		await user.type(screen.getByLabelText(/contrasena/i), "corta");
		await user.click(screen.getByRole("button", { name: /continuar/i }));

		await waitFor(() => {
			expect(screen.getByText(/al menos 12/i)).toBeInTheDocument();
		});
	});

	it("Given password valida sin MFA When submit Then cierra el login", async () => {
		useAuthStore.setState({ tempToken: "t" });
		const user = userEvent.setup();
		render((<LoginPasswordInput />) as ReactElement);

		await user.type(screen.getByLabelText(/contrasena/i), "abcdefghijkl");
		await user.click(screen.getByRole("button", { name: /continuar/i }));

		await waitFor(() => {
			expect(useAuthStore.getState().accessToken).not.toBe(null);
		});
	});
});

describe("LoginTotpInput", () => {
	it('Given click en "Usar codigo de recuperacion" When se muestra Then monta RecoveryCodeInput', async () => {
		useAuthStore.setState({ tempToken: "t" });
		const user = userEvent.setup();
		render((<LoginTotpInput />) as ReactElement);

		await user.click(
			screen.getByRole("button", { name: /usar codigo de recuperacion/i }),
		);

		expect(
			screen.getByLabelText(/codigo de recuperacion/i),
		).toBeInTheDocument();
	});

	it("Given 6 digitos validos When submit Then dispara login.verify-totp", async () => {
		useAuthStore.setState({ tempToken: "t" });
		const user = userEvent.setup();
		render((<LoginTotpInput />) as ReactElement);

		await user.type(screen.getByLabelText(/codigo totp/i), "123456");
		await user.click(screen.getByRole("button", { name: /^verificar$/i }));

		await waitFor(() => {
			expect(useAuthStore.getState().accessToken).not.toBe(null);
		});
	});
});

describe("RecoveryCodeInput", () => {
	it("Given un input When se monta Then muestra el label de recuperacion", () => {
		useAuthStore.setState({ tempToken: "t" });
		render((<RecoveryCodeInput />) as ReactElement);
		expect(
			screen.getByLabelText(/codigo de recuperacion/i),
		).toBeInTheDocument();
	});

	it("Given un code de 10 chars When submit Then consume el recovery code (setTokens)", async () => {
		useAuthStore.setState({ tempToken: "t" });
		const user = userEvent.setup();
		render((<RecoveryCodeInput />) as ReactElement);

		await user.type(
			screen.getByLabelText(/codigo de recuperacion/i),
			"abcdefghj0",
		);
		await user.click(screen.getByRole("button", { name: /usar codigo/i }));

		await waitFor(() => {
			expect(useAuthStore.getState().accessToken).not.toBe(null);
		});
	});
});
