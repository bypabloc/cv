import { render, screen, userEvent } from "@tests/utils/render";
import { describe, expect, it, vi } from "vitest";
import { SessionsPagination } from "@/features/sessions/components/SessionsPagination";

/**
 * @module tests/unit/features/sessions/sessions-pagination
 * @description Controles de paginacion: rango mostrado, botones anterior/
 *   siguiente y sus estados disabled (page<=1, !hasMore, isLoading).
 */

describe("SessionsPagination", () => {
	it("Given page 1 de 100 When render Then muestra el rango y deshabilita Anterior", () => {
		// Arrange + Act
		render(
			<SessionsPagination
				page={1}
				pageSize={20}
				total={100}
				hasMore={true}
				isLoading={false}
				onPageChange={vi.fn()}
			/>,
		);

		// Assert
		expect(screen.getByText("1-20 de 100")).toBeInTheDocument();
		expect(screen.getByRole("button", { name: /anterior/i })).toBeDisabled();
		expect(
			screen.getByRole("button", { name: /siguiente/i }),
		).not.toBeDisabled();
	});

	it("Given total 0 When render Then el rango arranca en 0", () => {
		// Arrange + Act
		render(
			<SessionsPagination
				page={1}
				pageSize={20}
				total={0}
				hasMore={false}
				isLoading={false}
				onPageChange={vi.fn()}
			/>,
		);

		// Assert
		expect(screen.getByText("0-0 de 0")).toBeInTheDocument();
		expect(screen.getByRole("button", { name: /siguiente/i })).toBeDisabled();
	});

	it("Given isLoading When render Then ambos botones deshabilitados", () => {
		// Arrange + Act
		render(
			<SessionsPagination
				page={2}
				pageSize={20}
				total={100}
				hasMore={true}
				isLoading={true}
				onPageChange={vi.fn()}
			/>,
		);

		// Assert
		expect(screen.getByRole("button", { name: /anterior/i })).toBeDisabled();
		expect(screen.getByRole("button", { name: /siguiente/i })).toBeDisabled();
	});

	it("Given click en Siguiente When habilitado Then llama onPageChange con page+1", async () => {
		// Arrange
		const onPageChange = vi.fn();
		const user = userEvent.setup();
		render(
			<SessionsPagination
				page={2}
				pageSize={20}
				total={100}
				hasMore={true}
				isLoading={false}
				onPageChange={onPageChange}
			/>,
		);

		// Act
		await user.click(screen.getByRole("button", { name: /siguiente/i }));
		await user.click(screen.getByRole("button", { name: /anterior/i }));

		// Assert
		expect(onPageChange).toHaveBeenNthCalledWith(1, 3);
		expect(onPageChange).toHaveBeenNthCalledWith(2, 1);
	});
});
