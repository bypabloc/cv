**07**

# Configurar la app del celular

[← Índice](README.md)

---

### Instalar

- **Android:** "ntfy" en Google Play o F-Droid.
- **iOS:** "ntfy" en App Store.

### 1. Agregar tu usuario para el servidor propio

⋮ → **Configuración** → **Usuarios** (sección *General*) → **Agregar usuario**:

| Campo | Valor |
| :-- | :-- |
| URL del servicio | `https://ntfy.tu-dominio.com` |
| Usuario | `admin` (o un usuario de solo lectura) |
| Contraseña | La que definiste al instalar |

### 2. Suscribirte al tópico

Pantalla principal → **+**:

| Campo | Valor |
| :-- | :-- |
| Tópico | `alertas` (**solo el nombre**, sin URL ni barras) |
| Usar otro servidor | Activado → `https://ntfy.tu-dominio.com` |
| Entrega instantánea (Android) | Activada: conexión permanente, avisos sin demora |

Al suscribirte verás los mensajes de las últimas 24 h (la caché del servidor).

### 3. Respaldo en ntfy.sh

Repite el paso 2 con tu tópico aleatorio de ntfy.sh y **sin** activar "Usar otro servidor". Si tu servidor cae, el aviso de falla llega por ahí.

### El error más común: tópico con `/`

Síntoma en la lista de suscripciones:

```
ntfy.sh/<tema-aleatorio>/Alertas
0 notificaciones, reconectando...  ⚠
```

- Se escribió en el campo **Tópico** la URL completa más un nombre.
- Un tópico **no puede tener `/`**: la app queda reconectando para siempre y no recibe nada.
- Solución: borrar la suscripción y crearla con **solo** el nombre del tópico.

### Si no llegan notificaciones

| Síntoma | Solución |
| :-- | :-- |
| "reconectando…" con ⚠ | Tópico mal escrito o servidor caído (`curl https://ntfy.tu-dominio.com/v1/health`) |
| Aparecen en la app pero no suenan | Ajustes de Android → Apps → ntfy → Notificaciones permitidas |
| Llegan tarde con la pantalla apagada | Ajustes → Batería → ntfy → **Sin restricciones** |
| iOS no recibe del servidor propio | Revisa `upstream-base-url: "https://ntfy.sh"` en `server.yml` |
| 401/403 al suscribirte | Usuario no agregado para esa URL o sin permiso de lectura en el tópico |

### Prioridades en el celular

- `min`/`low`: llega sin sonido (el reporte "OK" usa `low`).
- `high`: suena y vibra (el reporte "FALLO" usa `high`).
- `urgent`: suena aunque esté en silencio.

`ntfy` `android` `ios` `troubleshooting`
