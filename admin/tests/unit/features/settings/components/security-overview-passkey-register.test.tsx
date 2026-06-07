import { render, screen } from "@tests/utils/render";
import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";
import { SecurityOverviewPanel } from "@/features/settings/components/security-overview-panel";
import type { SecurityMethod } from "@/types/models";

/**
 * @module tests/unit/features/settings/components/security-overview-passkey-register
 * @description Verifica que la fila webauthn del panel monta el boton para
 *   registrar un passkey nuevo (WebAuthnRegisterButton).
 */

function method(overrides: Partial<SecurityMethod>): SecurityMethod {
	return {
		type: "webauthn",
		label: "Llaves de acceso",
		configured: false,
		enabled: false,
		required: false,
		preferred: false,
		created_at: null,
		last_used_at: null,
		detail: { credentials: [] },
		...overrides,
	};
}

vi.mock("@/features/auth", () => ({
	WebAuthnRegisterButton: () => (
		<button type="button">Registrar passkey</button>
	),
	TotpSetup: () => <div>totp-setup-stub</div>,
}));

vi.mock("@/features/settings/hooks/use-security-overview", () => ({
	useSecurityOverview: () => ({
		isLoading: false,
		isError: false,
		data: { methods: [method({})] },
	}),
}));

vi.mock("@/features/settings/hooks/use-toggle-method", () => ({
	useToggleMethod: () => ({ mutate: vi.fn(), isPending: false }),
}));

vi.mock("@/features/settings/hooks/use-set-required", () => ({
	useSetRequired: () => ({ mutate: vi.fn(), isPending: false }),
}));

describe("SecurityOverviewPanel webauthn register", () => {
	it("Given un method webauthn sin credenciales When render Then muestra el boton Registrar passkey", () => {
		// Arrange + Act
		render((<SecurityOverviewPanel />) as ReactElement);

		// Assert
		expect(
			screen.getByRole("button", { name: /registrar passkey/i }),
		).toBeInTheDocument();
	});
});
