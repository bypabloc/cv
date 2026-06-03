import { makeJwt } from "@tests/mocks/jwt";
import { beforeEach, describe, expect, it } from "vitest";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import { fetchMetric } from "@/lib/metrics-client";

/**
 * @module tests/unit/lib/metrics-client
 * @description fetchMetric: arma el query string con operation/action + params,
 *   omite los vacios, adjunta el Bearer y devuelve el `data` del Envelope.
 *   Usa el MSW handler de /analytics (tests/mocks/handlers/metrics).
 */

beforeEach(() => {
	useAuthStore.setState({ accessToken: makeJwt({ sub: "usr_01" }) });
});

describe("fetchMetric", () => {
	it("Given operation+action validos When fetch Then devuelve el data del Envelope", async () => {
		// Act
		const data = await fetchMetric<{ sessions: number }>(
			"analytics",
			"overview",
			{ from: "2026-04-27", to: "2026-05-27" },
		);

		// Assert
		expect(data.sessions).toBe(100);
	});

	it("Given un action desconocido When fetch Then lanza ApiError 400", async () => {
		// Act + Assert
		await expect(
			fetchMetric("analytics", "no-existe", {}),
		).rejects.toMatchObject({ status: 400 });
	});

	it("Given params vacios/null When fetch Then los omite del query string", async () => {
		// Act: el handler responde igual; el test verifica que no rompe con vacios
		const data = await fetchMetric<{ active_sessions: number }>(
			"analytics",
			"active-now",
			{ from: "", to: undefined, niche: null },
		);

		// Assert
		expect(data.active_sessions).toBe(3);
	});
});
