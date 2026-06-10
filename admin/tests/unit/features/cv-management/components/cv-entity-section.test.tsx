import { server } from "@tests/mocks/server";
import {
	act,
	render,
	screen,
	userEvent,
	waitFor,
	within,
} from "@tests/utils/render";
import { HttpResponse, http } from "msw";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { CvEntitySection } from "@/features/cv-management/components/cv-entity-section";

/**
 * @module tests/unit/features/cv-management/components/cv-entity-section
 * @description Verifica la pantalla integrada de una seccion (experiences
 *   contra MSW): lista, alta/edicion en dialog (form hidratado), borrado
 *   con confirmacion y reorden con la lista completa del niche activo.
 *
 *   El Select (niche selector + seniority) se mockea capturando
 *   value/onValueChange en orden de render.
 */

let capturedOnValueChange: ((next: string) => void)[] = [];

vi.mock("@/components/ui/select", () => ({
	Select: ({
		onValueChange,
		children,
	}: {
		onValueChange: (next: string) => void;
		children: ReactNode;
	}) => {
		capturedOnValueChange.push(onValueChange);
		return <div data-testid="select">{children}</div>;
	},
	SelectContent: ({ children }: { children: ReactNode }) => <>{children}</>,
	SelectItem: ({ value, children }: { value: string; children: ReactNode }) => (
		<div data-value={value}>{children}</div>
	),
	SelectTrigger: ({ children }: { children: ReactNode }) => <>{children}</>,
	SelectValue: ({ placeholder }: { placeholder?: string }) => (
		<span>{placeholder}</span>
	),
}));

beforeEach(() => {
	capturedOnValueChange = [];
});

const API = "https://api.test.the-full-stack.com";

interface CapturedRequest {
	action: string;
	body: Record<string, unknown>;
}

/** Override de /cv-admin que captura upsert/delete/reorder (catalogs pasa). */
function captureCvAdmin(captured: CapturedRequest[]): void {
	server.use(
		http.post(`${API}/cv-admin`, async ({ request }) => {
			const body = (await request.json()) as Record<string, unknown> & {
				action: string;
			};
			if (body.action === "catalogs") {
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { niches: ["generic", "vibe"], skills: [], techTags: [] },
				});
			}
			captured.push({ action: body.action, body });
			if (body.action === "reorder") {
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: {
						entity_type: body.entity_type,
						niche: body.niche,
						reordered: (body.ordered_slugs as string[]).length,
					},
				});
			}
			if (body.action.startsWith("delete-")) {
				return HttpResponse.json({
					is_valid: true,
					code: 0,
					data: { entity: body.slug, deleted: true },
				});
			}
			return HttpResponse.json({
				is_valid: true,
				code: 0,
				data: { entity: body.slug, id: "ent_01" },
			});
		}),
	);
}

async function waitForCards(count: number): Promise<void> {
	await waitFor(() => {
		expect(screen.getAllByTestId("cv-entity-card")).toHaveLength(count);
	});
}

