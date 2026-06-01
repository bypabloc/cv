import type {
	AuthenticationResponseJSON,
	RegistrationResponseJSON,
} from "@simplewebauthn/browser";
import { render, screen, userEvent, waitFor } from "@tests/utils/render";
import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";
import { WebAuthnLoginButton } from "@/features/auth/components/webauthn-login-button";
import { WebAuthnRegisterButton } from "@/features/auth/components/webauthn-register-button";
import { useAuthStore } from "@/features/auth/store/use-auth-store";

/**
 * @module tests/unit/features/auth/components/webauthn-buttons
 * @description Verifica que los botones WebAuthn pasen las options del backend
 *   a startRegistration/startAuthentication y reenvien el response.
 */

vi.mock("next/navigation", () => ({
	useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

const { startRegistrationMock, startAuthenticationMock } = vi.hoisted(() => ({
	startRegistrationMock: vi.fn(),
	startAuthenticationMock: vi.fn(),
}));
vi.mock("@simplewebauthn/browser", () => ({
	startRegistration: startRegistrationMock,
	startAuthentication: startAuthenticationMock,
}));

const REG_RESPONSE = { id: "reg" } as unknown as RegistrationResponseJSON;
const AUTH_RESPONSE = { id: "auth" } as unknown as AuthenticationResponseJSON;

describe("WebAuthnRegisterButton", () => {
	it("Given options del backend When click Then startRegistration recibe optionsJSON", async () => {
		startRegistrationMock.mockResolvedValue(REG_RESPONSE);
		const user = userEvent.setup();
		render((<WebAuthnRegisterButton />) as ReactElement);

		await user.click(screen.getByRole("button", { name: /agregar passkey/i }));

		await waitFor(() => {
			expect(startRegistrationMock).toHaveBeenCalledTimes(1);
		});
		const arg = startRegistrationMock.mock.calls[0]?.[0] as {
			optionsJSON: { challenge: string };
		};
		expect(arg.optionsJSON.challenge).toBe("fake");
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
