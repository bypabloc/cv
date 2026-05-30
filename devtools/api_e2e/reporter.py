"""Registro de resultados + reporte (pass/fail por caso + tiempos avg).

Cada llamada a un endpoint produce un `CaseResult`. El `Reporter`
acumula todos, imprime cada caso al vuelo y, al final, un resumen de
tiempos de respuesta promedio por endpoint + el veredicto pass/fail.
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
        """Promedio de todos los samples (segundos)."""
        return sum(self.elapsed) / len(self.elapsed) if self.elapsed else 0.0

    @property
    def cold(self) -> float:
        """Primer sample (peor caso / cold)."""
        return self.elapsed[0] if self.elapsed else 0.0

    @property
    def warm_avg(self) -> float:
        """Promedio de los samples 2..N; cae al unico si hay 1 sample."""
        warm = self.elapsed[1:] or self.elapsed
        return sum(warm) / len(warm) if warm else 0.0


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

    def print_timing_summary(self) -> None:
        """Tabla de tiempos de respuesta promedio por endpoint."""
        print()
        print('=' * 80)
        print('TIEMPOS DE RESPUESTA PROMEDIO (segundos)')
        print('=' * 80)
        print(f'{"Lambda":<15}{"Caso":<48}{"cold":>8}{"warm":>8}')
        print('-' * 80)
        for r in self.results:
            print(
                f'{r.lambda_name:<15}{r.name:<48}'
                f'{r.cold:>8.3f}{r.warm_avg:>8.3f}'
            )
        print('-' * 80)
        ok = [r for r in self.results if r.passed and r.elapsed]
        if ok:
            g_warm = sum(r.warm_avg for r in ok) / len(ok)
            g_cold = sum(r.cold for r in ok) / len(ok)
            print(f'{"GLOBAL (OK)":<15}{"":<48}{g_cold:>8.3f}{g_warm:>8.3f}')

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
