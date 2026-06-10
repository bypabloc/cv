import { render, screen, userEvent, waitFor } from "@tests/utils/render";
import { describe, expect, it, vi } from "vitest";
import { SimpleEntityForm } from "@/features/cv-management/components/simple-entity-form";
import type { CvCatalogs } from "@/features/cv-management/types";

/**
 * @module tests/unit/features/cv-management/components/simple-entity-form
 * @description Verifica el form parametrizado de entidades simples:
 *   hidratacion (certificate), submit con payload del contrato, errores por
 *   campo (label en el mensaje) y campos BiLang (award).
 */

const CATALOGS: CvCatalogs = {
	niches: ["generic", "vibe"],
	skills: [],
	techTags: [],
};

const CERTIFICATE = {
	slug: "cert-1",
	title: "AWS SAA",
	issuer: "AWS",
	date: "2024-01",
	url: "https://cert.test",
	niches: ["generic"],
	priority: { generic: 2 },
};

describe("SimpleEntityForm", () => {
	it("Given un certificate inicial When se renderiza Then hidrata todos los campos", () => {
		// Arrange + Act
		render(
			<SimpleEntityForm
				entity="certificate"
				initial={CERTIFICATE}
				onSubmit={vi.fn()}
				submitting={false}
				catalogs={CATALOGS}
			/>,
		);

		// Assert
		expect(screen.getByTestId("cv-field-slug")).toHaveValue("cert-1");
		expect(screen.getByTestId("cv-field-slug")).toBeDisabled();
		expect(screen.getByTestId("cv-field-title")).toHaveValue("AWS SAA");
		expect(screen.getByTestId("cv-field-issuer")).toHaveValue("AWS");
		expect(screen.getByTestId("cv-field-date")).toHaveValue("2024-01");
		expect(screen.getByTestId("cv-field-url")).toHaveValue("https://cert.test");
		expect(screen.getByTestId("niche-checkbox-generic")).toBeChecked();
		expect(screen.getByTestId("niche-priority-generic")).toHaveValue(2);
	});

	it("Given el certificate hidratado When se guarda Then emite el payload exacto", async () => {
		// Arrange
		const user = userEvent.setup();
		const onSubmit = vi.fn();
		render(
			<SimpleEntityForm
				entity="certificate"
				initial={CERTIFICATE}
				onSubmit={onSubmit}
				submitting={false}
				catalogs={CATALOGS}
			/>,
		);

		// Act
		await user.click(screen.getByTestId("cv-form-submit"));

		// Assert
		await waitFor(() => {
			expect(onSubmit).toHaveBeenCalledWith(CERTIFICATE);
		});
	});

	it("Given el alta vacia de certificate When se guarda Then errores con label y NO emite", async () => {
		// Arrange
		const user = userEvent.setup();
		const onSubmit = vi.fn();
		render(
			<SimpleEntityForm
				entity="certificate"
				onSubmit={onSubmit}
				submitting={false}
				catalogs={CATALOGS}
			/>,
		);

		// Act
		await user.click(screen.getByTestId("cv-form-submit"));

		// Assert
		await waitFor(() => {
			expect(screen.getByText("Titulo: campo obligatorio")).toBeInTheDocument();
		});
		expect(screen.getByText("El slug es obligatorio")).toBeInTheDocument();
		expect(screen.getByText("La fecha es obligatoria")).toBeInTheDocument();
		expect(
			screen.getByText("Selecciona al menos un niche"),
		).toBeInTheDocument();
		expect(onSubmit).not.toHaveBeenCalled();
	});

	it("Given un award con BiLang When se edita el title.en y guarda Then el payload lo refleja", async () => {
		// Arrange
		const user = userEvent.setup();
		const onSubmit = vi.fn();
		const award = {
			slug: "award-1",
			title: { es: "Premio", en: "Award" },
			issuer: "Org",
			date: "2023-05",
			motivation: { es: "m", en: "m-en" },
			niches: ["generic"],
			priority: {},
		};
		render(
			<SimpleEntityForm
				entity="award"
				initial={award}
				onSubmit={onSubmit}
				submitting={false}
				catalogs={CATALOGS}
			/>,
		);

		// Act
		await user.clear(screen.getByTestId("bilang-title-en"));
		await user.type(screen.getByTestId("bilang-title-en"), "Award 2.0");
		await user.click(screen.getByTestId("cv-form-submit"));

		// Assert: url opcional vacia se omite del payload.
		await waitFor(() => {
			expect(onSubmit).toHaveBeenCalledWith({
				slug: "award-1",
				title: { es: "Premio", en: "Award 2.0" },
				issuer: "Org",
				date: "2023-05",
				motivation: { es: "m", en: "m-en" },
				niches: ["generic"],
				priority: {},
			});
		});
	});

	it("Given un language sin name.en When se guarda Then el error señala el locale en", async () => {
		// Arrange
		const user = userEvent.setup();
		const onSubmit = vi.fn();
		render(
			<SimpleEntityForm
				entity="language"
				initial={{
					slug: "lang-1",
					name: { es: "Ingles", en: "" },
					level: { es: "Avanzado", en: "Advanced" },
					niches: ["generic"],
					priority: {},
				}}
				onSubmit={onSubmit}
				submitting={false}
				catalogs={CATALOGS}
			/>,
		);

		// Act
		await user.click(screen.getByTestId("cv-form-submit"));

		// Assert
		await waitFor(() => {
			expect(
				screen.getByText("Falta el texto en inglés (en)"),
			).toBeInTheDocument();
		});
		expect(onSubmit).not.toHaveBeenCalled();
	});
});
