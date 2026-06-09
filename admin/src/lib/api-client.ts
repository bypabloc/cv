import { broadcastAuth } from "@/features/auth/lib/broadcast";
import { withRefreshMutex } from "@/features/auth/lib/refresh-mutex";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import { env } from "./env";

/**
 * @module api-client
 * @description Fetch wrapper de los Lambdas. Agrega el Bearer del access JWT,
 *   maneja 401 con UN solo `/session/refresh` in-flight (mutex), y reintenta
 *   el request con el token rotado. El refresh token viaja en el BODY (SPA
 *   cross-origin, sin cookies). Ver decision 4 del plan a-admin.
 */

interface FetchOptions extends Omit<RequestInit, "body"> {
	body?: unknown;
	skipAuth?: boolean;
	skipRefresh?: boolean;
}

/**
 * @function flattenBody
 * @description El handler HTTP generico del backend (shared.lambda_kit.
 *   http_dispatch) espera el contrato FLAT: `{operation, action, ...campos}`
 *   con los campos del payload al NIVEL RAIZ del body, NO anidados en `data`.
 *   El cliente arma `{operation, action, data}` por ergonomia; aqui se
 *   aplana a `{operation, action, ...data}` antes de serializar. Enviar el
 *   `data` anidado hace que el backend lo trate como un campo llamado "data"
 *   -> el modelo Pydantic no encuentra `email`/`code`/etc -> INVALID_EVENT_DATA.
 */
function flattenBody(body: unknown): unknown {
	if (
		body !== null &&
		typeof body === "object" &&
		"operation" in body &&
		"action" in body &&
		"data" in body
	) {
		const { operation, action, data } = body as {
			operation: unknown;
			action: unknown;
			data: unknown;
		};
		const flatData = data !== null && typeof data === "object" ? data : {};
		return { operation, action, ...flatData };
	}
	return body;
}

/**
 * @function e2eBypassToken
 * @description SOLO E2E: cuando `NEXT_PUBLIC_E2E_BYPASS === 'true'`, devuelve el
 *   bypass token Ed25519 firmado que el spec Playwright inyecta en
 *   `window.__E2E_BYPASS_TOKEN__`. apiFetch lo manda en el header
 *   `X-Turnstile-Bypass-Token`; el backend dev acepta el bypass cuando
 *   `cf_turnstile_response` viaja vacio. En cualquier build que no sea E2E
 *   devuelve null (el bypass nunca se activa). Prod rechaza el bypass aunque
 *   llegue el header.
 */
function e2eBypassToken(): string | null {
	if (env.NEXT_PUBLIC_E2E_BYPASS !== "true") return null;
	if (typeof window === "undefined") return null;
	const token = (window as { __E2E_BYPASS_TOKEN__?: unknown })
		.__E2E_BYPASS_TOKEN__;
	return typeof token === "string" && token.length > 0 ? token : null;
}

export class ApiError extends Error {
	constructor(
		public readonly status: number,
		public readonly code: number,
		message: string,
		public readonly data?: unknown,
	) {
		super(message);
		this.name = "ApiError";
	}
}

async function parseBody(response: Response): Promise<unknown> {
	const text = await response.text();
	if (!text) return null;
	try {
		return JSON.parse(text);
	} catch {
		return text;
	}
}

export async function apiFetch<T = unknown>(
	endpoint: string,
	options: FetchOptions = {},
): Promise<T> {
	const {
		skipAuth = false,
		skipRefresh = false,
		body,
		headers: extraHeaders,
		...rest
	} = options;
	const url = `${env.NEXT_PUBLIC_API_ENDPOINT}${endpoint}`;

	const buildInit = (): RequestInit => {
		const headers = new Headers(extraHeaders);
		headers.set("Content-Type", "application/json");
		if (!skipAuth) {
			const token = useAuthStore.getState().accessToken;
			if (token) headers.set("Authorization", `Bearer ${token}`);
		}
		const bypass = e2eBypassToken();
		if (bypass) headers.set("X-Turnstile-Bypass-Token", bypass);
		return {
			...rest,
			headers,
			body: body !== undefined ? JSON.stringify(flattenBody(body)) : undefined,
		};
	};

	let response = await fetch(url, buildInit());

	if (response.status === 401 && !skipAuth && !skipRefresh) {
		const refreshed = await withRefreshMutex(performRefresh);
		if (refreshed) {
			response = await fetch(url, buildInit());
		} else {
			performLocalLogout();
			throw new ApiError(401, 4011, "Sesion expirada", null);
		}
	}

	const data = await parseBody(response);

	if (!response.ok) {
		const payload = (data ?? {}) as {
			error?: string;
			code?: number;
			message?: string;
		};
		throw new ApiError(
			response.status,
			payload.code ?? response.status,
			payload.message ?? payload.error ?? `HTTP ${response.status}`,
			data,
		);
	}

	// El backend responde FLAT: el body ES el payload del controller (NO un
	// wrapper {is_valid, code, data} — ver shared.lambda_kit.http_dispatch,
	// json_response(status, result.data)). El resto del admin tipa las
	// respuestas como Envelope<T> = {is_valid, code, data} por ergonomia;
	// aqui se re-envuelve la respuesta flat en ese shape para no tocar las
	// 26 actions ni los hooks. Si el backend YA devolviera el wrapper (futuro
	// o un endpoint legacy), se respeta tal cual.
	if (
		data !== null &&
		typeof data === "object" &&
		"is_valid" in data &&
		"data" in data
	) {
		return data as T;
	}
	return { is_valid: true, code: 0, data } as T;
}

/**
 * @function performRefresh
 * @description Rota la sesion via `/auth` session.refresh con el refresh
 *   token del store. El backend devuelve access + refresh nuevos (rota la
 *   familia). Devuelve true si tuvo exito. NUNCA pasa por el mutex de
 *   apiFetch (se llama directo con fetch).
 */
async function performRefresh(): Promise<boolean> {
	try {
		const refreshToken = useAuthStore.getState().refreshToken;
		if (!refreshToken) return false;
		const response = await fetch(`${env.NEXT_PUBLIC_API_ENDPOINT}/auth`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			// Contrato FLAT del backend: refresh_token al nivel raiz.
			body: JSON.stringify({
				operation: "session",
				action: "refresh",
				refresh_token: refreshToken,
			}),
		});
		if (!response.ok) return false;
		// Respuesta FLAT del backend: {access_token, refresh_token, ...} al
		// nivel raiz (NO envuelto en .data).
		const json = (await response.json()) as {
			access_token?: string;
			refresh_token?: string;
			expires_in?: number;
		};
		const access = json.access_token;
		const refresh = json.refresh_token;
		if (!access || !refresh) return false;
		useAuthStore.getState().setAccessToken(access);
		useAuthStore.getState().setRefreshToken(refresh);
		return true;
	} catch {
		return false;
	}
}

function performLocalLogout(): void {
	useAuthStore.getState().reset();
	broadcastAuth({ type: "LOGOUT" });
}
