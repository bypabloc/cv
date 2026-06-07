import { makeJwt } from "@tests/mocks/jwt";
import { beforeEach, describe, expect, it } from "vitest";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import { devicesClient } from "@/features/devices/api/devices-client";

/**
 * @module tests/unit/features/devices/devices-client
 * @description devicesClient: cada fn hace GET /analytics?operation=devices&
 *   action=... via fetchMetric y devuelve el data. Usa el MSW handler de
 *   /analytics (handlers/metrics).
 */

beforeEach(() => {
	useAuthStore.setState({ accessToken: makeJwt({ sub: "usr_01" }) });
});

describe("devicesClient.breakdown", () => {
	it("Given un rango valido When breakdown Then devuelve las 3 distribuciones del fixture", async () => {
		// Act
		const data = await devicesClient.breakdown({
			from: "2026-04-27",
			to: "2026-05-28",
		});

		// Assert
		expect(data.device_types).toHaveLength(1);
		expect(data.device_types[0]).toEqual({
			device_type: "desktop",
			sessions: 50,
		});
		expect(data.browsers).toHaveLength(1);
		expect(data.browsers[0]).toEqual({ browser: "Chrome", sessions: 40 });
		expect(data.os).toHaveLength(1);
		expect(data.os[0]).toEqual({ os: "Linux", sessions: 35 });
	});

	it("Given un rango sin from/to When breakdown Then resuelve igual (params omitidos)", async () => {
		// Act
		const data = await devicesClient.breakdown({});

		// Assert
		expect(data.device_types[0]?.device_type).toBe("desktop");
		expect(data.browsers[0]?.browser).toBe("Chrome");
		expect(data.os[0]?.os).toBe("Linux");
	});
});
