import { render, screen, userEvent, waitFor } from "@tests/utils/render";
import type { ReactElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { LoginForm } from "@/features/auth/components/login-form";
import { useAuthStore } from "@/features/auth/store/use-auth-store";

/**
 * @module tests/unit/features/auth/components/login-form
 * @description Verifica la maquina de stages del login de 2 pasos:
 *   - Zod bloquea email invalido (no llama API).
 *   - check-email con `methods_required` no vacio -> CHECKLIST.
 *   - check-email exists:false -> stage 'create'.
 *   - check-email unavailable -> Alert generico.
 *   - check-email con password pero SIN methods_required -> passwordless.
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

async function checkEmailWith(email: string): Promise<void> {
	const user = userEvent.setup();
	await user.type(screen.getByTestId("login-email"), email);
	await solveTurnstile();
	await user.click(screen.getByTestId("login-submit"));
}

describe("LoginForm", () => {
	beforeEach(() => {
		pushMock.mockClear();
		useAuthStore.getState().reset();
	});

	it("Given email invalido When submit Then NO llama a la API (Zod bloquea)", async () => {
		// Arrange
		render((<LoginForm />) as ReactElement);

		// Act
		await checkEmailWith("no-es-email");

		// Assert: el form sigue en el paso email (no avanza)
		await waitFor(() => {
			expect(screen.getByText(/email invalido/i)).toBeInTheDocument();
		});
		expect(screen.queryByTestId("login-checklist")).not.toBeInTheDocument();
	});

	it("Given cuenta con metodos required When check-email Then muestra el checklist", async () => {
		// Arrange
		render((<LoginForm />) as ReactElement);

		// Act: check-email -> methods_required no vacio -> login.start -> checklist
		await checkEmailWith("checklist@test.com");

		// Assert: aparece el checklist (login.start abrio el step=2)
		expect(await screen.findByTestId("login-checklist")).toBeInTheDocument();
		expect(screen.getByTestId("checklist-progress")).toHaveTextContent(
			"0 de 2 completados",
		);
	});

	it("Given email no registrado When check-email Then ofrece Crear cuenta", async () => {
		// Arrange
		render((<LoginForm />) as ReactElement);

		// Act
		await checkEmailWith("unknown@test.com");

		// Assert: muestra el alert de cuenta inexistente + boton Crear cuenta
		await waitFor(() => {
			expect(
				screen.getByText(/no existe una cuenta con ese email/i),
			).toBeInTheDocument();
		});
		expect(screen.getByTestId("login-create-account")).toBeInTheDocument();
	});

	it("Given Crear cuenta When click Then login.start crea el user y navega a /verify", async () => {
		// Arrange
		const user = userEvent.setup();
		render((<LoginForm />) as ReactElement);
		await checkEmailWith("unknown@test.com");
		const crear = await screen.findByTestId("login-create-account");

		// Act
		await user.click(crear);

		// Assert
		await waitFor(() => {
			expect(pushMock).toHaveBeenCalledWith("/verify?flow=login");
		});
	});

	it("Given cuenta sin metodos required When check-email Then ofrece passwordless", async () => {
		// Arrange: has_password true pero sin methods_required -> passwordless.
		render((<LoginForm />) as ReactElement);

		// Act
		await checkEmailWith("user@test.com");

		// Assert: stage passwordless (NO checklist, NO input de password directo)
		expect(await screen.findByTestId("login-passwordless")).toBeInTheDocument();
		expect(screen.queryByTestId("login-checklist")).not.toBeInTheDocument();
	});

	it("Given passwordless When click Continuar Then login.start navega a /verify", async () => {
		// Arrange
		const user = userEvent.setup();
		render((<LoginForm />) as ReactElement);
		await checkEmailWith("user@test.com");
		const continuar = await screen.findByTestId("login-passwordless");

		// Act
		await user.click(continuar);

		// Assert
		await waitFor(() => {
			expect(pushMock).toHaveBeenCalledWith("/verify?flow=login");
		});
	});

	it("Given cuenta no disponible When check-email Then muestra el Alert generico", async () => {
		// Arrange: check-email -> unavailable:true -> stage 'unavailable'.
		render((<LoginForm />) as ReactElement);

		// Act
		await checkEmailWith("blocked@test.com");

		// Assert
		expect(
			await screen.findByText(/no se puede iniciar sesion con esta cuenta/i),
		).toBeInTheDocument();
	});
});
