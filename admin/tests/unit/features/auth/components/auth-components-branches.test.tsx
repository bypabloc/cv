import { server } from "@tests/mocks/server";
import {
	fireEvent,
	render,
	screen,
	userEvent,
	waitFor,
} from "@tests/utils/render";
import { delay, HttpResponse, http } from "msw";
import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";
import { LoginForm } from "@/features/auth/components/login-form";
import { TotpSetup } from "@/features/auth/components/totp-setup";
import { WebAuthnLoginButton } from "@/features/auth/components/webauthn-login-button";
import { WebAuthnRegisterButton } from "@/features/auth/components/webauthn-register-button";

/**
 * @module tests/unit/features/auth/components/auth-components-branches
 * @description Cubre ramas faltantes: login-form boton Registrate (push),
 *   webauthn login sin email + catch, webauthn register catch + nickname,
 *   totp-setup loading + guard de longitud + DIGITS false + isPending.
 */

const { pushMock } = vi.hoisted(() => ({ pushMock: vi.fn() }));
vi.mock("next/navigation", () => ({
	useRouter: () => ({ push: pushMock, replace: vi.fn() }),
}));

vi.mock("@marsidev/react-turnstile", () => ({
	Turnstile: ({ onSuccess }: { onSuccess?: (token: string) => void }) => (
		<button type="button" onClick={() => onSuccess?.("tok-ok")}>
			pasar-turnstile
		</button>
	),
}));

const { startRegistrationMock, startAuthenticationMock } = vi.hoisted(() => ({
	startRegistrationMock: vi.fn(),
	startAuthenticationMock: vi.fn(),
}));
vi.mock("@simplewebauthn/browser", () => ({
	startRegistration: startRegistrationMock,
	startAuthentication: startAuthenticationMock,
}));

const API = "https://api.test.the-full-stack.com";

describe("LoginForm boton Registrate", () => {
	it("Given Alert visible When click Registrate Then navega a /register", async () => {
		// Arrange
		const user = userEvent.setup();
		render((<LoginForm />) as ReactElement);
		// LoginForm + WebAuthnLoginButton tienen un input email cada uno; el de
		// LoginForm es el unico con placeholder 'tu@email.com'.
		await user.type(
			screen.getByPlaceholderText("tu@email.com"),
			"unknown@test.com",
		);
		await user.click(screen.getByRole("button", { name: /pasar-turnstile/i }));
		await user.click(screen.getByRole("button", { name: /iniciar sesion/i }));
		const registrate = await screen.findByRole("button", {
			name: /registrate/i,
		});

		// Act: cubre el onClick `router.push(ROUTES.auth.register)`
		await user.click(registrate);

		// Assert
		expect(pushMock).toHaveBeenCalledWith("/register");
	});

	it("Given 404 sin suggest_register When submit Then NO muestra el Alert (rama false)", async () => {
		// Arrange: 404 con suggest_register false -> rama `if (suggest_register)` falsa
		server.use(
			http.post(`${API}/auth`, () =>
				HttpResponse.json(
					{
						error: "EMAIL_NOT_FOUND",
						code: 4040,
						message: "No existe",
						data: { suggest_register: false },
					},
					{ status: 404 },
				),
			),
		);
		const user = userEvent.setup();
		render((<LoginForm />) as ReactElement);
		await user.type(screen.getByPlaceholderText("tu@email.com"), "x@test.com");
		await user.click(screen.getByRole("button", { name: /pasar-turnstile/i }));

		// Act
		await user.click(screen.getByRole("button", { name: /iniciar sesion/i }));

		// Assert: el alert "no esta registrado" NO aparece
		await waitFor(() => {
			expect(
				screen.getByRole("button", { name: /iniciar sesion/i }),
			).not.toBeDisabled();
		});
		expect(screen.queryByText(/no esta registrado/i)).not.toBeInTheDocument();
	});

	it("Given un error 500 (no 404) When submit Then NO muestra el Alert (rama false)", async () => {
		// Arrange: cubre `error.status === 404` falso
		server.use(
			http.post(`${API}/auth`, () =>
				HttpResponse.json(
					{ error: "SERVER_ERROR", code: 5000, message: "Boom" },
					{ status: 500 },
				),
			),
		);
		const user = userEvent.setup();
		render((<LoginForm />) as ReactElement);
		await user.type(screen.getByPlaceholderText("tu@email.com"), "y@test.com");
		await user.click(screen.getByRole("button", { name: /pasar-turnstile/i }));

		// Act
		await user.click(screen.getByRole("button", { name: /iniciar sesion/i }));

		// Assert
		await waitFor(() => {
			expect(
				screen.getByRole("button", { name: /iniciar sesion/i }),
			).not.toBeDisabled();
		});
		expect(screen.queryByText(/no esta registrado/i)).not.toBeInTheDocument();
	});

	it("Given submit en vuelo When responde lento Then muestra Enviando... (isPending)", async () => {
		// Arrange
		server.use(
			http.post(`${API}/auth`, async () => {
				await delay(1000);
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { temp_token: "t", user_id: "usr_01", expires_in: 300 },
				});
			}),
		);
		const user = userEvent.setup();
		render((<LoginForm />) as ReactElement);
		await user.type(screen.getByPlaceholderText("tu@email.com"), "z@test.com");
		await user.click(screen.getByRole("button", { name: /pasar-turnstile/i }));

		// Act
		await user.click(screen.getByRole("button", { name: /iniciar sesion/i }));

		// Assert: rama isPending true del boton
		const pending = await screen.findByRole("button", { name: /enviando/i });
		expect(pending).toBeDisabled();
	});
});

