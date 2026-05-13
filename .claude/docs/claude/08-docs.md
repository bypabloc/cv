# 8. Documentacion (CLAUDE.md)

[Volver al indice](README.md) | [Anterior: Skills (Referencia)](07-skills.md)

## Que es CLAUDE.md

CLAUDE.md es un archivo markdown que Claude Code lee automaticamente al inicio de cada conversacion. Funciona como memoria persistente y archivo de configuracion, proporcionando contexto del proyecto que sobrevive entre sesiones.

Su contenido se convierte en parte del system prompt de Claude, lo que significa que influye directamente en el comportamiento de cada interaccion. El comando `/init` analiza tu codebase y genera un archivo inicial basado en el stack detectado.

## Jerarquia de Memoria

Claude Code implementa una jerarquia multi-nivel. Instrucciones mas especificas prevalecen sobre las generales:

| Tipo | Ubicacion | Proposito | Compartido con |
|------|-----------|-----------|----------------|
| **Managed policy** | `/etc/claude-code/CLAUDE.md` (Linux) | Politicas de organizacion | Todos los usuarios |
| **Proyecto** | `./CLAUDE.md` o `./.claude/CLAUDE.md` | Instrucciones del proyecto | Equipo via git |
| **Project rules** | `./.claude/rules/*.md` | Reglas modulares por tema | Equipo via git |
| **Personal** | `~/.claude/CLAUDE.md` | Preferencias personales | Solo tu (todos los proyectos) |
| **Proyecto local** | `./CLAUDE.local.md` | Preferencias locales (gitignored) | Solo tu (este proyecto) |
| **Auto memory** | `~/.claude/projects/<proyecto>/memory/` | Notas automaticas de Claude | Solo tu (por proyecto) |

**Orden de carga**:

1. `~/.claude/CLAUDE.md` (global personal)
2. `./CLAUDE.md` (proyecto raiz)
3. `.claude/rules/*.md` (rules modulares, alfabetico)
4. `~/.claude/projects/<hash>/memory/MEMORY.md` (auto-memory, primeras 200 lineas)

Archivos cargados despues override los anteriores cuando hay conflictos. Los CLAUDE.md en directorios hijos se cargan bajo demanda cuando Claude accede a archivos en esos directorios.

## Tamano Optimo

La relacion entre tamano y efectividad esta bien documentada:

| Tamano | Tasa de cumplimiento | Recomendacion |
|--------|---------------------|---------------|
| < 200 lineas | ~92% | Zona objetivo |
| 200-400 lineas | ~80% | Aceptable |
| > 400 lineas | ~71% | Demasiado largo, dividir |
| > 500 lineas | Degradacion significativa | Mover contenido a rules/skills |

Datos clave:

- Los LLMs pueden seguir ~150-200 instrucciones de forma fiable. El system prompt de Claude Code ya consume ~50, dejando ~100-150 para tu CLAUDE.md
- Reglas imperativas ("Usar TypeScript strict") logran 94% de cumplimiento; contenido descriptivo ("El proyecto usa TypeScript") baja a 73%
- Un CLAUDE.md de 200 lineas consume ~1,500 tokens (1.5% del context window de 128K)
- Un archivo de 500 lineas consume ~3,800 tokens, reduciendo capacidad de analisis

**Test de utilidad**: Para cada linea, preguntarse "¿Si elimino esto, Claude cometeria errores?" Si no, eliminar.

## Secciones Recomendadas

Un CLAUDE.md efectivo cubre tres dimensiones: **QUE** (stack, estructura), **POR QUE** (proposito, decisiones), y **COMO** (workflows, comandos, verificacion).

### Template minimo efectivo

```markdown
# Project: [Nombre]
[Descripcion en una linea y tech stack]

## Commands
- Build: `npm run build`
- Test: `npm test -- path/to/test`
- Lint: `npm run lint`
- Typecheck: `npm run typecheck`

## Architecture
- src/api/ - REST endpoints
- src/models/ - Database models
- src/services/ - Business logic

## Conventions
- Branch naming: feature/, hotfix/, bugfix/
- Commits: Conventional Commits (feat:, fix:, docs:)
- Components: PascalCase con prefijo DF

## Important
- Never modify migration files directly
- Auth tokens use JWT with 24h expiry
- Payment code requires security review before merge
```

