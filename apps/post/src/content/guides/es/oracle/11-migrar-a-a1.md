**11**

# Migrar de Micro a A1

[← Índice](README.md)

---

### Por qué migrar

- A1 con 1 GB evita el reclamo **sin carga artificial**: la memoria usada ya supera el 20 %.
- Más CPU y RAM (hasta 2 OCPU y 12 GB gratis).
- Se elimina el keepalive.

### Paso 1: conseguir capacidad

Deja el script del [capítulo 06](06-instancia.md) reintentando en segundo plano:

```bash
NAME=mi-vm-a1 nohup bash oci-crear-instancia.sh a1 > instancia-a1.env 2> intentos-a1.log &
```

Al conseguirla: `eval "$(cat instancia-a1.env)"` deja `I` e `IP` de la nueva instancia.

### Paso 2: preparar la A1

```bash
ssh -i ~/.ssh/oci_mi_vm ubuntu@$IP 'sudo bash -s' < vm-base.sh       # capítulo 07
```

- La arquitectura es `arm64`: instala tu servicio con paquetes o imágenes para ARM.
- **No** instales el keepalive.

### Paso 3: copiar datos

```bash
ssh mi-vm 'sudo tar czf - /ruta/de/tus/datos' | ssh -i ~/.ssh/oci_mi_vm ubuntu@$IP 'sudo tar xzf - -C /'
```

### Paso 4: reporte de estado

Instálalo como en el [capítulo 09](09-monitoreo.md). En A1 el control relevante es la **memoria**: cambia la línea del p95 de CPU por:

```bash
[ "$mem_pct" -ge 20 ] || fails+=("RAM ${mem_pct}% (Oracle podría reclamarla)")
```

### Paso 5: cambiar el DNS

Actualiza los registros `A` a la IP nueva. Con TTL de 300 s se propaga en ~5 min.

### Paso 6: borrar la Micro

```bash
oci compute instance terminate --instance-id "$I_MICRO" --preserve-boot-volume false --force
```

Tiempo total estimado: ~15 minutos una vez conseguida la capacidad.

`oracle-cloud` `a1-flex` `migracion` `arm64`
