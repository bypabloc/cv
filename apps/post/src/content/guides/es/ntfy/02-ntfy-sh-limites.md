**02**

# ntfy.sh gratis y sus límites

[← Índice](README.md)

Fuentes: [docs.ntfy.sh/publish, sección Limitations](https://docs.ntfy.sh/publish/) y [ntfy.sh/#pricing](https://ntfy.sh/#pricing) (octubre de 2026).

---

### Límites gratis (por IP, sin cuenta)

| Límite | ntfy.sh |
| :-- | :-- |
| Mensajes por día | **250** |
| Ráfaga | 60 requests seguidos, luego 1 cada 5 s |
| Tamaño del mensaje | 4.096 bytes (título 1 KB, tags 512 bytes) |
| Adjuntos | 2 MB cada uno, 20 MB en total, se borran a las 3 h |
| Emails | 5 por día |
| Conexiones de suscripción | 30 |
| Tráfico | 200 MB por día |
| Caché de mensajes | ~12 h |
| Tópicos reservados | Ninguno |

### Planes pagos

| Plan | USD | Mensajes/día | Tópicos reservados | Adjuntos |
| :-- | :-- | :-- | :-- | :-- |
| Supporter | 5 | 2.500 | 3 | 25 MB |
| Pro | 10 | 20.000 | 10 | 250 MB |
| Business | 20 | 50.000 | 50 | 1 GB |

La página no aclara si el precio es mensual o anual.

### Usarlo bien

- Tópico con nombre **largo y aleatorio** (funciona como contraseña):

```bash
echo "avisos-$(head -c 12 /dev/urandom | od -An -tx1 | tr -d ' \n')"
```

- Nunca envíes datos sensibles: quien conozca el nombre lee todo.

### Papel de ntfy.sh con un servidor propio

- **Respaldo**: el reporte de estado también publica ahí; si tu servidor cae, el aviso de falla igual llega.
- **Relay de iOS**: necesario aunque tengas servidor propio.

`ntfy` `ntfy-sh` `limites` `precios`
