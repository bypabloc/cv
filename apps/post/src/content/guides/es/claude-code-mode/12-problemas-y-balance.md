**12**

# Problemas, mitos y balance

[← Índice](README.md)

---

### Problemas y soluciones

| Problema | Causa | Solución |
| :-- | :-- | :-- |
| `Code Mode (experimental) isn't available` | Proveedor, autenticación, modelo o plugin no admitido | Lee el motivo en `/status` |
| No arranca al lanzarlo desde otra sesión | Hereda las variables `CLAUDE_*` | Terminal limpia |
| No puedo reanudar una sesión sin el modo | Una sesión iniciada con el modo solo se reanuda con él | Sesión nueva |
| La tarea tardó más que en modo normal | El script hizo una lectura por archivo | Pide "un solo comando de shell" o usa el modo normal |
| La respuesta dice que leyó todo, pero faltan datos | Un filtro del script descartó registros | Pide conteos por paso y lo descartado |
| Falta la parte del medio de un resultado | Corte a ~30 mil caracteres | Devuelve resúmenes o trozos |
| Mis hooks se volvieron lentos | Se disparan en cada llamada interna | Hooks livianos, `timeout` adecuado |
| Un guardián no bloqueó tras un error del hook | Desde 2.1.329 la llamada se ejecuta por defecto | `"onFailure": "block"` |
| No corre en mi automatización | `claude -p` no lo admite | Úsalo en sesiones interactivas |

### Afirmaciones que circulan

| Afirmación | Realidad |
| :-- | :-- |
| "Ahorra 37 % de tokens" | Es una cifra de la API de 2025, no de Code Mode |
| "Siempre es más rápido" | En archivos locales a menudo es igual o más lento |
| "Code Mode falla cerrado si un hook falla" | Cierto hasta 2.1.328; desde 2.1.329 hay que pedirlo con `onFailure` |
| "El clasificador de auto mode me protege igual" | Revisa el script, no los valores que calcula al correr |
| "Con Code Mode me dura más la cuota" | Nadie lo midió todavía |
| "Lo usa para todo" | El modelo decide; una pregunta simple sigue siendo una lectura |

### Mi balance

| Tipo de trabajo | Lo uso |
| :-- | :-- |
| Investigación y consultas con muchas llamadas MCP | **Sí** |
| Implementar algo con ciclos de editar, compilar y probar | **Sí** |
| Varias verificaciones independientes y comandos largos | **Sí** |
| Auditorías o cambios mecánicos sobre muchos archivos locales | No: un script de shell es más rápido |
| Automatizaciones con `claude -p` | No se puede |

### Lo que no medí

- El efecto real en la cuota de 5 horas y la semanal de mi suscripción.
- Sonnet 5.5 y Fable 5.2: mis sesiones fueron con Opus 5.5 y Haiku 5.5.
- La calidad del código resultante más allá de que las pruebas pasen.

### Riesgos que conviene tener presentes

- **Es experimental:** cambia cada pocos días y puede desaparecer.
- **Los filtros pueden mentir por omisión:** pide siempre conteos.
- **El clasificador queda parcialmente ciego:** las operaciones críticas necesitan reglas o hooks propios.
- **Un porcentaje sin su tarea no sirve:** mide en tu proyecto.

`troubleshooting` `mitos` `balance` `code-mode`
