# Plan Format - Seccion 8: Descomposicion para Paralelizacion

> Documento referenciado desde `.claude/rules/plan-format.md`. Solo aplicar para
> planes Large (11+ archivos) o cuando se planee implementar con multiples
> agentes en git worktrees.

## Cuando incluir esta seccion

- Plan Large (11+ archivos) que se beneficie de paralelizacion
- Implementacion con multiples agentes concurrentes (subagentes paralelos en git worktrees)
- Refactors o migraciones cross-cutting con archivos independientes

Para planes Small/Medium, OMITIR esta seccion (no es necesaria).

## Reglas de paralelizabilidad

Cada tarea debe pasar 3 checks antes de marcarse como paralelizable:

1. **File Exclusivity**: archivos de escritura no se solapan con tareas concurrentes
2. **Interface Stability**: no cambia firmas/contratos de API que afecten otras tareas
3. **Bounded Scope**: archivos y directorios claramente delimitados

## Estructura de cada tarea

Cada tarea incluye 6 campos obligatorios:

- **Archivos**: paths exactos donde se va a escribir
- **AC referenciados**: AC-X, AC-Y de la seccion 3 del plan
- **Depende de**: lista de tareas que deben completarse primero (o `ninguna`)
- **Paralelizable con**: lista de tareas concurrentes seguras (o `ninguna`)
- **Verify**: comando ejecutable de verificacion
- **Done**: criterio observable de completitud

## Plantilla de seccion 8

```markdown
## 8. Descomposicion para Paralelizacion

### Tareas (orden topologico)

#### T1: Crear modelo y migration
- **Archivos**: `server/apps/products/models/product.py`, migrations
- **AC referenciados**: AC-1, AC-2
- **Depende de**: ninguna (raiz)
- **Paralelizable con**: T2 (no se solapan archivos)
- **Verify**: `manage.py makemigrations` + `migrate` exitosos
- **Done**: modelo creado, migration aplicada, test de creacion basica pasa

#### T2: Crear enums y exceptions
- **Archivos**: `server/apps/products/enums/status.py`, `server/apps/products/exceptions.py`
- **AC referenciados**: AC-3
- **Depende de**: ninguna (raiz)
- **Paralelizable con**: T1
- **Verify**: import `from apps.products.enums import ProductStatus` funciona
- **Done**: enums y exceptions disponibles para imports

#### T3: Service layer
- **Archivos**: `server/apps/products/services/creation.py`
- **AC referenciados**: AC-1, AC-2, AC-3
- **Depende de**: T1, T2
- **Paralelizable con**: ninguna (depende de raices)
- **Verify**: unit tests del service pasan
- **Done**: service creado, tests pasando, coverage >= 80%
```

## Reglas de granularidad y limites

- Granularidad por tamano de plan: Small=3-5 tareas, Medium=5-10, Large=10-20
- Si supera 20 tareas, descomponer en multiples planes (Huge)
- Limite practico de paralelizacion: **5-7 agentes concurrentes** (overhead de
  review crece despues)
- Tareas raiz (sin dependencias) primero — habilitan paralelismo inmediato
- NUNCA mas de un agente escribiendo en el mismo archivo simultaneamente

## Anti-patrones de paralelizacion

- Tareas con archivos solapados marcadas como "Paralelizable con" → race conditions
- Tareas que cambian interfaces publicas concurrentemente con consumidores → builds rotos
- "Paralelizable con: todas" sin verificacion real → falso positivo
- Mas de 7 agentes concurrentes → coordinacion humana se vuelve cuello de botella
- Tareas hoja (que dependen de muchas otras) marcadas como urgentes → bloquean el grafo

## Referencias

- Workflow Anthropic Explore → Plan → Implement → Commit
- `.claude/rules/plan-format.md` (regla principal, secciones 1-7 y 9)
- `.claude/rules/harness-protocol.md` (subagentes con output en disco)
