import { render, screen, waitFor } from "@tests/utils/render";
import { describe, expect, it } from "vitest";
import CvManagementPage from "@/app/(admin)/cv/page";

/**
 * @module tests/unit/app/cv/page
 * @description Verifica que la page /cv monta el overview real de la
 *   feature cv-management (cards por seccion + publish card) en lugar del
 *   placeholder "Proximamente".
 */
describe("CvManagementPage", () => {
	it("Given el overview When render Then muestra el titulo Gestion de CV", () => {
		// Arrange + Act
		render(<CvManagementPage />);

		// Assert
		expect(
			screen.getByRole("heading", { name: "Gestion de CV" }),
		).toBeInTheDocument();
	});

	it("Given el overview When render Then muestra las cards de seccion y la publish card", async () => {
		// Arrange + Act
		render(<CvManagementPage />);

		// Assert
		expect(
			screen.getByTestId("cv-section-card-experiences"),
		).toBeInTheDocument();
		expect(screen.getByTestId("cv-publish-card")).toBeInTheDocument();
		expect(screen.queryByText("Proximamente")).not.toBeInTheDocument();
		await waitFor(() => {
			expect(
				screen.getByTestId("cv-section-count-experiences"),
			).toHaveTextContent("2");
		});
	});
});