describe("CvEntitySection", () => {
	it("Given las fixtures When se renderiza experiences Then lista 2 cards con sus slugs", async () => {
		// Arrange + Act
		render(<CvEntitySection section="experiences" />);

		// Assert
		await waitForCards(2);
		const cards = screen.getAllByTestId("cv-entity-card");
		expect(cards[0]).toHaveAttribute("data-slug", "destacame-architect");
		expect(cards[1]).toHaveAttribute("data-slug", "acme-fullstack");
	});

	it("Given cv-entity-new When se clickea Then abre el dialog con el form vacio", async () => {
		// Arrange
		const user = userEvent.setup();
		render(<CvEntitySection section="experiences" />);
		await waitForCards(2);

		// Act
		await user.click(screen.getByTestId("cv-entity-new"));

		// Assert: el titulo vive DENTRO del dialog (el boton de alta comparte
		// el texto "Nueva entrada").
		const dialog = screen.getByTestId("cv-entity-form-dialog");
		expect(within(dialog).getByText("Nueva entrada")).toBeInTheDocument();
		expect(screen.getByTestId("cv-field-slug")).toHaveValue("");
		expect(screen.getByTestId("cv-field-slug")).toBeEnabled();
	});

	it("Given editar una card When se clickea Then el form hidrata la entidad y al guardar envia upsert", async () => {
		// Arrange
		const captured: CapturedRequest[] = [];
		captureCvAdmin(captured);
		const user = userEvent.setup();
		render(<CvEntitySection section="experiences" />);
		await waitForCards(2);

		// Act: abrir edicion de la primera.
		await user.click(screen.getAllByTestId("cv-entity-edit")[0] as HTMLElement);

		// Assert: hidratacion.
		expect(screen.getByTestId("cv-field-slug")).toHaveValue(
			"destacame-architect",
		);
		expect(screen.getByTestId("cv-field-slug")).toBeDisabled();
		expect(screen.getByTestId("cv-field-company")).toHaveValue("Destacame");

		// Act: guardar.
		await user.click(screen.getByTestId("cv-form-submit"));

		// Assert: upsert-experience con el slug + el dialog cierra.
		await waitFor(() => {
			expect(captured).toHaveLength(1);
		});
		expect(captured[0]?.action).toBe("upsert-experience");
		expect(captured[0]?.body.slug).toBe("destacame-architect");
		await waitFor(() => {
			expect(
				screen.queryByTestId("cv-entity-form-dialog"),
			).not.toBeInTheDocument();
		});
	});

	it("Given eliminar una card When se confirma Then envia delete-experience y cierra", async () => {
		// Arrange
		const captured: CapturedRequest[] = [];
		captureCvAdmin(captured);
		const user = userEvent.setup();
		render(<CvEntitySection section="experiences" />);
		await waitForCards(2);

		// Act
		await user.click(
			screen.getAllByTestId("cv-entity-delete")[1] as HTMLElement,
		);
		await user.click(screen.getByTestId("cv-entity-delete-confirm"));

		// Assert
		await waitFor(() => {
			expect(captured).toHaveLength(1);
		});
		expect(captured[0]?.action).toBe("delete-experience");
		expect(captured[0]?.body.slug).toBe("acme-fullstack");
	});

	it("Given eliminar cancelado When se cancela Then NO sale ningun delete", async () => {
		// Arrange
		const captured: CapturedRequest[] = [];
		captureCvAdmin(captured);
		const user = userEvent.setup();
		render(<CvEntitySection section="experiences" />);
		await waitForCards(2);

		// Act
		await user.click(
			screen.getAllByTestId("cv-entity-delete")[0] as HTMLElement,
		);
		await user.click(screen.getByTestId("cv-entity-delete-cancel"));

		// Assert
		expect(captured).toHaveLength(0);
	});

	it("Given un niche activo When se sube la segunda card Then envia reorder con la lista completa", async () => {
		// Arrange
		const captured: CapturedRequest[] = [];
		captureCvAdmin(captured);
		const user = userEvent.setup();
		render(<CvEntitySection section="experiences" />);
		await waitForCards(2);

		// Act: activar el niche generic via el Select mockeado (indice 0 =
		// selector de niche de la lista) y reordenar.
		act(() => {
			capturedOnValueChange[0]?.("generic");
		});
		await waitFor(() => {
			expect(screen.getAllByTestId("cv-entity-move-up")).toHaveLength(2);
		});
		await user.click(
			screen.getAllByTestId("cv-entity-move-up")[1] as HTMLElement,
		);

		// Assert: reorder con entity_type experience, el niche y TODOS los slugs.
		await waitFor(() => {
			expect(captured).toHaveLength(1);
		});
		expect(captured[0]?.action).toBe("reorder");
		expect(captured[0]?.body.entity_type).toBe("experience");
		expect(captured[0]?.body.niche).toBe("generic");
		expect(captured[0]?.body.ordered_slugs).toEqual([
			"acme-fullstack",
			"destacame-architect",
		]);
	});

	it("Given la seccion projects When se edita la card Then monta ProjectForm hidratado", async () => {
		// Arrange
		const user = userEvent.setup();
		render(<CvEntitySection section="projects" />);
		await waitForCards(1);

		// Act
		await user.click(screen.getAllByTestId("cv-entity-edit")[0] as HTMLElement);

		// Assert: campos propios del form de proyecto.
		expect(screen.getByTestId("cv-field-slug")).toHaveValue(
			"portfolio-monorepo",
		);
		expect(screen.getByTestId("cv-field-name")).toHaveValue(
			"Portfolio multi-niche",
		);
		expect(screen.getByTestId("bilang-caseStudyProblem-es")).toHaveValue(
			"Problema",
		);
	});

	it("Given la seccion skills When se abre el alta Then monta SkillCategoryForm", async () => {
		// Arrange
		const user = userEvent.setup();
		render(<CvEntitySection section="skills" />);
		await waitFor(() => {
			expect(screen.getByText("Sin entradas")).toBeInTheDocument();
		});

		// Act
		await user.click(screen.getByTestId("cv-entity-new"));

		// Assert: el tag-input ordenado de skills es propio de ese form.
		expect(screen.getByTestId("tag-input-skills")).toBeInTheDocument();
		expect(screen.getByTestId("bilang-name-es")).toBeInTheDocument();
	});

	it("Given la seccion certificates When se crea una entrada Then envia upsert-certificate", async () => {
		// Arrange
		const captured: CapturedRequest[] = [];
		captureCvAdmin(captured);
		const user = userEvent.setup();
		render(<CvEntitySection section="certificates" />);
		await waitFor(() => {
			expect(screen.getByText("Sin entradas")).toBeInTheDocument();
		});

		// Act: abrir el alta y completar el form simple.
		await user.click(screen.getByTestId("cv-entity-new"));
		await user.type(screen.getByTestId("cv-field-slug"), "cert-e2e");
		await user.type(screen.getByTestId("cv-field-title"), "Cert E2E");
		await user.type(screen.getByTestId("cv-field-issuer"), "AWS");
		await user.type(screen.getByTestId("cv-field-date"), "2026-01");
		await user.type(screen.getByTestId("cv-field-url"), "https://cert.test");
		await user.click(screen.getByTestId("niche-checkbox-generic"));
		await user.click(screen.getByTestId("cv-form-submit"));

		// Assert
		await waitFor(() => {
			expect(captured).toHaveLength(1);
		});
		expect(captured[0]?.action).toBe("upsert-certificate");
		expect(captured[0]?.body.slug).toBe("cert-e2e");
		expect(captured[0]?.body.niches).toEqual(["generic"]);
	});

	it("Given el dialog abierto When se presiona Escape Then cierra sin request", async () => {
		// Arrange
		const captured: CapturedRequest[] = [];
		captureCvAdmin(captured);
		const user = userEvent.setup();
		render(<CvEntitySection section="experiences" />);
		await waitForCards(2);
		await user.click(screen.getByTestId("cv-entity-new"));

		// Act
		await user.keyboard("{Escape}");

		// Assert
		await waitFor(() => {
			expect(
				screen.queryByTestId("cv-entity-form-dialog"),
			).not.toBeInTheDocument();
		});
		expect(captured).toHaveLength(0);
	});

	it("Given la seccion publications (sin lectura) When se renderiza Then muestra la nota", async () => {
		// Arrange + Act
		render(<CvEntitySection section="publications" />);

		// Assert
		await waitFor(() => {
			expect(screen.getByRole("note")).toHaveTextContent(
				"aun no tiene lectura publica",
			);
		});
	});
});
