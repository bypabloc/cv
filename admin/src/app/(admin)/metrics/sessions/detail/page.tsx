"use client";

import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { SessionDetailView } from "@/features/sessions/components/SessionDetailView";

/**
 * @page MetricsSessionDetailPage
 * @description Detalle de una sesion de visitante. Ruta ESTATICA
 *   (`/metrics/sessions/detail?id=<session_id>`) en vez de dinamica `[id]`:
 *   `output: 'export'` no admite rutas dinamicas sin params conocidos en
 *   build. El id viaja como query param y se lee client-side con
 *   `useSearchParams` (dentro de Suspense, obligatorio en export).
 */
function SessionDetailContent() {
	const params = useSearchParams();
	const sessionId = params.get("id") ?? "";
	return <SessionDetailView sessionId={sessionId} />;
}

export default function MetricsSessionDetailPage() {
	return (
		<Suspense fallback={null}>
			<SessionDetailContent />
		</Suspense>
	);
}