### Template de produccion (equipo)

```markdown
# Payment Service
Backend de pagos para mercados CL/MX. Django 5 + DRF + PostgreSQL.

## Commands
- Dev server: `python manage.py runserver`
- Test single: `pytest path/to/test.py -v`
- Test all: `pytest --cov --tb=short`
- Lint: `ruff check .`
- Format: `black . && isort .`
- Migrations: `python manage.py makemigrations && python manage.py migrate`

## Architecture
- apps/payments/ - Procesamiento de pagos (Getnet, Transbank)
- apps/users/ - Autenticacion y perfiles
- apps/webhooks/ - Handlers de notificaciones
- libs/validators/ - Validaciones RUT, RFC, tarjetas

## Stack
- Python 3.14 + Django 6 + DRF
- PostgreSQL 18
- pytest + factory_boy para testing

## Conventions
- Branches: feature/, hotfix/, bugfix/ (separador / obligatorio)
- Commits: Conventional Commits en ingles
- Code: black (line-length 80) + isort (profile black)
- Views: siempre select_related/prefetch_related
- Tests: pytest con AAA pattern, coverage > 80%

## Security (CRITICAL)
- NUNCA loguear passwords, tokens JWT, codes de verificacion, RUT/RUC completo
- Validar inputs en fronteras de controller (serializers DRF)
- Mercado Pago: tokenizar tarjetas via MP SDK (nunca guardar PAN/CVV)
- Audit logs obligatorios en cambios de estado de Appointment, Payment, Refund

## Git
- Base branches: master (prod), release (pre-prod), dev
- PR obligatorio para merge a release/master
- Code review requerido antes de merge
```

### Que incluir vs excluir

| Incluir | Excluir |
|---------|---------|
| Comandos de build/test que Claude no puede adivinar | Convenciones estandar del lenguaje |
| Reglas de estilo que difieren de defaults | Documentacion detallada de API (linkear) |
| Instrucciones de testing y runners preferidos | Informacion que cambia frecuentemente |
| Convenciones de git (branches, PRs, commits) | Descripciones archivo por archivo |
| Decisiones arquitectonicas especificas | Tutoriales o explicaciones largas |
| Quirks del entorno (env vars requeridas) | Practicas evidentes ("escribir codigo limpio") |
| Gotchas o comportamientos no obvios | Secrets (API keys, passwords, tokens) |

## @-Referencias (Imports)

CLAUDE.md puede importar archivos adicionales usando sintaxis `@path/to/import`:

```markdown
# En CLAUDE.md
Ver @README.md para overview del proyecto.

# Imports de archivos adicionales
- Git workflow: @docs/git-instructions.md
- Overrides personales: @~/.claude/portfolio-instructions.md
```

### Reglas de imports

- Paths relativos y absolutos permitidos
- Los relativos se resuelven relativo al **archivo que contiene el import**, no al working directory
- Imports recursivos permitidos con **max profundidad de 5 niveles**
- Imports dentro de code spans (`` `@package` ``) y code blocks NO se evaluan
- La primera vez que Claude encuentra imports externos, muestra dialogo de aprobacion
- Verificar imports cargados con `/memory`

### Ejemplo de imports en proyecto

```markdown
# CLAUDE.md principal
# Importar reglas compartidas del equipo
@~/.company/shared-rules.md
@~/.company/security-policy.md

# Importar docs del proyecto
@docs/architecture.md
@docs/api-contracts.md

# Overrides locales (cada dev tiene el suyo)
# En CLAUDE.local.md:
@~/.claude/personal-preferences.md
```

## CLAUDE.local.md

Archivo de proyecto para preferencias personales que **no se commitea** a version control (se agrega automaticamente a `.gitignore`).

Usos:
- URLs de sandbox y datos de prueba personales
- Shortcuts de tooling local
- Paths especificos del entorno
- Datasets de prueba preferidos

```markdown
# CLAUDE.local.md (no commiteado)

## Mi entorno
- DB local: postgresql://localhost:5432/payments_dev
- Redis: localhost:6379
- Sandbox URL: https://sandbox.getnet.cl/api/v1

## Preferencias
- Cuando testee, usar factory_boy en vez de fixtures
- Preferred test user: test@example.com / rut: 12.345.678-5
```

## Sistema de Auto Memory

