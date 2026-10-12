**10**

# Operación y borrado

[← Índice](README.md)

---

### Estado de la instancia

```bash
oci compute instance get --instance-id "$I" --query 'data."lifecycle-state"' --raw-output   # RUNNING
oci compute instance list -c "$C" --query 'data[].{n:"display-name",s:"lifecycle-state",forma:shape}' --output table
```

### Encender, apagar, reiniciar

```bash
oci compute instance action --instance-id "$I" --action SOFTRESET   # reinicio ordenado
oci compute instance action --instance-id "$I" --action STOP
oci compute instance action --instance-id "$I" --action START
```

> Una instancia **detenida** no usa CPU y cuenta como inactiva para el reclamo.

### Actualizaciones

- `unattended-upgrades` instala los parches de seguridad solo.
- Si el reporte dice "requiere reinicio":

```bash
ssh mi-vm 'sudo apt-get update && sudo apt-get -y upgrade && sudo reboot'
```

Todo lo que esté `enable` en systemd (servicios, timer del reporte) y los crons arrancan solos.

### Respaldo

La VM puede ser reclamada. Respalda fuera:

- **Scripts de instalación:** en un repo; recrean el servidor en minutos.
- **Datos y configuración:** lo que tu servicio guarde, más `/etc/cron.d/oci-keepalive` y `/etc/vm-report.env`.

```bash
ssh mi-vm 'sudo tar czf - /etc/cron.d /etc/vm-report.env /ruta/de/tus/datos' > respaldo-$(date +%F).tgz
```

Oracle también permite respaldar el volumen de arranque (5 respaldos gratis):

```bash
BV=$(oci compute boot-volume-attachment list -c "$C" --availability-domain "$AD" --instance-id "$I" \
  --query 'data[0]."boot-volume-id"' --raw-output)
oci bv boot-volume-backup create --boot-volume-id "$BV" --display-name "mi-vm-$(date +%F)"
```

### Ver la IP pública

```bash
oci compute instance list-vnics --instance-id "$I" --query 'data[0]."public-ip"' --raw-output
```

### Borrar todo

Orden: primero lo que depende de otros recursos.

```bash
oci compute instance terminate --instance-id "$I" --preserve-boot-volume false --force --wait-for-state TERMINATED
oci network subnet delete --subnet-id "$SN" --force --wait-for-state TERMINATED
oci network route-table update --rt-id "$RT" --route-rules '[]' --force
oci network internet-gateway delete --ig-id "$IG" --force --wait-for-state TERMINATED
oci network vcn delete --vcn-id "$V" --force --wait-for-state TERMINATED
oci iam compartment delete --compartment-id "$C" --force     # puede tardar varios minutos
```

Además:

- Borra los registros DNS que apuntaban a la IP.
- Revoca la API key en la consola (**My profile → API keys → Delete**) si ya no la usarás.
- Borra la clave SSH local: `rm -f ~/.ssh/oci_mi_vm ~/.ssh/oci_mi_vm.pub`.

`oracle-cloud` `operacion` `backup` `teardown`
