# 6. Rules

[Volver al indice](README.md) | [Anterior: Tips y Recursos](05-tips-y-recursos.md) | [Siguiente: Skills (Referencia)](07-skills.md)

## Que Son las Rules

Las rules son archivos markdown modulares en `.claude/rules/` que proporcionan instrucciones especificas por dominio a Claude Code. Introducidas en la version **v2.0.64** (diciembre 2025), son la alternativa escalable a un CLAUDE.md monolitico.

Cada archivo `.md` en `.claude/rules/` se **carga automaticamente** al inicio de sesion con la **misma prioridad** que CLAUDE.md. La diferencia clave: las rules soportan **filtrado por path** via frontmatter YAML, activandose solo cuando Claude trabaja con archivos que matchean los patrones.

## Como Funcionan

### Carga automatica

Claude Code descubre recursivamente todos los archivos `.md` dentro de `.claude/rules/` (incluyendo subdirectorios) sin configuracion. La secuencia de carga:

1. Lee `~/.claude/CLAUDE.md` (personal)
2. Lee `./CLAUDE.md` o `./.claude/CLAUDE.md` (proyecto)
3. Descubre recursivamente todos los `.md` en `.claude/rules/`
4. Aplica filtrado por path segun frontmatter
5. Lee `CLAUDE.local.md` (local, no commiteado)

### Rules con filtrado por path

Las rules pueden ser **condicionalmente scopeadas** usando frontmatter YAML con el campo `paths` o `globs`. Cuando una rule tiene este campo, **solo se carga** cuando Claude trabaja con archivos que matchean los patrones glob.

```yaml
---
globs: "src/api/**/*.ts"
---

# API Development Rules

- Todos los endpoints deben incluir validacion de input
- Usar el formato estandar de respuesta de error
- Incluir comentarios de documentacion OpenAPI
```

Rules **sin** campo `paths`/`globs` se cargan incondicionalmente en cada sesion.

### Verificar rules cargadas

```bash
# En Claude Code, ejecutar:
/memory    # Ver que archivos de memoria estan cargados (incluye rules)
```

## Jerarquia y Precedencia

| Nivel | Ubicacion | Aplica a | Compartido con |
|-------|-----------|----------|----------------|
| **Personal** | `~/.claude/rules/*.md` | Todos tus proyectos | Solo tu |
| **Proyecto** | `./.claude/rules/*.md` | Solo este proyecto | Equipo via git |

**Precedencia**: Las rules de proyecto tienen **mayor prioridad** y pueden override las personales. Esto sigue el mismo patron que CLAUDE.md: instrucciones mas especificas prevalecen sobre las generales.

Jerarquia completa de memoria:

| Tipo | Ubicacion | Prioridad |
|------|-----------|-----------|
| Managed policy | `/etc/claude-code/CLAUDE.md` (Linux) | Maxima |
| Proyecto CLAUDE.md | `./CLAUDE.md` | Alta |
| **Proyecto rules** | **`./.claude/rules/*.md`** | **Alta (igual que CLAUDE.md)** |
| Personal CLAUDE.md | `~/.claude/CLAUDE.md` | Media |
| Proyecto local | `./CLAUDE.local.md` | Media |
| Auto memory | `~/.claude/projects/<proyecto>/memory/` | Menor |

## Frontmatter Reference

Las rules tienen un frontmatter mas simple que los skills. Campos soportados:

| Campo | Tipo | Requerido | Descripcion |
|-------|------|-----------|-------------|
| `paths` | string o array | No | Patrones glob para scope condicional |
| `globs` | string | No | Alternativa a `paths` (mas fiable, ver nota) |

### Bug conocido con `paths` (febrero 2026)