Auto memory es un directorio persistente donde Claude guarda notas automaticamente mientras trabaja.

### Estructura

```text
~/.claude/projects/<proyecto>/memory/
├── MEMORY.md          # Indice conciso, cargado cada sesion (primeras 200 lineas)
├── debugging.md       # Notas sobre patrones de debugging
├── api-conventions.md # Decisiones de diseno de API
└── patterns.md        # Patrones descubiertos en el proyecto
```

### Comportamiento critico

- Solo las **primeras 200 lineas** de MEMORY.md se cargan al inicio (lineas posteriores se truncan silenciosamente)
- Archivos de temas (debugging.md, etc.) NO se cargan al inicio; Claude los lee bajo demanda
- El path `<proyecto>` se deriva del root del repositorio git
- Git worktrees obtienen directorios de memoria separados

### Controlar auto memory

```bash
# Forzar encendido
export CLAUDE_CODE_DISABLE_AUTO_MEMORY=0

# Forzar apagado
export CLAUDE_CODE_DISABLE_AUTO_MEMORY=1
```

Tambien puedes decirle directamente a Claude: "recuerda que usamos pnpm, no npm" y lo guardara en auto memory.

## Patron HANDOFF.md

Patron para continuidad de sesion cuando el context window se llena o al transferir trabajo entre sesiones.

### Problema que resuelve

Cuando el contexto alcanza 70-80% de capacidad, la compactacion resume la conversacion pero puede perder detalles criticos de trabajo. Re-establecer contexto sin handoff toma 10-15 minutos; con handoff, 2-3 minutos.

### Formato

```markdown
# Session Handoff
- Generated: 2026-02-25T14:30:00Z
- Branch: feature/identity-validators

## Goal
Implementar validadores de identidad para mercados CL (RUT) y PE (RUC)

## Completed
- [x] Modulo validador en src/validators/
- [x] Algoritmo modulo 11 con digito verificador K (RUT chileno)
- [x] Algoritmo modulo 11 con multiplicadores 5,4,3,2,7,6,5,4,3,2 (RUC peruano)
- [x] Tests unitarios para identificadores validos/invalidos

## Not Yet Done
- [ ] Integracion con validacion de RFC
- [ ] Tests de integracion con API de pago
- [ ] Traducciones de mensajes de error (es-MX)

## Failed Approaches
- Validacion solo con regex: no maneja digitos de verificacion Luhn
- Libreria 'card-validator' conflicta con nuestro bundler

## Key Decisions
- Validador custom en vez de libreria (tamano de bundle)
- Validacion de CVV diferida al lado de API per requisitos PCI

## Key Files
- src/validators/card.ts (implementacion principal)
- tests/validators/card.test.ts (suite de tests)
- src/types/payment.ts (definiciones de tipos)
```

### Workflow con HANDOFF.md

```text
1. Contexto al 70-80% → Crear HANDOFF.md con estado actual
2. Ejecutar /compact o iniciar sesion nueva
3. En la nueva sesion: "Lee HANDOFF.md y continua desde donde quede"
4. Claude recupera contexto en 2-3 minutos
```

### Alternativas integradas

```bash
claude --continue    # Retomar la conversacion mas reciente
claude --resume      # Seleccionar de sesiones recientes
/rename "payment-gateway-validation"  # Nombrar sesion para encontrarla despues
```

## Documentacion para Equipos

### Patron centralizado (para organizaciones)

```text
shared-rules/                        # Repo central de reglas
├── shared/
│   ├── rules/                       # Reglas por stack
│   │   ├── react-nextjs.md
│   │   ├── python-django.md
│   │   └── general.md
│   └── templates/                   # Templates CLAUDE.md por tipo de repo
│       ├── frontend.claude.md
│       └── backend.claude.md
├── repos/                           # Overrides por repo
│   └── special-repo/
│       └── CLAUDE.md
└── distribute.sh                    # Script para distribuir a todos los repos
```

### Patron monorepo

```text
/monorepo/
├── CLAUDE.md                    # Compartido: git, CI, reglas cross-package
├── packages/
│   ├── frontend/
│   │   └── CLAUDE.md           # Convenciones React, componentes
│   ├── backend/
│   │   └── CLAUDE.md           # Convenciones API, patrones DB
│   └── shared/
│       └── CLAUDE.md           # Tipos compartidos, utilidades
└── .claude/
    └── rules/
        ├── testing.md          # Estandares de testing (todos)
        └── security.md         # Reglas de seguridad (todos)
```

