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
		return {
			...rest,
			headers,
			body: body !== undefined ? JSON.stringify(body) : undefined,
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

	return data as T;
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
			body: JSON.stringify({
				operation: "session",
				action: "refresh",
				data: { refresh_token: refreshToken },
			}),
		});
		if (!response.ok) return false;
		const json = (await response.json()) as {
			data?: {
				access_token?: string;
				refresh_token?: string;
				expires_in?: number;
			};
		};
		const access = json.data?.access_token;
		const refresh = json.data?.refresh_token;
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
