import { render, screen } from "@tests/utils/render";
import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";
import { SecurityOverviewPanel } from "@/features/settings/components/security-overview-panel";
import type { SecurityMethod } from "@/types/models";

/**
 * @module tests/unit/features/settings/components/security-overview-emailcode-listed
 * @description Verifica que el panel unificado SI renderiza la fila del metodo
 *   `email_code` (estado activo/inactivo + requerido + configurar), igual que
 *   el resto de los metodos. (Antes se filtraba; el usuario pidio listarlo.)
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
	EmailCodeSetup: () => <div>email-code-setup-stub</div>,
	useDeleteCredential: () => ({ mutate: vi.fn(), isPending: false }),
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
					detail: { confirmed: true },
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

vi.mock("@/features/settings/hooks/use-delete-method", () => ({
	useDeleteMethod: () => ({ mutate: vi.fn(), isPending: false }),
}));

describe("SecurityOverviewPanel email_code listado", () => {
	it("Given un method email_code en el overview When render Then SI renderiza su fila (label + switch requerido)", () => {
		// Arrange + Act
		render((<SecurityOverviewPanel />) as ReactElement);

		// Assert: email_code aparece como una fila mas, con su control requerido.
		expect(screen.getByText(/codigo por email/i)).toBeInTheDocument();
		expect(screen.getByTestId("security-row-email_code")).toBeInTheDocument();
		// y TOTP sigue listado.
		expect(screen.getByText("TOTP")).toBeInTheDocument();
	});
});
