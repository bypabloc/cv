"""Registro de resultados + reporte (pass/fail por caso + tiempos avg).

Cada llamada a un endpoint produce un `CaseResult`. El `Reporter`
acumula todos, imprime cada caso al vuelo y, al final, un resumen de
tiempos de respuesta + el veredicto pass/fail.

El cold start es un fenomeno POR-LAMBDA (lo paga solo el PRIMER invoke del
contenedor). Por eso el reporte NO atribuye un cold a cada caso: lo agrupa
por Lambda y lo asigna al PRIMER caso de cada Lambda (en orden de ejecucion,
que es el orden de insercion). Los casos siguientes ya corren sobre el
contenedor caliente -> su tiempo cuenta como warm, NO como cold.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field


@dataclass
class CaseResult:
    """Resultado de un caso (1 endpoint, 1 escenario, N samples)."""

    lambda_name: str
    name: str
    method: str
    status_codes: list[int]
    expected: str
    passed: bool
    elapsed: list[float]
    note: str = ''

    @property
    def avg(self) -> float:
        """Promedio de TODOS los samples (segundos)."""
        return sum(self.elapsed) / len(self.elapsed) if self.elapsed else 0.0

    @property
    def cold(self) -> float:
        """Primer sample del caso (peor caso del caso, NO el cold del Lambda).

        OJO: solo es el cold start REAL del Lambda si este caso fue el PRIMER
        invoke de su contenedor. La atribucion correcta la hace el Reporter
        en `timing_rows()`; esta propiedad es el dato crudo per-caso.
        """
        return self.elapsed[0] if self.elapsed else 0.0


@dataclass
class TimingRow:
    """Fila de tiempos ya clasificada cold/warm a nivel Lambda.

    `cold` solo esta poblado en el PRIMER caso de cada Lambda (su primer
    invoke real); en el resto es None porque el contenedor ya estaba caliente.
    `warm` es el promedio de los samples calientes del caso: del primer caso
    son los samples 2..N (el 1ro fue el cold); del resto, TODOS sus samples.
    """

    lambda_name: str
    name: str
    cold: float | None
    warm: float | None
    passed: bool


@dataclass
class Reporter:
    """Acumula CaseResult e imprime el reporte final."""

    results: list[CaseResult] = field(default_factory=list)

    def add(self, result: CaseResult) -> None:
        """Registra un caso e imprime su linea inmediatamente."""
        self.results.append(result)
        mark = 'PASS' if result.passed else 'FAIL'
        suffix = f'  ({result.note})' if result.note else ''
        print(
            f'  [{mark}] {result.name:<48} '
            f'codes={result.status_codes} avg={result.avg:.3f}s{suffix}',
            flush=True,
        )

    def passed_count(self) -> int:
        """Numero de casos que pasaron."""
        return sum(1 for r in self.results if r.passed)

    def all_passed(self) -> bool:
        """True si todos los casos pasaron."""
        return all(r.passed for r in self.results)

    def timing_rows(self) -> list[TimingRow]:
        """Clasifica cada caso en cold (1er invoke del Lambda) + warm.

        Recorre los resultados en orden de ejecucion (= orden de insercion).
        El PRIMER caso con samples de cada Lambda se lleva el cold start; el
        resto corre caliente (cold=None). Ver el docstring del modulo.
        """
        seen: set[str] = set()
        rows: list[TimingRow] = []
        for r in self.results:
            is_first = r.lambda_name not in seen
            if not r.elapsed:
                rows.append(
                    TimingRow(r.lambda_name, r.name, None, None, r.passed)
                )
                continue
            seen.add(r.lambda_name)
            if is_first:
                cold: float | None = r.elapsed[0]
                warm_samples = r.elapsed[1:]
            else:
                cold = None
                warm_samples = r.elapsed
            warm = (
                sum(warm_samples) / len(warm_samples) if warm_samples else None
            )
            rows.append(TimingRow(r.lambda_name, r.name, cold, warm, r.passed))
        return rows

    def cold_start_by_lambda(self) -> dict[str, float]:
        """Cold start por Lambda: el primer invoke (passed) de cada contenedor.

        Mapea lambda_name -> segundos del primer invoke real. Solo cuenta
        casos que pasaron (un caso fallido tiene timing no confiable).
        """
        cold: dict[str, float] = {}
        for row in self.timing_rows():
            if row.cold is not None and row.passed:
                cold[row.lambda_name] = row.cold
        return cold

    def print_timing_summary(self) -> None:
        """Cold start por Lambda (agrupado) + tiempos por caso (cold/warm)."""
        rows = self.timing_rows()
        cold_by_lambda = self.cold_start_by_lambda()

        # 1) Cold start por Lambda (agrupado por path: 1 cold por contenedor).
        print()
        print('=' * 80)
        print('COLD START POR LAMBDA (primer invoke del contenedor, segundos)')
        print('=' * 80)
        print(f'{"Lambda":<15}{"cold":>8}  primer caso')
        print('-' * 80)
        first_case: dict[str, str] = {}
        for row in rows:
            if row.cold is not None and row.lambda_name not in first_case:
                first_case[row.lambda_name] = row.name
        for lambda_name, cold in cold_by_lambda.items():
            print(
                f'{lambda_name:<15}{cold:>8.3f}  '
                f'{first_case.get(lambda_name, "")}'
            )
        print('-' * 80)
        if cold_by_lambda:
            avg_cold = sum(cold_by_lambda.values()) / len(cold_by_lambda)
            print(f'{"COLD avg":<15}{avg_cold:>8.3f}')

        # 2) Detalle por caso: cold solo en el 1er invoke; el resto, warm.
        print()
        print('=' * 80)
        print("TIEMPOS POR CASO (segundos) — cold='-' = Lambda ya caliente")
        print('=' * 80)
        print(f'{"Lambda":<15}{"Caso":<48}{"cold":>8}{"warm":>8}')
        print('-' * 80)
        warm_ok: list[float] = []
        for row in rows:
            cold_cell = (
                f'{row.cold:>8.3f}' if row.cold is not None else f'{"-":>8}'
            )
            warm_cell = (
                f'{row.warm:>8.3f}' if row.warm is not None else f'{"-":>8}'
            )
            print(f'{row.lambda_name:<15}{row.name:<48}{cold_cell}{warm_cell}')
            if row.warm is not None and row.passed:
                warm_ok.append(row.warm)
        print('-' * 80)
        g_cold = (
            sum(cold_by_lambda.values()) / len(cold_by_lambda)
            if cold_by_lambda
            else None
        )
        g_warm = sum(warm_ok) / len(warm_ok) if warm_ok else None
        g_cold_cell = f'{g_cold:>8.3f}' if g_cold is not None else f'{"-":>8}'
        g_warm_cell = f'{g_warm:>8.3f}' if g_warm is not None else f'{"-":>8}'
        label = 'cold=avg/Lambda, warm=avg casos'
        print(f'{"GLOBAL":<15}{label:<48}{g_cold_cell}{g_warm_cell}')

    def print_final(self) -> None:
        """Resumen pass/fail + listado de fallos."""
        total = len(self.results)
        ok = self.passed_count()
        print()
        print('=' * 80)
        print(f'RESULTADO: {ok}/{total} casos PASS')
        print('=' * 80)
        fails = [r for r in self.results if not r.passed]
        if fails:
            print('FALLOS:')
            for r in fails:
                note = f' ({r.note})' if r.note else ''
                print(
                    f'  {r.lambda_name}.{r.name} '
                    f'codes={r.status_codes} esperado={r.expected}{note}'
                )
