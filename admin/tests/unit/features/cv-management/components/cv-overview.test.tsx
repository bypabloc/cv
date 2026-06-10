import { render, screen, waitFor } from "@tests/utils/render";
import { describe, expect, it } from "vitest";
import { CvOverview } from "@/features/cv-management/components/cv-overview";

/**
 * @module tests/unit/features/cv-management/components/cv-overview
 * @description Verifica el overview de /cv: 10 cards de seccion con CONTEO
 *   real del GET /cv (2 experiencias, 1 proyecto, profile=1), guion para
 *   publications (sin lectura) y la publish-card presente.
 */

describe("CvOverview", () => {
	it("Given las fixtures del GET /cv When se renderiza Then las 10 cards muestran su conteo", async () => {
		// Arrange + Act
		render(<CvOverview />);

		// Assert: las 10 cards existen.
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
			expect(
				screen.getByTestId(`cv-section-card-${section}`),
			).toBeInTheDocument();
		}

		// Conteos exactos de las fixtures.
		await waitFor(() => {
			expect(
				screen.getByTestId("cv-section-count-experiences"),
			).toHaveTextContent("2");
		});
		expect(screen.getByTestId("cv-section-count-projects")).toHaveTextContent(
			"1",
		);
		expect(screen.getByTestId("cv-section-count-profile")).toHaveTextContent(
			"1",
		);
		await waitFor(() => {
			expect(screen.getByTestId("cv-section-count-awards")).toHaveTextContent(
				"0",
			);
		});
		// publications: sin lectura publica -> guion.
		expect(
			screen.getByTestId("cv-section-count-publications"),
		).toHaveTextContent("—");
	});

	it("Given el overview When se renderiza Then cada card linkea a su sub-ruta", async () => {
		// Arrange + Act
		render(<CvOverview />);

		// Assert
		await waitFor(() => {
			expect(screen.getByTestId("cv-section-card-experiences")).toHaveAttribute(
				"href",
				"/cv/experiences",
			);
		});
		expect(screen.getByTestId("cv-section-card-profile")).toHaveAttribute(
			"href",
			"/cv/profile",
		);
	});

	it("Given el overview When se renderiza Then incluye la publish-card", async () => {
		// Arrange + Act
		render(<CvOverview />);

		// Assert
		expect(screen.getByTestId("cv-publish-card")).toBeInTheDocument();
		expect(screen.getByTestId("cv-publish-button")).toBeEnabled();
		await waitFor(() => {
			expect(screen.getByTestId("cv-publish-status")).toHaveTextContent(
				"queued",
			);
		});
	});
});
