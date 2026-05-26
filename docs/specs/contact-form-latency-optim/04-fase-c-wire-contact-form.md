# Fase C: Wire contact_form al kit shared

## Objetivo

Conectar el lambda `contact_form` a las 2 piezas nuevas del shared kit:

1. Importa y llama `register_warmup(['sqs', 'dynamodb', 'ssm'])` en
   module-scope del `handler.py` (Fase B).
2. Hereda automaticamente el `check_or_raise` paralelo (Fase A — no
   requiere cambio en el contact_form, solo el import sigue siendo
   `from shared.rate_limit import check_or_raise`).

Adicionalmente, declara el wiring en el `manifest.yaml` como documentacion.

## Cambios

### 1. `services/contact_form/core/handler.py`

```diff
 from __future__ import annotations

 import os
 import sys

+# SnapStart warmup hook: pre-calienta handshakes TLS de boto3 antes del
+# snapshot. Reduce ~200-500ms de la primera invocacion post-restore (cada
+# microVM nuevo restaurado). Wired solo cuando snap_start: true en el
+# manifest. Lista de clientes alineada con `uses.tables` + `uses.queues` +
+# `uses.secrets` del manifest: dynamodb (rate_limit + cache),
+# sqs (publicar a portfolio-contact-form-${stage}), ssm (resolver el
+# queue URL + turnstile-secret + bypass-secret).
+from shared.lambda_kit.snap_start_warmup import register_warmup
+register_warmup(clients=['sqs', 'dynamodb', 'ssm'])
+
 from shared.lambda_kit import build_event_model
 # ... resto de los imports SIN CAMBIOS ...
```

**Por que module-scope, no dentro del handler**: el warmup tiene que correr
durante el INIT del lambda (cuando AWS toma el snapshot SnapStart). Si lo
ponemos dentro del handler, corre en cada invocacion warm (re-paga 200ms
por servicio). Module-scope corre UNA VEZ.

### 2. `services/contact_form/manifest.yaml`

```diff
 snap_start: true
+# Pre-warmup de handshakes TLS de boto3 antes del snapshot. Reduce la
+# primera invocacion post-restore en ~200-500ms por servicio. Cada nombre
+# corresponde a un cliente boto3 que el lambda usa en el path HTTP. El
+# wire real esta en core/handler.py — este campo es DOCUMENTAL (devtools
+# no lo consume).
+snap_start_warmup:
+  - sqs        # publica a portfolio-contact-form-${stage}
+  - dynamodb   # rate_limit + cache + (legacy: contacts)
+  - ssm        # queue URL + turnstile-secret + bypass-secret
```

**Por que documental y no consumido por devtools**: el manifiesto sirve
como contrato leible por el desarrollador. La fuente de verdad del wiring
es el codigo (`handler.py`). Si en el futuro queremos que devtools valide
el match entre `snap_start_warmup` del manifest y el codigo, se puede
agregar un check en `serverless lint-deps` — fuera de scope de este plan.

### 3. Test unitario nuevo

`services/contact_form/tests/unit/test_handler_warmup_wired.py`:

```python
"""
Given el lambda contact_form,
When importamos el handler,
Then register_warmup se llama con ['sqs', 'dynamodb', 'ssm'].
"""
from __future__ import annotations
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


def test_handler_calls_register_warmup_in_module_scope():
    """
    Given el handler del contact_form,
    When se importa el modulo (fresh, sin cached),
    Then register_warmup se invoca con la lista exacta declarada en el manifest.
    """
    # Si el modulo handler ya esta importado, sacarlo para forzar re-import
    import sys
    sys.modules.pop('core.handler', None)

    with patch('shared.lambda_kit.snap_start_warmup.register_warmup') as mock_warmup:
        import core.handler  # noqa: F401 — el side-effect es lo que medimos

    # Debe haberse llamado UNA SOLA VEZ con la lista exacta
    mock_warmup.assert_called_once_with(clients=['sqs', 'dynamodb', 'ssm'])
```

## NO hace falta tocar el controller

`contact_form/core/controllers/contact/create.py` importa
`from shared.rate_limit import check_or_raise`. El nuevo `check_or_raise`
paralelo mantiene la firma EXACTA y el contrato de excepciones, asi que
el controller funciona sin cambios. Los tests unit del controller siguen
verdes sin modificacion.

## Verificacion local

```bash
# 1. Tests del lambda
python devtools/run.py serverless tests --type=unit --lambda=contact_form

# 2. lint-deps sigue verde
python devtools/run.py serverless lint-deps --lambda=contact_form

# 3. Import smoke: simular el cold start localmente
cd serverless/lambda
.venv/bin/python -c "import services.contact_form.core.handler; print('handler import OK')"
```

## Sin cambios en

- `services/contact_form/core/controllers/contact/create.py` (sigue igual)
- `services/contact_form/core/services/contact_service.py` (sigue igual)
- `services/contact_form/pyproject.toml` (sin deps nuevas — boto3 ya esta
  como transitivo via `shared/aws` y `shared/queue`)
- IAM policies (sin permisos nuevos)
