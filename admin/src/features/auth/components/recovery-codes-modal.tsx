"use client";

import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogTitle,
} from "@/components/ui/dialog";

/**
 * @component RecoveryCodesModal
 * @description Muestra los 10 recovery codes UNA sola vez (no se vuelven a
 *   leer) + acciones Copiar / Descargar. El caller controla `open`/`onClose`.
 *
 * @props {boolean} open - Si el modal esta abierto
 * @props {string[]} codes - Los 10 codes a mostrar
 * @props {() => void} onClose - Cierra el modal
 */
export function RecoveryCodesModal({
	open,
	codes,
	onClose,
}: {
	open: boolean;
	codes: string[];
	onClose: () => void;
}) {
	const onCopy = async () => {
		await navigator.clipboard.writeText(codes.join("\n"));
		toast.success("Codigos copiados");
	};

	const onDownload = () => {
		const blob = new Blob([codes.join("\n")], { type: "text/plain" });
		const url = URL.createObjectURL(blob);
		const link = document.createElement("a");
		link.href = url;
		link.download = "recovery-codes.txt";
		link.click();
		URL.revokeObjectURL(url);
	};

	return (
		<Dialog open={open} onOpenChange={(next) => !next && onClose()}>
			<DialogContent>
				<DialogHeader>
					<DialogTitle>Codigos de recuperacion</DialogTitle>
					<DialogDescription>
						Guardalos ahora: no se volveran a mostrar.
					</DialogDescription>
				</DialogHeader>

				<ul className="grid grid-cols-2 gap-2 font-mono text-sm">
					{codes.map((code) => (
						<li key={code}>{code}</li>
					))}
				</ul>

				<DialogFooter>
					<Button
						type="button"
						variant="outline"
						onClick={() => {
							void onCopy();
						}}
					>
						Copiar
					</Button>
					<Button type="button" variant="outline" onClick={onDownload}>
						Descargar
					</Button>
					<Button type="button" onClick={onClose}>
						Ya los guarde
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
