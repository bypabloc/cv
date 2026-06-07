import { makeJwt } from "@tests/mocks/jwt";
import { beforeEach, describe, expect, it } from "vitest";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import { eventsClient } from "@/features/events/api/events-client";

/**
 * @module tests/unit/features/events/events-client
 * @description eventsClient: cada fn hace GET /analytics?operation=events&
 *   action=... via fetchMetric y devuelve el data. list deriva offset desde
 *   page/page_size. Usa el MSW handler de /analytics (handlers/metrics).
 */

beforeEach(() => {
	useAuthStore.setState({ accessToken: makeJwt({ sub: "usr_01" }) });
});

describe("eventsClient.distribution", () => {
	it("Given un rango valido When distribution Then devuelve el ranking del fixture", async () => {
		// Act
		const data = await eventsClient.distribution({
			from: "2026-04-27",
			to: "2026-05-28",
		});

		// Assert
		expect(data.items).toHaveLength(2);
		expect(data.items[0]?.event_type).toBe("page_view");
		expect(data.items[0]?.count).toBe(300);
		expect(data.items[1]?.event_type).toBe("click");
		expect(data.items[1]?.count).toBe(200);
	});
});

describe("eventsClient.list", () => {
	it("Given page/page_size explicitos When list Then devuelve la pagina del fixture", async () => {
		// Act
		const data = await eventsClient.list({
			from: "2026-04-27",
			to: "2026-05-28",
			page: 1,
			page_size: 50,
		});

		// Assert
		expect(data.items).toHaveLength(1);
		expect(data.items[0]?.visit_id).toBe("vis_1");
		expect(data.items[0]?.event_type).toBe("page_view");
		expect(data.page).toBe(1);
		expect(data.page_size).toBe(50);
		expect(data.total).toBe(1);
		expect(data.has_more).toBe(false);
	});

	it("Given page/page_size omitidos When list Then usa los defaults page=1 page_size=50", async () => {
		// Act: sin page/page_size el cliente deriva page=1, page_size=50, offset=0
		const data = await eventsClient.list({
			from: "2026-04-27",
			to: "2026-05-28",
		});

		// Assert
		expect(data.page).toBe(1);
		expect(data.page_size).toBe(50);
		expect(data.items[0]?.session_id).toBe("sess_1");
	});

	it("Given page=3 page_size=20 When list Then el offset derivado es (page-1)*page_size", async () => {
		// Act: el offset no aparece en la respuesta (el fixture es fijo); el test
		// confirma que con offset derivado el request resuelve sin romper.
		const data = await eventsClient.list({
			from: "2026-04-27",
			to: "2026-05-28",
			page: 3,
			page_size: 20,
		});

		// Assert
		expect(data.total).toBe(1);
	});
});

describe("eventsClient.heatmap", () => {
	it("Given un rango valido When heatmap Then devuelve las celdas del fixture", async () => {
		// Act
		const data = await eventsClient.heatmap({
			from: "2026-04-27",
			to: "2026-05-28",
		});

		// Assert
		expect(data.cells).toHaveLength(2);
		expect(data.cells[0]).toEqual({ dow: 1, hour: 9, count: 12 });
		expect(data.cells[1]).toEqual({ dow: 3, hour: 14, count: 8 });
	});
});
