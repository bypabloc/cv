import { HttpResponse, http } from "msw";
import { makeJwt, nowSec } from "../jwt";

const API = "https://api.test.the-full-stack.com";

interface AuthBody {
	operation: string;
	action: string;
	[key: string]: unknown;
}

const MOCK_USER = {
	id: "usr_01",
	email: "user@test.com",
	status: "active" as const,
	has_password: true,
	mfa_methods: [] as ("totp" | "webauthn" | "email_code")[],
};

function authPair() {
	return {
		access_token: makeJwt({ sub: "usr_01", email: MOCK_USER.email }),
		refresh_token: makeJwt({
			sub: "usr_01",
			family_id: "fam_01",
			exp: nowSec() + 2_592_000,
		}),
		expires_in: 900,
		user: MOCK_USER,
	};
}

/**
 * @module tests/mocks/handlers/auth
 * @description MSW handlers de `/auth` (register/login/verify/session/mfa/
 *   webauthn). Replican el contrato del Lambda auth desplegado.
 */
export const authHandlers = [
	http.post(`${API}/auth`, async ({ request }) => {
		const body = (await request.json()) as AuthBody;
		// Contrato FLAT del backend (shared.lambda_kit.http_dispatch): los
		// campos del payload viajan al NIVEL RAIZ del body, no anidados en
		// `data`. `data` = todo menos operation/action (refleja el backend
		// real; antes los mocks asumian {operation,action,data} anidado, que
		// el backend NUNCA acepto -> los tests pasaban pero el real fallaba).
		const { operation, action, ...data } = body;

		// --- register ---
		if (operation === "register" && action === "start") {
			if (data.email === "exists@test.com") {
				return HttpResponse.json(
					{
						error: "EMAIL_ALREADY_REGISTERED",
						code: 4090,
						message: "Email ya registrado",
					},
					{ status: 409 },
				);
			}
			return HttpResponse.json(
				{
					is_valid: true,
					code: 0,
					data: { temp_token: "mock-temp", user_id: "usr_01", expires_in: 300 },
				},
				{ status: 201 },
			);
		}
		if (operation === "register" && action === "verify-code") {
			if (data.code === "12345678") {
				return HttpResponse.json({ is_valid: true, code: 0, data: authPair() });
			}
			return HttpResponse.json(
				{ error: "INVALID_CODE", code: 4001, message: "Codigo invalido" },
				{ status: 400 },
			);
		}

		// --- login ---
		if (operation === "login" && action === "check-email") {
			// Banderas FLAT (sin lista de metodos) + temp_token precheck. El
			// caller decide el paso 2 y manda el temp en Authorization a start.
			if (data.email === "unknown@test.com") {
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { exists: false, temp_token: "mock-precheck-token" },
				});
			}
			if (data.email === "blocked@test.com") {
				// unavailable: SIN temp (no hay flujo que continuar).
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { exists: true, unavailable: true },
				});
			}
			if (data.email === "passwordless@test.com") {
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: {
						exists: true,
						has_password: false,
						temp_token: "mock-precheck-token",
					},
				});
			}
			if (data.email === "checklist@test.com") {
				// Cuenta ACTIVE con metodos `required` (password + totp) -> el
				// caller pasa al CHECKLIST tras login.start. El orden de
				// methods_required es fijo (password, totp).
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: {
						exists: true,
						has_password: true,
						temp_token: "pre-cl",
						methods_required: [
							{
								type: "password",
								input: "password",
								sent: null,
								dispatch_action: "verify-password",
							},
							{
								type: "totp",
								input: "code6",
								sent: null,
								dispatch_action: "verify-totp",
							},
						],
					},
				});
			}
			if (data.email === "checklist-email@test.com") {
				// Cuenta ACTIVE con un solo metodo `required` email_code (requiere
				// envio previo del code: sent=false).
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: {
						exists: true,
						has_password: false,
						temp_token: "pre-cl-email",
						methods_required: [
							{
								type: "email_code",
								input: "code8",
								sent: false,
								dispatch_action: "send-email-code",
							},
						],
					},
				});
			}
			// Default: cuenta existente con password pero SIN metodos `required`
			// -> el flujo cae a passwordless (magic-link / code), no a un input
			// de password directo.
			return HttpResponse.json({
				is_valid: true,
				code: 0,
				data: {
					exists: true,
					has_password: true,
					temp_token: "mock-precheck-token",
				},
			});
		}
		if (operation === "login" && action === "start") {
			// login.start ya NO usa Turnstile: exige el temp precheck en
			// Authorization (lo emitio check-email). Sin el -> 401.
			const auth = request.headers.get("Authorization") ?? "";
			const precheck = auth.startsWith("Bearer ")
				? auth.slice("Bearer ".length).trim()
				: "";
			if (precheck === "") {
				return HttpResponse.json(
					{ is_valid: false, code: 4003, data: { error: "MISSING_PRECHECK" } },
					{ status: 401 },
				);
			}
			if (precheck === "pre-cl") {
				// Checklist password + totp: login.start abre el step=2 con la
				// lista de `methods` pendientes y un temp inicial (rolling).
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: {
						temp_token: "cl-step2-0",
						user_id: "usr_01",
						expires_in: 300,
						step: 2,
						mfa_complete: false,
						methods: ["password", "totp"],
					},
				});
			}
			if (precheck === "pre-cl-email") {
				// Checklist email_code: un solo metodo pendiente.
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: {
						temp_token: "cl-email-0",
						user_id: "usr_01",
						expires_in: 300,
						step: 2,
						mfa_complete: false,
						methods: ["email-code"],
					},
				});
			}
			if (data.email === "unknown@test.com") {
				// login.start CREA el user (registro fusionado): devuelve
				// temp_token + created. El 404 EMAIL_NOT_FOUND ya NO ocurre.
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: {
						temp_token: "mock-temp-created",
						user_id: "usr_new",
						expires_in: 300,
						created: true,
						methods: ["magic-link", "email-code"],
					},
				});
			}
			if (data.email === "mfa@test.com") {
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: {
						temp_token: "mock-temp-mfa",
						user_id: "usr_01",
						expires_in: 300,
						methods: ["totp"],
					},
				});
			}
			// Login con password directo: password incorrecta -> 401.
			if (data.password === "wrong-password-99") {
				return HttpResponse.json(
					{ is_valid: false, code: 4000, data: { error: "INVALID_PASSWORD" } },
					{ status: 401 },
				);
			}
			return HttpResponse.json({
				is_valid: true,
				code: 0,
				data: {
					temp_token: "mock-temp-login",
					user_id: "usr_01",
					expires_in: 300,
					methods: ["magic-link", "email-code"],
				},
			});
		}
		if (operation === "login" && action === "send-email-code") {
			return HttpResponse.json({ is_valid: true, code: 0, data: { ok: true } });
		}
		if (operation === "login" && action === "verify-code") {
			// Checklist email_code: el code 8-chars cierra el unico metodo
			// pendiente -> AuthResponse completo (mfa_complete).
			if (data.temp_token === "cl-email-0") {
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { ...authPair(), mfa_complete: true },
				});
			}
			return HttpResponse.json({ is_valid: true, code: 0, data: authPair() });
		}
		if (operation === "login" && action === "verify-password") {
			// Checklist (rolling): password como PRIMER factor. Recibe el temp
			// inicial cl-step2-0, marca password hecho y devuelve un temp NUEVO
			// cl-step2-1 (rolling) + el unico metodo pendiente (totp).
			if (data.temp_token === "cl-step2-0") {
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: {
						temp_token: "cl-step2-1",
						step: 2,
						mfa_complete: false,
						methods: ["totp"],
					},
				});
			}
			// Checklist (orden inverso): password como SEGUNDO factor. Recibe el
			// temp rotado por el totp previo (cl-step2-tp) -> cierra el login.
			if (data.temp_token === "cl-step2-tp") {
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { ...authPair(), mfa_complete: true },
				});
			}
			// Sin MFA -> AuthResponse directo (standalone / sin checklist).
			return HttpResponse.json({ is_valid: true, code: 0, data: authPair() });
		}
		if (operation === "login" && action === "verify-totp") {
			if (data.code === "000000") {
				return HttpResponse.json(
					{ error: "INVALID_TOTP", code: 4001, message: "Codigo invalido" },
					{ status: 400 },
				);
			}
			// Checklist (rolling): totp como ULTIMO factor. Exige el temp NUEVO
			// que devolvio verify-password (cl-step2-1, NO el inicial) -> cierra
			// el login con AuthResponse (mfa_complete).
			if (data.temp_token === "cl-step2-1") {
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { ...authPair(), mfa_complete: true },
				});
			}
			// Checklist (orden inverso): totp como PRIMER factor. Recibe el temp
			// inicial -> rota a cl-step2-tp y deja password pendiente.
			if (data.temp_token === "cl-step2-0") {
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: {
						temp_token: "cl-step2-tp",
						step: 2,
						mfa_complete: false,
						methods: ["password"],
					},
				});
			}
			return HttpResponse.json({ is_valid: true, code: 0, data: authPair() });
		}

		// --- verify ---
		if (operation === "verify" && action === "set-password") {
			return HttpResponse.json({ is_valid: true, code: 0, data: authPair() });
		}
		if (operation === "verify" && action === "resend-code") {
			return HttpResponse.json({ is_valid: true, code: 0, data: { ok: true } });
		}

		// --- session ---
		if (operation === "session" && action === "refresh") {
			const pair = authPair();
			return HttpResponse.json({
				is_valid: true,
				code: 0,
				data: {
					access_token: pair.access_token,
					refresh_token: pair.refresh_token,
					expires_in: 900,
				},
			});
		}
		if (operation === "session" && action === "logout") {
			return HttpResponse.json({ is_valid: true, code: 0, data: { ok: true } });
		}

		// --- mfa ---
		if (operation === "mfa" && action === "setup-totp") {
			return HttpResponse.json({
				is_valid: true,
				code: 0,
				data: {
					secret_b32: "JBSWY3DPEHPK3PXP",
					otpauth_url:
						"otpauth://totp/the-full-stack:user@test.com?secret=JBSWY3DPEHPK3PXP&issuer=the-full-stack",
				},
			});
		}
		if (operation === "mfa" && action === "confirm-totp") {
			return HttpResponse.json({
				is_valid: true,
				code: 0,
				data: {
					methods: [
						{
							kind: "totp",
							confirmed_at: new Date().toISOString(),
							is_preferred: true,
						},
					],
					webauthn_count: 0,
					total_mfa: 1,
				},
			});
		}
		if (operation === "mfa" && action === "setup-email-code") {
			return HttpResponse.json({
				is_valid: true,
				code: 0,
				data: {
					methods: [
						{
							kind: "email_code",
							confirmed_at: new Date().toISOString(),
							is_preferred: false,
						},
					],
					webauthn_count: 0,
					total_mfa: 1,
				},
			});
		}
		if (operation === "mfa" && action === "set-preferred") {
			return HttpResponse.json({
				is_valid: true,
				code: 0,
				data: {
					methods: [
						{
							kind: data.kind as string,
							confirmed_at: new Date().toISOString(),
							is_preferred: true,
						},
					],
					webauthn_count: 0,
					total_mfa: 1,
				},
			});
		}
		if (operation === "mfa" && action === "disable") {
			return HttpResponse.json(
				{
					error: "MUST_KEEP_ONE_MFA_METHOD",
					code: 4093,
					message: "Debes conservar al menos un metodo MFA",
				},
				{ status: 409 },
			);
		}
		if (operation === "mfa" && action === "list") {
			return HttpResponse.json({
				is_valid: true,
				code: 0,
				data: {
					methods: [
						{
							kind: "totp",
							confirmed_at: new Date().toISOString(),
							is_preferred: true,
						},
					],
					webauthn_count: 1,
					total_mfa: 2,
				},
			});
		}
		if (operation === "mfa" && action === "recovery-codes-generate") {
			return HttpResponse.json({
				is_valid: true,
				code: 0,
				data: {
					codes: Array.from(
						{ length: 10 },
						(_, i) => `RECOV${String(i).padStart(5, "0")}`,
					),
				},
			});
		}
		if (operation === "mfa" && action === "recovery-codes-consume") {
			return HttpResponse.json({ is_valid: true, code: 0, data: authPair() });
		}

		// --- webauthn ---
		if (operation === "webauthn" && action === "register-options") {
			return HttpResponse.json({
				is_valid: true,
				code: 0,
				data: {
					challenge_id: "chal_01",
					options: {
						challenge: "fake",
						rp: { id: "admin.test.the-full-stack.com", name: "admin" },
						user: {
							id: "dXNy",
							name: "user@test.com",
							displayName: "user@test.com",
						},
						pubKeyCredParams: [],
					},
				},
			});
		}
		if (operation === "webauthn" && action === "register-verify") {
			return HttpResponse.json({
				is_valid: true,
				code: 0,
				data: { methods: [], webauthn_count: 1, total_mfa: 1 },
			});
		}
		if (operation === "webauthn" && action === "login-options") {
			return HttpResponse.json({
				is_valid: true,
				code: 0,
				data: {
					challenge_id: "chal_02",
					options: {
						challenge: "fake",
						rpId: "admin.test.the-full-stack.com",
						allowCredentials: [],
					},
				},
			});
		}
		if (operation === "webauthn" && action === "login-verify") {
			return HttpResponse.json({ is_valid: true, code: 0, data: authPair() });
		}
		if (operation === "webauthn" && action === "list-credentials") {
			return HttpResponse.json({
				is_valid: true,
				code: 0,
				data: {
					credentials: [
						{
							id: "cred_01",
							nickname: "YubiKey",
							last_used_at: null,
							created_at: new Date().toISOString(),
						},
					],
				},
			});
		}
		if (operation === "webauthn" && action === "delete-credential") {
			return HttpResponse.json({
				is_valid: true,
				code: 0,
				data: { credentials: [] },
			});
		}

		// Soft-enable / set-required: el backend responde 204 (sin payload). El
		// cliente re-envuelve el body vacio en {is_valid:true, code:0, data:null}.
		const enableRequiredActions = new Set([
			"enable",
			"set-required",
			"disable",
		]);
		if (
			(operation === "mfa" || operation === "webauthn") &&
			enableRequiredActions.has(action)
		) {
			return new HttpResponse(null, { status: 204 });
		}

		return HttpResponse.json(
			{ error: "NOT_IMPLEMENTED", code: 5010 },
			{ status: 501 },
		);
	}),
];
