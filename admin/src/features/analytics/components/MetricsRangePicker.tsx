"use client";

import { CalendarIcon } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Input } from "@/components/ui/input";
import {
	Popover,
	PopoverContent,
	PopoverTrigger,
} from "@/components/ui/popover";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
	combineDateTime,
	formatRangeLabel,
	handleDayPick,
	QUICK_PRESETS,
	RELATIVE_GRID,
	type RelativeUnit,
	type ResolvedRange,
	resolveAbsolute,
	resolveRelative,
	toDateInput,
	toTimeInput,
} from "../lib/range-presets";

/**
 * @component MetricsRangePicker
 * @description Selector de rango estilo Amazon CloudWatch: chips rapidos
 *   (5m/30m/1h/3h/12h/Custom), pestana Relative (grid Minutes/Hours/Days/Weeks
 *   + Duration + Unit) y pestana Absolute (2 calendarios + Start/End date+time).
 *   Al aplicar produce `{from, to, bucket}` (from/to datetime ISO, bucket
 *   derivado del span) que consume la page /metrics.
 *
 * @props {ResolvedRange} range - rango actual.
 * @props {(range: ResolvedRange) => void} onChange - callback al aplicar.
 */
const UNIT_LABELS: Record<RelativeUnit, string> = {
	minutes: "Minutes",
	hours: "Hours",
	days: "Days",
	weeks: "Weeks",
};

