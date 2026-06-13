import { render, screen, waitFor } from "@tests/utils/render";
import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";
import { TurnstileWidget } from "@/features/auth/components/turnstile-widget";

/**
 * @module tests/unit/features/auth/components/turnstile-widget-bypass
 * @description Verifica el modo E2E del widget (NEXT_PUBLIC_E2E_BYPASS=true):
 *   NO renderiza el Turnstile real, monta el placeholder oculto y auto-emite
 *   el token sentinel '' para habilitar el submit (el bypass real viaja en
 *   el header que inyecta apiFetch).
 */

vi.mock("@/lib/env", () => ({
	env: {
		NEXT_PUBLIC_API_ENDPOINT: "https://api.test.the-full-stack.com",
		NEXT_PUBLIC_TURNSTILE_SITEKEY: "1x00000000000000000000AA",
		NEXT_PUBLIC_ADMIN_URL: "https://admin.test.the-full-stack.com",
		NEXT_PUBLIC_AUTH_REFRESH_LEAD_MS: 30_000,
		NEXT_PUBLIC_WEBAUTHN_RP_ID: "admin.test.the-full-stack.com",
		NEXT_PUBLIC_FEATURE_MFA: "true",
		NEXT_PUBLIC_E2E_BYPASS: "true",
	},
}));

vi.mock("@marsidev/react-turnstile", () => ({
	Turnstile: () => <div data-testid="turnstile-real" />,
}));

describe("TurnstileWidget (modo E2E bypass)", () => {
	it("Given E2E_BYPASS=true When se renderiza Then monta el placeholder y auto-emite token vacio", async () => {
		// Arrange
		const onToken = vi.fn();

		// Act
		render((<TurnstileWidget onToken={onToken} />) as ReactElement);

		// Assert: sin widget real, placeholder oculto + token sentinel ''.
		expect(screen.getByTestId("turnstile-e2e-bypass")).toBeInTheDocument();
		expect(screen.queryByTestId("turnstile-real")).not.toBeInTheDocument();
		await waitFor(() => {
			expect(onToken).toHaveBeenCalledWith("");
		});
	});
});
