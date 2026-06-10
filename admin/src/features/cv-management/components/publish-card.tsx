"use client";

import { Rocket } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import {
	AlertDialog,
	AlertDialogAction,
	AlertDialogCancel,
	AlertDialogContent,
	AlertDialogDescription,
	AlertDialogFooter,
	AlertDialogHeader,
	AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { usePublish, usePublishStatus } from "../hooks/use-publish";
import type { PublishStatusResponse } from "../types";

/**
 * @component PublishCard
 * @description Boton "Publicar cambios" con AlertDialog de confirmacion
 *   (avisa que dispara el deploy de las 6 apps del env): publish.dispatch
 *   -> toast con link a GitHub Actions. Muestra el publish-status (ultimo
 *   run del ref del stage).
 */
function statusLabel(status: PublishStatusResponse | undefined): string {
	if (!status || status.status === "none") {
		return "Sin publicaciones recientes";
	}
	const conclusion = status.conclusion ? ` · ${status.conclusion}` : "";
	const created = status.created_at ? ` · ${status.created_at}` : "";
	return `${status.status}${conclusion}${created}`;
}

export function PublishCard() {
	const status = usePublishStatus();
	const publish = usePublish();
	const [confirmOpen, setConfirmOpen] = useState(false);

	const handleConfirm = (): void => {
		setConfirmOpen(false);
		publish.mutate(undefined, {
			onSuccess: (envelope) => {
				toast.success(
					<span>
						Publicacion lanzada.{" "}
						<a
							data-testid="cv-publish-actions-link"
							className="underline"
							href={envelope.data.actions_url}
							target="_blank"
							rel="noreferrer"
						>
							Ver en Actions
						</a>
					</span>,
				);
			},
		});
	};

	return (
		<Card data-testid="cv-publish-card">
			<CardHeader>
				<CardTitle className="flex items-center gap-2">
					<Rocket className="h-4 w-4" /> Publicar cambios
				</CardTitle>
				<CardDescription>
					Dispara el workflow de deploy de las 6 apps del entorno con el
					contenido actual del CV.
				</CardDescription>
			</CardHeader>
			<CardContent className="flex flex-wrap items-center justify-between gap-3">
				<div
					data-testid="cv-publish-status"
					className="text-sm text-muted-foreground"
				>
					{status.isLoading ? (
						<Skeleton className="h-4 w-48" />
					) : (
						<span>
							{statusLabel(status.data)}{" "}
							{status.data?.url ? (
								<a
									className="underline"
									href={status.data.url}
									target="_blank"
									rel="noreferrer"
								>
									Ver run
								</a>
							) : null}
						</span>
					)}
				</div>
				<Button
					type="button"
					data-testid="cv-publish-button"
					disabled={publish.isPending}
					onClick={() => setConfirmOpen(true)}
				>
					{publish.isPending ? "Publicando..." : "Publicar cambios"}
				</Button>
			</CardContent>

			<AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
				<AlertDialogContent>
					<AlertDialogHeader>
						<AlertDialogTitle>Publicar el CV</AlertDialogTitle>
						<AlertDialogDescription>
							Esto dispara un deploy de las 6 apps del entorno (workflow
							deploy-apps.yml). El contenido actual de la base de datos se
							publicara en el sitio.
						</AlertDialogDescription>
					</AlertDialogHeader>
					<AlertDialogFooter>
						<AlertDialogCancel data-testid="cv-publish-cancel">
							Cancelar
						</AlertDialogCancel>
						<AlertDialogAction
							data-testid="cv-publish-confirm"
							onClick={handleConfirm}
						>
							Publicar
						</AlertDialogAction>
					</AlertDialogFooter>
				</AlertDialogContent>
			</AlertDialog>
		</Card>
	);
}
