"""Runner de casos: ejecuta una llamada N veces y clasifica el resultado.

Un "caso" es una funcion `() -> Response`. El runner la corre `samples`
veces, recolecta status + elapsed y decide PASS/FAIL contra el status
esperado (int, lista de ints, o rango '2xx'/'4xx'/'5xx').
"""

from __future__ import annotations

from collections.abc import Callable

from reporter import CaseResult
from reporter import Reporter
from support import Response


SAMPLES_DEFAULT = 5


def _matches(code: int, expected: object) -> bool:
    if isinstance(expected, bool):  # bool es subclase de int: descartar
        return False
    if isinstance(expected, int):
        return code == expected
    if isinstance(expected, list):
        return code in expected
    if expected == '2xx':
        return 200 <= code < 300
    if expected == '4xx':
        return 400 <= code < 500
    if expected == '5xx':
        return 500 <= code < 600
    return False


def _describe(expected: object) -> str:
    if isinstance(expected, str):
        return expected
    if isinstance(expected, list):
        return f'in {expected}'
    return str(expected)


class Runner:
    """Ejecuta casos contra un reporter compartido."""

    def __init__(self, reporter: Reporter, *, samples: int = SAMPLES_DEFAULT):
        self._reporter = reporter
        self._samples = samples

    def case(
        self,
        *,
        lambda_name: str,
        name: str,
        method: str,
        call: Callable[[], Response],
        expected: object,
        samples: int | None = None,
        note: str = '',
    ) -> Response:
        """Corre `call` N veces, clasifica, registra. Devuelve la ultima
        Response (para encadenar pasos del flujo)."""
        n = samples if samples is not None else self._samples
        codes: list[int] = []
        elapsed: list[float] = []
        last: Response | None = None
        for _ in range(n):
            last = call()
            codes.append(last.status)
            elapsed.append(last.elapsed)
        passed = all(_matches(code, expected) for code in codes)
        self._reporter.add(CaseResult(
            lambda_name=lambda_name,
            name=name,
            method=method,
            status_codes=codes,
            expected=_describe(expected),
            passed=passed,
            elapsed=elapsed,
            note=note,
        ))
        return last  # type: ignore[return-value]

    def step(
        self,
        *,
        lambda_name: str,
        name: str,
        method: str,
        call: Callable[[], Response],
        expected: object,
        note: str = '',
    ) -> Response:
        """Como `case` pero 1 sola muestra (paso que muta estado y no se
        puede repetir, ej. consumir un code single-use)."""
        return self.case(
            lambda_name=lambda_name, name=name, method=method, call=call,
            expected=expected, samples=1, note=note,
        )


def make_body(operation: str, action: str, **fields: object) -> dict:
    """Body FLAT del request: operation/action + campos al nivel raiz."""
    return {'operation': operation, 'action': action, **fields}
