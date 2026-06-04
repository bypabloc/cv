import { render, screen } from "@tests/utils/render";
import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";
import { SecurityOverviewPanel } from "@/features/settings/components/security-overview-panel";
import type { SecurityMethod } from "@/types/models";

/**
 * @module tests/unit/features/settings/components/security-overview-no-emailcode
 * @description Verifica que el panel unificado NO renderiza una fila para el
 *   metodo `email_code` (es el canal de entrada del login, no un metodo
 *   configurable), pero SI renderiza el resto (ej. totp).
 */

function method(overrides: Partial<SecurityMethod>): SecurityMethod {
	return {
		type: "totp",
		label: "TOTP",
		configured: false,
		enabled: false,
		required: false,
		preferred: false,
		created_at: null,
		last_used_at: null,
		detail: {},
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
		data: {
			methods: [
				method({
					type: "email_code",
					label: "Codigo por email",
					configured: true,
					enabled: true,
				}),
				method({ type: "totp", label: "TOTP", configured: false }),
			],
		},
	}),
}));

vi.mock("@/features/settings/hooks/use-toggle-method", () => ({
	useToggleMethod: () => ({ mutate: vi.fn(), isPending: false }),
}));

vi.mock("@/features/settings/hooks/use-set-required", () => ({
	useSetRequired: () => ({ mutate: vi.fn(), isPending: false }),
}));

describe("SecurityOverviewPanel email_code filtering", () => {
	it("Given un method email_code en el overview When render Then NO renderiza su fila pero SI la de TOTP", () => {
		// Arrange + Act
		render((<SecurityOverviewPanel />) as ReactElement);

		// Assert: el panel filtra email_code (no aparece su label)
		expect(screen.queryByText(/codigo por email/i)).toBeNull();
		// pero TOTP si se lista
		expect(screen.getByText("TOTP")).toBeInTheDocument();
	});
});
