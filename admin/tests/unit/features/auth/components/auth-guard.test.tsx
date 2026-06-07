import { makeJwt, nowSec } from "@tests/mocks/jwt";
import { server } from "@tests/mocks/server";
import { render, screen, waitFor } from "@tests/utils/render";
import { delay, HttpResponse, http } from "msw";
import type { ReactElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AuthGuard } from "@/features/auth/components/auth-guard";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import type { User } from "@/types/models";

/**
 * @module tests/unit/features/auth/components/auth-guard
 * @description Lazy auth: SIN texto "Verificando sesion" (return null mientras
 *   rehydrating o !authed). reload con refresh vigente -> rehidrata via UN
 *   refresh y muestra children; sin refresh o refresh fallido -> redirige;
 *   sesion vigente -> children directos.
 */

const API = "https://api.test.the-full-stack.com";

const { replaceMock } = vi.hoisted(() => ({ replaceMock: vi.fn() }));
vi.mock("next/navigation", () => ({
	useRouter: () => ({ push: vi.fn(), replace: replaceMock }),
	usePathname: () => "/settings",
}));

const USER: User = {
	id: "usr_01",
	email: "u@t.com",
	status: "active",
	has_password: false,
	mfa_methods: [],
};

beforeEach(() => {
	replaceMock.mockClear();
	useAuthStore.getState().reset();
});

describe("AuthGuard", () => {
	it("Given reload con refresh vigente When monta Then NO renderiza children ni redirige durante el refresh, y tras refresh OK muestra children", async () => {
		// Arrange: estado post-reload (access null, refresh persistido vigente).
		// El refresh tiene latencia real para observar la ventana de gate.
		useAuthStore.setState({
			accessToken: null,
			refreshToken: makeJwt({ sub: "usr_01", exp: nowSec() + 2_592_000 }),
			refreshExpiry: (nowSec() + 2_592_000) * 1000,
			user: USER,
		});
		server.use(
			http.post(`${API}/auth`, async () => {
				await delay(50);
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: {
						access_token: makeJwt({ sub: "usr_01", exp: nowSec() + 900 }),
						refresh_token: makeJwt({
							sub: "usr_01",
							exp: nowSec() + 2_592_000,
						}),
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

		// Assert: durante la ventana del refresh, ni children ni redirect.
		expect(screen.queryByText("protegido")).not.toBeInTheDocument();
		expect(replaceMock).not.toHaveBeenCalled();
		// Tras el refresh (MSW) el access se hidrata -> children.
		await waitFor(() => {
			expect(screen.getByText("protegido")).toBeInTheDocument();
		});
		expect(replaceMock).not.toHaveBeenCalled();
	});

	it("Given reload sin refresh token When monta Then redirige a /login con next y no muestra children", async () => {
		// Arrange: estado inicial (sin refresh) ya seteado por beforeEach.

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
			expect(replaceMock).toHaveBeenCalledWith("/login?next=%2Fsettings");
		});
		expect(screen.queryByText("protegido")).not.toBeInTheDocument();
	});

	it("Given reload con refresh vigente pero el refresh FALLA When monta Then resetea y redirige a /login", async () => {
		// Arrange: refresh vigente, pero el backend rechaza el refresh (401).
		useAuthStore.setState({
			accessToken: null,
			refreshToken: makeJwt({ sub: "usr_01", exp: nowSec() + 2_592_000 }),
			refreshExpiry: (nowSec() + 2_592_000) * 1000,
			user: USER,
		});
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

		// Assert
		await waitFor(() => {
			expect(replaceMock).toHaveBeenCalledWith("/login?next=%2Fsettings");
		});
		expect(screen.queryByText("protegido")).not.toBeInTheDocument();
	});

	it("Given sesion vigente When se renderiza Then muestra los children sin redirigir", () => {
		// Arrange: access vigente en memoria -> useSessionRehydrate no rehidrata.
		useAuthStore.setState({
			accessToken: makeJwt({ sub: "usr_01", exp: nowSec() + 900 }),
			refreshToken: makeJwt({ sub: "usr_01", exp: nowSec() + 2_592_000 }),
			refreshExpiry: (nowSec() + 2_592_000) * 1000,
			user: USER,
		});

		// Act
		render(
			(
				<AuthGuard>
					<p>protegido</p>
				</AuthGuard>
			) as ReactElement,
		);

		// Assert
		expect(screen.getByText("protegido")).toBeInTheDocument();
		expect(replaceMock).not.toHaveBeenCalled();
	});
});