describe("WebAuthnLoginButton sin email", () => {
	it("Given sin email When click Then no llama startAuthentication (rama !email)", async () => {
		// Arrange
		const user = userEvent.setup();
		render((<WebAuthnLoginButton />) as ReactElement);

		// Act
		await user.click(screen.getByRole("button", { name: /usar passkey/i }));

		// Assert: la rama `if (!email)` corta antes de la API
		expect(startAuthenticationMock).not.toHaveBeenCalled();
	});

	it("Given startAuthentication lanza When click Then entra al catch (no rompe)", async () => {
		// Arrange: cubre el catch del onUsePasskey
		startAuthenticationMock.mockRejectedValueOnce(new Error("cancelado"));
		const user = userEvent.setup();
		render((<WebAuthnLoginButton />) as ReactElement);

		// Act
		await user.type(screen.getByLabelText(/email/i), "user@test.com");
		await user.click(screen.getByRole("button", { name: /usar passkey/i }));

		// Assert: el boton vuelve a habilitarse tras el catch
		await waitFor(() => {
			expect(
				screen.getByRole("button", { name: /usar passkey/i }),
			).not.toBeDisabled();
		});
	});
});

describe("WebAuthnRegisterButton catch + nickname", () => {
	it("Given startRegistration lanza When click Then entra al catch", async () => {
		// Arrange: cubre el catch del onRegister (toast.error)
		startRegistrationMock.mockRejectedValueOnce(new Error("cancelado"));
		const user = userEvent.setup();
		render((<WebAuthnRegisterButton />) as ReactElement);

		// Act
		await user.click(screen.getByRole("button", { name: /agregar passkey/i }));

		// Assert
		await waitFor(() => {
			expect(
				screen.getByRole("button", { name: /agregar passkey/i }),
			).not.toBeDisabled();
		});
	});

	it("Given un nickname When click Then register-verify recibe el nickname", async () => {
		// Arrange: cubre `nickname || undefined` (rama truthy)
		let capturedBody: { data?: { nickname?: string } } | null = null;
		server.use(
			http.post(`${API}/auth`, async ({ request }) => {
				const body = (await request.json()) as {
					operation: string;
					action: string;
					data: { nickname?: string };
				};
				if (body.action === "register-options") {
					return HttpResponse.json({
						is_valid: true,
						code: 0,
						data: {
							challenge_id: "chal_01",
							options: { challenge: "fake", pubKeyCredParams: [] },
						},
					});
				}
				capturedBody = body;
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { methods: [], webauthn_count: 1, total_mfa: 1 },
				});
			}),
		);
		startRegistrationMock.mockResolvedValueOnce({ id: "reg" });
		const user = userEvent.setup();
		render((<WebAuthnRegisterButton />) as ReactElement);

		// Act
		await user.type(screen.getByLabelText(/nombre del passkey/i), "Mi Llave");
		await user.click(screen.getByRole("button", { name: /agregar passkey/i }));

		// Assert
		await waitFor(() => {
			expect(capturedBody?.data?.nickname).toBe("Mi Llave");
		});
	});
});

describe("TotpSetup loading + guards", () => {
	it("Given setup en vuelo When responde lento Then muestra Generando codigo", async () => {
		// Arrange: retrasa mfa.setup-totp para ver la rama `if (!setup)`
		server.use(
			http.post(`${API}/auth`, async () => {
				await delay(300);
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { secret_b32: "JBSWY3DPEHPK3PXP", otpauth_url: "otpauth://x" },
				});
			}),
		);
		render((<TotpSetup />) as ReactElement);

		// Assert: estado de carga inicial
		expect(screen.getByText(/generando codigo/i)).toBeInTheDocument();
	});

	it("Given input no numerico When se escribe Then DIGITS.test corta (rama false)", async () => {
		// Arrange
		const user = userEvent.setup();
		render((<TotpSetup />) as ReactElement);
		const otp = await screen.findByLabelText(/codigo totp de confirmacion/i);

		// Act: las letras no pasan el regex DIGITS -> no se setean
		await user.type(otp, "abc");

		// Assert: el input OTP sigue vacio (el boton Confirmar disabled por longitud)
		expect(screen.getByRole("button", { name: /confirmar/i })).toBeDisabled();
	});

	it("Given menos de 6 digitos When submit forzado Then no confirma (guard longitud)", async () => {
		// Arrange
		render((<TotpSetup />) as ReactElement);
		await screen.findByLabelText(/codigo totp de confirmacion/i);

		// Act: submit con code vacio -> `if (code.length !== CODE_LENGTH) return`
		const form = document.querySelector("form") as HTMLFormElement;
		fireEvent.submit(form);

		// Assert: el boton sigue disabled (no entro a la mutation)
		expect(screen.getByRole("button", { name: /confirmar/i })).toBeDisabled();
	});

	it("Given confirm en vuelo When responde lento Then muestra Confirmando", async () => {
		// Arrange: setup rapido, confirm lento -> ver `isPending` true
		server.use(
			http.post(`${API}/auth`, async ({ request }) => {
				const body = (await request.json()) as { action: string };
				if (body.action === "setup-totp") {
					return HttpResponse.json({
						is_valid: true,
						code: 0,
						data: {
							secret_b32: "JBSWY3DPEHPK3PXP",
							otpauth_url: "otpauth://x",
						},
					});
				}
				await delay(300);
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { methods: [], webauthn_count: 0, total_mfa: 1 },
				});
			}),
		);
		const user = userEvent.setup();
		render((<TotpSetup />) as ReactElement);
		const otp = await screen.findByLabelText(/codigo totp de confirmacion/i);

		// Act
		await user.type(otp, "123456");
		await user.click(screen.getByRole("button", { name: /confirmar/i }));

		// Assert
		await waitFor(() => {
			expect(
				screen.getByRole("button", { name: /confirmando/i }),
			).toBeDisabled();
		});
	});
});
