import {
	render,
	screen,
	userEvent,
	waitFor,
	within,
} from "@tests/utils/render";
import type { ReactElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { LoginChecklist } from "@/features/auth/components/login-checklist";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import type { MethodRequired } from "@/types/api";

/**
 * @module tests/unit/features/auth/components/login-checklist
 * @description Tests del checklist de login (metodos `required`): renderiza un
 *   input por metodo, marca cada factor completado, el tempToken es ROLLING
 *   (el verify del siguiente metodo usa el temp_token NUEVO), cierra el login
 *   con AuthResponse (setTokens + router.replace), permite cualquier orden,
 *   maneja el email_code (envio previo) y el link de recovery.
 */

const { replaceMock } = vi.hoisted(() => ({ replaceMock: vi.fn() }));
vi.mock("next/navigation", () => ({
	useRouter: () => ({ push: vi.fn(), replace: replaceMock }),
}));

const PASSWORD_TOTP: MethodRequired[] = [
	{
		type: "password",
		input: "password",
		sent: null,
		dispatch_action: "verify-password",
	},
	{ type: "totp", input: "code6", sent: null, dispatch_action: "verify-totp" },
];

const EMAIL_CODE: MethodRequired[] = [
	{
		type: "email_code",
		input: "code8",
		sent: false,
		dispatch_action: "send-email-code",
	},
];

/** El card de un metodo se ubica por el testid de su input. */
function passwordCard(): HTMLElement {
	return screen
		.getByTestId("checklist-password")
		.closest("div.rounded-lg") as HTMLElement;
}

function totpCard(): HTMLElement {
	return screen
		.getByTestId("checklist-totp")
		.closest("div.rounded-lg") as HTMLElement;
}

async function submitPassword(): Promise<void> {
	const user = userEvent.setup();
	await user.type(screen.getByTestId("checklist-password"), "a-strong-pass-12");
	await user.click(
		within(passwordCard()).getByRole("button", { name: /continuar/i }),
	);
}

async function submitTotp(): Promise<void> {
	const user = userEvent.setup();
	await user.type(screen.getByTestId("checklist-totp"), "123456");
	await user.click(
		within(totpCard()).getByRole("button", { name: /^verificar$/i }),
	);
}

describe("LoginChecklist", () => {
	beforeEach(() => {
		replaceMock.mockClear();
		useAuthStore.getState().reset();
	});

	it("Given methods_required password+totp When se monta Then un input por metodo y 0 de 2", () => {
		// Arrange / Act
		render(
			(
				<LoginChecklist
					methodsRequired={PASSWORD_TOTP}
					initialTempToken="cl-step2-0"
					email="user@test.com"
					initialPending={["password", "totp"]}
				/>
			) as ReactElement,
		);

		// Assert: progreso inicial + ambos inputs presentes
		expect(screen.getByTestId("checklist-progress")).toHaveTextContent(
			"0 de 2 completados",
		);
		expect(screen.getByTestId("checklist-password")).toBeInTheDocument();
		expect(screen.getByTestId("checklist-totp")).toBeInTheDocument();
	});

	it("Given password completado When verify devuelve totp pendiente Then 1 de 2 y rolling token", async () => {
		// Arrange
		render(
			(
				<LoginChecklist
					methodsRequired={PASSWORD_TOTP}
					initialTempToken="cl-step2-0"
					email="user@test.com"
					initialPending={["password", "totp"]}
				/>
			) as ReactElement,
		);

		// Act: el verify-password (temp cl-step2-0) devuelve cl-step2-1 + [totp].
		await submitPassword();

		// Assert: password satisfecho -> 1 de 2 completados.
		await waitFor(() => {
			expect(screen.getByTestId("checklist-progress")).toHaveTextContent(
				"1 de 2 completados",
			);
		});
		// El temp ROLLING: el verify-totp exige el temp NUEVO (cl-step2-1). El
		// handler responde 200 (AuthResponse) SOLO si recibe cl-step2-1; si
		// recibiera el viejo cl-step2-0, caeria al branch de rotacion (deja
		// password pendiente) y NO cerraria el login.
		await submitTotp();
		await waitFor(() => {
			expect(replaceMock).toHaveBeenCalledWith("/");
		});
	});

	it("Given el ultimo metodo When verify devuelve AuthResponse Then setTokens + replace(dashboard)", async () => {
		// Arrange
		render(
			(
				<LoginChecklist
					methodsRequired={PASSWORD_TOTP}
					initialTempToken="cl-step2-0"
					email="user@test.com"
					initialPending={["password", "totp"]}
				/>
			) as ReactElement,
		);

		// Act: password -> totp (cierra con mfa_complete)
		await submitPassword();
		await waitFor(() => {
			expect(screen.getByTestId("checklist-progress")).toHaveTextContent(
				"1 de 2 completados",
			);
		});
		await submitTotp();

		// Assert: tokens seteados + navegacion a la raiz del admin
		await waitFor(() => {
			expect(useAuthStore.getState().accessToken).not.toBe(null);
		});
		expect(replaceMock).toHaveBeenCalledWith("/");
	});

	it("Given cualquier orden When totp primero luego password Then cierra el login", async () => {
		// Arrange
		render(
			(
				<LoginChecklist
					methodsRequired={PASSWORD_TOTP}
					initialTempToken="cl-step2-0"
					email="user@test.com"
					initialPending={["password", "totp"]}
				/>
			) as ReactElement,
		);

		// Act: totp PRIMERO (temp cl-step2-0 -> rota a cl-step2-tp + [password]).
		await submitTotp();
		await waitFor(() => {
			expect(screen.getByTestId("checklist-progress")).toHaveTextContent(
				"1 de 2 completados",
			);
		});
		// Luego password con el temp rotado (cl-step2-tp) -> cierra el login.
		await submitPassword();

		// Assert
		await waitFor(() => {
			expect(replaceMock).toHaveBeenCalledWith("/");
		});
		expect(useAuthStore.getState().accessToken).not.toBe(null);
	});

	it("Given metodo email_code When click Enviar codigo Then envia y luego verify-code cierra", async () => {
		// Arrange: un solo metodo email_code (sent:false -> boton de envio).
		const user = userEvent.setup();
		render(
			(
				<LoginChecklist
					methodsRequired={EMAIL_CODE}
					initialTempToken="cl-email-0"
					email="user@test.com"
					initialPending={["email-code"]}
				/>
			) as ReactElement,
		);

		// Act: enviar el code (send-email-code) -> el boton de envio desaparece.
		await user.click(screen.getByTestId("checklist-send-code"));
		await waitFor(() => {
			expect(
				screen.queryByTestId("checklist-send-code"),
			).not.toBeInTheDocument();
		});
		// Luego ingresar el code de 8 chars -> verify-code cierra el login.
		await user.type(screen.getByTestId("checklist-email-code"), "ABCDEFGH");
		await user.click(screen.getByRole("button", { name: /^verificar$/i }));

		// Assert
		await waitFor(() => {
			expect(replaceMock).toHaveBeenCalledWith("/");
		});
	});

	it("Given el link de recuperacion When click Then muestra el RecoveryCodeInput", async () => {
		// Arrange
		const user = userEvent.setup();
		render(
			(
				<LoginChecklist
					methodsRequired={PASSWORD_TOTP}
					initialTempToken="cl-step2-0"
					email="user@test.com"
					initialPending={["password", "totp"]}
				/>
			) as ReactElement,
		);

		// Act
		await user.click(screen.getByTestId("checklist-use-recovery"));

		// Assert: aparece el input de recovery (10 chars) y el titulo (heading)
		expect(screen.getByTestId("checklist-recovery")).toBeInTheDocument();
		expect(
			screen.getByRole("heading", { name: /codigo de recuperacion/i }),
		).toBeInTheDocument();
	});
});
