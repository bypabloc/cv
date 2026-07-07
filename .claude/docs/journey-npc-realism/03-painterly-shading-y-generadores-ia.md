# Painterly shading (Etapa 2) y generadores IA 3D locales

> [Indice](README.md) | Anterior: [export + Three.js](02-export-y-threejs-integracion.md) | Siguiente: [prompts Claude Code](04-prompts-claude-code.md)

## Técnica painterly de "Gato con Botas: El Último Deseo" (insumo Etapa 2)

Documentado por el VFX Supervisor de DreamWorks (Mark Edwards) en
prensa especializada (`beforesandafters.com`, corroborado por ACM
SIGGRAPH Blog, Animation World Network, VFX Voice, MovieWeb — todos
citando la misma fuente, sin paper técnico peer-reviewed detrás):

1. **Rim light como decisión estilística deliberada** (confianza alta,
   3-0): "cheated" — colocado por legibilidad/efecto gráfico, NO por
   precisión física. Cita directa: *"We both loved the graphic feeling
   you can get from that rim light... gave us that freedom to just use
   it because it looked good."* Portable directo a un `ShaderMaterial`
   custom de Three.js con un término de rim controlado por el artista
   (no acoplado a la iluminación de la escena).
2. **"Stamp maps"** (confianza media, 2-1): nubes de puntos procedurales
   proyectadas sobre superficies de personajes con coherencia temporal
   (funciona porque está "en espacio de referencia/UV estable"), usadas
   para aplicar texturas de pincelada con pasadas de render separadas
   compuestas en la imagen final. **No hay receta exacta reproducible**
   (sin fórmulas de ruido ni matemática de shader publicadas) — sirve
   de inspiración conceptual: un ruido tipo Voronoi/point-scatter en un
   shader, o una textura de albedo/normal horneada con trazos en espacio
   UV estable.

Esta sección es insumo conceptual para un plan FUTURO (Etapa 2, fuera
del scope del plan actual de geometría/rig).

## Generadores IA 3D locales — por qué NO se usan como ruta primaria

TripoSR, InstantMesh y Wonder3D son los 3 baselines de imagen-a-3D local
más relevantes, con números de rendimiento verificados con confianza
ALTA (3-0 unánime cada uno):

| Herramienta | Rendimiento verificado | Licencia/local — claim ORIGINAL | Resultado de la verificación adversarial |
|---|---|---|---|
| TripoSR | <0.5s en A100, ~6GB VRAM | "100% local sin cuenta, MIT" | **REFUTADO** (0-3) — la parte de "100% local sin cuenta" |
| InstantMesh | Zero123++ multivista + LRM, ~10s | "código+pesos+demo bajo CC BY 4.0, reusable con atribución" | **REFUTADO** (0-3) |
| Wonder3D | difusión cross-domain, 2-3 min | "MIT + corre 100% local (mirror Aliyun)" | **REFUTADO** (1-2) |
| Pipeline ComfyUI combinado | orquesta los 3 | "corre 100% local sin cuenta" | **REFUTADO** (0-3) |

**Conclusión**: los números de velocidad/VRAM son confiables, pero las
claims sobre licencia permisiva + "sin cuenta" para uso profesional/
portfolio **no sobrevivieron** la verificación adversarial (probablemente
por requisitos de descarga de pesos vía Hugging Face con gating, o
licencias más estrictas de lo que sugieren los abstracts). **No usar
estas herramientas sin releer a mano el archivo `LICENSE` real de cada
repo** y confirmar si la descarga de pesos exige token/cuenta.

Por esta razón, el pipeline de este proyecto usa **MPFB2** (verificado
3-0, GPLv3, sin cuenta, requiere Blender >=4.2) como ruta primaria para
la malla base, no estos generadores IA.

## Puentes Claude Code ↔ Blender (evaluado y descartado como dependencia)

`claude-blender` (`github.com/minihellboy/claude-blender`) es un bridge
MCP open-source (MIT) que expone 20+ tools a Claude Code, incluyendo
ejecutar `bpy` arbitrario vía JSON-RPC/TCP en `localhost:9876`, con
integraciones opcionales de IA local. Confirmado (confianza media, 2-1):
es un proyecto comunitario de baja actividad, no oficial de Anthropic ni
de Blender Foundation. **Se descarta como dependencia** — la ruta
recomendada es invocar `blender --background --python script.py`
directo vía el tool Bash de Claude Code, sin pasar por MCP (más control,
sin dependencia de un proyecto de baja madurez).

## Anti-patrones

| Anti-patrón | Por qué | Corrección |
|-------------|---------|------------|
| Usar TripoSR/InstantMesh/Wonder3D asumiendo "sin cuenta + licencia libre" | Ambas claims fueron refutadas en la verificación adversarial | Releer el `LICENSE` real de cada repo antes de adoptar; usar MPFB2 mientras tanto |
| Copiar "stamp maps" como receta exacta | Solo hay descripción conceptual en prensa, sin paper técnico | Usarlo como inspiración (ruido Voronoi/point-scatter), no como fórmula literal |
| Depender de `claude-blender` (MCP) para producción | Proyecto comunitario de baja actividad, no verificado | `blender --background --python` directo vía Bash |
