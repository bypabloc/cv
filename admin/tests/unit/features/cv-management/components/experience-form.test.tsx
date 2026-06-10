import { act, render, screen, userEvent, waitFor } from "@tests/utils/render";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ExperienceForm } from "@/features/cv-management/components/experience-form";
import type { CvCatalogs, CvExperience } from "@/features/cv-management/types";

/**
 * @module tests/unit/features/cv-management/components/experience-form
 * @description Verifica el form de experiencia: hidratacion exacta con la
 *   entidad inicial, submit valido emitiendo el payload del contrato y
 *   errores de validacion BiLang (locale faltante) sin emitir submit.
 *
 *   El shadcn Select (Radix) se mockea (portal/pointer events poco fiables
 *   en happy-dom) capturando value/onValueChange.
 */

let capturedValues: string[] = [];
let capturedOnValueChange: ((next: string) => void)[] = [];

vi.mock("@/components/ui/select", () => ({
	Select: ({
		value,
		onValueChange,
		children,
	}: {
		value: string;
		onValueChange: (next: string) => void;
		children: ReactNode;
	}) => {
		capturedValues.push(value);
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
	capturedValues = [];
	capturedOnValueChange = [];
});

const CATALOGS: CvCatalogs = {
	niches: ["generic", "vibe"],
	skills: [
		{ slug: "python", name: "Python" },
		{ slug: "vue", name: "Vue" },
	],
	techTags: [],
};

const EXPERIENCE: CvExperience = {
	slug: "exp-1",
	role: { es: "Arquitecto", en: "Architect" },
	company: "Acme",
	country: "Peru",
	companyUrl: "https://acme.test",
	start: "2021-03",
	end: "2024-01",
	seniority: "senior",
	summary: { es: "Resumen", en: "Summary" },
	metricsEstimated: true,
	responsibilities: { es: ["r1"], en: ["r1-en"] },
	achievements: { es: ["a1"], en: ["a1-en"] },
	skillsTechnical: ["Vue"],
	skillsSoft: ["Liderazgo"],
	niches: ["generic"],
	priority: { generic: 5 },
};

describe("ExperienceForm", () => {
	it("Given una experiencia inicial When se renderiza Then hidrata todos los campos", () => {
		// Arrange + Act
		render(
			<ExperienceForm
				initial={EXPERIENCE}
				onSubmit={vi.fn()}
				submitting={false}
				catalogs={CATALOGS}
			/>,
		);

		// Assert: campos planos + BiLang + bullets + tags + niches + select.
		expect(screen.getByTestId("cv-field-slug")).toHaveValue("exp-1");
		expect(screen.getByTestId("cv-field-slug")).toBeDisabled();
		expect(screen.getByTestId("bilang-role-es")).toHaveValue("Arquitecto");
		expect(screen.getByTestId("bilang-role-en")).toHaveValue("Architect");
		expect(screen.getByTestId("cv-field-company")).toHaveValue("Acme");
		expect(screen.getByTestId("cv-field-country")).toHaveValue("Peru");
		expect(screen.getByTestId("cv-field-companyUrl")).toHaveValue(
			"https://acme.test",
		);
		expect(screen.getByTestId("cv-field-start")).toHaveValue("2021-03");
		expect(screen.getByTestId("cv-field-end")).toHaveValue("2024-01");
		expect(capturedValues[0]).toBe("senior");
		expect(screen.getByTestId("bilang-summary-es")).toHaveValue("Resumen");
		expect(screen.getByTestId("cv-field-metricsEstimated")).toBeChecked();
		expect(screen.getAllByTestId("bilang-item-row")).toHaveLength(2);
		const chips = screen.getAllByTestId("tag-chip");
		expect(chips.map((chip) => chip.getAttribute("data-value"))).toEqual([
			"Vue",
			"Liderazgo",
		]);
		expect(screen.getByTestId("niche-checkbox-generic")).toBeChecked();
		expect(screen.getByTestId("niche-priority-generic")).toHaveValue(5);
	});

	it("Given el form hidratado When se guarda Then emite el payload exacto del contrato", async () => {
		// Arrange
		const user = userEvent.setup();
		const onSubmit = vi.fn();
		render(
			<ExperienceForm
				initial={EXPERIENCE}
				onSubmit={onSubmit}
				submitting={false}
				catalogs={CATALOGS}
			/>,
		);

		// Act
		await user.click(screen.getByTestId("cv-form-submit"));

		// Assert: round-trip exacto.
		await waitFor(() => {
			expect(onSubmit).toHaveBeenCalledWith(EXPERIENCE);
		});
	});

	it("Given el alta vacia When se guarda Then muestra el error del locale es y NO emite", async () => {
		// Arrange
		const user = userEvent.setup();
		const onSubmit = vi.fn();
		render(
			<ExperienceForm
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
				screen.getByText("Falta el texto en español (es)"),
			).toBeInTheDocument();
		});
		expect(
			screen.getByText("Falta el texto en inglés (en)"),
		).toBeInTheDocument();
		expect(screen.getByText("Selecciona la seniority")).toBeInTheDocument();
		expect(
			screen.getByText("Selecciona al menos un niche"),
		).toBeInTheDocument();
		expect(onSubmit).not.toHaveBeenCalled();
	});

	it("Given una fecha 2026-13 When se guarda Then muestra Mes invalido (01-12)", async () => {
		// Arrange
		const user = userEvent.setup();
		const onSubmit = vi.fn();
		render(
			<ExperienceForm
				initial={EXPERIENCE}
				onSubmit={onSubmit}
				submitting={false}
				catalogs={CATALOGS}
			/>,
		);

		// Act
		await user.clear(screen.getByTestId("cv-field-start"));
		await user.type(screen.getByTestId("cv-field-start"), "2026-13");
		await user.click(screen.getByTestId("cv-form-submit"));

		// Assert
		await waitFor(() => {
			expect(screen.getByText("Mes invalido (01-12)")).toBeInTheDocument();
		});
		expect(onSubmit).not.toHaveBeenCalled();
	});

	it("Given submitting When se renderiza Then el boton dice Guardando y esta deshabilitado", () => {
		// Arrange + Act
		render(
			<ExperienceForm
				initial={EXPERIENCE}
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

	it("Given el select de seniority When emite un valor Then el form lo adopta", async () => {
		// Arrange
		const user = userEvent.setup();
		const onSubmit = vi.fn();
		render(
			<ExperienceForm
				initial={{ ...EXPERIENCE, seniority: "mid" }}
				onSubmit={onSubmit}
				submitting={false}
				catalogs={CATALOGS}
			/>,
		);

		// Act: el mock del Select expone onValueChange.
		act(() => {
			capturedOnValueChange[0]?.("lead");
		});
		await user.click(screen.getByTestId("cv-form-submit"));

		// Assert
		await waitFor(() => {
			expect(onSubmit).toHaveBeenCalledWith({
				...EXPERIENCE,
				seniority: "lead",
			});
		});
	});
});
