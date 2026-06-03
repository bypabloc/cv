import { makeJwt, nowSec } from "@tests/mocks/jwt";
import { server } from "@tests/mocks/server";
import { render, screen, waitFor } from "@tests/utils/render";
import { HttpResponse, http } from "msw";
import type { ReactElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AuthGuard } from "@/features/auth/components/auth-guard";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import type { User } from "@/types/models";

/**
 * @module tests/unit/features/auth/components/auth-guard
 * @description Verifica el gate de bootstrap (fix de persistencia de sesion):
 *   reload con refresh vigente -> hidrata sin redirigir; sin refresh o refresh
 *   fallido -> redirige; sesion vigente -> children.
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
	useAuthStore.getState().setBootstrapping(true);
});

describe("AuthGuard", () => {
	it("Given reload con refresh vigente When monta Then verifica sesion, NO redirige y tras refresh OK muestra children", async () => {
		// Arrange: estado post-reload (access null, refresh persistido vigente).
		useAuthStore.setState({
			accessToken: null,
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

		// Assert: primero el placeholder, sin redirect.
		expect(screen.getByText(/verificando sesion/i)).toBeInTheDocument();
		// Tras el refresh (MSW) el access se hidrata -> children.
		await waitFor(() => {
			expect(screen.getByText("protegido")).toBeInTheDocument();
		});
		expect(replaceMock).not.toHaveBeenCalled();
	});

	it("Given reload sin refresh token When monta Then redirige a /login con next", async () => {
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

	it("Given reload con refresh vigente pero el refresh FALLA When monta Then redirige a /login", async () => {
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

	it("Given sesion vigente When se renderiza Then muestra los children", () => {
		// Arrange
		useAuthStore.setState({
			accessToken: makeJwt({ sub: "usr_01", exp: nowSec() + 900 }),
			refreshToken: makeJwt({ sub: "usr_01", exp: nowSec() + 2_592_000 }),
			refreshExpiry: (nowSec() + 2_592_000) * 1000,
			user: USER,
			bootstrapping: false,
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
	});
});
