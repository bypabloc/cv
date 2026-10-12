**08**

# Publicar con curl

[← Índice](README.md)

Todos los ejemplos usan `$NTFY_TOKEN` (un token `tk_...`) y el tópico `alertas`.

```bash
read -rsp 'Token de ntfy: ' NTFY_TOKEN; echo; export NTFY_TOKEN
```

---

### 1. Mensaje simple

```bash
curl -H "Authorization: Bearer $NTFY_TOKEN" -d "Backup terminado" https://ntfy.tu-dominio.com/alertas
```

### 2. Título, prioridad y emoji

```bash
curl -H "Authorization: Bearer $NTFY_TOKEN" \
     -H "Title: Deploy prod" -H "Priority: high" -H "Tags: rocket" \
     -d "Deploy a prod OK" https://ntfy.tu-dominio.com/alertas
```

- `Priority`: `min`, `low`, `default`, `high`, `urgent`.
- `Tags`: nombres de emoji (`warning`, `white_check_mark`, `rotating_light`, `rocket`, `wave`).

### 3. Abrir una URL al tocarla

```bash
curl -H "Authorization: Bearer $NTFY_TOKEN" \
     -H "Click: https://github.com/<usuario>/<repo>/actions" \
     -d "CI terminó" https://ntfy.tu-dominio.com/alertas
```

### 4. Usuario y contraseña en vez de token

```bash
curl -u admin -d "Hola" https://ntfy.tu-dominio.com/alertas   # pide la clave
```

### 5. Avisar el resultado de un comando

```bash
make test \
  && curl -H "Authorization: Bearer $NTFY_TOKEN" -H "Tags: white_check_mark" -d "Tests OK" https://ntfy.tu-dominio.com/alertas \
  || curl -H "Authorization: Bearer $NTFY_TOKEN" -H "Tags: rotating_light" -H "Priority: high" -d "Tests fallaron" https://ntfy.tu-dominio.com/alertas
```

### 6. Programar un aviso

```bash
curl -H "Authorization: Bearer $NTFY_TOKEN" -H "In: 30m" -d "Revisa el horno" https://ntfy.tu-dominio.com/alertas
```

Mínimo 10 s, máximo 3 días.

### 7. Leer los mensajes recientes

```bash
curl -s -H "Authorization: Bearer $NTFY_TOKEN" "https://ntfy.tu-dominio.com/alertas/json?poll=1&since=1h" | jq -r '.message'
```

### 8. Salud del servidor (sin token)

```bash
curl https://ntfy.tu-dominio.com/v1/health      # {"healthy":true}
```

### 9. En ntfy.sh (sin token)

```bash
curl -H "Title: Aviso" -d "Hola" https://ntfy.sh/<tema-aleatorio>
```

### Respuesta

Un `POST` correcto devuelve el mensaje en JSON:

```json
{"id":"sMMIjkAXy6WU","time":1791754000,"event":"message","topic":"alertas","message":"Backup terminado"}
```

| Código | Significado |
| :-- | :-- |
| 200 | Publicado |
| 401 / 403 | Sin token, token inválido o sin permiso en el tópico |
| 429 | Límite de tasa |

> Publicar en un tópico al que nadie está suscrito funciona igual, pero no le llega a nadie.

`ntfy` `curl` `cli`
