**06**

# Usuarios, permisos y tokens

[← Índice](README.md)

Todos los comandos se ejecutan **en el servidor** con `sudo`.

---

### Modelo

- `auth-default-access: deny-all`: sin usuario o token nadie lee ni publica.
- Un usuario **admin** con acceso total.
- **Un token por sistema** que publica (tu PC, el reporte del servidor, un CI…): si uno se filtra, revocas solo ese.

### Usuarios

```bash
sudo ntfy user list
sudo ntfy user add --role=admin admin        # pide la clave (o la toma de NTFY_PASSWORD)
sudo ntfy user add lector                    # usuario normal
sudo ntfy user change-pass admin
sudo ntfy user del lector
```

### Permisos por tópico (usuarios no admin)

```bash
sudo ntfy access lector alertas read-only    # solo leer
sudo ntfy access ci deploys write-only       # solo publicar
sudo ntfy access lector 'proyecto-*' rw      # comodines
sudo ntfy access                             # ver todos
sudo ntfy access --reset lector alertas      # quitar
```

### Tokens

```bash
sudo ntfy token add --label mi-pc admin            # imprime tk_...
sudo ntfy token add --label ci --expires=90d admin
sudo ntfy token list admin
sudo ntfy token remove admin tk_xxxxxxxx
```

Tokens que usa esta guía:

| Token | Dónde vive | Para qué |
| :-- | :-- | :-- |
| `mi-pc` | Variable de entorno de tu PC | Avisos de scripts y de Claude Code ([capítulo 09](09-claude-code.md)) |
| `server-report` | `/etc/ntfy-report.env` en el servidor (root, `600`) | Reporte de estado ([capítulo 10](10-reporte-de-estado.md)) |

### Formas de autenticarse al publicar

| Forma | Ejemplo | Cuándo |
| :-- | :-- | :-- |
| Token (recomendada) | `-H "Authorization: Bearer tk_..."` | Scripts y servidores |
| Usuario y clave | `-u admin` (pide la clave) | Pruebas manuales; la app del celular |
| En la URL | `?auth=<base64>` | Solo si no hay headers; queda en logs |

### Buenas prácticas

- Nunca pegues un token en un repo, chat o ticket.
- Revoca y recrea cualquier token expuesto.
- Usa `--expires` para tokens temporales.

`ntfy` `auth` `tokens` `acl`