### Symlinks para compartir rules entre proyectos

```bash
# Compartir reglas comunes entre proyectos
ln -s ~/shared-claude-rules .claude/rules/shared

# Compartir archivos individuales
ln -s ~/company-standards/security.md .claude/rules/security.md
```

### Enterprise/managed deployment

Las organizaciones pueden deployar CLAUDE.md centralmente:

```bash
# Linux
/etc/claude-code/CLAUDE.md

# macOS
/Library/Application Support/ClaudeCode/CLAUDE.md
```

Estos tienen la **maxima prioridad** y override todos los demas niveles.

## Knowledge Tree: Base de Conocimiento Navegable

Un Knowledge Tree es una estructura de archivos `.md` donde cada archivo es un nodo con conocimiento enfocado en UN tema, enlazado a otros nodos. Claude navega el arbol leyendo solo los nodos relevantes para la tarea actual, en vez de cargar todo de golpe.

```text
CLAUDE.md (raiz)                          ← siempre en contexto (~500 tokens)
├── docs/architecture.md                  ← se lee bajo demanda
│   ├── docs/layers/http-layer.md            ← se lee si trabaja con http-layer
│   └── docs/layers/models.md             ← se lee si trabaja con models
├── docs/testing.md                       ← se lee bajo demanda
│   └── docs/testing/mock-patterns.md     ← se lee si necesita mocks
├── docs/security.md                      ← se lee bajo demanda
└── docs/domain/payments.md               ← se lee bajo demanda
    ├── docs/domain/getnet.md             ← se lee si trabaja con Getnet
    └── docs/domain/forpay.md             ← se lee si trabaja con ForPay
```

| Sin Knowledge Tree | Con Knowledge Tree |
|--------------------|-------------------|
| CLAUDE.md de 2000 lineas = 50% del contexto consumido siempre | CLAUDE.md de 100 lineas = 2% del contexto |
| Claude ignora reglas por saturacion (>200 instrucciones) | Claude lee 3-5 nodos enfocados (~150 instrucciones total) |
| Informacion irrelevante compite por atencion | Solo informacion relevante a la tarea |

### Arquitectura de 3 Capas

| Capa | Ubicacion | Cuando se carga | Presupuesto |
|------|-----------|-----------------|-------------|
| **1. Raiz** | `CLAUDE.md` | Siempre (cada sesion) | Max 100-150 lineas (~500 tokens) |
| **2. Nodos principales** | `docs/*.md` | Bajo demanda (cuando la tarea lo requiere) | 50-200 lineas por nodo |
| **3. Nodos detallados** | `docs/subtema/*.md` | Bajo demanda profundo (solo cuando necesita detalles) | 50-300 lineas por nodo |

**Profundidad maxima**: 3 niveles. Mas de 3 genera cadenas de lectura que consumen tokens y confunden la navegacion.

### Formato de Cada Nodo

Cada archivo del arbol sigue esta estructura:

```markdown
# [Titulo del Nodo]

> [Descripcion de 1 linea: que contiene este nodo]

## Contenido principal

[Conocimiento enfocado del tema. Conciso, en prosa o listas.]

## Reglas criticas

- SIEMPRE [regla positiva]
- NUNCA [regla negativa]

## Navegacion

Si necesitas mas detalle sobre:
- **[Subtema A]**: Lee [docs/subtema-a.md](docs/subtema-a.md)
- **[Subtema B]**: Lee [docs/subtema-b.md](docs/subtema-b.md)

Contexto padre: [docs/padre.md](docs/padre.md)
```

### Directivas de Navegacion

Las directivas son instrucciones **explicitas** para que Claude sepa cuando leer otro nodo. Sin directivas, Claude no navega.

**Tipo 1 — Condicional** (la mas comun):

```markdown
## Navegacion

Si necesitas trabajar con:
- **Bifrost HTTP**: Lee [docs/layers/http-layer.md](docs/layers/http-layer.md)
- **Modelos compartidos**: Lee [docs/layers/models.md](docs/layers/models.md)
```

**Tipo 2 — Obligatoria** (para operaciones criticas):

