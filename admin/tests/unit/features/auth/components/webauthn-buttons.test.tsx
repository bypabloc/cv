import type {
	AuthenticationResponseJSON,
	RegistrationResponseJSON,
} from "@simplewebauthn/browser";
import { server } from "@tests/mocks/server";
import { render, screen, userEvent, waitFor } from "@tests/utils/render";
import { HttpResponse, http } from "msw";
import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";
import { WebAuthnLoginButton } from "@/features/auth/components/webauthn-login-button";
import { WebAuthnRegisterButton } from "@/features/auth/components/webauthn-register-button";
import { useAuthStore } from "@/features/auth/store/use-auth-store";

/**
 * @module tests/unit/features/auth/components/webauthn-buttons
 * @description Verifica que los botones WebAuthn pasen las options del backend
 *   a startRegistration/startAuthentication, reenvien el response, y que el
 *   register surface el error real (WebAuthnError) en vez de un toast
 *   generico que oculta la causa.
 */

vi.mock("next/navigation", () => ({
	useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

const { startRegistrationMock, startAuthenticationMock, MockWebAuthnError } =
	vi.hoisted(() => {
		// Replica minima de @simplewebauthn/browser.WebAuthnError. El mock
		// reemplaza el modulo ENTERO, asi que el componente importa ESTA clase
		// y su `instanceof` la reconoce. Evita `importActual` del barrel real
		// (arrastra el AbortService singleton + helpers DOM -> agota el worker
		// pool al correr toda la suite -> "Worker exited unexpectedly").
		class MockWebAuthnError extends Error {
			code: string;
			constructor({
				message,
				code,
				cause,
			}: {
				message: string;
				code: string;
				cause: Error;
			}) {
				super(message, { cause });
				this.name = cause.name;
				this.code = code;
			}
		}
		return {
			startRegistrationMock: vi.fn(),
			startAuthenticationMock: vi.fn(),
			MockWebAuthnError,
		};
	});
vi.mock("@simplewebauthn/browser", () => ({
	startRegistration: startRegistrationMock,
	startAuthentication: startAuthenticationMock,
	WebAuthnError: MockWebAuthnError,
}));

const { toastSuccessMock, toastErrorMock } = vi.hoisted(() => ({
	toastSuccessMock: vi.fn(),
	toastErrorMock: vi.fn(),
}));
// Toaster es un componente null en estos tests (no se renderiza el real).
// Evita `importActual("sonner")` (carga el Toaster real en el worker).
vi.mock("sonner", () => ({
	toast: { success: toastSuccessMock, error: toastErrorMock },
	Toaster: () => null,
}));

const API = "https://api.test.the-full-stack.com";
const REG_RESPONSE = { id: "reg" } as unknown as RegistrationResponseJSON;
const AUTH_RESPONSE = { id: "auth" } as unknown as AuthenticationResponseJSON;

describe("WebAuthnRegisterButton", () => {
	it("Given options envueltas en publicKey When click Then startRegistration recibe el contenido PLANO (sin re-envolver)", async () => {
		startRegistrationMock.mockReset();
		startRegistrationMock.mockResolvedValue(REG_RESPONSE);
		const user = userEvent.setup();
		render((<WebAuthnRegisterButton />) as ReactElement);

		await user.click(screen.getByRole("button", { name: /agregar passkey/i }));

		await waitFor(() => {
			expect(startRegistrationMock).toHaveBeenCalledTimes(1);
		});
		const arg = startRegistrationMock.mock.calls[0]?.[0] as {
			optionsJSON: { challenge: string; publicKey?: unknown };
		};
		// El backend envuelve en `options.publicKey`; el componente debe pasar
		// ESE contenido (plano) a optionsJSON, NO el wrapper. Si re-envolviera,
		// `optionsJSON.challenge` seria undefined (la causa del bug ".replace").
		expect(arg.optionsJSON.challenge).toBe("fake");
		expect(arg.optionsJSON.publicKey).toBeUndefined();
	});

	it("Given el ceremony completo When click Then dispara toast.success y NO toast.error", async () => {
		startRegistrationMock.mockReset();
		toastSuccessMock.mockReset();
		toastErrorMock.mockReset();
		startRegistrationMock.mockResolvedValue(REG_RESPONSE);
		const user = userEvent.setup();
		render((<WebAuthnRegisterButton />) as ReactElement);

		await user.click(screen.getByRole("button", { name: /agregar passkey/i }));

		await waitFor(() => {
			expect(toastSuccessMock).toHaveBeenCalledTimes(1);
		});
		expect(toastErrorMock).not.toHaveBeenCalled();
	});

	it("Given el authenticator ya registrado (InvalidStateError) When click Then toast.error con mensaje especifico", async () => {
		startRegistrationMock.mockReset();
		toastErrorMock.mockReset();
		startRegistrationMock.mockRejectedValue(
			new MockWebAuthnError({
				message: "The authenticator was previously registered",
				code: "ERROR_AUTHENTICATOR_PREVIOUSLY_REGISTERED",
				cause: Object.assign(new Error("ya existe"), {
					name: "InvalidStateError",
				}),
			}),
		);
		const user = userEvent.setup();
		render((<WebAuthnRegisterButton />) as ReactElement);

		await user.click(screen.getByRole("button", { name: /agregar passkey/i }));

		await waitFor(() => {
			expect(toastErrorMock).toHaveBeenCalledWith(
				"Este dispositivo ya tiene un passkey registrado para tu cuenta.",
			);
		});
	});

	it("Given otro WebAuthnError (no InvalidStateError) When click Then toast.error con el message del browser", async () => {
		startRegistrationMock.mockReset();
		toastErrorMock.mockReset();
		startRegistrationMock.mockRejectedValue(
			new MockWebAuthnError({
				message: "The RP ID is invalid for this domain",
				code: "ERROR_INVALID_RP_ID",
				cause: Object.assign(new Error("rp id"), { name: "SecurityError" }),
			}),
		);
		const user = userEvent.setup();
		render((<WebAuthnRegisterButton />) as ReactElement);

		await user.click(screen.getByRole("button", { name: /agregar passkey/i }));

		await waitFor(() => {
			expect(toastErrorMock).toHaveBeenCalledWith(
				"No pudimos crear el passkey: The RP ID is invalid for this domain",
			);
		});
	});

	it("Given register-verify falla en el backend When click Then toast.error con el codigo del servidor", async () => {
		startRegistrationMock.mockReset();
		toastErrorMock.mockReset();
		startRegistrationMock.mockResolvedValue(REG_RESPONSE);
		// El ceremony del browser tiene exito, pero el backend rechaza el verify.
		server.use(
			http.post(`${API}/auth`, async ({ request }) => {
				const body = (await request.json()) as { action: string };
				if (body.action === "register-options") {
					return HttpResponse.json({
						is_valid: true,
						code: 0,
						data: {
							challenge_id: "chal_01",
							options: {
								publicKey: { challenge: "fake", pubKeyCredParams: [] },
							},
						},
					});
				}
				return HttpResponse.json(
					{ error: "WEBAUTHN_REGISTRATION_FAILED", code: 1002 },
					{ status: 400 },
				);
			}),
		);
		const user = userEvent.setup();
		render((<WebAuthnRegisterButton />) as ReactElement);

		await user.click(screen.getByRole("button", { name: /agregar passkey/i }));

		await waitFor(() => {
			expect(toastErrorMock).toHaveBeenCalledWith(
				"El servidor rechazo el passkey (1002): WEBAUTHN_REGISTRATION_FAILED",
			);
		});
	});

	it("Given un error generico When click Then toast.error con el mensaje por defecto", async () => {
		startRegistrationMock.mockReset();
		toastErrorMock.mockReset();
		startRegistrationMock.mockRejectedValue(new Error("boom"));
		const user = userEvent.setup();
		render((<WebAuthnRegisterButton />) as ReactElement);

		await user.click(screen.getByRole("button", { name: /agregar passkey/i }));

		await waitFor(() => {
			expect(toastErrorMock).toHaveBeenCalledWith(
				"No pudimos registrar el passkey",
			);
		});
	});
});

describe("WebAuthnLoginButton", () => {
	it("Given email + options When click Then startAuthentication recibe optionsJSON y cierra sesion", async () => {
		startAuthenticationMock.mockResolvedValue(AUTH_RESPONSE);
		const user = userEvent.setup();
		render((<WebAuthnLoginButton />) as ReactElement);

		await user.type(screen.getByLabelText(/email/i), "user@test.com");
		await user.click(screen.getByRole("button", { name: /usar passkey/i }));

		await waitFor(() => {
			expect(startAuthenticationMock).toHaveBeenCalledTimes(1);
		});
		await waitFor(() => {
			expect(useAuthStore.getState().accessToken).not.toBe(null);
		});
	});
});
