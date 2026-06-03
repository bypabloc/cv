import { makeJwt, nowSec } from "@tests/mocks/jwt";
import { render, screen, waitFor } from "@tests/utils/render";
import type { ReactElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AuthGuard } from "@/features/auth/components/auth-guard";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import type { User } from "@/types/models";

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
});
