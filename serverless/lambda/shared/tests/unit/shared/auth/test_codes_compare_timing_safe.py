"""
Given un code correcto y un code incorrecto del mismo length,
When se ejecuta compare_code 200 veces para cada caso,
Then el tiempo total es similar (delta < factor 2x) — smoke test de
secrets.compare_digest siendo timing-safe.

Nota: este test es heuristico, no determinista. Sirve para detectar
regresiones obvias (ej. si alguien cambia compare_code por '==').
"""

import time

import pytest
from shared.auth.codes import compare_code, generate_code, hash_code

pytestmark = pytest.mark.unit


def _bench(*, code: str, stored_hash: bytes, iterations: int) -> float:
    start = time.perf_counter()
    for _ in range(iterations):
        compare_code(code=code, stored_hash=stored_hash)
    return time.perf_counter() - start


def test_codes_compare_timing_is_similar_for_correct_and_wrong():
    # Arrange
    correct = generate_code()
    wrong = generate_code()
    while wrong == correct:
        wrong = generate_code()
    stored = hash_code(correct)
    iterations = 200

    # Warm-up
    _bench(code=correct, stored_hash=stored, iterations=50)
    _bench(code=wrong, stored_hash=stored, iterations=50)

    # Act
    t_correct = _bench(code=correct, stored_hash=stored, iterations=iterations)
    t_wrong = _bench(code=wrong, stored_hash=stored, iterations=iterations)

    # Assert: ratio < 2x. Tolerancia generosa porque GC/jit puede afectar.
    ratio = max(t_correct, t_wrong) / min(t_correct, t_wrong)
    assert ratio < 2.0, f'ratio={ratio} t_correct={t_correct} t_wrong={t_wrong}'