Existe un bug documentado (GitHub issues #13905, #17204, #21858) con el parsing del campo `paths`. Los formatos que **funcionan**:

```yaml
# Patron unico sin comillas (funciona)
---
paths: **/*.py
---

# CSV separado por comas (funciona)
---
paths: "**/*.ts,**/*.tsx"
---

# Campo globs - alternativa mas fiable
---
globs: "**/*.ts,**/*.tsx"
---
```

Formatos que **NO funcionan** (fallan silenciosamente):

```yaml
# Array YAML con strings entre comillas - NO FUNCIONA
---
paths:
  - "**/*.ts"
  - "**/*.tsx"
---

# String unico entre comillas en paths - NO FUNCIONA
---
paths: "**/*.ts"
---
```

**Recomendacion**: Usar `globs` con patrones separados por comas hasta que se corrija el bug.

## Patrones Glob

| Patron | Matchea |
|--------|---------|
| `**/*.ts` | Todos los archivos TypeScript en cualquier directorio |
| `src/**/*` | Todos los archivos bajo `src/` |
| `*.md` | Archivos markdown solo en la raiz del proyecto |
| `src/components/*.tsx` | Componentes React directamente en ese directorio (no anidados) |
| `**/*.test.ts` | Todos los archivos de test en cualquier lugar |
| `**/*.{ts,tsx}` | Archivos `.ts` y `.tsx` (brace expansion) |
| `{src,lib}/**/*.ts` | TypeScript en ambos `src/` y `lib/` |

Multiples patrones separados por comas:

```yaml
---
globs: "src/**/*.ts,lib/**/*.ts,tests/**/*.test.ts"
---
```

## Rules vs CLAUDE.md

| Aspecto | CLAUDE.md | `.claude/rules/` |
|---------|-----------|-------------------|
| **Carga** | Siempre, cada sesion | Siempre (con path-filter opcional) |
| **Contenido** | Estandares globales, indice | Conocimiento especifico por dominio |
| **Ideal para** | Comandos de build, workflow git, overview | Guias por lenguaje, seguridad, testing |
| **Scope** | Todo el proyecto | Dominios o tipos de archivo especificos |
| **Tamano** | < 200 lineas ideal | Cada archivo < 200-500 lineas |
| **Organizacion** | Archivo unico | Multiples archivos enfocados |

### Arbol de decision

```text
¿Es una convencion universal del proyecto?
  SI → CLAUDE.md
  NO → ¿Es especifico a ciertos tipos de archivo?
    SI → .claude/rules/ con frontmatter `globs`
    NO → ¿Es material de referencia necesario a veces?
      SI → Skill (se carga solo cuando es relevante)
      NO → ¿Es un workflow que activas manualmente?
        SI → Skill con disable-model-invocation: true
        NO → ¿DEBE ejecutarse siempre sin excepcion?
          SI → Hook (deterministico)
          NO → Skill o subagente
```

## Ejemplos Reales

### Estructura de directorio recomendada

```text
.claude/rules/
├── general.md              # Sin paths — siempre cargado
├── code-style.md           # Sin paths — siempre cargado
├── frontend/
│   ├── vue.md              # globs: **/*.vue,**/*.ts
│   └── styles.md           # globs: **/*.css,**/*.scss
├── backend/
│   ├── api.md              # globs: src/api/**/*
│   └── database.md         # globs: **/migrations/**,**/*.sql
├── security.md             # globs: src/auth/**,src/payments/**
└── testing.md              # globs: **/*.test.*,**/tests/**
```

### Rule de Python (`python.md`)

```yaml
---
globs: "**/*.py"
---

# Python Development Standards

## Estilo
- Black formatter con line-length 80
- isort con profile='black'
- Type hints requeridos en todas las funciones

## Testing
- pytest con coverage >= 80%
- pytest-mock para mocking
- Doctests obligatorios en funciones utilitarias

## Django
- Optimizar queries con select_related/prefetch_related
- Nunca usar .all() sin paginacion en views
- Usar F() y Q() para queries complejas

## Ejemplo de view correcta

```python
class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet para operaciones de pago."""

    queryset = Payment.objects.select_related(
        'user', 'provider'
    ).prefetch_related('transactions')
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        return super().get_queryset().filter(
            user=self.request.user
        )
```
```

### Rule de React/Next.js (`next-dashboard.md`)

```yaml
---
globs: "dashboard/**/*.tsx,dashboard/**/*.ts"
---

# Next.js 16 + React 19.2 + TypeScript 6 Standards

## Componentes
- Server Components por default (NO agregar `'use client'` salvo necesidad real)
- File naming kebab-case, export PascalCase (`payment-card.tsx` -> `<PaymentCard>`)
- Props tipadas con interface o type alias
- shadcn primitives en `components/ui/` NO se modifican con logica de negocio

## Hooks
- Prefijo "use" (`use-theme.ts`, `use-auth.ts`)
- Custom hooks en `hooks/` o co-localizados con la feature
- Retornar tuples o objetos tipados explicitos

## Stores (Zustand)
- Siempre `'use client'` arriba (Zustand es client-only)
- Selectores en consumidores: `useAuthStore((s) => s.user)`
- Persistencia opcional via `persist` middleware

## Server Actions
- `'use server'` en archivos `modules/<dominio>/actions/<verb-noun>.ts`
- Validacion con Zod `.safeParse()` (NUNCA `throw` como flujo de control)
- Retornar discriminated union: `{ ok: true, data } | { ok: false, error }`

## Ejemplo de componente correcto

```tsx
// dashboard/components/features/payments/payment-card.tsx
interface PaymentCardProps {
  variant?: 'primary' | 'secondary'
  disabled?: boolean
  children: React.ReactNode
}

export function PaymentCard({
  variant = 'primary',
  disabled = false,
  children,
}: PaymentCardProps): React.JSX.Element {
  return (
    <div
      className={cn(
        'rounded-md border border-base bg-surface p-4',
        variant === 'primary' && 'border-primary',
        disabled && 'opacity-50 pointer-events-none',
      )}
      data-testid="payment-card"
    >
      {children}
    </div>
  )
}
```
```

### Rule de seguridad (`security.md`)

```yaml
---
globs: "src/auth/**/*,src/payments/**/*,**/validators.py"
---

# Security-Critical Code Rules

## Datos sensibles
- NUNCA loguear passwords, tokens JWT, codigos de verificacion, RUT/RUC completo
- Mercado Pago: NUNCA almacenar `card_number` ni CVV (tokenizar via MP SDK)
- Webhooks MP: validar firma `x-signature` antes de procesar payload

## Validaciones
- Validar TODOS los inputs en fronteras de funcion
- Usar queries parametrizadas exclusivamente (nunca string interpolation)
- Sanitizar outputs para prevenir XSS

## Autenticacion
- JWT con RS256 para firmar tokens
- Access token TTL: 15 minutos maximo
- Refresh token con rotacion obligatoria

## Ejemplo de validacion segura

```python
from django.core.validators import RegexValidator

rut_validator = RegexValidator(
    regex=r'^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$',
    message='RUT invalido. Formato: XX.XXX.XXX-X'
)

def validate_payment_input(data: dict) -> dict:
    """Valida input de pago en frontera del controller."""
    amount = data.get('amount')
    if not isinstance(amount, (int, float)) or amount <= 0:
        raise ValidationError('Monto debe ser positivo')
    if amount > 999999999:
        raise ValidationError('Monto excede limite')
    # Nunca loguear datos sensibles
    logger.info('Payment validated', extra={
        'amount': amount,
        'card_last_four': data.get('card_number', '')[-4:],
    })
    return data
```
```

### Rule de testing (`testing.md`)

```yaml
---
globs: "**/*.test.*,**/*.spec.*,**/tests/**"
---

# Test Writing Standards

## Nomenclatura
- Nombres descriptivos: "should [accion] when [condicion]"
- Ejemplo: "should return 400 when email is invalid"

## Estructura
- Patron AAA: Arrange, Act, Assert
- Una asercion por test cuando sea posible
- Mock dependencias externas, nunca llamar APIs reales

## Coverage
- Minimo 80% para codigo nuevo
- 100% para logica de negocio financiera

## Ejemplo de test correcto

```python
import pytest
from unittest.mock import patch

class TestPaymentValidator:
    """Tests para validador de pagos."""

    def test_should_accept_valid_amount(self):
        # Arrange
        data = {'amount': 15000, 'currency': 'CLP'}

        # Act
        result = validate_payment_input(data)

        # Assert
        assert result['amount'] == 15000

    def test_should_reject_negative_amount(self):
        # Arrange
        data = {'amount': -100, 'currency': 'CLP'}

        # Act & Assert
        with pytest.raises(ValidationError, match='positivo'):
            validate_payment_input(data)

    @patch('services.payment_gateway.charge')
    def test_should_handle_gateway_timeout(self, mock_charge):
        # Arrange
        mock_charge.side_effect = TimeoutError()

        # Act & Assert
        with pytest.raises(PaymentError, match='timeout'):
            process_payment({'amount': 5000})
```
```

### Rule de migraciones (`migrations.md`)

```yaml
---
globs: "**/migrations/**/*,**/*.sql"
---

# Migration Safety Rules

- Siempre incluir instrucciones de rollback
- Testear migraciones en copia de datos de produccion primero
- Nunca eliminar columnas en la misma migracion que remueve codigo dependiente
- Agregar constraints NOT NULL con valores default en pasos separados
- Nunca modificar migraciones ya aplicadas en produccion

## Ejemplo de migracion segura

```python
# migrations/0042_add_payment_status.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('payments', '0041_previous'),
    ]

    operations = [
        # Paso 1: Agregar columna con default
        migrations.AddField(
            model_name='payment',
            name='status',
            field=models.CharField(
                max_length=20,
                default='pending',
                choices=[
                    ('pending', 'Pending'),
                    ('completed', 'Completed'),
                    ('failed', 'Failed'),
                ],
            ),
        ),
        # Paso 2: Backfill en migracion de datos separada
    ]
```
```

## Migracion desde CLAUDE.md Monolitico

Si tu CLAUDE.md excede 150+ lineas:

```text
ANTES: CLAUDE.md (500 lineas, todo en un archivo)
├── Reglas generales (100 lineas)        ← mantener en CLAUDE.md
├── Git workflow (50 lineas)             ← mantener en CLAUDE.md
├── Guia Python (100 lineas)             ← mover a rules/python.md
├── Guia Vue (80 lineas)                 ← mover a rules/vue.md
├── Seguridad (70 lineas)                ← mover a rules/security.md
└── Testing (100 lineas)                 ← mover a rules/testing.md

DESPUES:
├── CLAUDE.md (150 lineas)               ← 3x mas ligero
└── .claude/rules/
    ├── python.md (100 lineas, globs: **/*.py)
    ├── vue.md (80 lineas, globs: **/*.vue,**/*.ts)
    ├── security.md (70 lineas, globs: src/auth/**,src/payments/**)
    └── testing.md (100 lineas, globs: **/*.test.*)
```

Pasos:

1. Identificar secciones tematicas en CLAUDE.md
2. Extraer cada seccion a un archivo `.claude/rules/` enfocado
3. Agregar frontmatter `globs` donde las reglas aplican a tipos de archivo especificos
4. Simplificar CLAUDE.md a overview del proyecto y comandos universales
5. Verificar con `/memory` que las rules se cargan correctamente
6. Commitear a version control

## Relacion con settings.json

`settings.json` y rules son sistemas **paralelos**:

| Sistema | Controla | Ejemplo |
|---------|----------|---------|
| `.claude/settings.json` | Que **puede hacer** Claude (permisos) | `permissions.allow: ["Bash(git:*)"]` |
| `.claude/rules/*.md` | Que **debe hacer** Claude (instrucciones) | "Usar pytest, nunca unittest" |

No hay configuracion de rules dentro de settings.json. Los permisos de tools, hooks, y plugins se manejan en settings; las convenciones de codigo y estandares se manejan en rules.

## Fuentes

- [Manage Claude's memory - Docs oficiales](https://code.claude.com/docs/en/memory)
- [Claude Code Rules Directory: Modular Instructions - claudefa.st](https://claudefa.st/blog/guide/mechanics/rules-directory)
- [Claude Code Gets Path-Specific Rules - paddo.dev](https://paddo.dev/blog/claude-rules-path-specific-native/)
- [Claude Code Customization Guide - marioottmann.com](https://marioottmann.com/articles/claude-code-customization-guide)
- [GitHub Issue #17204: paths frontmatter format](https://github.com/anthropics/claude-code/issues/17204)
- [GitHub Issue #13905: YAML syntax in rules](https://github.com/anthropics/claude-code/issues/13905)

---

[Siguiente: Skills (Referencia)](07-skills.md)
