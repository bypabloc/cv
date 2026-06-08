import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { server } from "@tests/mocks/server";
import { HttpResponse, http } from "msw";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import {
	planGroupRequired,
	useSetPasskeysGroupRequired,
} from "@/features/settings/hooks/use-set-passkeys-group-required";
import type { SecurityPasskey } from "@/types/models";

/**
 * @module tests/unit/features/settings/hooks/use-set-passkeys-group-required
 * @description Cubre el toggle MAESTRO del grupo de passkeys: la planificacion
 *   pura (`planGroupRequired`) y la mutation (camino feliz + error 409).
 */

vi.mock("next/navigation", () => ({
	useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

const API = "https://api.test.the-full-stack.com";

function passkey(over: Partial<SecurityPasskey>): SecurityPasskey {
	return {
		credential_id: "cred_x",
		nickname: "Passkey",
		transports: null,
		enabled: true,
		required: false,
		created_at: "2026-06-08T00:00:00Z",
		last_used_at: null,
		...over,
	};
}

function wrapper({ children }: { children: ReactNode }) {
	const client = new QueryClient({
		defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
	});
	return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("planGroupRequired", () => {
	it("Given destino true y ninguna requerida When plan Then marca la primera activa", () => {
		// Arrange
		const passkeys = [
			passkey({ credential_id: "a", enabled: true, required: false }),
			passkey({ credential_id: "b", enabled: true, required: false }),
		];

		// Act
		const plan = planGroupRequired(true, passkeys);

		// Assert
		expect(plan).toEqual([{ credential_id: "a", required: true }]);
	});

	it("Given destino true y ya hay una requerida When plan Then no muta nada (idempotente)", () => {
		// Arrange
		const passkeys = [
			passkey({ credential_id: "a", enabled: true, required: false }),
			passkey({ credential_id: "b", enabled: true, required: true }),
		];

		// Act
		const plan = planGroupRequired(true, passkeys);

		// Assert
		expect(plan).toEqual([]);
	});

	it("Given destino true sin passkeys activas When plan Then no muta nada", () => {
		// Arrange
		const passkeys = [
			passkey({ credential_id: "a", enabled: false, required: false }),
		];

		// Act
		const plan = planGroupRequired(true, passkeys);

		// Assert
		expect(plan).toEqual([]);
	});

	it("Given destino true salta inactivas When plan Then marca la primera ACTIVA", () => {
		// Arrange
		const passkeys = [
			passkey({ credential_id: "a", enabled: false, required: false }),
			passkey({ credential_id: "b", enabled: true, required: false }),
		];

		// Act
		const plan = planGroupRequired(true, passkeys);

		// Assert
		expect(plan).toEqual([{ credential_id: "b", required: true }]);
	});

	it("Given destino false When plan Then desmarca TODAS las requeridas", () => {
		// Arrange
		const passkeys = [
			passkey({ credential_id: "a", enabled: true, required: true }),
			passkey({ credential_id: "b", enabled: true, required: false }),
			passkey({ credential_id: "c", enabled: false, required: true }),
		];

		// Act
		const plan = planGroupRequired(false, passkeys);

		// Assert
		expect(plan).toEqual([
			{ credential_id: "a", required: false },
			{ credential_id: "c", required: false },
		]);
	});
});

describe("useSetPasskeysGroupRequired", () => {
	it("Given el backend responde 204 a set-required When mutate(true) Then queda success", async () => {
		// Arrange: MSW por defecto responde 204 a webauthn.set-required.
		const passkeys = [passkey({ credential_id: "a", required: false })];

		// Act
		const { result } = renderHook(() => useSetPasskeysGroupRequired(), {
			wrapper,
		});
		result.current.mutate({ required: true, passkeys });

		// Assert
		await waitFor(() => expect(result.current.isSuccess).toBe(true));
	});

	it("Given set-required responde 409 When mutate(true) Then queda error", async () => {
		// Arrange: override -> 409 MUST_KEEP_ONE.
		server.use(
			http.post(`${API}/auth`, () =>
				HttpResponse.json(
					{
						error: "MUST_KEEP_ONE_MFA_METHOD",
						code: 4093,
						message: "Debes conservar al menos un metodo",
					},
					{ status: 409 },
				),
			),
		);
		const passkeys = [passkey({ credential_id: "a", required: true })];

		// Act
		const { result } = renderHook(() => useSetPasskeysGroupRequired(), {
			wrapper,
		});
		result.current.mutate({ required: false, passkeys });

		// Assert
		await waitFor(() => expect(result.current.isError).toBe(true));
	});

	it("Given set-required responde 500 When mutate(false) Then queda error (rama no-409)", async () => {
		// Arrange: override -> 500 (cubre el toast generico, no el 409).
		server.use(
			http.post(`${API}/auth`, () =>
				HttpResponse.json(
					{ error: "SERVER_ERROR", code: 5000, message: "fallo interno" },
					{ status: 500 },
				),
			),
		);
		const passkeys = [passkey({ credential_id: "a", required: true })];

		// Act
		const { result } = renderHook(() => useSetPasskeysGroupRequired(), {
			wrapper,
		});
		result.current.mutate({ required: false, passkeys });

		// Assert
		await waitFor(() => expect(result.current.isError).toBe(true));
	});

	it("Given destino true y ya hay una requerida When mutate Then success sin tocar la red", async () => {
		// Arrange: plan vacio -> 0 requests. El override 500 NO debe disparar
		// error porque no se hace ninguna llamada.
		server.use(
			http.post(`${API}/auth`, () =>
				HttpResponse.json({ error: "X", code: 5000 }, { status: 500 }),
			),
		);
		const passkeys = [passkey({ credential_id: "a", required: true })];

		// Act
		const { result } = renderHook(() => useSetPasskeysGroupRequired(), {
			wrapper,
		});
		result.current.mutate({ required: true, passkeys });

		// Assert
		await waitFor(() => expect(result.current.isSuccess).toBe(true));
	});
});