```markdown
## IMPORTANTE

ANTES de crear un nuevo servicio Lambda, lee OBLIGATORIAMENTE:
1. [docs/architecture.md](docs/architecture.md) — estructura de servicios
2. [docs/testing.md](docs/testing.md) — estructura de tests requerida
3. [docs/security.md](docs/security.md) — reglas de seguridad del booking SaaS
```

**Tipo 3 — Referencia bajo demanda**:

```markdown
Error codes documentados en [docs/standards/error-codes.md](docs/standards/error-codes.md).
```

**Tipo 4 — Breadcrumb de retorno**:

```markdown
Contexto padre: [docs/architecture.md](docs/architecture.md)
```

Directivas **imperativas** (no pasivas):

```markdown
# MAL — pasivo, Claude lo ignora
Hay mas informacion sobre http-layer disponible en docs/layers/http-layer.md

# BIEN — imperativo, Claude lo sigue
Para la API completa de http-layer, LEE [docs/layers/http-layer.md](docs/layers/http-layer.md)
```

### Combinando docs/ + rules/ + skills/

Los tres mecanismos tienen propositos distintos y se complementan:

| Mecanismo | Cuando se carga | Quien lo activa | Uso ideal |
|-----------|-----------------|-----------------|-----------|
| `docs/` | Cuando Claude lee un enlace de navegacion | Directiva en otro .md | Conocimiento pasivo bajo demanda |
| `rules/` | Automatico al tocar archivos que matchean `globs:` | Claude Code (path-matching) | Reglas por tipo de archivo |
| `skills/` | Cuando Claude determina relevancia por description | Claude Code (description matching) | Workflows repetibles con pasos |

**Regla**: Conocimiento pasivo (referencia, contexto) → `docs/`. Regla por tipo de archivo → `rules/`. Workflow con pasos → `skills/`.

**Rules enlazando a docs:**

```yaml
# .claude/rules/python.md
---
globs: "**/*.py"
---

# Python Standards

## ResultDict Pattern
Todas las funciones retornan ResultDict. Ver detalles completos en
[docs/standards/result-dict.md](docs/standards/result-dict.md).
```

**Skills enlazando a docs:**

```yaml
# .claude/skills/new-service/SKILL.md
---
name: new-service
description: >
  Create a new Lambda service. Use when the user says "create service",
  "new lambda", or "add microservice".
disable-model-invocation: true
---

# Crear nuevo servicio

## Pre-requisitos
Lee [docs/architecture.md](docs/architecture.md) para entender la estructura.

## Pasos
1. Crear directorio en el stack apropiado
2. Copiar template desde services/_template/
3. Configurar serverless.yml
4. Crear tests basicos
5. Ejecutar make prepare LAMBDA=nombre
```

### Ejemplo Completo: CLAUDE.md Raiz con Knowledge Tree

```markdown
# payment-service

Backend de pagos para mercados CL/MX. Django 5 + DRF + PostgreSQL.

## Comandos
- Test: `pytest path/to/test.py -v`
- Lint: `ruff check .`
- Dev: `python manage.py runserver`

## Stack
- Python 3.14, Django 6, DRF
- PostgreSQL 18

## Arbol de conocimiento

Antes de trabajar, identifica que contexto necesitas:

| Tema | Archivo | Cuando leer |
|------|---------|-------------|
| Arquitectura | [docs/architecture.md](docs/architecture.md) | Crear servicios, entender estructura |
| Testing | [docs/testing.md](docs/testing.md) | Escribir o modificar tests |
| Seguridad | [docs/security.md](docs/security.md) | Manejar secrets, inputs, logging |
| Dominio | [docs/domain.md](docs/domain.md) | Entender flujos de booking/appointment/pago |
| API Providers | [docs/providers.md](docs/providers.md) | Integrar con Mercado Pago, AWS SES, WhatsApp, etc. |

## Gotchas
- Archivos temporales en `./tmp/`, nunca `/tmp/`
- `find` aliasado a `fdfind` — usar Glob tool
```

### Ejemplo: Nodo Capa 2 (docs/providers.md)

