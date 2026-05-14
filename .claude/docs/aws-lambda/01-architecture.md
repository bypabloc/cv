# Arquitectura del runtime Lambda 2026

> Modelo de ejecucion de AWS Lambda con Python 3.13: managed runtime,
> event loop, init phase, cold start, memory model, architecture CPU.

[← README](./README.md) | [Siguiente: Handler patterns →](./02-handler-patterns.md)

## Runtime managed Python 3.13

AWS Lambda ofrece Python 3.13.x como runtime managed (no container image
personalizado). Noviembre 2024: AWS lanzo soporte oficial para Python 3.13
en Lambda, con soporte garantizado hasta octubre 2029 (PEP 693: LTS release).

El runtime esta disponible en **todas las regiones AWS**, incluyendo GovCloud
y China. Se actualizara automaticamente con parches de seguridad y bug fixes.

Para especificar: `Runtime: python3.13` en SAM template o `python3.13` en
consola de Lambda.

Fin de soporte para Python 3.9:
- Dic 15, 2025: AWS deja de soportar py39
- Feb 3, 2026: NO se pueden crear Lambdas con py39
- Mar 9, 2026: NO se puede actualizar existentes con py39

**Migracion obligatoria**: si hoy tienes py39, migrar antes de dic 2025.

## Event loop y execution model

Lambda ejecuta tu handler **una sola vez por invocacion**. El flow es:

```
┌─────────────────────────────────────┐
│ 1. INIT PHASE (~100-200ms)          │
│ ────────────────────────────────    │
│ - Load runtime (Python VM)          │
│ - Import modules (top-level)        │
│ - Execute code fuera del handler    │
│ - Inicializar conexiones globales   │
└─────────────────────────────────────┘
                  │
        ┌─────────▼─────────┐
        │ INVOKE            │ ◄─ Repetido N veces por cold start
        │ ─────────────────
        │ - Executar handler
        │ - event + context
        │ - Return response
        └──────────────────┘
                  │
        ┌─────────▼─────────┐
        │ FREEZE            │
        │ ─────────────────
        │ Memory snapshot
        │ (para SnapStart)
        └──────────────────┘
```

El init phase es **critico para cold start**. Todo lo que importas en el
top-level del modulo (boto3, requests, decorators) consume tiempo aqui.

### Cold start anatomy

**Cold start**: primera invocacion despues de deployment o timeout > 15 min.

Desglose tipico (Python 3.13, 512MB memory, sin SnapStart):
- Init phase: 200-500ms (mas alto si muchos imports/dependencies)
- Invocacion: 50-200ms
- Total: 250-700ms

Con SnapStart (Nov 2025+, Python 3.12+):
- Snapshot restore: 10-50ms (90% mas rapido)
- Invocacion: 50-200ms
- Total: 60-250ms

Sin SnapStart, usa provisioned concurrency o Lambda Power Tuning para
medir exactamente tu caso.

## Memory model

Lambda aloca memoria en increments de **1 MB** de 128 MB a 10,240 MB.

Cada MB adicional = incremento proporcional de CPU (no lineal, AWS lo
declara).

```
Memory  | vCPU aprox | GB-seconds / 1M invokes
─────────────────────────────────────────────
256 MB  | 0.25       | 106.67 GB-seconds → $1.78
512 MB  | 0.5        | 213.33 GB-seconds → $3.56
1024 MB | 1.0        | 426.67 GB-seconds → $7.11
```

**Estrategia para este proyecto**:
- contact-form (form + SES + DynamoDB): 512 MB (tiempo ~150ms)
- turnstile-validator (HTTP + cached): 256 MB (tiempo ~100ms)
- tracking-pixel (DynamoDB PutItem): 256 MB (tiempo ~50ms)

Pricing: $0.20 per 1M requests + $0.0000166667 per GB-second (us-east-1).
Con 100 invokes/dia contact-form (512MB, 150ms):
- ~3000 invokes/mes = free tier (1M/mes)
- GB-seconds: 3000 * 0.512 * 0.15 / 3600 = 0.064 GB-seconds
- Costo: ~$0.001/mes (negligible)

## SnapStart: Python 3.13 (Nov 2025)

SnapStart toma un snapshot del execution environment **totalmente inicializado**
despues de la init phase, y restaura desde ese snapshot en invocaciones posteriores.

```
First invocation (cold):
────────────────────
Init phase (~200ms)
  │ imports, top-level code, global variables
  │
  ▼
Invocation (~50ms)
  │ handler runs
  │
  ▼
SNAPSHOT CAPTURED (~10ms)
  │ VM memory frozen

Subsequent invocations (warm):
──────────────────────────────
RESTORE FROM SNAPSHOT (~10ms)
  │ Memory unfrozen, ready to invoke
  │
  ▼
Invocation (~50ms)
```

**Trade-offs**:

Pros:
- ~90% reduccion en cold start (de 300ms a 30ms tipico)
- Sin cambios en codigo, activar con un flag en SAM
- Costo: +15% aprox de memoria (snapshot storage)
- Soporta conexiones globales (boto3 clients reutilizables)

Cons:
- Solo Python 3.12+, Java 21+, .NET 8
- No soporta container images, provisioned concurrency, EFS, >512MB ephemeral storage
- Runtime hooks requeridos para clean re-initialization (ej. clear credentials)
- Cost: +15% de storage en S3 interno

Para este caso (form contact, bajo trafico), SnapStart no es **obligatorio**
pero recomendado si se activa cold start optimization.

## Architecture: x86_64 vs arm64 (Graviton2)

Lambda soporta dos arquitecturas en Python 3.13:

| Aspecto | x86_64 | arm64 (Graviton2) |
|--------|--------|-------------------|
| Default | Si | No (specify en SAM) |
| Precio | $0.0000166667/GB-s | $0.0000133333/GB-s (-20%) |
| Performance | 100% baseline | +19% (según AWS benchmarks) |
| Compatibilidad | Todas las libs | Casi todas, verificar native binaries |

**Para este proyecto: x86_64** (default, menos complejidad).

Si en el futuro busca optimizar costos, arm64 es opcion: compatible con
boto3, requests, pydantic. Requiere SAM `Architectures: [arm64]`.

## Concurrency model

Lambda maneja invocaciones concurrentes. Tienes dos opciones:

1. **Reserved Concurrency**: garantizadas X invocaciones simultaneas. Costo:
   $0.015 per concurrent unit/hora (no recomendado para bajo trafico).
2. **Provisioned Concurrency**: pre-inicializa Y instances. Costo: $0.0000041667
   per instance/segundo. NO recomendado para este caso.

Para contact-form (100 req/mes): **sin reserved/provisioned** (default on-demand).

Lambda throttlea si excedes el account limit (~1000 concurrent globally).
Para este proyecto, nunca seria problema.

## Timeouts y limits

- Max execution time: 15 minutos (900 segundos)
- Max memory: 10,240 MB (10 GB)
- Max tmp disk (/tmp): 10,240 MB (ephemeral)
- Max deployment package: 50 MB (zip), 250 MB (uncompressed with layers)

Para contact-form (SES send ~1s + DynamoDB put ~100ms): **timeout = 30 seg**
(plenty de margen).

Verificado a fecha 2026-05-13.
