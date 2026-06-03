import { makeJwt, nowSec } from "@tests/mocks/jwt";
import { server } from "@tests/mocks/server";
import { render, screen, waitFor } from "@tests/utils/render";
import { delay, HttpResponse, http } from "msw";
import type { ReactElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AuthGuard } from "@/features/auth/components/auth-guard";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import type { User } from "@/types/models";

const API = "https://api.test.the-full-stack.com";

/**
 * @module tests/unit/features/auth/components/auth-guard-reload-repro
 * @description Reproduce el bug REAL "F5 -> /login": tras un reload el store se
 *   rehidrata SOLO de localStorage, el access es null, y el `/session/refresh`
 *   NO devuelve user (igual que prod). La sesion debe sostenerse en base al
 *   access JWT, INDEPENDIENTE de si `user` esta presente.
 */

const { replaceMock } = vi.hoisted(() => ({ replaceMock: vi.fn() }));
vi.mock("next/navigation", () => ({
	useRouter: () => ({ push: vi.fn(), replace: replaceMock }),
	usePathname: () => "/",
}));

const USER: User = {
	id: "019e8b33-6b48-7833-93d5-996d35d75fd5",
	email: "u@t.com",
	status: "active",
	has_password: false,
	mfa_methods: [],
};

function seedPersisted(state: Record<string, unknown>): void {
	localStorage.setItem(
		"portfolio-admin-auth",
		JSON.stringify({ state, version: 0 }),
	);
}

beforeEach(() => {
	replaceMock.mockClear();
	localStorage.clear();
	useAuthStore.getState().reset();
	// `reset()` NO toca `bootstrapping` (lo gobiernan los hooks de bootstrap).
	// En un reload real el store nace con bootstrapping=true; lo restauramos
	// aca para que cada caso parta del estado post-reload, no del residual del
	// test anterior.
	useAuthStore.getState().setBootstrapping(true);
});

describe("AuthGuard tras reload (rehidratacion real de localStorage)", () => {
	it("Given una sesion persistida CON user y luego reload When monta Then NO redirige y muestra children", async () => {
		// Arrange: el persist deja refreshToken + refreshExpiry + user.
		const refreshToken = makeJwt({ sub: USER.id, exp: nowSec() + 2_592_000 });
		seedPersisted({
			refreshToken,
			refreshExpiry: (nowSec() + 2_592_000) * 1000,
			user: USER,
		});
		await useAuthStore.persist.rehydrate();
		expect(useAuthStore.getState().accessToken).toBe(null);

		// Act
		render(
			(
				<AuthGuard>
					<p>protegido</p>
				</AuthGuard>
			) as ReactElement,
		);

		// Assert
		await waitFor(() => {
			expect(screen.getByText("protegido")).toBeInTheDocument();
		});
		expect(replaceMock).not.toHaveBeenCalled();
	});

	it("Given una sesion persistida SIN user (storage viejo/parcial) y reload When el refresh OK (que NO trae user) Then sostiene la sesion por el access JWT, NO redirige", async () => {
		// Arrange: localStorage SIN user (ej. entrada previa al user-in-partialize,
		// o un refresh-only). El /session/refresh del backend NO devuelve user.
		const refreshToken = makeJwt({ sub: USER.id, exp: nowSec() + 2_592_000 });
		seedPersisted({
			refreshToken,
			refreshExpiry: (nowSec() + 2_592_000) * 1000,
			// user ausente a proposito
		});
		await useAuthStore.persist.rehydrate();
		expect(useAuthStore.getState().accessToken).toBe(null);
		expect(useAuthStore.getState().user).toBe(null);

		// Act
		render(
			(
				<AuthGuard>
					<p>protegido</p>
				</AuthGuard>
			) as ReactElement,
		);

		// Assert: con un access JWT valido tras el refresh, la sesion vive aunque
		// user sea null. ANTES del fix esto redirigia a /login (isAuthenticated
		// exigia user) -> ESTE es el bug reportado.
		await waitFor(() => {
			expect(screen.getByText("protegido")).toBeInTheDocument();
		});
		expect(replaceMock).not.toHaveBeenCalled();
	});

	it("Given un reload con refresh LENTO (async real ~50ms) When monta Then NO redirige durante la ventana del refresh y termina en children", async () => {
		// Arrange: refresh con latencia real (el bug en dev: el redirect fire
		// DESPUES de que el refresh 200 resuelve, por una race de orden de los
		// set() entre setAccessToken y setBootstrapping). Un MSW instantaneo NO
		// reproducia esto; con delay se acerca al timing de produccion.
		const refreshToken = makeJwt({ sub: USER.id, exp: nowSec() + 2_592_000 });
		seedPersisted({
			refreshToken,
			refreshExpiry: (nowSec() + 2_592_000) * 1000,
			user: USER,
		});
		await useAuthStore.persist.rehydrate();
		server.use(
			http.post(`${API}/auth`, async () => {
				await delay(50);
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: {
						access_token: makeJwt({ sub: USER.id, exp: nowSec() + 900 }),
						refresh_token: makeJwt({ sub: USER.id, exp: nowSec() + 2_592_000 }),
						expires_in: 900,
					},
				});
			}),
		);

		// Act
		render(
			(
				<AuthGuard>
					<p>protegido</p>
				</AuthGuard>
			) as ReactElement,
		);
		// Durante la ventana del refresh: placeholder, NUNCA redirect.
		expect(screen.getByText(/verificando sesion/i)).toBeInTheDocument();

		// Assert: termina en children, sin haber redirigido en ningun momento.
		await waitFor(() => {
			expect(screen.getByText("protegido")).toBeInTheDocument();
		});
		expect(replaceMock).not.toHaveBeenCalled();
	});

	it("Given un reload y el backend responde el refresh FLAT (sin envelope, como prod) When monta Then hidrata el access y muestra children", async () => {
		// Arrange: el backend REAL responde FLAT — {access_token, refresh_token,
		// expires_in, token_type} al nivel raiz, SIN el wrapper {is_valid,code,
		// data}. apiFetch lo re-envuelve. El bug en dev (guard atascado en
		// "Verificando sesion") aparece si doRefresh no extrae bien el access de
		// esa respuesta. Los otros tests devolvian el shape YA enveloped (MSW),
		// enmascarando el path real.
		const refreshToken = makeJwt({ sub: USER.id, exp: nowSec() + 2_592_000 });
		seedPersisted({
			refreshToken,
			refreshExpiry: (nowSec() + 2_592_000) * 1000,
			user: USER,
		});
		await useAuthStore.persist.rehydrate();
		server.use(
			http.post(`${API}/auth`, () =>
				// FLAT, sin {is_valid, code, data}.
				HttpResponse.json({
					access_token: makeJwt({ sub: USER.id, exp: nowSec() + 900 }),
					refresh_token: makeJwt({ sub: USER.id, exp: nowSec() + 2_592_000 }),
					expires_in: 900,
					token_type: "Bearer",
				}),
			),
		);

		// Act
		render(
			(
				<AuthGuard>
					<p>protegido</p>
				</AuthGuard>
			) as ReactElement,
		);

		// Assert: hidrata el access y muestra children (NO se queda en el
		// placeholder ni redirige).
		await waitFor(() => {
			expect(screen.getByText("protegido")).toBeInTheDocument();
		});
		expect(replaceMock).not.toHaveBeenCalled();
	});
});
