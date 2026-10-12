**01**

# Qué es ntfy y cuándo montar el tuyo

[← Índice](README.md)

---

### En una línea

- Servidor **pub/sub por HTTP**: publicas con un `POST` a `https://<servidor>/<tópico>` y todo dispositivo suscrito a ese tópico recibe una notificación push.
- Open source (Apache 2.0 / GPLv2), escrito en Go, un solo binario.
- **ntfy.sh** es la instancia pública del autor; cualquiera puede instalar la suya.

### Cómo llega el mensaje al celular

```mermaid
flowchart LR
    S["Script / PC\n(curl POST)"] -->|HTTPS + token| N["Tu servidor ntfy\nntfy.tu-dominio.com"]
    N -->|conexión persistente\n(entrega instantánea)| A["App Android"]
    N -->|"aviso sin contenido"| R["ntfy.sh (relay)"]
    R -->|APNs| I["App iOS"]
```

| Pieza | Cómo funciona |
| :-- | :-- |
| Publicar | `POST`/`PUT` a `/<tópico>`. El tópico se crea solo al primer uso |
| Android | La app mantiene una conexión abierta (WebSocket o stream JSON) con tu servidor |
| iOS | Apple solo deja enviar push a quien firmó la app: tu servidor avisa a ntfy.sh (`upstream-base-url`), que despierta la app vía APNs; la app luego pide el contenido a tu servidor |
| Almacenamiento | SQLite con caché corta (aquí 24 h); no es una cola persistente |

### Conceptos

| Concepto | Qué es |
| :-- | :-- |
| **Tópico** | Canal. Sin autenticación, su nombre funciona como contraseña |
| **Usuario** | Cuenta con permisos de lectura/escritura por tópico |
| **Token** | Credencial `tk_...` de un usuario, ideal para scripts; revocable por separado |
| **Prioridad** | `min` a `urgent`; `urgent` suena aunque el celular esté en silencio |
| **Tags** | Emojis por nombre (`warning`, `rocket`) que aparecen en la notificación |

### Opciones

| Opción | Costo | Privado | Mantenimiento | Cuándo |
| :-- | :-- | :-- | :-- | :-- |
| ntfy.sh gratis | USD 0 | No: quien adivine el tópico lo lee | Ninguno | Avisos personales sin datos sensibles |
| ntfy.sh Supporter | USD 5 | Sí (3 tópicos reservados) | Ninguno | Privacidad sin administrar un servidor |
| **Servidor propio** | El de la VM | Sí | Medio | Control total, dominio propio, límites propios |

### Qué implica el servidor propio

| Se gana | Se asume |
| :-- | :-- |
| Tópicos privados con usuario y token | Parches, certificados y monitoreo |
| Sin el límite de 250 mensajes diarios | Si el servidor cae, no hay avisos (por eso ntfy.sh queda de respaldo) |
| Tu dominio | Una VM siempre encendida con IP pública |

`ntfy` `push-notifications` `pub-sub` `alternativas`
