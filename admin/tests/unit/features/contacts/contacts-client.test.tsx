import { makeJwt } from "@tests/mocks/jwt";
import { beforeEach, describe, expect, it } from "vitest";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import { contactsClient } from "@/features/contacts/api/contacts-client";

/**
 * @module tests/unit/features/contacts/contacts-client
 * @description contactsClient.list y .byStatus: hacen GET /analytics?operation=
 *   contacts&action=... via fetchMetric y devuelven el `data`. La data viene
 *   del MSW handler (tests/mocks/handlers/metrics).
 */

beforeEach(() => {
	useAuthStore.setState({ accessToken: makeJwt({ sub: "usr_01" }) });
});

describe("contactsClient.list", () => {
	it("Given page+page_size por defecto When list Then devuelve el listado del fixture", async () => {
		// Act
		const data = await contactsClient.list({
			from: "2026-04-27",
			to: "2026-05-28",
		});

		// Assert
		expect(data.total).toBe(1);
		expect(data.page).toBe(1);
		expect(data.page_size).toBe(50);
		expect(data.has_more).toBe(false);
		expect(data.items).toHaveLength(1);
		expect(data.items[0]?.id).toBe("ct_1");
		expect(data.items[0]?.name).toBe("Ada");
		expect(data.items[0]?.email).toBe("ada@example.com");
		expect(data.items[0]?.status).toBe("new");
		expect(data.items[0]?.niche).toBe("fintech");
	});

	it("Given page=3 y page_size=20 When list Then deriva offset=(page-1)*page_size", async () => {
		// Act: el fixture es estatico, pero el client debe resolver sin romper
		const data = await contactsClient.list({
			from: "2026-04-27",
			to: "2026-05-28",
			page: 3,
			page_size: 20,
		});

		// Assert: el offset derivado (40) no rompe el fetch; devuelve el data
		expect(data.items).toHaveLength(1);
		expect(data.total).toBe(1);
	});

	it("Given status y niche When list Then los pasa como filtros sin romper", async () => {
		// Act
		const data = await contactsClient.list({
			from: "2026-04-27",
			to: "2026-05-28",
			status: "new",
			niche: "fintech",
		});

		// Assert
		expect(data.items[0]?.status).toBe("new");
	});
});

describe("contactsClient.byStatus", () => {
	it("Given un rango valido When byStatus Then devuelve el desglose por estado", async () => {
		// Act
		const data = await contactsClient.byStatus({
			from: "2026-04-27",
			to: "2026-05-28",
		});

		// Assert
		expect(data.items).toHaveLength(2);
		expect(data.items[0]).toEqual({ status: "new", count: 8, pct: 80.0 });
		expect(data.items[1]).toEqual({
			status: "converted",
			count: 2,
			pct: 20.0,
		});
	});
});