```markdown
# Payment Providers

> Integraciones con proveedores de pago: configuracion, API, flujos.

## Proveedores activos

| Proveedor | Mercado | Servicio | Doc detallada |
|-----------|---------|----------|---------------|
| Getnet | Chile | payment_getnet_click | [docs/providers/getnet.md](docs/providers/getnet.md) |
| Transbank | Chile | payment_transbank | [docs/providers/transbank.md](docs/providers/transbank.md) |
| Conekta | Mexico | payment_conekta | [docs/providers/conekta.md](docs/providers/conekta.md) |

## Reglas criticas

- NUNCA loguear numeros de tarjeta completos (solo ultimos 4 digitos)
- SIEMPRE validar firma/hash de webhooks antes de procesar
- Timeout maximo para llamadas a proveedores: 30 segundos

## Documentacion incluida (LOCAL — NO buscar en internet)

Cada proveedor tiene documentacion local de su API. SIEMPRE leer
el archivo local ANTES de buscar en internet.

Contexto padre: [CLAUDE.md](../CLAUDE.md)
```

### Ejemplo: Nodo Capa 3 (docs/providers/getnet.md)

```markdown
# Getnet Chile

> API de pago con tarjeta via Getnet Click. Spec completa local.

## Endpoints principales

- `POST /api/v1/charges` — Crear cargo
- `GET /api/v1/charges/{id}` — Consultar cargo
- `POST /api/v1/charges/{id}/refund` — Reversa

## Flujo de pago

1. Frontend envia datos tokenizados
2. Backend llama `POST /charges` con token + monto
3. Getnet retorna status (approved/declined/pending)
4. Webhook confirma estado final asincronamente

## Codigos de respuesta

| Codigo | Significado | Accion |
|--------|-------------|--------|
| 00 | Aprobado | Confirmar pago al usuario |
| 05 | Rechazado por emisor | Reintentar con otra tarjeta |
| 51 | Fondos insuficientes | Notificar al usuario |
| 99 | Error interno Getnet | Reintentar con backoff exponencial |

## Gotchas

- El campo `amount` es en centavos (15000 = $150.00 CLP)
- Webhook puede llegar hasta 5 minutos despues del cargo
- Reversa solo disponible dentro de 24 horas

## Documentacion completa de la API

Para la especificacion completa, LEE [docs/docstring_official.md](docs/docstring_official.md).
Este archivo ES la documentacion oficial para este proyecto. NO buscar en internet.

Contexto padre: [docs/providers.md](../providers.md)
```

### Prevencion de Web Search en Docs Locales

Cuando un nodo contiene documentacion local de APIs externas, Claude puede interpretar "documentacion oficial" como trigger para buscar en internet. Prevencion:

**En CLAUDE.md (directiva global):**

```markdown
## Politica de documentacion (OBLIGATORIO)

Este proyecto contiene copias locales de documentacion de APIs externas.
Los archivos locales son la fuente AUTORITATIVA.

ANTES de buscar en internet cualquier documentacion de API:
1. VERIFICAR si existe una copia local en docs/
2. LEER el archivo local si existe
3. SOLO buscar en internet si la doc local no cubre la pregunta
```

**En cada nodo con docs de API (directiva local):**

```markdown
## Documentacion incluida (LOCAL — NO buscar en internet)

| Documento | Archivo | Contenido |
|-----------|---------|-----------|
| API Getnet (oficial) | [docs/docstring_official.md](docs/docstring_official.md) | Endpoints, payloads, codigos |
| Codigos de error | [docs/error_codes.md](docs/error_codes.md) | Tabla completa |

REGLA: SIEMPRE leer estos archivos ANTES de buscar en internet.
```

**Frases a evitar** (triggean web search):

| Frase problematica | Alternativa segura |
|--------------------|--------------------|
| "documentacion oficial de Getnet" | "especificacion de la API (archivo local)" |
| "segun la documentacion de [proveedor]" | "segun [docs/archivo.md](docs/archivo.md)" |
| "ver la API de GetNet" | "LEE [docs/docstring_official.md](docs/docstring_official.md)" |

### Estructura de Directorio Completa

