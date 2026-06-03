import { render, screen } from "@tests/utils/render";
import { describe, expect, it } from "vitest";
import { TopReferrersTable } from "@/features/analytics/components/TopReferrersTable";
import type { RankItem } from "@/features/analytics/types";

/**
 * @module tests/unit/features/analytics/TopReferrersTable
 * @description TopReferrersTable: tabla generica de ranking. La etiqueta de la
 *   fila se resuelve del primer campo no-numerico (referrer / utm_*) presente,
 *   con fallback "(desconocido)". Mensaje vacio si no hay items.
 */

describe("TopReferrersTable", () => {
	it("Given referrers When se renderiza Then usa el campo referrer como etiqueta", () => {
		// Arrange
		const items: RankItem[] = [
			{ referrer: "(direct)", visits: 40, unique_visitors: 30 },
		];

		// Act
		render(<TopReferrersTable label="Referrer" items={items} />);

		// Assert
		expect(screen.getByText("Referrer")).toBeInTheDocument();
		expect(screen.getByText("(direct)")).toBeInTheDocument();
		expect(screen.getByText("40")).toBeInTheDocument();
	});

	it("Given utm_source When no hay referrer Then usa utm_source como etiqueta", () => {
		// Arrange
		const items: RankItem[] = [{ utm_source: "google", visits: 10 }];

		// Act
		render(<TopReferrersTable label="Fuente" items={items} />);

		// Assert
		expect(screen.getByText("google")).toBeInTheDocument();
	});

	it("Given utm_medium When no hay referrer ni source Then usa utm_medium", () => {
		// Arrange
		const items: RankItem[] = [{ utm_medium: "cpc", visits: 5 }];

		// Act
		render(<TopReferrersTable label="Medio" items={items} />);

		// Assert
		expect(screen.getByText("cpc")).toBeInTheDocument();
	});

	it("Given utm_campaign When es el unico campo Then usa utm_campaign", () => {
		// Arrange
		const items: RankItem[] = [{ utm_campaign: "launch", visits: 3 }];

		// Act
		render(<TopReferrersTable label="Campaña" items={items} />);

		// Assert
		expect(screen.getByText("launch")).toBeInTheDocument();
	});

	it("Given un item sin ningun campo etiqueta When se renderiza Then usa el fallback", () => {
		// Arrange
		const items: RankItem[] = [{ visits: 1 }];

		// Act
		render(<TopReferrersTable label="X" items={items} />);

		// Assert
		expect(screen.getByText("(desconocido)")).toBeInTheDocument();
	});

	it("Given items vacios When se renderiza Then muestra el mensaje vacio", () => {
		// Arrange + Act
		render(<TopReferrersTable label="Referrer" items={[]} />);

		// Assert
		expect(
			screen.getByText("Sin datos en el rango seleccionado."),
		).toBeInTheDocument();
		expect(screen.queryByRole("table")).not.toBeInTheDocument();
	});
});
