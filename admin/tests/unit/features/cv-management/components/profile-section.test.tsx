import { server } from "@tests/mocks/server";
import { render, screen, userEvent, waitFor } from "@tests/utils/render";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";
import { ProfileSection } from "@/features/cv-management/components/profile-section";

/**
 * @module tests/unit/features/cv-management/components/profile-section
 * @description Verifica la pantalla del profile: skeleton mientras cargan
 *   profile+catalogos, hidratacion del form con el GET /cv y guardado via
 *   upsert-profile (request FLAT capturado).
 */

const API = "https://api.test.the-full-stack.com";

describe("ProfileSection", () => {
	it("Given las queries en vuelo When se renderiza Then muestra el skeleton", () => {
		// Arrange + Act
		render(<ProfileSection />);

		// Assert
		expect(screen.getByTestId("cv-profile-skeleton")).toBeInTheDocument();
	});

	it("Given el profile del backend When resuelve Then hidrata el form", async () => {
		// Arrange + Act
		render(<ProfileSection />);

		// Assert
		await waitFor(() => {
			expect(screen.getByTestId("cv-field-name")).toHaveValue(
				"Pablo Contreras",
			);
		});
		expect(screen.getByTestId("cv-field-handle")).toHaveValue("bypabloc");
		expect(screen.getByTestId("bilang-headline-es")).toHaveValue(
			"Full Stack Senior",
		);
		expect(screen.getByTestId("cv-field-yearsExperience")).toHaveValue(10);
	});

	it("Given el form hidratado When se guarda Then envia upsert-profile con el contrato FLAT", async () => {
		// Arrange: capturar el body del POST /cv admin.
		let capturedBody: Record<string, unknown> | null = null;
		server.use(
			http.post(`${API}/cv`, async ({ request }) => {
				const body = (await request.json()) as Record<string, unknown>;
				// El catalogs de la misma pantalla sigue respondiendo su shape.
				if (body.action === "catalogs") {
					return HttpResponse.json({
						is_valid: true,
						code: 0,
						data: { niches: ["generic"], skills: [], techTags: [] },
					});
				}
				capturedBody = body;
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { entity: "bypabloc", id: "ent_01" },
				});
			}),
		);
		const user = userEvent.setup();
		render(<ProfileSection />);
		await waitFor(() => {
			expect(screen.getByTestId("cv-field-name")).toHaveValue(
				"Pablo Contreras",
			);
		});

		// Act
		await user.click(screen.getByTestId("cv-form-submit"));

		// Assert: operation/action al nivel raiz + campos del payload.
		await waitFor(() => {
			expect(capturedBody).not.toBeNull();
		});
		const body = capturedBody as unknown as Record<string, unknown>;
		expect(body.operation).toBe("content");
		expect(body.action).toBe("upsert-profile");
		expect(body.handle).toBe("bypabloc");
		expect(body.name).toBe("Pablo Contreras");
	});
});
