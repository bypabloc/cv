# Riesgos y decisiones abiertas

No bloquean iniciar la implementación — se resuelven durante las tareas
indicadas.

1. **Pack sci-fi para `futuro` sin CC0 100% verificado todavía**
   (tarea T4b). Se profundiza en poly.pizza/itch.io hasta confirmar
   licencia exacta antes de descargar. Plan B si no aparece nada
   satisfactorio: vestir `futuro` con el pack genérico de Quaternius +
   preservar el `futurePortal` (shader GLSL propio que ya existe en
   `props.ts`, no depende de assets externos).
2. **Cobertura de animaciones del pack Quaternius** (tarea T3). Las 24
   animaciones incluidas no están confirmadas 1:1 contra los 7
   `CharacterPose` actuales (`idle/walk/fight/sit/kneel/wave/talk`). Se
   audita la lista real de clips al cargar el `.glb`; gaps se resuelven
   con Mixamo (auto-rig + retarget), sin costo de licencia adicional.
3. **`NoToneMapping` vs. tone mapping nuevo** (tarea T2). Spider-Verse es
   un look gráfico/plano, no cinemático-HDR como Messenger — se decide
   empíricamente si el halftone shader alcanza para la identidad visual
   sin tocar el tone mapping, o si hace falta ACES. No se decide a
   priori.
4. **`feature/journey-npc-realism` y `apps/journey-realistic` quedan
   huérfanos** — no se tocan en este plan. Si en el futuro se decide
   limpiar (borrar rama/carpeta) o rescatar algo (el research de
   licencias de generadores IA text-to-3D, por ejemplo), es una decisión
   aparte, fuera de este plan.
5. **`HalftoneShader`/`ChromaticAberrationShader` son prototipo, no
   producción pulida** (tarea T2). Puede requerir iteración visual
   (frecuencia de puntos, grosor de contorno, intensidad de aberración)
   que no se puede planificar de antemano — se ajusta mirando el
   resultado real en pantalla, con el dueño validando.
