import { render, screen, waitFor } from "@tests/utils/render";
import { afterEach, describe, expect, it, vi } from "vitest";
import { CvShell } from "@/features/cv-management/components/cv-shell";

/**
 * @module tests/unit/features/cv-management/components/cv-shell
 * @description Verifica el marco de /cv/**: gate admin-only (skeleton
 *   mientras resuelve, pantalla de no autorizado para no-admin — NUNCA
 *   redirect a login) y el sub-nav con las 10 secciones + resumen, con la
 *   activa marcada por pathname NORMALIZADO (trailingSlash: true del export
 *   hace que usePathname() llegue con slash final; los hrefs van sin el).
 */

const useIsAdminMock = vi.fn();
vi.mock("@/features/admin-shell/hooks/use-is-admin", () => ({
	useIsAdmin: () => useIsAdminMock(),
}));

const usePathnameMock = vi.fn(() => "/cv");
vi.mock("next/navigation", () => ({
	usePathname: () => usePathnameMock(),
}));

afterEach(() => {
	useIsAdminMock.mockReset();
	usePathnameMock.mockReset();
	usePathnameMock.mockReturnValue("/cv");
});

describe("CvShell", () => {
	it("Given el rol sin resolver When se renderiza Then muestra skeleton sin children", () => {
		// Arrange
		useIsAdminMock.mockReturnValue({ isAdmin: false, isResolved: false });

		// Act
		render(
			<CvShell>
				<p>contenido</p>
			</CvShell>,
		);

		// Assert
		expect(screen.getByTestId("cv-shell-loading")).toBeInTheDocument();
		expect(screen.queryByText("contenido")).not.toBeInTheDocument();
	});

	it("Given un NO-admin When se renderiza Then pantalla de no autorizado sin children ni redirect", () => {
		// Arrange
		useIsAdminMock.mockReturnValue({ isAdmin: false, isResolved: true });

		// Act
		render(
			<CvShell>
				<p>contenido</p>
			</CvShell>,
		);

		// Assert
		expect(
			screen.getByText("No tienes acceso a esta seccion"),
		).toBeInTheDocument();
		expect(screen.queryByText("contenido")).not.toBeInTheDocument();
		expect(screen.queryByTestId("cv-subnav")).not.toBeInTheDocument();
	});

	it("Given un admin When se renderiza Then sub-nav con resumen + 10 secciones y children", () => {
		// Arrange
		useIsAdminMock.mockReturnValue({ isAdmin: true, isResolved: true });

		// Act
		render(
			<CvShell>
				<p>contenido</p>
			</CvShell>,
		);

		// Assert
		expect(screen.getByText("contenido")).toBeInTheDocument();
		expect(screen.getByTestId("cv-subnav-overview")).toHaveAttribute(
			"href",
			"/cv",
		);
		const sections = [
			"profile",
			"experiences",
			"projects",
			"education",
			"certificates",
			"awards",
			"languages",
			"endorsements",
			"publications",
			"skills",
		];
		for (const section of sections) {
			expect(screen.getByTestId(`cv-subnav-${section}`)).toHaveAttribute(
				"href",
				`/cv/${section}`,
			);
		}
	});

	it("Given el pathname /cv/experiences When se renderiza Then marca esa seccion activa", async () => {
		// Arrange
		useIsAdminMock.mockReturnValue({ isAdmin: true, isResolved: true });
		usePathnameMock.mockReturnValue("/cv/experiences");

		// Act
		render(
			<CvShell>
				<p>contenido</p>
			</CvShell>,
		);

		// Assert: la activa lleva text-accent-foreground; el resumen no (las
		// inactivas tienen hover:bg-accent, por eso no se usa bg-accent).
		await waitFor(() => {
			expect(screen.getByTestId("cv-subnav-experiences").className).toContain(
				"text-accent-foreground",
			);
		});
		expect(screen.getByTestId("cv-subnav-overview").className).not.toContain(
			"text-accent-foreground",
		);
	});

	it("Given el pathname /cv/experiences/ (trailing slash del export) When se renderiza Then marca esa seccion activa", async () => {
		// Arrange
		useIsAdminMock.mockReturnValue({ isAdmin: true, isResolved: true });
		usePathnameMock.mockReturnValue("/cv/experiences/");

		// Act
		render(
			<CvShell>
				<p>contenido</p>
			</CvShell>,
		);

		// Assert: normaliza el slash final -> el tab matchea igual; el
		// resumen NO se marca (no es prefijo-match).
		await waitFor(() => {
			expect(screen.getByTestId("cv-subnav-experiences").className).toContain(
				"text-accent-foreground",
			);
		});
		expect(screen.getByTestId("cv-subnav-overview").className).not.toContain(
			"text-accent-foreground",
		);
	});

	it("Given el pathname /cv/ (trailing slash) When se renderiza Then SOLO el resumen queda activo", async () => {
		// Arrange
		useIsAdminMock.mockReturnValue({ isAdmin: true, isResolved: true });
		usePathnameMock.mockReturnValue("/cv/");

		// Act
		render(
			<CvShell>
				<p>contenido</p>
			</CvShell>,
		);

		// Assert
		await waitFor(() => {
			expect(screen.getByTestId("cv-subnav-overview").className).toContain(
				"text-accent-foreground",
			);
		});
		expect(screen.getByTestId("cv-subnav-experiences").className).not.toContain(
			"text-accent-foreground",
		);
		expect(screen.getByTestId("cv-subnav-profile").className).not.toContain(
			"text-accent-foreground",
		);
	});

	it("Given el pathname /cv/profile/ When se renderiza Then el resumen NO queda activo (igualdad exacta)", async () => {
		// Arrange
		useIsAdminMock.mockReturnValue({ isAdmin: true, isResolved: true });
		usePathnameMock.mockReturnValue("/cv/profile/");

		// Act
		render(
			<CvShell>
				<p>contenido</p>
			</CvShell>,
		);

		// Assert
		await waitFor(() => {
			expect(screen.getByTestId("cv-subnav-profile").className).toContain(
				"text-accent-foreground",
			);
		});
		expect(screen.getByTestId("cv-subnav-overview").className).not.toContain(
			"text-accent-foreground",
		);
	});
});