```text
.claude/
├── CLAUDE.md                         # RAIZ: indice + comandos (~100 lineas)
├── docs/                             # Knowledge tree (bajo demanda)
│   ├── architecture.md               # Capa 2: arquitectura
│   ├── testing.md                    # Capa 2: testing
│   ├── security.md                   # Capa 2: seguridad
│   ├── domain.md                     # Capa 2: dominio de negocio
│   ├── providers.md                  # Capa 2: proveedores de pago
│   ├── layers/                       # Capa 3: detalles de layers
│   │   ├── http-layer.md
│   │   └── models.md
│   ├── testing/                      # Capa 3: detalles de testing
│   │   └── mock-patterns.md
│   └── providers/                    # Capa 3: detalles por proveedor
│       ├── getnet.md
│       └── transbank.md
├── rules/                            # Path-matched (auto-load)
│   ├── python.md                     # Se carga al tocar *.py
│   ├── react.md                      # Se carga al tocar *.tsx
│   └── security.md                   # Se carga al tocar auth/**, payments/**
└── skills/                           # Workflows invocables
    ├── deploy/
    │   └── SKILL.md
    └── new-service/
        └── SKILL.md
```

### Checklist de Knowledge Tree

```text
[ ] CLAUDE.md raiz < 150 lineas con tabla de "Arbol de conocimiento"
[ ] 3-6 nodos principales en docs/ (Capa 2)
[ ] Sub-nodos en docs/subtema/ (Capa 3) donde se necesita profundidad
[ ] Cada nodo tiene seccion "Navegacion" con directivas imperativas
[ ] Cada nodo (excepto raiz) tiene breadcrumb "Contexto padre:"
[ ] Ningun nodo supera 300 lineas
[ ] Profundidad maxima: 3 niveles
[ ] Rules enlazan a docs/ cuando necesitan profundizar
[ ] Skills enlazan a docs/ como pre-requisitos
[ ] Directiva anti-web-search en CLAUDE.md si hay docs de APIs externas
[ ] Todo commiteado en version control
```

## Anti-patrones

| Anti-patron | Problema | Solucion |
|-------------|----------|----------|
| **CLAUDE.md cocina** | Demasiado largo, Claude ignora la mitad | Podar ruthlessly, mover a rules/skills |
| **Corregir sin parar** | Contexto contaminado con intentos fallidos | Despues de 2 correcciones, `/clear` y re-prompt |
| **Mezclar tareas** | Historial irrelevante consume contexto | `/clear` entre tareas no relacionadas |
| **Auto-generar CLAUDE.md** | `/init` produce contenido generico | Usar `/init` como punto de partida, luego refinar |
| **Usar Claude como linter** | "Nunca envies un LLM a hacer el trabajo de un linter" | Usar hooks deterministicos |
| **Sin CLAUDE.md** | 60% de tickets de soporte vienen de esto | Crear al menos un archivo minimo |
| **Incluir secrets** | API keys, passwords expuestos en git | Variables de entorno, `.env` fuera del repo |
| **Reglas descriptivas** | "El proyecto usa X" logra 73% cumplimiento | Usar imperativo: "Usar X siempre" (94%) |

## Checklist para un Buen CLAUDE.md

```text
[ ] Tamano < 200 lineas (ideal) o < 500 (maximo)
[ ] Comandos de build, test, lint documentados
[ ] Convenciones de git (branches, commits)
[ ] Arquitectura de alto nivel (directorios clave)
[ ] Reglas de seguridad si aplica
[ ] No contiene secrets ni datos sensibles
[ ] Cada linea es necesaria (test de utilidad)
[ ] Reglas en forma imperativa, no descriptiva
[ ] Contenido especifico por lenguaje movido a .claude/rules/
[ ] Commiteado en version control
```

## Fuentes

- [Manage Claude's memory - Docs oficiales](https://code.claude.com/docs/en/memory)
- [Claude Code Best Practices - Docs oficiales](https://code.claude.com/docs/en/best-practices)
- [Using CLAUDE.md Files - Anthropic Blog](https://claude.com/blog/using-claude-md-files)
- [Writing a good CLAUDE.md - HumanLayer](https://www.humanlayer.dev/blog/writing-a-good-claude-md)
- [CLAUDE.md Guide - Builder.io](https://www.builder.io/blog/claude-md-guide)
- [Writing CLAUDE.md for Mature Codebases](https://blog.huikang.dev/2025/05/31/writing-claude-md.html)
- [Claude Code Memory System Deep Dive - SFEIR](https://institute.sfeir.com/en/claude-code/claude-code-memory-system-claude-md/deep-dive/)
- [Smart Handoff for Claude Code](https://blog.skinnyandbald.com/never-lose-your-flow-smart-handoff-for-claude-code/)

---

[Volver al indice](README.md)
