import { render, screen, userEvent, waitFor } from "@tests/utils/render";
import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";
import { LoginForm } from "@/features/auth/components/login-form";
import { useAuthStore } from "@/features/auth/store/use-auth-store";

/**
 * @module tests/unit/features/auth/components/login-form
 * @description Verifica validacion Zod (email invalido no llama API), el
 *   camino feliz (setea tempToken) y el 404 (Alert + boton Registrate).
 */

const { pushMock } = vi.hoisted(() => ({ pushMock: vi.fn() }));
vi.mock("next/navigation", () => ({
	useRouter: () => ({ push: pushMock, replace: vi.fn() }),
}));

// Turnstile real carga un script remoto: lo reemplazamos por un boton que
// emite el token via onSuccess.
vi.mock("@marsidev/react-turnstile", () => ({
	Turnstile: ({ onSuccess }: { onSuccess?: (token: string) => void }) => (
		<button type="button" onClick={() => onSuccess?.("tok-ok")}>
			pasar-turnstile
		</button>
	),
}));

// WebAuthn login button monta @simplewebauthn; lo apagamos para este test.
vi.mock("@/features/auth/components/webauthn-login-button", () => ({
	WebAuthnLoginButton: () => null,
}));

async function solveTurnstile(): Promise<void> {
	await userEvent.click(
		screen.getByRole("button", { name: /pasar-turnstile/i }),
	);
}

describe("LoginForm", () => {
	it("Given email invalido When submit Then NO llama a la API (Zod bloquea)", async () => {
		// Arrange
		const user = userEvent.setup();
		render((<LoginForm />) as ReactElement);

		// Act
		await user.type(screen.getByLabelText(/email/i), "no-es-email");
		await solveTurnstile();
		await user.click(screen.getByRole("button", { name: /iniciar sesion/i }));

		// Assert: el store nunca recibio un tempToken (la API no se invoco)
		await waitFor(() => {
			expect(screen.getByText(/email invalido/i)).toBeInTheDocument();
		});
		expect(useAuthStore.getState().tempToken).toBe(null);
	});

	it("Given email valido + Turnstile When submit Then setea tempToken", async () => {
		// Arrange
		const user = userEvent.setup();
		render((<LoginForm />) as ReactElement);

		// Act
		await user.type(screen.getByLabelText(/email/i), "user@test.com");
		await solveTurnstile();
		await user.click(screen.getByRole("button", { name: /iniciar sesion/i }));

		// Assert
		await waitFor(() => {
			expect(useAuthStore.getState().tempToken).toBe("mock-temp-login");
		});
	});

	it("Given email no registrado When submit Then muestra Alert + boton Registrate", async () => {
		// Arrange
		const user = userEvent.setup();
		render((<LoginForm />) as ReactElement);

		// Act
		await user.type(screen.getByLabelText(/email/i), "unknown@test.com");
		await solveTurnstile();
		await user.click(screen.getByRole("button", { name: /iniciar sesion/i }));

		// Assert
		await waitFor(() => {
			expect(screen.getByText(/no esta registrado/i)).toBeInTheDocument();
		});
		expect(
			screen.getByRole("button", { name: /registrate/i }),
		).toBeInTheDocument();
	});
});
