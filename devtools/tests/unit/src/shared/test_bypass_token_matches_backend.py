"""Paridad firma-devtools / verifica-backend del token de bypass.

devtools (`devtools/shared/bypass_token.py`) firma; el backend
(`serverless/lambda/shared/crypto/bypass_token.py`) verifica. Como ambos
usan el namespace `shared.*` y NO se pueden importar a la vez, este test
firma con devtools y verifica el token corriendo el verificador del
backend en un SUBPROCESO aislado (su propio sys.path).

Es el ancla que evita que los dos formatos se desincronicen.
"""

from pathlib import Path
import subprocess
import sys
import time

import pytest

from shared.bypass_token import generate_keypair
from shared.bypass_token import sign_bypass_token


# Repo root: devtools/tests/unit/src/shared/<file> -> parents[5].
_REPO_ROOT = Path(__file__).resolve().parents[5]
_BACKEND_LAMBDA = _REPO_ROOT / 'serverless' / 'lambda'


def _verify_with_backend(token: str, public_key_b64: str, stage: str) -> str:
    """Corre el verificador del backend en subproceso; devuelve 'OK'/'FAIL:..'.

    Usa el python del .venv del backend (tiene cryptography) si existe;
    si no, el del proceso actual (devtools .venv tambien la tiene).
    """
    backend_venv = _REPO_ROOT / 'serverless' / '.venv' / 'bin' / 'python'
    interpreter = str(backend_venv) if backend_venv.exists() else sys.executable
    # El verificador lee token / public_key / stage / backend-path de argv
    # (no interpolados en el source) para evitar inyeccion de codigo.
    script = (
        'import sys, time\n'
        'sys.path.insert(0, sys.argv[1])\n'
        'from shared.crypto.bypass_token import verify_bypass_token\n'
        'token, pub, stage = sys.argv[2], sys.argv[3], sys.argv[4]\n'
        'try:\n'
        '    p = verify_bypass_token('
        'token, public_key_b64=pub, stage=stage, now=int(time.time()) + 5)\n'
        '    print("OK" if p["stage"] == stage else "FAIL:stage")\n'
        'except Exception as e:\n'
        '    print(f"FAIL:{type(e).__name__}")\n'
    )
    result = subprocess.run(  # noqa: S603 -- interpreter de confianza (.venv)
        [
            interpreter,
            '-c',
            script,
            str(_BACKEND_LAMBDA),
            token,
            public_key_b64,
            stage,
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return (result.stdout or result.stderr).strip().splitlines()[-1]


@pytest.mark.unit
def test_devtools_token_verifies_on_backend() -> None:
    """
    Given un token firmado por devtools para stage='dev',
    When lo verifica el verificador del backend con la publica del par,
    Then el backend lo acepta (paridad de formato).
    """
    private_b64, public_b64 = generate_keypair()
    token = sign_bypass_token(
        stage='dev',
        private_key_b64=private_b64,
        now=int(time.time()),
    )

    verdict = _verify_with_backend(token, public_b64, 'dev')

    assert verdict == 'OK'


@pytest.mark.unit
def test_backend_rejects_wrong_stage_token() -> None:
    """
    Given un token devtools firmado para 'dev',
    When el backend lo verifica exigiendo stage='stage',
    Then lo rechaza (stage-binding) — la paridad incluye el mismatch.
    """
    private_b64, public_b64 = generate_keypair()
    token = sign_bypass_token(
        stage='dev',
        private_key_b64=private_b64,
        now=int(time.time()),
    )

    verdict = _verify_with_backend(token, public_b64, 'stage')

    assert verdict.startswith('FAIL')
