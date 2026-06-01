"use client";

import { Menu } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
	Sheet,
	SheetContent,
	SheetTitle,
	SheetTrigger,
} from "@/components/ui/sheet";
import { cn } from "@/lib/utils";
import { NAV_ITEMS } from "../lib/nav-items";

/**
 * @component MobileSidebar
 * @description Navegacion en mobile via Sheet (mismos items que Sidebar).
 *   El trigger (hamburguesa) solo se muestra por debajo de lg.
 */
export function MobileSidebar() {
	const pathname = usePathname();
	const [open, setOpen] = useState(false);

	return (
		<Sheet open={open} onOpenChange={setOpen}>
			<SheetTrigger asChild>
				<Button
					variant="ghost"
					size="icon"
					className="lg:hidden"
					aria-label="Abrir menu"
				>
					<Menu className="h-5 w-5" />
				</Button>
			</SheetTrigger>
			<SheetContent side="left" className="w-60 p-0">
				<SheetTitle className="px-6 py-4 font-mono text-sm uppercase tracking-widest text-muted-foreground">
					Admin
				</SheetTitle>
				<nav className="space-y-1 px-3">
					{NAV_ITEMS.map(({ href, label, icon: Icon }) => {
						const active = pathname === href || pathname.startsWith(`${href}/`);
						return (
							<Link
								key={href}
								href={href}
								onClick={() => setOpen(false)}
								className={cn(
									"flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
									active
										? "bg-accent text-accent-foreground"
										: "text-muted-foreground hover:bg-accent hover:text-foreground",
								)}
							>
								<Icon className="h-4 w-4" />
								{label}
							</Link>
						);
					})}
				</nav>
			</SheetContent>
		</Sheet>
	);
}
