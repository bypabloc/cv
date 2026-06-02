import { HttpResponse, http } from "msw";

const API = "https://api.test.the-full-stack.com";

interface UsersBody {
	operation: string;
	action: string;
	[key: string]: unknown;
}

const PROFILE = {
	id: "usr_01",
	email: "user@test.com",
	display_name: "Pablo",
	status: "active" as const,
	locale: "es" as const,
	timezone: "America/Santiago",
	marketing_consent: false,
	created_at: "2026-01-01T00:00:00Z",
};

const SESSIONS = [
	{
		session_id: "sess_current",
		family_id: "fam_01",
		ip: "190.0.0.1",
		user_agent: "Mozilla/5.0 (Chrome)",
		created_at: "2026-05-01T10:00:00Z",
		last_seen_at: "2026-05-27T10:00:00Z",
		is_current: true,
	},
	{
		session_id: "sess_other",
		family_id: "fam_02",
		ip: "190.0.0.2",
		user_agent: "Mozilla/5.0 (Safari iPhone)",
		created_at: "2026-05-10T10:00:00Z",
		last_seen_at: "2026-05-26T10:00:00Z",
		is_current: false,
	},
];

const ADMIN_USERS = [
	{
		user_id: "usr_01",
		email: "user@test.com",
		display_name: "Pablo",
		status: "active" as const,
		created_at: "2026-01-01T00:00:00Z",
		total_mfa: 2,
	},
	{
		user_id: "usr_02",
		email: "other@test.com",
		display_name: null,
		status: "disabled" as const,
		created_at: "2026-02-01T00:00:00Z",
		total_mfa: 0,
	},
];

/**
 * @module tests/mocks/handlers/users
 * @description MSW handlers de `/users` (profile/status/admin). Replican el
 *   contrato del Lambda users desplegado, incluyendo la action NUEVA
 *   profile.change-password.
 */
export const usersHandlers = [
	http.post(`${API}/users`, async ({ request }) => {
		const body = (await request.json()) as UsersBody;
		// Contrato FLAT del backend: campos al nivel raiz, no anidados en
		// `data`. `data` = todo menos operation/action.
		const { operation, action, ...data } = body;

		// --- profile ---
		if (operation === "profile" && action === "get") {
			return HttpResponse.json({
				is_valid: true,
				code: 0,
				data: { profile: PROFILE },
			});
		}
		if (operation === "profile" && action === "update") {
			return HttpResponse.json({
				is_valid: true,
				code: 0,
				data: {
					profile: { ...PROFILE, display_name: data.display_name as string },
				},
			});
		}
		if (operation === "profile" && action === "change-email") {
			return HttpResponse.json({
				is_valid: true,
				code: 0,
				data: { request_id: "req_01", expires_in: 900 },
			});
		}
		if (operation === "profile" && action === "confirm-email-change") {
			return HttpResponse.json({ is_valid: true, code: 0, data: { ok: true } });
		}
		if (operation === "profile" && action === "change-password") {
			if (data.current_password === "wrong-current-pass") {
				return HttpResponse.json(
					{
						error: "INVALID_PASSWORD",
						code: 4005,
						message: "Contrasena actual incorrecta",
					},
					{ status: 401 },
				);
			}
			return HttpResponse.json({ is_valid: true, code: 0, data: { ok: true } });
		}
		if (operation === "profile" && action === "delete-account") {
			return HttpResponse.json({ is_valid: true, code: 0, data: { ok: true } });
		}

		// --- status ---
		if (operation === "status" && action === "get") {
			return HttpResponse.json({
				is_valid: true,
				code: 0,
				data: {
					user_id: "usr_01",
					status: "active",
					current_session_id: "sess_current",
				},
			});
		}
		if (operation === "status" && action === "list-sessions") {
			return HttpResponse.json({
				is_valid: true,
				code: 0,
				data: { sessions: SESSIONS },
			});
		}
		if (operation === "status" && action === "revoke-session") {
			if (data.session_id === "sess_current") {
				return HttpResponse.json(
					{
						error: "CANNOT_REVOKE_CURRENT_SESSION",
						code: 4002,
						message: "No puedes revocar la sesion actual",
					},
					{ status: 400 },
				);
			}
			return HttpResponse.json({ is_valid: true, code: 0, data: { ok: true } });
		}

		// --- admin ---
		if (operation === "admin" && action === "list-users") {
			return HttpResponse.json({
				is_valid: true,
				code: 0,
				data: {
					users: ADMIN_USERS,
					page: 1,
					page_size: 50,
					total: ADMIN_USERS.length,
				},
			});
		}
		if (operation === "admin" && action === "get-user") {
			const found = ADMIN_USERS.find((u) => u.user_id === data.user_id);
			if (!found) {
				return HttpResponse.json(
					{ error: "NOT_FOUND", code: 4040 },
					{ status: 404 },
				);
			}
			return HttpResponse.json({
				is_valid: true,
				code: 0,
				data: { user: found },
			});
		}
		if (
			operation === "admin" &&
			["disable-user", "enable-user", "delete-user", "force-logout"].includes(
				action,
			)
		) {
			return HttpResponse.json({ is_valid: true, code: 0, data: { ok: true } });
		}
		if (operation === "admin" && action === "list-admin-actions") {
			return HttpResponse.json({
				is_valid: true,
				code: 0,
				data: {
					actions: [
						{
							action_id: "act_01",
							actor_user_id: "usr_01",
							target_user_id: "usr_02",
							action: "disable-user",
							created_at: "2026-05-20T10:00:00Z",
						},
					],
				},
			});
		}

		return HttpResponse.json(
			{ error: "NOT_IMPLEMENTED", code: 5010 },
			{ status: 501 },
		);
	}),
];
