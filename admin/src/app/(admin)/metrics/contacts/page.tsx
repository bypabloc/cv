"use client";

import { Mail } from "lucide-react";
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorAlert } from "@/components/ui/error-alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MetricsDateRange } from "@/features/analytics/components/MetricsDateRange";
import { useMetricsRange } from "@/features/analytics/hooks/use-metrics-range";
import { ContactByStatusChart } from "@/features/contacts/components/ContactByStatusChart";
import { ContactByStatusTable } from "@/features/contacts/components/ContactByStatusTable";
import { ContactListTable } from "@/features/contacts/components/ContactListTable";
import { ContactStatusFilter } from "@/features/contacts/components/ContactStatusFilter";
import { useContactList } from "@/features/contacts/hooks/use-contact-list";
import { useContactsByStatus } from "@/features/contacts/hooks/use-contacts-by-status";
import type { ContactStatus } from "@/features/contacts/types";

const PAGE_SIZE = 50;

/**
 * @page MetricsContactsPage
 * @description Area de contactos (`/metrics/contacts`) con dos tabs: el
 *   listado crudo paginado (contacts/list, con filtro por estado) y el
 *   desglose por estado (contacts/by-status, chart + tabla). El rango from/to
 *   es compartido por la page. Datos PII: no se persisten.
 */
export default function MetricsContactsPage() {
	const { range, setRange } = useMetricsRange();
	const [page, setPage] = useState(1);
	const [status, setStatus] = useState<ContactStatus | undefined>(undefined);

	const list = useContactList({
		...range,
		page,
		page_size: PAGE_SIZE,
		status,
	});
	const byStatus = useContactsByStatus(range);

	return (
		<section className="space-y-6">
			<header className="flex flex-wrap items-center justify-between gap-3">
				<div className="flex items-center gap-3">
					<Mail className="h-5 w-5 text-muted-foreground" />
					<h1 className="text-2xl font-semibold">Contactos</h1>
				</div>
				<MetricsDateRange
					range={range}
					onChange={(next) => {
						setPage(1);
						setRange(next);
					}}
				/>
			</header>

			<Tabs defaultValue="list">
				<TabsList>
					<TabsTrigger value="list">Listado</TabsTrigger>
					<TabsTrigger value="by-status">Por estado</TabsTrigger>
				</TabsList>

				<TabsContent value="list">
					<Card>
						<CardHeader className="flex flex-row items-center justify-between gap-3 space-y-0">
							<CardTitle>Listado de contactos</CardTitle>
							<ContactStatusFilter
								value={status}
								onChange={(next) => {
									setPage(1);
									setStatus(next);
								}}
							/>
						</CardHeader>
						<CardContent>
							{list.error ? (
								<ErrorAlert error={list.error} />
							) : (
								<ContactListTable
									data={list.data}
									isLoading={list.isLoading}
									page={page}
									onPageChange={setPage}
								/>
							)}
						</CardContent>
					</Card>
				</TabsContent>

				<TabsContent value="by-status">
					<Card>
						<CardHeader>
							<CardTitle>Contactos por estado</CardTitle>
						</CardHeader>
						<CardContent className="space-y-6">
							{byStatus.error ? (
								<ErrorAlert error={byStatus.error} />
							) : (
								<>
									<ContactByStatusChart
										data={byStatus.data}
										isLoading={byStatus.isLoading}
									/>
									{!byStatus.isLoading && byStatus.data ? (
										<ContactByStatusTable items={byStatus.data.items} />
									) : null}
								</>
							)}
						</CardContent>
					</Card>
				</TabsContent>
			</Tabs>
		</section>
	);
}
