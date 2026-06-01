import { render, screen, userEvent, waitFor } from "@tests/utils/render";
import { describe, expect, it, vi } from "vitest";
import { Header } from "@/features/admin-shell/components/header";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import type { User } from "@/types/models";

/**
 * @module tests/unit/features/admin-shell/components/header
 * @description Verifica el Header del app shell: muestra el email del user en
 *   el menu, el fallback 'Sesion activa' sin user, y que el item Cerrar sesion
 *   dispara el logout (reset del store).
 */

const { replaceMock } = vi.hoisted(() => ({ replaceMock: vi.fn() }));

vi.mock("next/navigation", () => ({
	useRouter: () => ({ push: vi.fn(), replace: replaceMock }),
	usePathname: () => "/settings",
	useSearchParams: () => new URLSearchParams(),
}));

const USER: User = {
	id: "usr_header",
	email: "header@test.com",
	status: "active",
	has_password: false,
	mfa_methods: [],
};

describe("Header", () => {
	it("Given un user en el store When abre el menu Then muestra su email", async () => {
		// Arrange
		const user = userEvent.setup();
		useAuthStore.setState({ accessToken: "tok", user: USER });
		render(<Header />);

		// Act
		await user.click(screen.getByRole("button", { name: /menu de usuario/i }));

		// Assert
		expect(await screen.findByText("header@test.com")).toBeInTheDocument();
	});

	it("Given sin user When abre el menu Then muestra el fallback Sesion activa", async () => {
		// Arrange
		const user = userEvent.setup();
		render(<Header />);

		// Act
		await user.click(screen.getByRole("button", { name: /menu de usuario/i }));

		// Assert
		expect(await screen.findByText("Sesion activa")).toBeInTheDocument();
	});

	it("Given el menu abierto When click en Cerrar sesion Then resetea el store", async () => {
		// Arrange
		const user = userEvent.setup();
		useAuthStore.setState({ accessToken: "tok", user: USER });
		render(<Header />);

		// Act
		await user.click(screen.getByRole("button", { name: /menu de usuario/i }));
		await user.click(await screen.findByText(/cerrar sesion/i));

		// Assert: el logout (best-effort vs MSW) termina reseteando el store
		await waitFor(() => {
			expect(useAuthStore.getState().accessToken).toBe(null);
		});
	});
});
