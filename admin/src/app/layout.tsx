import { MswProvider } from "@/components/msw-provider";
import { Toaster } from "@/components/ui/sonner";
import { RootProviders } from "@/providers/root-providers";
import "@/styles/globals.css";
// Validar env al cargar (fail-fast en build)
import "@/lib/env";
import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
	title: "Admin | the-full-stack",
	description: "Panel de administracion",
	robots: "noindex, nofollow",
};

export default function RootLayout({ children }: { children: ReactNode }) {
	return (
		<html lang="es" suppressHydrationWarning>
			<body>
				<MswProvider>
					<RootProviders>{children}</RootProviders>
				</MswProvider>
				<Toaster position="top-right" richColors closeButton />
			</body>
		</html>
	);
}
