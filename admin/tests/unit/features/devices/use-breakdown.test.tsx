import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { makeJwt } from "@tests/mocks/jwt";
import { renderHook, waitFor } from "@tests/utils/render";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it } from "vitest";
import { useAuthStore } from "@/features/auth/store/use-auth-store";
import { useBreakdown } from "@/features/devices/hooks/use-breakdown";

/**
 * @module tests/unit/features/devices/use-breakdown
 * @description useBreakdown: distribucion de sesiones por dispositivo, navegador
 *   y sistema operativo (devices/breakdown). Desempaqueta el envelope y devuelve
 *   las 3 distribuciones del fixture MSW.
 */

function makeWrapper() {
	const client = new QueryClient({
		defaultOptions: { queries: { retry: false, gcTime: 0 } },
	});
	return function Wrapper({ children }: { children: ReactNode }) {
		return (
			<QueryClientProvider client={client}>{children}</QueryClientProvider>
		);
	};
}

beforeEach(() => {
	useAuthStore.setState({ accessToken: makeJwt({ sub: "usr_01" }) });
});

describe("useBreakdown", () => {
	it("Given un rango valido When la query resuelve Then devuelve las 3 distribuciones del fixture", async () => {
		// Arrange + Act
		const { result } = renderHook(
			() => useBreakdown({ from: "2026-04-27", to: "2026-05-28" }),
			{ wrapper: makeWrapper() },
		);

		// Assert
		await waitFor(() => {
			expect(result.current.isSuccess).toBe(true);
		});
		expect(result.current.data?.device_types).toHaveLength(1);
		expect(result.current.data?.device_types[0]?.device_type).toBe("desktop");
		expect(result.current.data?.device_types[0]?.sessions).toBe(50);
		expect(result.current.data?.browsers[0]?.browser).toBe("Chrome");
		expect(result.current.data?.browsers[0]?.sessions).toBe(40);
		expect(result.current.data?.os[0]?.os).toBe("Linux");
		expect(result.current.data?.os[0]?.sessions).toBe(35);
	});
});
