import { render, screen, userEvent, waitFor } from "@tests/utils/render";
import type { ReactElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { LoginForm } from "@/features/auth/components/login-form";
import { useAuthStore } from "@/features/auth/store/use-auth-store";

/**
 * @module tests/unit/features/auth/components/login-form
 * @description Verifica el flujo de 2 pasos: validacion Zod (email invalido no
 *   llama API), check-email -> input de password (cuenta con password) y
 *   check-email -> "Crear cuenta" (email inexistente, login.start crea el user).
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
	beforeEach(() => {
		pushMock.mockClear();
		useAuthStore.getState().reset();
	});

	it("Given email invalido When submit Then NO llama a la API (Zod bloquea)", async () => {
		// Arrange
		const user = userEvent.setup();
		render((<LoginForm />) as ReactElement);

		// Act
		await user.type(screen.getByLabelText(/email/i), "no-es-email");
		await solveTurnstile();
		await user.click(screen.getByRole("button", { name: /^continuar$/i }));

		// Assert: el form sigue en el paso email (no avanza)
		await waitFor(() => {
			expect(screen.getByText(/email invalido/i)).toBeInTheDocument();
		});
		expect(screen.queryByTestId("login-password")).not.toBeInTheDocument();
	});

	it("Given cuenta con password When check-email Then muestra el input de password", async () => {
		// Arrange
		const user = userEvent.setup();
		render((<LoginForm />) as ReactElement);

		// Act
		await user.type(screen.getByLabelText(/email/i), "user@test.com");
		await solveTurnstile();
		await user.click(screen.getByRole("button", { name: /^continuar$/i }));

		// Assert: avanza al paso 2 (input password)
		expect(await screen.findByTestId("login-password")).toBeInTheDocument();
	});

	it("Given email no registrado When check-email Then ofrece Crear cuenta", async () => {
		// Arrange
		const user = userEvent.setup();
		render((<LoginForm />) as ReactElement);

		// Act
		await user.type(screen.getByLabelText(/email/i), "unknown@test.com");
		await solveTurnstile();
		await user.click(screen.getByRole("button", { name: /^continuar$/i }));

		// Assert: muestra el alert de cuenta inexistente + boton Crear cuenta
		await waitFor(() => {
			expect(
				screen.getByText(/no existe una cuenta con ese email/i),
			).toBeInTheDocument();
		});
		expect(
			screen.getByRole("button", { name: /crear cuenta/i }),
		).toBeInTheDocument();
	});

	it("Given Crear cuenta When click Then login.start crea el user y navega a /verify", async () => {
		// Arrange
		const user = userEvent.setup();
		render((<LoginForm />) as ReactElement);
		await user.type(screen.getByLabelText(/email/i), "unknown@test.com");
		await solveTurnstile();
		await user.click(screen.getByRole("button", { name: /^continuar$/i }));
		const crear = await screen.findByRole("button", { name: /crear cuenta/i });

		// Act
		await user.click(crear);

		// Assert
		await waitFor(() => {
			expect(pushMock).toHaveBeenCalledWith("/verify?flow=login");
		});
		expect(useAuthStore.getState().tempToken).toBe("mock-temp-created");
	});

	it("Given password correcta When submit Then login.start con el precheck navega a /verify", async () => {
		// Arrange: cuenta con password (default) -> input de password.
		const user = userEvent.setup();
		render((<LoginForm />) as ReactElement);
		await user.type(screen.getByLabelText(/email/i), "user@test.com");
		await solveTurnstile();
		await user.click(screen.getByRole("button", { name: /^continuar$/i }));
		await screen.findByTestId("login-password");

		// Act: el precheck (mock-precheck-token) viaja en Authorization, NO el
		// captcha. login.start con password OK -> temp + navega.
		await user.type(
			screen.getByTestId("login-password"),
			"a-strong-passphrase-12",
		);
		await user.click(screen.getByTestId("login-password-submit"));

		// Assert
		await waitFor(() => {
			expect(pushMock).toHaveBeenCalledWith("/verify?flow=login");
		});
		expect(useAuthStore.getState().tempToken).toBe("mock-temp-login");
	});

	it("Given password incorrecta When submit Then muestra el error inline (401)", async () => {
		// Arrange
		const user = userEvent.setup();
		render((<LoginForm />) as ReactElement);
		await user.type(screen.getByLabelText(/email/i), "user@test.com");
		await solveTurnstile();
		await user.click(screen.getByRole("button", { name: /^continuar$/i }));
		await screen.findByTestId("login-password");

		// Act: password que el mock rechaza con 401 INVALID_PASSWORD.
		await user.type(screen.getByTestId("login-password"), "wrong-password-99");
		await user.click(screen.getByTestId("login-password-submit"));

		// Assert: error inline, NO navega.
		await waitFor(() => {
			expect(screen.getByText(/contrasena incorrecta/i)).toBeInTheDocument();
		});
		expect(pushMock).not.toHaveBeenCalled();
	});
});