export function MetricsRangePicker({
	range,
	onChange,
}: {
	range: ResolvedRange;
	onChange: (range: ResolvedRange) => void;
}) {
	const [open, setOpen] = useState(false);
	const [tab, setTab] = useState<"relative" | "absolute">("relative");

	// Relative custom (Duration + Unit).
	const [amount, setAmount] = useState(1);
	const [unit, setUnit] = useState<RelativeUnit>("hours");

	// Absolute (from/to date+time).
	const [fromDate, setFromDate] = useState(() =>
		toDateInput(new Date(range.from)),
	);
	const [fromTime, setFromTime] = useState(() =>
		toTimeInput(new Date(range.from)),
	);
	const [toDate, setToDate] = useState(() => toDateInput(new Date(range.to)));
	const [toTime, setToTime] = useState(() => toTimeInput(new Date(range.to)));

	const apply = (resolved: ResolvedRange) => {
		onChange(resolved);
		setOpen(false);
	};

	const applyRelative = () => {
		apply(resolveRelative(Math.max(1, amount), unit));
	};

	const applyAbsolute = () => {
		const from = combineDateTime(fromDate, fromTime);
		const to = combineDateTime(toDate, toTime);
		if (from && to) {
			apply(resolveAbsolute(from, to));
		}
	};

	return (
		<Popover open={open} onOpenChange={setOpen}>
			<PopoverTrigger asChild>
				<Button variant="outline" size="sm" className="gap-2">
					<CalendarIcon className="h-4 w-4" />
					{formatRangeLabel(range)}
				</Button>
			</PopoverTrigger>
			<PopoverContent className="w-[min(92vw,28rem)] p-0" align="end">
				{/* Fila superior de chips rapidos (replica la imagen). */}
				<div className="flex flex-wrap items-center gap-1 border-b p-2">
					{QUICK_PRESETS.map((preset) => (
						<Button
							key={preset.id}
							type="button"
							variant="ghost"
							size="sm"
							onClick={() => apply(resolveRelative(preset.amount, preset.unit))}
						>
							{preset.label}
						</Button>
					))}
					<Button
						type="button"
						variant="secondary"
						size="sm"
						onClick={() => setTab("relative")}
					>
						Custom
					</Button>
				</div>

				<Tabs
					value={tab}
					onValueChange={(value) => setTab(value as "relative" | "absolute")}
					className="p-3"
				>
					<TabsList className="mb-3">
						<TabsTrigger value="relative">Relative</TabsTrigger>
						<TabsTrigger value="absolute">Absolute</TabsTrigger>
					</TabsList>

					<TabsContent value="relative" className="space-y-4">
						{(Object.keys(RELATIVE_GRID) as RelativeUnit[]).map((u) => (
							<div key={u} className="flex items-center gap-2">
								<span className="w-16 text-xs text-muted-foreground">
									{UNIT_LABELS[u]}
								</span>
								<div className="flex flex-wrap gap-1">
									{RELATIVE_GRID[u].map((n) => (
										<Button
											key={`${u}-${n}`}
											type="button"
											variant={
												amount === n && unit === u ? "default" : "outline"
											}
											size="sm"
											onClick={() => apply(resolveRelative(n, u))}
										>
											{n}
										</Button>
									))}
								</div>
							</div>
						))}

						<div className="flex flex-wrap items-end gap-3 border-t pt-3">
							<div className="flex flex-col gap-1 text-xs text-muted-foreground">
								<label htmlFor="range-duration">Duration</label>
								<Input
									id="range-duration"
									type="number"
									min={1}
									value={amount}
									onChange={(e) => setAmount(Number(e.target.value))}
									className="w-24"
								/>
							</div>
							<div className="flex flex-col gap-1 text-xs text-muted-foreground">
								<label htmlFor="range-unit">Unit of time</label>
								<Select
									value={unit}
									onValueChange={(value) => setUnit(value as RelativeUnit)}
								>
									<SelectTrigger id="range-unit" className="w-32">
										<SelectValue />
									</SelectTrigger>
									<SelectContent>
										<SelectItem value="minutes">Minutes</SelectItem>
										<SelectItem value="hours">Hours</SelectItem>
										<SelectItem value="days">Days</SelectItem>
										<SelectItem value="weeks">Weeks</SelectItem>
									</SelectContent>
								</Select>
							</div>
							<Button type="button" size="sm" onClick={applyRelative}>
								Apply
							</Button>
						</div>
					</TabsContent>

					<TabsContent value="absolute" className="space-y-3">
						<div className="flex flex-wrap gap-3">
							<Calendar
								mode="single"
								selected={combineDateTime(fromDate, fromTime) ?? undefined}
								onSelect={(d) => handleDayPick(d, setFromDate)}
							/>
							<Calendar
								mode="single"
								selected={combineDateTime(toDate, toTime) ?? undefined}
								onSelect={(d) => handleDayPick(d, setToDate)}
							/>
						</div>
						<div className="grid grid-cols-2 gap-3">
							<div className="flex flex-col gap-1 text-xs text-muted-foreground">
								<label htmlFor="range-from-date">Start date</label>
								<Input
									id="range-from-date"
									value={fromDate}
									placeholder="YYYY-MM-DD"
									onChange={(e) => setFromDate(e.target.value)}
								/>
							</div>
							<div className="flex flex-col gap-1 text-xs text-muted-foreground">
								<label htmlFor="range-from-time">Start time</label>
								<Input
									id="range-from-time"
									value={fromTime}
									placeholder="hh:mm:ss"
									onChange={(e) => setFromTime(e.target.value)}
								/>
							</div>
							<div className="flex flex-col gap-1 text-xs text-muted-foreground">
								<label htmlFor="range-to-date">End date</label>
								<Input
									id="range-to-date"
									value={toDate}
									placeholder="YYYY-MM-DD"
									onChange={(e) => setToDate(e.target.value)}
								/>
							</div>
							<div className="flex flex-col gap-1 text-xs text-muted-foreground">
								<label htmlFor="range-to-time">End time</label>
								<Input
									id="range-to-time"
									value={toTime}
									placeholder="hh:mm:ss"
									onChange={(e) => setToTime(e.target.value)}
								/>
							</div>
						</div>
						<div className="flex justify-end gap-2">
							<Button
								type="button"
								variant="ghost"
								size="sm"
								onClick={() => setOpen(false)}
							>
								Cancel
							</Button>
							<Button type="button" size="sm" onClick={applyAbsolute}>
								Apply
							</Button>
						</div>
					</TabsContent>
				</Tabs>
			</PopoverContent>
		</Popover>
	);
}
