"use client";

import { Turnstile } from "@marsidev/react-turnstile";
import { useEffect } from "react";
import { env } from "@/lib/env";

/**
 * @component TurnstileWidget
 * @description Wrapper de Cloudflare Turnstile con el sitekey del env. Emite el
 *   token de challenge via `onToken`; lo limpia (null) si expira o falla, para
 *   que el form bloquee el submit hasta tener un token vigente.
 *
 *   En modo E2E (`NEXT_PUBLIC_E2E_BYPASS === 'true'`) NO renderiza el widget
 *   real (que exige interaccion humana / red a Cloudflare): auto-emite un
 *   token sentinel para habilitar el submit. El bypass REAL del backend lo
 *   aporta el header `X-Turnstile-Bypass-Token` (token Ed25519 firmado) que
 *   inyecta apiFetch; el `cf_turnstile_response` viaja vacio.
 *
 * @props {(token: string | null) => void} onToken - Recibe el token (o null)
 */
export function TurnstileWidget({
	onToken,
}: {
	onToken: (token: string | null) => void;
}) {
	const e2eBypass = env.NEXT_PUBLIC_E2E_BYPASS === "true";

	useEffect(() => {
		// En E2E: habilita el submit con un token vacio. El form manda
		// cf_turnstile_response='' y el bypass real va en el header.
		if (e2eBypass) onToken("");
	}, [e2eBypass, onToken]);

	if (e2eBypass) {
		return <div data-testid="turnstile-e2e-bypass" hidden aria-hidden="true" />;
	}

	return (
		<Turnstile
			siteKey={env.NEXT_PUBLIC_TURNSTILE_SITEKEY}
			onSuccess={(token) => onToken(token)}
			onExpire={() => onToken(null)}
			onError={() => onToken(null)}
			options={{ theme: "auto" }}
		/>
	);
}
