import { render, screen, userEvent } from "@tests/utils/render";
import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";
import { TurnstileWidget } from "@/features/auth/components/turnstile-widget";

/**
 * @module tests/unit/features/auth/components/turnstile-widget
 * @description Verifica que el widget propague el token al callback onToken.
 */

vi.mock("@marsidev/react-turnstile", () => ({
	Turnstile: ({
		siteKey,
		onSuccess,
		onExpire,
		onError,
	}: {
		siteKey: string;
		onSuccess?: (token: string) => void;
		onExpire?: () => void;
		onError?: () => void;
	}) => (
		<div>
			<span data-testid="sitekey">{siteKey}</span>
			<button type="button" onClick={() => onSuccess?.("tok-123")}>
				success
			</button>
			<button type="button" onClick={() => onExpire?.()}>
				expire
			</button>
			<button type="button" onClick={() => onError?.()}>
				error
			</button>
		</div>
	),
}));

describe("TurnstileWidget", () => {
	it("Given onSuccess When resuelve Then emite el token; onExpire emite null", async () => {
		const onToken = vi.fn();
		const user = userEvent.setup();
		render((<TurnstileWidget onToken={onToken} />) as ReactElement);

		expect(screen.getByTestId("sitekey")).toHaveTextContent(
			"1x00000000000000000000AA",
		);

		await user.click(screen.getByRole("button", { name: "success" }));
		expect(onToken).toHaveBeenCalledWith("tok-123");

		await user.click(screen.getByRole("button", { name: "expire" }));
		expect(onToken).toHaveBeenCalledWith(null);

		onToken.mockClear();
		await user.click(screen.getByRole("button", { name: "error" }));
		expect(onToken).toHaveBeenCalledWith(null);
	});
});
