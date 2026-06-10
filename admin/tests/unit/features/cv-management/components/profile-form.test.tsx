import { render, screen, userEvent, waitFor } from "@tests/utils/render";
import { describe, expect, it, vi } from "vitest";
import { ProfileForm } from "@/features/cv-management/components/profile-form";
import type { CvCatalogs, CvProfile } from "@/features/cv-management/types";

/**
 * @module tests/unit/features/cv-management/components/profile-form
 * @description Verifica el form del profile singleton: hidratacion
 *   (contactos + stats + niches sin prioridad), submit con el payload del
 *   contrato y validacion de email.
 */

const CATALOGS: CvCatalogs = {
	niches: ["generic", "vibe"],
	skills: [],
	techTags: [],
};

const PROFILE: CvProfile = {
	name: "Pablo",
	handle: "bypabloc",
	headline: { es: "Full Stack", en: "Full Stack" },
	summary: { es: "Resumen", en: "Summary" },
	location: "Lima",
	availability: { es: "Disponible", en: "Available" },
	contacts: {
		email: "owner@test.com",
		phone: "+51 999",
		linkedin: "https://li.test",
		github: "https://gh.test",
		website: "https://web.test",
	},
	avatarUrl: "https://cdn.test/a.webp",
	niches: ["generic"],
	stats: {
		yearsExperience: 10,
		companies: 5,
		countries: 3,
		certifications: 7,
	},
};

describe("ProfileForm", () => {
	it("Given un profile inicial When se renderiza Then hidrata contactos, stats y niches", () => {
		// Arrange + Act
		render(
			<ProfileForm
				initial={PROFILE}
				onSubmit={vi.fn()}
				submitting={false}
				catalogs={CATALOGS}
			/>,
		);

		// Assert
		expect(screen.getByTestId("cv-field-name")).toHaveValue("Pablo");
		expect(screen.getByTestId("cv-field-handle")).toHaveValue("bypabloc");
		expect(screen.getByTestId("bilang-headline-es")).toHaveValue("Full Stack");
		expect(screen.getByTestId("cv-field-email")).toHaveValue("owner@test.com");
		expect(screen.getByTestId("cv-field-phone")).toHaveValue("+51 999");
		expect(screen.getByTestId("cv-field-yearsExperience")).toHaveValue(10);
		expect(screen.getByTestId("cv-field-certifications")).toHaveValue(7);
		expect(screen.getByTestId("niche-checkbox-generic")).toBeChecked();
		// Sin prioridad: el profile no se reordena.
		expect(
			screen.queryByTestId("niche-priority-generic"),
		).not.toBeInTheDocument();
	});

	it("Given el form hidratado When se guarda Then emite el payload exacto", async () => {
		// Arrange
		const user = userEvent.setup();
		const onSubmit = vi.fn();
		render(
			<ProfileForm
				initial={PROFILE}
				onSubmit={onSubmit}
				submitting={false}
				catalogs={CATALOGS}
			/>,
		);

		// Act
		await user.click(screen.getByTestId("cv-form-submit"));

		// Assert
		await waitFor(() => {
			expect(onSubmit).toHaveBeenCalledWith(PROFILE);
		});
	});

	it("Given un email invalido When se guarda Then muestra Email invalido y NO emite", async () => {
		// Arrange
		const user = userEvent.setup();
		const onSubmit = vi.fn();
		render(
			<ProfileForm
				initial={PROFILE}
				onSubmit={onSubmit}
				submitting={false}
				catalogs={CATALOGS}
			/>,
		);

		// Act
		await user.clear(screen.getByTestId("cv-field-email"));
		await user.type(screen.getByTestId("cv-field-email"), "no-es-email");
		await user.click(screen.getByTestId("cv-form-submit"));

		// Assert
		await waitFor(() => {
			expect(screen.getByText("Email invalido")).toBeInTheDocument();
		});
		expect(onSubmit).not.toHaveBeenCalled();
	});

	it("Given submitting When se renderiza Then el boton dice Guardando y esta deshabilitado", () => {
		// Arrange + Act
		render(
			<ProfileForm
				initial={PROFILE}
				onSubmit={vi.fn()}
				submitting
				catalogs={CATALOGS}
			/>,
		);

		// Assert
		const submit = screen.getByTestId("cv-form-submit");
		expect(submit).toBeDisabled();
		expect(submit).toHaveTextContent("Guardando...");
	});

	it("Given el picker de niches When se marca vibe Then el payload lo incluye sin prioridad", async () => {
		// Arrange
		const user = userEvent.setup();
		const onSubmit = vi.fn();
		render(
			<ProfileForm
				initial={PROFILE}
				onSubmit={onSubmit}
				submitting={false}
				catalogs={CATALOGS}
			/>,
		);

		// Act
		await user.click(screen.getByTestId("niche-checkbox-vibe"));
		await user.click(screen.getByTestId("cv-form-submit"));

		// Assert: el profile no maneja prioridades.
		await waitFor(() => {
			expect(onSubmit).toHaveBeenCalledWith({
				...PROFILE,
				niches: ["generic", "vibe"],
			});
		});
	});

	it("Given el alta sin datos When se guarda Then señala los locales faltantes del headline", async () => {
		// Arrange
		const user = userEvent.setup();
		const onSubmit = vi.fn();
		render(
			<ProfileForm
				onSubmit={onSubmit}
				submitting={false}
				catalogs={CATALOGS}
			/>,
		);

		// Act
		await user.click(screen.getByTestId("cv-form-submit"));

		// Assert: headline + summary son los 2 BiLang requeridos del profile.
		await waitFor(() => {
			expect(
				screen.getAllByText("Falta el texto en español (es)"),
			).toHaveLength(2);
		});
		expect(onSubmit).not.toHaveBeenCalled();
	});
});
