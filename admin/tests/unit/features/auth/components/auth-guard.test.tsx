import { makeJwt, nowSec } from "@tests/mocks/jwt";
import { render, screen, waitFor } from "@tests/utils/render";
import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";
import { AuthGuard } from "@/features/auth/components/auth-guard";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import type { User } from "@/types/models";

/**
 * @module tests/unit/features/auth/components/auth-guard
 * @description Verifica redirect sin sesion y render de children con sesion.
 */

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

describe("AuthGuard", () => {
	it("Given sin token When se renderiza Then redirige a /login con next", async () => {
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
