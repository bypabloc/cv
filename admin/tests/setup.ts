import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterAll, afterEach, beforeAll, vi } from "vitest";

// Env vars antes de que cualquier import de @/lib/env las valide.
vi.stubEnv("NEXT_PUBLIC_API_ENDPOINT", "https://api.test.the-full-stack.com");
vi.stubEnv("NEXT_PUBLIC_TURNSTILE_SITEKEY", "1x00000000000000000000AA");
vi.stubEnv("NEXT_PUBLIC_ADMIN_URL", "https://admin.test.the-full-stack.com");
vi.stubEnv("NEXT_PUBLIC_AUTH_REFRESH_LEAD_MS", "30000");
vi.stubEnv("NEXT_PUBLIC_WEBAUTHN_RP_ID", "admin.test.the-full-stack.com");
vi.stubEnv("NEXT_PUBLIC_FEATURE_MFA", "true");

// Polyfill BroadcastChannel (happy-dom no lo trae; MSW v2 + nuestro auth lo usan).
if (typeof globalThis.BroadcastChannel === "undefined") {
	class MockBroadcastChannel {
		name: string;
		onmessage: ((event: MessageEvent) => void) | null = null;
		constructor(name: string) {
			this.name = name;
		}
		postMessage(): void {}
		close(): void {}
		addEventListener(): void {}
		removeEventListener(): void {}
	}
	(
		globalThis as unknown as { BroadcastChannel: typeof MockBroadcastChannel }
	).BroadcastChannel = MockBroadcastChannel;
}

// matchMedia polyfill (next-themes / use-media-query lo usan).
if (typeof globalThis.matchMedia === "undefined") {
	(
		globalThis as unknown as { matchMedia: (q: string) => MediaQueryList }
	).matchMedia = (query: string) =>
		({
			matches: false,
			media: query,
			onchange: null,
			addEventListener: () => {},
			removeEventListener: () => {},
			addListener: () => {},
			removeListener: () => {},
			dispatchEvent: () => false,
		}) as unknown as MediaQueryList;
}

// Suprime el ReferenceError benigno de happy-dom cuando una query/fetch en
// vuelo (invalidacion de Tanstack tras una mutation) resuelve DESPUES de que
// happy-dom desmonto `window` en el teardown del test. No afecta asserts (los
// tests ya esperan con waitFor); es ruido de teardown, no un fallo real.
process.on("unhandledRejection", (reason) => {
	if (
		reason instanceof ReferenceError &&
		reason.message.includes("window is not defined")
	) {
		return;
	}
	throw reason;
});

const { server } = await import("./mocks/server");
const { useAuthStore } = await import("@/features/auth/store/use-auth-store");

beforeAll(() => {
	server.listen({ onUnhandledRequest: "error" });
});

afterEach(() => {
	cleanup();
	server.resetHandlers();
	useAuthStore.getState().reset();
	localStorage.clear();
});

afterAll(() => {
	server.close();
});
