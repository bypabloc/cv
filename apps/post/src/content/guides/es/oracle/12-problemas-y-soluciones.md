**12**

# Problemas y soluciones

[← Índice](README.md)

---

### Alta y CLI

| Problema | Causa | Solución |
| :-- | :-- | :-- |
| No aparece la región que quiero | No admite cuentas gratis o cambió la disponibilidad | Elegir otra de la lista; la región no se cambia después |
| `NotAuthenticated` | Fingerprint, `user` o `tenancy` mal copiados en `~/.oci/config` | Volver a copiar el *Configuration file preview* y verificar el fingerprint con `openssl` |
| `Missing option(s) --tenancy-id` | `iam region-subscription list` exige el tenancy | `--tenancy-id "$(awk -F= '/^tenancy=/{print $2}' ~/.oci/config)"` |
| Advertencia de permisos del config | Archivos legibles por otros | `oci setup repair-file-permissions --file ~/.oci/config` |
| `oci: command not found` tras instalar | PATH de `uv` no cargado | `uv tool update-shell` y abrir otra terminal |

### Red e instancia

| Problema | Causa | Solución |
| :-- | :-- | :-- |
| `NotAuthorizedOrNotFound` justo después de crear el compartment | Propagación | `sleep 20` antes de crear la VCN |
| "Out of host capacity" en A1 | Sin hosts ARM libres para la capa gratis | Reintentar en bucle cada 2 min o usar Micro |
| Cupos de A1 enormes en `oci limits` | Son del crédito de prueba | Respetar 2 OCPU / 12 GB de Always Free |
| SSH `Connection refused` | cloud-init aún arrancando | Esperar 1–2 min y reintentar |
| 80/443 no responden aunque la Security List los permite | `iptables` de la imagen con `REJECT` final | Insertar el `ACCEPT` antes del `REJECT` y `netfilter-persistent save` |
| `apt` muere por falta de memoria en la Micro | 1 GB sin swap | Swap de 1 GB (capítulo 07) |

### Reclamo y monitoreo

| Problema | Causa | Solución |
| :-- | :-- | :-- |
| Un reporte dice "CPU 0 %" | Foto de un instante | Mirar el **p95 de 7 días** |
| En Micro la RAM alta no protege | La regla de memoria solo aplica a A1 | Keepalive de CPU |
| "Cada 45 min" con cron dispara a :00 y :45 | `*/45` no es un intervalo real | Timer de systemd con `OnUnitActiveSec=45min` |
| Una línea de cron con `%` se corta | `%` es especial en crontab | Escaparlo como `\%` |
| La VM caída no avisa | No puede reportar si está muerta | La **ausencia** de reporte por más de 45 min es la alarma |
| Instancia reclamada | p95 de CPU (y red; en A1 también memoria) bajo 20 % por 7 días | Recrearla con los scripts; IP nueva → actualizar DNS |

`troubleshooting` `oracle-cloud`
