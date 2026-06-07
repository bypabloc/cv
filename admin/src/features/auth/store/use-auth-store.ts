import { jwtDecode } from "jwt-decode";
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";
import type { User } from "@/types/models";

/**
 * @module use-auth-store
 * @description Store de auth (Zustand + persist).
 *
 * Persistencia:
 * - `refreshToken`, `refreshExpiry`, `user` -> localStorage (sobreviven reload).
 * - `accessToken` -> SOLO memoria (rota en cada refresh; persistirlo deja
 *   stale token tras reload).
 * - `tempToken` -> SOLO memoria (efimero, 5 min, flujo register/login).
 *
 * Lazy auth: al reload `accessToken === null`; `useSessionRehydrate` hace UN
 * refresh silencioso desde el `refresh_token` para hidratar el access. NO hay
 * timer proactivo ni validacion del access: cada peticion HTTP descubre su
 * 401 en el `api-client` centralizado.
 */

interface AuthState {
	accessToken: string | null;
	refreshToken: string | null;
	refreshExpiry: number | null;
	tempToken: string | null;
	user: User | null;

	setTokens: (
		access: string,
		refresh: string,
		user?: User | null,
		refreshExpiry?: number | null,
	) => void;
	setAccessToken: (token: string | null) => void;
	setRefreshToken: (token: string | null) => void;
	setTempToken: (token: string | null) => void;
	setUser: (user: User | null) => void;
	clearTokens: () => void;
	reset: () => void;

	isAuthenticated: () => boolean;
	isAccessExpired: () => boolean;
}

function decodeExp(token: string): number | null {
	try {
		const { exp } = jwtDecode<{ exp: number }>(token);
		return exp * 1000;
	} catch {
		return null;
	}
}

// EMPTY limpia los tokens/user (logout, clear, reset).
const EMPTY = {
	accessToken: null,
	refreshToken: null,
	refreshExpiry: null,
	tempToken: null,
	user: null,
} as const;

export const useAuthStore = create<AuthState>()(
	persist(
		(set, get) => ({
			...EMPTY,

			// `user` es opcional: algunos cierres del login (checklist) NO
			// re-envian el perfil. Cuando llega `undefined`, se conserva el user
			// actual (el bootstrap/refresh lo hidrata); `null` lo limpia.
			setTokens: (access, refresh, user, refreshExpiry) =>
				set((state) => ({
					accessToken: access,
					refreshToken: refresh,
					user: user === undefined ? state.user : user,
					refreshExpiry: refreshExpiry ?? decodeExp(refresh),
				})),
			setAccessToken: (token) => set({ accessToken: token }),
			setRefreshToken: (token) =>
				set({
					refreshToken: token,
					refreshExpiry: token ? decodeExp(token) : null,
				}),
			setTempToken: (token) => set({ tempToken: token }),
			setUser: (user) => set({ user }),
			clearTokens: () => set({ ...EMPTY }),
			reset: () => set({ ...EMPTY }),

			// La sesion vive si hay un access JWT valido y no expirado. NO se
			// exige `user`: es solo data de perfil para la UI, y el
			// `/session/refresh` NO lo devuelve (solo access+refresh). Exigir
			// `user` rompia la persistencia tras reload cuando el storage no lo
			// tenia (entrada vieja/parcial) aunque el refresh hubiera hidratado
			// un access valido -> redirect erroneo a /login.
			isAuthenticated: () => {
				const { accessToken } = get();
				if (!accessToken) return false;
				return !get().isAccessExpired();
			},

			isAccessExpired: () => {
				const { accessToken } = get();
				if (!accessToken) return true;
				const exp = decodeExp(accessToken);
				if (exp === null) return true;
				return Date.now() >= exp;
			},
		}),
		{
			name: "portfolio-admin-auth",
			storage: createJSONStorage(() => localStorage),
			partialize: (state) => ({
				refreshToken: state.refreshToken,
				refreshExpiry: state.refreshExpiry,
				user: state.user,
			}),
		},
	),
);
