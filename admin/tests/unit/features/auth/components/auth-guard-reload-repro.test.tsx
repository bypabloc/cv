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
 * @description Reproduce el modelo "lazy auth" tras reload: el store se rehidrata
 *   SOLO de localStorage (access null, refresh vigente). `useSessionRehydrate`
 *   hace UN refresh silencioso para hidratar el access; la sesion persiste tras
 *   el reload sin rebotar a /login. Si el refresh falla, redirige. El refresh NO
 *   devuelve user (igual que prod): la sesion vive por el access JWT.
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
});

describe("AuthGuard tras reload (rehidratacion real de localStorage)", () => {
	it("Given una sesion persistida CON user y luego reload When monta Then el refresh-en-reload hidrata el access, NO redirige y muestra children", async () => {
		// Arrange: el persist deja refreshToken + refreshExpiry + user; access null.
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

		// Assert: la sesion persiste tras el reload via el refresh-en-reload.
		await waitFor(() => {
			expect(screen.getByText("protegido")).toBeInTheDocument();
		});
		expect(replaceMock).not.toHaveBeenCalled();
	});

	it("Given una sesion persistida SIN user (storage viejo/parcial) y reload When el refresh OK (que NO trae user) Then sostiene la sesion por el access JWT, NO redirige", async () => {
		// Arrange: localStorage SIN user. El /session/refresh del backend NO
		// devuelve user. La sesion debe vivir igual mientras el access JWT valga.
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
		// user sea null.
		await waitFor(() => {
			expect(screen.getByText("protegido")).toBeInTheDocument();
		});
		expect(replaceMock).not.toHaveBeenCalled();
	});

	it("Given un reload con refresh LENTO (async real ~50ms) When monta Then NO redirige durante la ventana del refresh y termina en children", async () => {
		// Arrange: refresh con latencia real (acerca al timing de produccion). El
		// gate del rehydrate no debe redirigir antes de que ese refresh resuelva.
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
		// Durante la ventana del refresh: ni children ni redirect.
		expect(screen.queryByText("protegido")).not.toBeInTheDocument();
		expect(replaceMock).not.toHaveBeenCalled();

		// Assert: termina en children, sin haber redirigido en ningun momento.
		await waitFor(() => {
			expect(screen.getByText("protegido")).toBeInTheDocument();
		});
		expect(replaceMock).not.toHaveBeenCalled();
	});

	it("Given un reload y el backend responde el refresh FLAT (sin envelope, como prod) When monta Then hidrata el access y muestra children", async () => {
		// Arrange: el backend REAL responde FLAT — {access_token, refresh_token,
		// expires_in, token_type} al nivel raiz, SIN el wrapper {is_valid,code,
		// data}. apiFetch lo re-envuelve. Los otros tests devuelven el shape YA
		// enveloped (MSW), enmascarando el path real.
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

		// Assert: hidrata el access y muestra children (no redirige).
		await waitFor(() => {
			expect(screen.getByText("protegido")).toBeInTheDocument();
		});
		expect(replaceMock).not.toHaveBeenCalled();
	});

	it("Given un reload con refresh vigente pero el refresh FALLA (401) When monta Then resetea y redirige a /login", async () => {
		// Arrange: refresh vigente persistido, pero el backend lo rechaza.
		const refreshToken = makeJwt({ sub: USER.id, exp: nowSec() + 2_592_000 });
		seedPersisted({
			refreshToken,
			refreshExpiry: (nowSec() + 2_592_000) * 1000,
			user: USER,
		});
		await useAuthStore.persist.rehydrate();
		server.use(
			http.post(`${API}/auth`, () =>
				HttpResponse.json(
					{ error: "TOKEN_REUSE_DETECTED", code: 4011 },
					{ status: 401 },
				),
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

		// Assert: el rehydrate falla -> store.reset() -> redirect a /login.
		await waitFor(() => {
			expect(replaceMock).toHaveBeenCalledWith("/login?next=%2F");
		});
		expect(screen.queryByText("protegido")).not.toBeInTheDocument();
	});
});
