"use client";

import type { ReactNode } from "react";
import { QueryProvider } from "./query-provider";
import { ThemeProvider } from "./theme-provider";

/**
 * @component RootProviders
 * @description Composicion de providers: ThemeProvider > QueryProvider.
 * @props {ReactNode} children - Arbol de la app
 */
export function RootProviders({ children }: { children: ReactNode }) {
	return (
		<ThemeProvider>
			<QueryProvider>{children}</QueryProvider>
		</ThemeProvider>
	);
}
