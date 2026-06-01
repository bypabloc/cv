"use client";

import { Monitor, Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useMounted } from "@/hooks/use-mounted";

/**
 * @component ThemeToggle
 * @description Selector dark/light/system via next-themes. Renderiza un
 *   placeholder estable hasta montar (evita hydration mismatch del icono).
 */
export function ThemeToggle() {
	const { theme, setTheme } = useTheme();
	const mounted = useMounted();

	return (
		<DropdownMenu>
			<DropdownMenuTrigger asChild>
				<Button variant="ghost" size="icon" aria-label="Cambiar tema">
					{!mounted || theme === "system" ? (
						<Monitor className="h-4 w-4" />
					) : theme === "light" ? (
						<Sun className="h-4 w-4" />
					) : (
						<Moon className="h-4 w-4" />
					)}
				</Button>
			</DropdownMenuTrigger>
			<DropdownMenuContent align="end">
				<DropdownMenuItem onClick={() => setTheme("light")}>
					<Sun className="mr-2 h-4 w-4" /> Claro
				</DropdownMenuItem>
				<DropdownMenuItem onClick={() => setTheme("dark")}>
					<Moon className="mr-2 h-4 w-4" /> Oscuro
				</DropdownMenuItem>
				<DropdownMenuItem onClick={() => setTheme("system")}>
					<Monitor className="mr-2 h-4 w-4" /> Sistema
				</DropdownMenuItem>
			</DropdownMenuContent>
		</DropdownMenu>
	);
}
