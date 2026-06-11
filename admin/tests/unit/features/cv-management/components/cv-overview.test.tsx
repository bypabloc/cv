import { server } from "@tests/mocks/server";
import { render, screen, waitFor } from "@tests/utils/render";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";
import { CvOverview } from "@/features/cv-management/components/cv-overview";

/**
 * @module tests/unit/features/cv-management/components/cv-overview
 * @description Verifica el overview de /cv: UN solo content.get-all del que
 *   las 10 cards derivan su conteo (2 experiencias, 1 proyecto, profile=1,
 *   2 publications reales), error -> guion, y la publish-card presente.
 */

const API = "https://api.test.the-full-stack.com";

const ALL_SECTIONS = [
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

describe("CvOverview", () => {
	it("Given el fixture del get-all When se renderiza Then las 10 cards derivan su conteo de UN solo request", async () => {
		// Arrange: contar los content.get-all que salen al backend.
		let getAllCount = 0;
		server.use(
			http.post(`${API}/cv`, async ({ request }) => {
				const body = (await request.json()) as {
					operation: string;
					action: string;
				};
				if (body.operation === "content" && body.action === "get-all") {
					getAllCount += 1;
					return HttpResponse.json({
						is_valid: true,
						code: 0,
						data: {
							profile: { name: "Pablo Contreras", handle: "bypabloc" },
							experiences: [{ slug: "a" }, { slug: "b" }],
							projects: [{ slug: "c" }],
							skills: [],
							education: [],
							certificates: [],
							awards: [],
							languages: [],
							endorsements: [],
							publications: [{ slug: "d" }, { slug: "e" }],
						},
					});
				}
				// publish.status de la publish-card.
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { status: "queued", ref: "dev" },
				});
			}),
		);

		// Act
		render(<CvOverview />);

		// Assert: las 10 cards existen.
		for (const section of ALL_SECTIONS) {
			expect(
				screen.getByTestId(`cv-section-card-${section}`),
			).toBeInTheDocument();
		}

		// Conteos exactos derivados del get-all (incl. publications real).
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
		expect(screen.getByTestId("cv-section-count-awards")).toHaveTextContent(
			"0",
		);
		expect(
			screen.getByTestId("cv-section-count-publications"),
		).toHaveTextContent("2");

		// UN solo fetch para las 10 cards.
		expect(getAllCount).toBe(1);
	});

	it("Given el overview con las fixtures default When se renderiza Then publications cuenta las 2 del fixture", async () => {
		// Arrange + Act: handler default (CV_FULL_ADMIN_FIXTURE).
		render(<CvOverview />);

		// Assert
		await waitFor(() => {
			expect(
				screen.getByTestId("cv-section-count-publications"),
			).toHaveTextContent("2");
		});
		expect(screen.getByTestId("cv-section-count-skills")).toHaveTextContent(
			"0",
		);
	});

	it("Given un get-all en error When se renderiza Then las cards muestran guion", async () => {
		// Arrange
		server.use(
			http.post(`${API}/cv`, async ({ request }) => {
				const body = (await request.json()) as {
					operation: string;
					action: string;
				};
				if (body.operation === "content" && body.action === "get-all") {
					return HttpResponse.json(
						{ error: "FORBIDDEN", code: 4030, message: "No autorizado" },
						{ status: 403 },
					);
				}
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { status: "none", ref: "dev" },
				});
			}),
		);

		// Act
		render(<CvOverview />);

		// Assert
		await waitFor(() => {
			expect(
				screen.getByTestId("cv-section-count-experiences"),
			).toHaveTextContent("—");
		});
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
