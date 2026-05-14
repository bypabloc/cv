# API Token: permisos, creacion, rotacion

> Como crear, manejar, rotar y revocar el API token de Cloudflare con
> permisos minimos para gestionar el deploy del portfolio.

[← Architecture](./01-architecture.md) | [README](./README.md) | [Siguiente: Pages API setup →](./03-pages-api-setup.md)

## Permisos minimos

| Resource | Permission | Scope |
|----------|-----------|-------|
| Account → **Cloudflare Pages** | Edit | tu account |
| Zone → **DNS** | Edit | `the-full-stack.com` |
| Zone → **SSL and Certificates** | Read | `the-full-stack.com` |
| User → **User Details** | Read | All accounts |

### Por que cada uno

- **Pages Edit**: crear/modificar/borrar proyectos, attachar custom
  domains, configurar env vars y build_config.
- **DNS Edit**: crear/listar/actualizar CNAMEs en la zona.
- **SSL Read**: verificar status de certs (Universal SSL emite solo,
  no requiere Edit).
- **User Details Read**: necesario para `/user/tokens/verify` (validar
  que el token esta activo).

### Permisos a EVITAR

- ❌ `Account Admin` — overprovisioned
- ❌ `API Token Management` — permite rotar el token mismo (riesgo)
- ❌ `Account Settings: Edit` — innecesario
- ❌ Cualquier `Zone: *` wildcard — usar zona especifica

### Permisos opcionales (solo si necesario)

- `Zone → Zone Settings: Edit` — si vas a cambiar Always Use HTTPS,
  TLS minimo, etc.
- `Zone → SSL and Certificates: Edit` — solo si gestionas certs custom
  (no para Universal SSL).
- `Zone → Page Rules: Edit` / `Firewall: Edit` — solo si automatizas
  rules.
- `Account → Workers Scripts: Edit` — solo si migras a Workers Static
  Assets en el futuro.

## Crear el token (2026)

1. Dashboard https://dash.cloudflare.com/profile/api-tokens
2. **Create Token** → **Create Custom Token** (no usar templates pre-hechos)
3. Name: `portfolio-pages-api` (o similar identificable)
4. Permissions: agregar los 4 de la tabla arriba
5. Account Resources: seleccionar tu account
6. Zone Resources: seleccionar `the-full-stack.com` (no wildcard)
7. **TTL**: 7-30 dias (rotar regularmente). 7 dias es ideal para tareas
   one-shot; 30 si vas a iterar.
8. **Create Token** y **copiar inmediato** — Cloudflare lo muestra
   UNA sola vez.

## Almacenamiento local

```bash
# Template en el repo (sin valores)
cp tmp/cloudflare-creds.env.template tmp/cloudflare-creds.env

# Editar el archivo y completar:
# CLOUDFLARE_API_TOKEN=v1.0_xxx...
# ACCOUNT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# tmp/ esta en .gitignore — el archivo NO se commitea
```

## Verificar el token

```bash
set -a; . tmp/cloudflare-creds.env; set +a

# Check token activo
curl -s "https://api.cloudflare.com/client/v4/user/tokens/verify" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN"
# Esperado: success=true, status=active

# Check acceso a Pages
curl -s "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/pages/projects" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN"
# Esperado: success=true, result=[lista de proyectos]
```

## Account ID

Dashboard → cualquier sitio en CF → panel derecho **Account ID**
(string de 32 chars hexadecimal). NO es secreto, pero igual no lo
publiques.

## Rotacion (cada 7-30 dias)

1. Crear token nuevo (mismos permisos) en el dashboard.
2. Reemplazar el valor en `tmp/cloudflare-creds.env`.
3. Esperar ~1h para que requests en vuelo terminen.
4. Eliminar token viejo desde el dashboard.

## Si el token se filtra

**INMEDIATO:**

1. Dashboard → My Profile → API Tokens → eliminar el token comprometido
2. Si esta en historia de git: revisar con
   `git log --all -p | grep -i cloudflare` y purgar si aparece
   (`git filter-branch` o BFG Repo Cleaner)
3. Crear token nuevo y actualizar `tmp/cloudflare-creds.env`
4. Revisar Audit Logs en CF (Account → Audit Logs) por actividad
   sospechosa con el token viejo

## Cleanup despues de una tarea

```bash
# Borrar credenciales locales
rm -f tmp/cloudflare-creds.env

# Revocar token en el dashboard (no se puede via API sin permiso de
# token management, que es justo lo que NO queremos darle)
# → https://dash.cloudflare.com/profile/api-tokens → eliminar
```

No es necesario tener el token siempre activo. Crear uno cuando se
necesita, revocarlo al terminar — minimiza la superficie de ataque.
