**04**

# API key y CLI `oci`

[← Índice](README.md)

---

### Por qué la CLI

- Todo queda en comandos repetibles (y en esta guía).
- Permite **reintentar automáticamente** la creación de la instancia cuando no hay capacidad, algo tedioso desde la consola web.
- Oracle no usa un token simple: usa una **API signing key** (par RSA) asociada a tu usuario.

### 1. Generar la API key en la consola

1. Ícono de perfil (arriba a la derecha) → **My profile**.
2. En *Resources* (abajo a la izquierda) → **API keys** → **Add API key**.
3. **Generate API key pair** → **Download private key** (`.pem`) → **Add**.
4. Copia el bloque **Configuration file preview**:

```ini
[DEFAULT]
user=ocid1.user.oc1..<...>
fingerprint=aa:bb:cc:...
tenancy=ocid1.tenancy.oc1..<...>
region=sa-santiago-1
key_file=<path to your private keyfile>
```

### 2. Guardar clave y config

```bash
mkdir -p ~/.oci
mv ~/Downloads/<tu-clave>.pem ~/.oci/oci_api_key.pem

cat > ~/.oci/config <<'EOF'
[DEFAULT]
user=<USER_OCID>
fingerprint=<FINGERPRINT>
tenancy=<TENANCY_OCID>
region=sa-santiago-1
key_file=~/.oci/oci_api_key.pem
EOF

chmod 700 ~/.oci && chmod 600 ~/.oci/*
```

Verificar que el fingerprint corresponde a la clave:

```bash
openssl rsa -in ~/.oci/oci_api_key.pem -pubout -outform DER | openssl md5 -c
```

### 3. Instalar la CLI

```bash
uv tool install oci-cli      # o: pipx install oci-cli
oci --version
```

Si dice `command not found`: ejecuta `uv tool update-shell` y abre otra terminal.

### 4. Verificar el acceso (solo lectura)

```bash
T=$(awk -F= '/^tenancy=/{print $2}' ~/.oci/config)
oci iam region-subscription list --tenancy-id "$T" --output table
```

Resultado esperado:

```
| is-home-region | region-key | region-name   | status |
| True           | SCL        | sa-santiago-1 | READY  |
```

> **Ojo:** `oci iam region-subscription list` sin `--tenancy-id` falla con `Missing option(s) --tenancy-id`.

### 5. Ver tus cupos

```bash
oci iam availability-domain list --compartment-id "$T" --query 'data[].name'
for l in standard-a1-core-count standard-a1-memory-count; do
  oci limits value list --compartment-id "$T" --service-name compute --name "$l" \
    --query 'data[].{ad:"availability-domain",value:value}' --output table
done
```

### Seguridad

- La clave tiene **el poder de tu usuario administrador** sobre toda la cuenta.
- Nunca la pegues en un chat, repo o ticket. Guárdala solo en `~/.oci/`.
- Revócala en **API keys → Delete** si se filtra.
- Para limitar el alcance: crea un usuario aparte con una política solo sobre el compartment del proyecto.

### Errores frecuentes

| Error | Causa o solución |
| :-- | :-- |
| `NotAuthenticated` | Fingerprint, `user` o `tenancy` mal copiados |
| Advertencia de permisos | `oci setup repair-file-permissions --file ~/.oci/config` |
| `Missing option(s) --tenancy-id` | Ese comando exige el tenancy explícito |

`oci-cli` `api-key` `autenticacion`
