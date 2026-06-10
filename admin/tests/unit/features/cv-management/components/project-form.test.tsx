import { act, render, screen, userEvent, waitFor } from "@tests/utils/render";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ProjectForm } from "@/features/cv-management/components/project-form";
import type { CvCatalogs, CvProject } from "@/features/cv-management/types";

/**
 * @module tests/unit/features/cv-management/components/project-form
 * @description Verifica el form de proyecto: hidratacion exacta (links,
 *   metricas ordenadas, case study detallado de 6 textareas, stack), submit
 *   con el payload del contrato y validacion (summary BiLang).
 *
 *   Los 2 shadcn Selects (status, projectType) se mockean en orden de
 *   render: [0] = status, [1] = projectType.
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
	skills: [],
	techTags: [
		{ slug: "astro", name: "Astro" },
		{ slug: "nextjs", name: "Next.js" },
	],
};

const PROJECT: CvProject = {
	slug: "proj-1",
	name: "Portfolio",
	summary: { es: "Resumen", en: "Summary" },
	description: { es: "Desc", en: "Desc-en" },
	url: "https://x.test",
	links: [{ label: "Demo", url: "https://demo.test" }],
	repo: "https://gh.test",
	status: "active",
	projectType: "web",
	isConfidential: false,
	metricsEstimated: true,
	stack: ["Astro"],
	caseStudy: { es: "cs", en: "cs-en" },
	caseStudyDetailed: {
		problem: { es: "p", en: "p-en" },
		process: { es: "q", en: "q-en" },
		result: { es: "r", en: "r-en" },
	},
	metrics: { lighthouse: "100", visitors: "5k" },
	niches: ["generic"],
	priority: { generic: 4 },
};

describe("ProjectForm", () => {
	it("Given un proyecto inicial When se renderiza Then hidrata campos, links, metricas y case study", () => {
		// Arrange + Act
		render(
			<ProjectForm
				initial={PROJECT}
				onSubmit={vi.fn()}
				submitting={false}
				catalogs={CATALOGS}
			/>,
		);

		// Assert
		expect(screen.getByTestId("cv-field-slug")).toHaveValue("proj-1");
		expect(screen.getByTestId("cv-field-name")).toHaveValue("Portfolio");
		expect(screen.getByTestId("bilang-summary-es")).toHaveValue("Resumen");
		expect(screen.getByTestId("cv-link-key")).toHaveValue("Demo");
		expect(screen.getByTestId("cv-link-value")).toHaveValue(
			"https://demo.test",
		);
		// Selects en orden: [0]=status, [1]=projectType.
		expect(capturedValues[0]).toBe("active");
		expect(capturedValues[1]).toBe("web");
		// Metricas ordenadas.
		const metricKeys = screen.getAllByTestId("cv-metric-key");
		expect(metricKeys[0]).toHaveValue("lighthouse");
		expect(metricKeys[1]).toHaveValue("visitors");
		// Case study detallado: 6 textareas (3 pares BiLang).
		expect(screen.getByTestId("bilang-caseStudyProblem-es")).toHaveValue("p");
		expect(screen.getByTestId("bilang-caseStudyProcess-en")).toHaveValue(
			"q-en",
		);
		expect(screen.getByTestId("bilang-caseStudyResult-es")).toHaveValue("r");
		// Stack chip.
		expect(screen.getByTestId("tag-chip")).toHaveAttribute(
			"data-value",
			"Astro",
		);
	});

	it("Given el form hidratado When se guarda Then emite el payload exacto", async () => {
		// Arrange
		const user = userEvent.setup();
		const onSubmit = vi.fn();
		render(
			<ProjectForm
				initial={PROJECT}
				onSubmit={onSubmit}
				submitting={false}
				catalogs={CATALOGS}
			/>,
		);

		// Act
		await user.click(screen.getByTestId("cv-form-submit"));

		// Assert
		await waitFor(() => {
			expect(onSubmit).toHaveBeenCalledWith(PROJECT);
		});
	});

	it("Given el alta vacia When se guarda Then errores de summary/estado/niches y NO emite", async () => {
		// Arrange
		const user = userEvent.setup();
		const onSubmit = vi.fn();
		render(
			<ProjectForm
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
		expect(screen.getByText("Selecciona el estado")).toBeInTheDocument();
		expect(screen.getByText("Selecciona el tipo")).toBeInTheDocument();
		expect(onSubmit).not.toHaveBeenCalled();
	});

	it("Given submitting When se renderiza Then el boton dice Guardando y esta deshabilitado", () => {
		// Arrange + Act
		render(
			<ProjectForm
				initial={PROJECT}
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

	it("Given el picker de niches When se marca vibe Then el payload lo incluye con prioridad 1", async () => {
		// Arrange
		const user = userEvent.setup();
		const onSubmit = vi.fn();
		render(
			<ProjectForm
				initial={PROJECT}
				onSubmit={onSubmit}
				submitting={false}
				catalogs={CATALOGS}
			/>,
		);

		// Act
		await user.click(screen.getByTestId("niche-checkbox-vibe"));
		await user.click(screen.getByTestId("cv-form-submit"));

		// Assert
		await waitFor(() => {
			expect(onSubmit).toHaveBeenCalledWith({
				...PROJECT,
				niches: ["generic", "vibe"],
				priority: { generic: 4, vibe: 1 },
			});
		});
	});

	it("Given los selects When emiten valores Then el payload los adopta", async () => {
		// Arrange
		const user = userEvent.setup();
		const onSubmit = vi.fn();
		render(
			<ProjectForm
				initial={PROJECT}
				onSubmit={onSubmit}
				submitting={false}
				catalogs={CATALOGS}
			/>,
		);

		// Act
		act(() => {
			capturedOnValueChange[0]?.("inactive");
			capturedOnValueChange[1]?.("cli");
		});
		await user.click(screen.getByTestId("cv-form-submit"));

		// Assert
		await waitFor(() => {
			expect(onSubmit).toHaveBeenCalledWith({
				...PROJECT,
				status: "inactive",
				projectType: "cli",
			});
		});
	});
});
