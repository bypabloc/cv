import { server } from "@tests/mocks/server";
import { render, screen, userEvent, waitFor } from "@tests/utils/render";
import { delay, HttpResponse, http } from "msw";
import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";
import { LoginPasswordInput } from "@/features/auth/components/login-password-input";
import { MagicLinkPrompt } from "@/features/auth/components/magic-link-prompt";
import { RecoveryCodeInput } from "@/features/auth/components/recovery-code-input";
import { RegisterForm } from "@/features/auth/components/register-form";
import { SetPasswordForm } from "@/features/auth/components/set-password-form";
import { useAuthStore } from "@/features/auth/store/use-auth-store";

/**
 * @module tests/unit/features/auth/components/forms-pending-states
 * @description Cubre la rama `isPending === true` de los forms: con una
 *   respuesta MSW retrasada, el boton muestra el label de carga (Verificando.../
 *   Guardando.../Reenviando.../Enviando...) y queda disabled. Eso ejercita el
 *   ternario y la rama `isPending ||` del disabled.
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

const API = "https://api.test.the-full-stack.com";

function delayAuth() {
	server.use(
		http.post(`${API}/auth`, async () => {
			// Delay holgado: el estado isPending debe seguir visible cuando el
			// assertion (waitFor/findByRole) lo busca, aun con la suite completa.
			await delay(1000);
			return HttpResponse.json({ is_valid: true, code: 0, data: { ok: true } });
		}),
	);
}

describe("LoginPasswordInput pending", () => {
	it("Given submit en vuelo When responde lento Then muestra Verificando...", async () => {
		// Arrange
		delayAuth();
		useAuthStore.setState({ tempToken: "t" });
		const user = userEvent.setup();
		render((<LoginPasswordInput />) as ReactElement);

		// Act
		await user.type(screen.getByLabelText(/contrasena/i), "abcdefghijkl");
		await user.click(screen.getByRole("button", { name: /continuar/i }));

		// Assert: rama isPending true
		await waitFor(() => {
			expect(
				screen.getByRole("button", { name: /verificando/i }),
			).toBeDisabled();
		});
	});
});

describe("RecoveryCodeInput pending", () => {
	it("Given submit en vuelo When responde lento Then muestra Verificando...", async () => {
		// Arrange
		delayAuth();
		useAuthStore.setState({ tempToken: "t" });
		const user = userEvent.setup();
		render((<RecoveryCodeInput />) as ReactElement);

		// Act
		await user.type(
			screen.getByLabelText(/codigo de recuperacion/i),
			"abcdefghj0",
		);
		await user.click(screen.getByRole("button", { name: /usar codigo/i }));

		// Assert
		await waitFor(() => {
			expect(
				screen.getByRole("button", { name: /verificando/i }),
			).toBeDisabled();
		});
	});
});

describe("SetPasswordForm pending", () => {
	it("Given submit en vuelo When responde lento Then muestra Guardando...", async () => {
		// Arrange
		delayAuth();
		useAuthStore.setState({ tempToken: "t" });
		const user = userEvent.setup();
		render((<SetPasswordForm />) as ReactElement);

		// Act
		const inputs = screen.getAllByLabelText(/contrasena/i);
		await user.type(inputs[0] as HTMLElement, "abcdefghijkl");
		await user.type(inputs[1] as HTMLElement, "abcdefghijkl");
		await user.click(
			screen.getByRole("button", { name: /guardar contrasena/i }),
		);

		// Assert: findByRole reintenta hasta que el boton entra en isPending
		const pendingButton = await screen.findByRole("button", {
			name: /guardando/i,
		});
		expect(pendingButton).toBeDisabled();
	});
});

describe("MagicLinkPrompt pending", () => {
	it("Given reenvio en vuelo When responde lento Then muestra Reenviando...", async () => {
		// Arrange
		delayAuth();
		useAuthStore.setState({ tempToken: "t" });
		const user = userEvent.setup();
		render((<MagicLinkPrompt />) as ReactElement);

		// Act
		await user.click(screen.getByRole("button", { name: /reenviar email/i }));

		// Assert
		await waitFor(() => {
			expect(
				screen.getByRole("button", { name: /reenviando/i }),
			).toBeDisabled();
		});
	});
});

describe("RegisterForm pending", () => {
	it("Given submit en vuelo When responde lento Then muestra Enviando...", async () => {
		// Arrange
		delayAuth();
		const user = userEvent.setup();
		render((<RegisterForm />) as ReactElement);

		// Act
		await user.type(screen.getByLabelText(/email/i), "new@test.com");
		await user.click(screen.getByRole("button", { name: /pasar-turnstile/i }));
		await user.click(screen.getByRole("button", { name: /crear cuenta/i }));

		// Assert
		await waitFor(() => {
			expect(screen.getByRole("button", { name: /enviando/i })).toBeDisabled();
		});
	});
});
