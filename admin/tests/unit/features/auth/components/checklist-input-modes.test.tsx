import type { AuthenticationResponseJSON } from "@simplewebauthn/browser";
import { server } from "@tests/mocks/server";
import { render, screen, userEvent, waitFor } from "@tests/utils/render";
import { HttpResponse, http } from "msw";
import type { ReactElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { LoginPasswordInput } from "@/features/auth/components/login-password-input";
import { RecoveryCodeInput } from "@/features/auth/components/recovery-code-input";
import { WebAuthnLoginButton } from "@/features/auth/components/webauthn-login-button";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import type { VerifyResult } from "@/types/api";

/**
 * @module tests/unit/features/auth/components/checklist-input-modes
 * @description Cubre el MODO CHECKLIST (props `tempToken` + `onResult` o
 *   `email` + `onResult`) de los inputs parametrizados que aun tenian ramas sin
 *   ejercitar: el onError 401 del password, el modo checklist completo del
 *   recovery code (exito + 403 + error generico) y el render + runPasskey del
 *   boton WebAuthn.
 */

const { startAuthenticationMock } = vi.hoisted(() => ({
	startAuthenticationMock: vi.fn(),
}));
vi.mock("@simplewebauthn/browser", () => ({
	startAuthentication: startAuthenticationMock,
}));

const { toastErrorMock } = vi.hoisted(() => ({ toastErrorMock: vi.fn() }));
vi.mock("sonner", async () => {
	const actual = await vi.importActual<typeof import("sonner")>("sonner");
	return { ...actual, toast: { ...actual.toast, error: toastErrorMock } };
});

vi.mock("next/navigation", () => ({
	useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

const API = "https://api.test.the-full-stack.com";

const FAKE_RESPONSE = {
	id: "cred",
	rawId: "cred",
	response: {},
	type: "public-key",
	clientExtensionResults: {},
} as unknown as AuthenticationResponseJSON;

describe("LoginPasswordInput (modo checklist) error 401", () => {
	beforeEach(() => {
		useAuthStore.getState().reset();
	});

	it("Given password incorrecta When checklist verify devuelve 401 Then marca el campo y NO llama onResult", async () => {
		// Arrange: verify-password 401 -> rama onError (form.setError password).
		server.use(
			http.post(`${API}/auth`, () =>
				HttpResponse.json(
					{ error: "INVALID_PASSWORD", code: 4000, message: "Password mala" },
					{ status: 401 },
				),
			),
		);
		const onResult = vi.fn();
		const user = userEvent.setup();
		render(
			(
				<LoginPasswordInput
					tempToken="cl-step2-0"
					onResult={onResult}
					testid="cl-pw"
				/>
			) as ReactElement,
		);

		// Act
		await user.type(screen.getByTestId("cl-pw"), "a-strong-pass-12");
		await user.click(screen.getByRole("button", { name: /continuar/i }));

		// Assert: el mensaje de error inline aparece; onResult nunca corre.
		await waitFor(() => {
			expect(screen.getByText(/contrasena incorrecta/i)).toBeInTheDocument();
		});
		expect(onResult).not.toHaveBeenCalled();
		expect(useAuthStore.getState().accessToken).toBe(null);
	});
});

describe("RecoveryCodeInput (modo checklist)", () => {
	beforeEach(() => {
		useAuthStore.getState().reset();
		toastErrorMock.mockClear();
	});

	it("Given tempToken+onResult When submit code valido Then entrega el AuthResponse (sin tokens)", async () => {
		// Arrange: el handler recovery-codes-consume devuelve authPair().
		const onResult = vi.fn();
		const user = userEvent.setup();
		render(
			(
				<RecoveryCodeInput
					tempToken="cl-recovery"
					onResult={onResult}
					testid="cl-recovery"
				/>
			) as ReactElement,
		);

		// Act
		await user.type(screen.getByTestId("cl-recovery"), "abcdefghj0");
		await user.click(screen.getByRole("button", { name: /usar codigo/i }));

		// Assert: onResult recibe el AuthResponse; el store queda intacto.
		await waitFor(() => {
			expect(onResult).toHaveBeenCalledTimes(1);
		});
		const result = onResult.mock.calls[0]?.[0] as VerifyResult;
		expect("access_token" in result).toBe(true);
		expect(useAuthStore.getState().accessToken).toBe(null);
	});

	it("Given checklist consume devuelve 403 When submit Then muestra toast de factor fuerte y NO llama onResult", async () => {
		// Arrange: 403 RECOVERY_REQUIRES_STRONG_FACTOR -> rama onError especifica.
		server.use(
			http.post(`${API}/auth`, () =>
				HttpResponse.json(
					{
						error: "RECOVERY_REQUIRES_STRONG_FACTOR",
						code: 4030,
						message: "Necesitas un factor fuerte",
					},
					{ status: 403 },
				),
			),
		);
		const onResult = vi.fn();
		const user = userEvent.setup();
		render(
			(
				<RecoveryCodeInput
					tempToken="cl-recovery"
					onResult={onResult}
					testid="cl-recovery"
				/>
			) as ReactElement,
		);

		// Act
		await user.type(screen.getByTestId("cl-recovery"), "abcdefghj0");
		await user.click(screen.getByRole("button", { name: /usar codigo/i }));

		// Assert
		await waitFor(() => {
			expect(toastErrorMock).toHaveBeenCalledWith(
				"Necesitas un factor fuerte para usar un codigo de recuperacion",
			);
		});
		expect(onResult).not.toHaveBeenCalled();
	});

	it("Given checklist consume devuelve error NO-403 When submit Then muestra toast generico (error.message)", async () => {
		// Arrange: 400 -> rama onError generica (toast.error(error.message)).
		server.use(
			http.post(`${API}/auth`, () =>
				HttpResponse.json(
					{
						error: "INVALID_RECOVERY_CODE",
						code: 4001,
						message: "Codigo malo",
					},
					{ status: 400 },
				),
			),
		);
		const onResult = vi.fn();
		const user = userEvent.setup();
		render(
			(
				<RecoveryCodeInput
					tempToken="cl-recovery"
					onResult={onResult}
					testid="cl-recovery"
				/>
			) as ReactElement,
		);

		// Act
		await user.type(screen.getByTestId("cl-recovery"), "abcdefghj0");
		await user.click(screen.getByRole("button", { name: /usar codigo/i }));

		// Assert: el toast lleva el mensaje del ApiError.
		await waitFor(() => {
			expect(toastErrorMock).toHaveBeenCalledWith("Codigo malo");
		});
		expect(onResult).not.toHaveBeenCalled();
	});
});

describe("WebAuthnLoginButton (modo checklist)", () => {
	beforeEach(() => {
		useAuthStore.getState().reset();
		startAuthenticationMock.mockReset();
		toastErrorMock.mockClear();
	});

	it("Given email+onResult When se monta Then NO pide email (solo el boton de passkey)", () => {
		// Arrange / Act: el modo checklist renderiza solo el boton (rama 71-79).
		render(
			(
				<WebAuthnLoginButton
					email="user@test.com"
					onResult={vi.fn()}
					testid="cl-webauthn"
				/>
			) as ReactElement,
		);

		// Assert: el input de email del modo standalone NO existe.
		expect(screen.getByTestId("cl-webauthn")).toBeInTheDocument();
		expect(screen.queryByLabelText(/email \(para passkey\)/i)).toBeNull();
	});

	it("Given email+onResult When click Then runPasskey usa mutateAsync y entrega el result (sin tokens)", async () => {
		// Arrange: startAuthentication resuelve -> login-verify devuelve authPair.
		startAuthenticationMock.mockResolvedValueOnce(FAKE_RESPONSE);
		const onResult = vi.fn();
		const user = userEvent.setup();
		render(
			(
				<WebAuthnLoginButton
					email="user@test.com"
					onResult={onResult}
					testid="cl-webauthn"
				/>
			) as ReactElement,
		);

		// Act
		await user.click(screen.getByTestId("cl-webauthn"));

		// Assert: onResult recibe el VerifyResult; el store NO se toca (silent).
		await waitFor(() => {
			expect(onResult).toHaveBeenCalledTimes(1);
		});
		const result = onResult.mock.calls[0]?.[0] as VerifyResult;
		expect("access_token" in result).toBe(true);
		expect(useAuthStore.getState().accessToken).toBe(null);
	});

	it("Given email+onResult When startAuthentication lanza Then entra al catch (toast) y NO llama onResult", async () => {
		// Arrange: el browser cancela -> runPasskey lanza -> catch en onUsePasskey.
		startAuthenticationMock.mockRejectedValueOnce(new Error("cancelado"));
		const onResult = vi.fn();
		const user = userEvent.setup();
		render(
			(
				<WebAuthnLoginButton
					email="user@test.com"
					onResult={onResult}
					testid="cl-webauthn"
				/>
			) as ReactElement,
		);

		// Act
		await user.click(screen.getByTestId("cl-webauthn"));

		// Assert
		await waitFor(() => {
			expect(toastErrorMock).toHaveBeenCalledWith(
				"No pudimos iniciar el login con passkey",
			);
		});
		expect(onResult).not.toHaveBeenCalled();
	});
});
