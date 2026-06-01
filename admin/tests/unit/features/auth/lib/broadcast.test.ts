import { afterEach, describe, expect, it, vi } from "vitest";
import { AUTH_CHANNEL, broadcastAuth } from "@/features/auth/lib/broadcast";

/**
 * @module tests/unit/features/auth/lib/broadcast
 * @description Verifica el emisor BroadcastChannel y el guard SSR.
 */
describe("broadcastAuth", () => {
	afterEach(() => {
		vi.unstubAllGlobals();
	});

	it("Given BroadcastChannel disponible When se emite Then postea el mensaje y cierra", () => {
		// Arrange
		const postMessage = vi.fn();
		const close = vi.fn();
		const names: string[] = [];
		class FakeChannel {
			constructor(name: string) {
				names.push(name);
			}
			postMessage = postMessage;
			close = close;
		}
		vi.stubGlobal("BroadcastChannel", FakeChannel);

		// Act
		broadcastAuth({ type: "LOGOUT" });

		// Assert
		expect(names).toEqual([AUTH_CHANNEL]);
		expect(postMessage).toHaveBeenCalledWith({ type: "LOGOUT" });
		expect(close).toHaveBeenCalledTimes(1);
	});

	it("Given BroadcastChannel undefined When se emite Then no lanza (guard SSR)", () => {
		// Arrange
		vi.stubGlobal("BroadcastChannel", undefined);

		// Act + Assert
		expect(() => broadcastAuth({ type: "LOGOUT" })).not.toThrow();
	});
});
