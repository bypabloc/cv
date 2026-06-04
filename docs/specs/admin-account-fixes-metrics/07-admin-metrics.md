# 07 — Admin: /metrics (gráfica, retención, rango CloudWatch, refresh)

[← panel seguridad](06-admin-security-panel.md) · [Siguiente: ejecución →](08-ejecucion.md)

> Cubre AC-16..AC-20. Frontend admin (consume el analytics extendido de fase
> 4).

## AC-16 — gráfica "Eventos en el tiempo" vacía (diagnóstico + fix)

El `TimeseriesChart` mapea `data.points` correcto y el JSON real del usuario
tiene 8 puntos (counts 6..3875). La gráfica muestra el eje Y (hasta 4000) sin
línea. Diagnóstico en runtime con el JSON real como fixture:

- Hipótesis 1: `data?.timeseries` que llega del `dashboard` tiene los points
  pero el componente recibe `undefined` por un desajuste de key en el
  `DashboardResponse` (ej. `dashboard.timeseries.points` vs lo que el cliente
  desempaqueta). Verificar `analytics-client.dashboard()` + el tipo
  `TimeseriesResponse`.
- Hipótesis 2: el XAxis con `dataKey="ts"` (categórico) y `type="monotone"`
  con `dot={false}` no dibuja si hay 1 punto o si los `ts` colapsan. Con 8
  puntos debería dibujar; confirmar.
- Hipótesis 3: el `stroke="var(--primary)"` resuelve a un color
  transparente/igual al fondo en el theme actual → la línea existe pero es
  invisible. **Sospechoso fuerte** (la imagen muestra el grid pero no la
  línea). Verificar que `--primary` tiene contraste; si es el caso, usar un
  color explícito del DS o `dot` visible.

Fix según hallazgo + test con el JSON real del usuario como fixture (8 puntos)
que asserta que se renderizan los `<path>`/puntos de la línea.

## AC-17 — tooltip de retención (D-9)

`RetentionChart.tsx`: agregar una leyenda/tooltip que explique:
"Nuevos = primera visita en el rango. Recurrentes = ya habían visitado antes
del rango y volvieron. 0% = ningún visitante previo volvió en este rango."
SIN mención a correos. No toca el backend (la lógica es correcta).

## AC-18 / AC-19 — selector de rango estilo CloudWatch (D-7, fase 4)

Reemplazar `MetricsDateRange` (hoy 2 calendarios simples) por un dropdown que
replica la imagen:

- Trigger: botón con el rango actual.
- Popover con barra superior de chips: `5m | 30m | 1h | 3h | 12h | Custom` +
  toggle `Compare (Off)` (decorativo/no-op por ahora).
- Pestañas `Relative | Absolute`:
  - **Relative**: grid de presets — `Minutes (5/10/15/30/45)`,
    `Hours (1/2/3/6/8/12)`, `Days (1/2/3/4/5/6)`, `Weeks (1/2/3/4)` +
    `Duration` (input numérico) + `Unit of time` (dropdown Minutes/Hours/
    Days/Weeks). Botones `Cancel` / `Apply`.
  - **Absolute**: 2 calendarios lado a lado (mes actual + siguiente) +
    inputs `Start date`, `Start time`, `End date`, `End time` (formato
    YY/MM/DD + hh:mm:ss 24h). Botones `Cancel` / `Apply`.

Al aplicar:
- Relative: calcula `from = now - duración`, `to = now`, en **datetime ISO**
  (con hora). El `bucket` se deriva de la duración: < ~2h → `minute`;
  < ~3d → `hour`; resto → `day`/`week`. La page pasa `from`/`to` datetime +
  el `bucket` derivado al `useDashboard`.
- Absolute: `from`/`to` como datetime ISO (con la hora elegida) + bucket
  derivado del span.

El `useMetricsRange` pasa a manejar `{from, to}` como **datetime ISO** (no
solo `YYYY-MM-DD`) + el `bucket` derivado. El backend (fase 4) ya acepta
datetime + bucket minute/hour. La page deja de hardcodear `bucket: "day"`.

> Componente nuevo: `MetricsRangePicker.tsx` (reemplaza `MetricsDateRange`).
> Construir con primitivas shadcn (Popover, Tabs, Button, Calendar, Input,
> Select). Replica visual de la imagen. Es el componente más grande de la
> fase.

## AC-20 — sin polling, botón "Actualizar" (D-8)

- `use-dashboard.ts`: quitar `refetchInterval: 15_000`. `staleTime` puede
  quedar alto (60s) o `Infinity` (solo recarga manual). Sin
  `refetchOnWindowFocus`.
- `use-active-now.ts`: quitar `refetchInterval`. El badge active-now se
  recarga con el botón.
- `metrics/page.tsx`: agregar un botón "Actualizar" en el header que
  `queryClient.invalidateQueries({ queryKey: analyticsKeys.all })` (o el
  prefijo de analytics) → recarga todas las queries de analytics incl.
  active-now. Mostrar un spinner mientras `isFetching`.

## 7. Archivos afectados (fase 7)

### Crear
- `admin/src/features/analytics/components/MetricsRangePicker.tsx` — dropdown
  CloudWatch (Relative/Absolute). [AC-18, AC-19]
- `admin/src/features/analytics/lib/range-presets.ts` — helpers: preset →
  `{from, to, bucket}` datetime; bucket derivado del span.
- `admin/tests/unit/features/analytics/components/MetricsRangePicker.test.tsx`
  [AC-18, AC-19]
- `admin/tests/unit/features/analytics/lib/range-presets.test.ts` — preset
  "1h" → from/to datetime + bucket minute/hour. [AC-19]
- `admin/tests/unit/features/analytics/components/TimeseriesChart-renders.test.tsx`
  — con el JSON real (8 puntos) renderiza la línea. [AC-16]

### Modificar
- `admin/src/features/analytics/components/TimeseriesChart.tsx` — fix de
  render (según diagnóstico: color, key o shape). [AC-16]
  - Verificar: el test de render + visual en preview.
- `admin/src/features/analytics/components/RetentionChart.tsx` — tooltip
  explicativo. [AC-17]
- `admin/src/features/analytics/hooks/use-metrics-range.ts` — `{from, to}`
  datetime ISO + `bucket` derivado.
- `admin/src/features/analytics/hooks/use-dashboard.ts` — quitar
  `refetchInterval`. [AC-20]
- `admin/src/features/analytics/hooks/use-active-now.ts` — quitar
  `refetchInterval`. [AC-20]
- `admin/src/app/(admin)/metrics/page.tsx` — usar `MetricsRangePicker`, pasar
  `bucket` derivado (no hardcodear "day"), botón "Actualizar". [AC-18, AC-20]
- `admin/src/features/analytics/types.ts` — `DateRangeParams`/
  `DashboardParams` con `from`/`to` datetime + `bucket` extendido (minute).
- `admin/src/features/analytics/api/query-keys.ts` — si hace falta un
  `analyticsKeys.all` para invalidar todo.
- `admin/tests/unit/features/analytics/hooks/...` — ajustar tests que
  asumían `refetchInterval` o `bucket: "day"`.

### Eliminar
- `admin/src/features/analytics/components/MetricsDateRange.tsx` — lo
  reemplaza `MetricsRangePicker`.

## Verificación (fase 7)

```bash
pnpm --filter @portfolio/admin lint
pnpm --filter @portfolio/admin typecheck
pnpm --filter @portfolio/admin test
pnpm --filter @portfolio/admin build
```

Parte C (dev real): /metrics dibuja la línea de eventos; retención con
tooltip; el dropdown CloudWatch funciona (Relative "1h" → datetime + bucket);
sin polling; el botón "Actualizar" recarga. [AC-16..AC-20]

[← panel seguridad](06-admin-security-panel.md) · [Siguiente: ejecución →](08-ejecucion.md)
