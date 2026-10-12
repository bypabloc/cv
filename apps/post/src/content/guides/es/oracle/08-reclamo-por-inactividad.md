**08**

# Reclamo por inactividad: la regla y cómo evitarla

[← Índice](README.md)

---

### La regla oficial

Texto exacto de [Always Free Resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm):

> Oracle will deem virtual machine and bare metal compute instances as idle if, during a 7-day period, the following are true:
> - CPU utilization for the 95th percentile is less than 20%
> - Network utilization is less than 20%
> - Memory utilization is less than 20% *(applies to A1 shapes only)*

> Idle Always Free compute instances may be reclaimed by Oracle.

### Cómo leerla

- Las condiciones van **unidas por "y"**: la instancia es inactiva solo si **todas** se cumplen. **Basta con que una supere el 20 %** para no serlo.
- **Percentil 95 de 7 días:** se ordenan todas las mediciones de la semana y se toma la que deja el 95 % por debajo. Si la CPU pasa de 20 % durante algo más del **5 % del tiempo**, el p95 supera 20 %.
- **La memoria solo cuenta en A1.** En la Micro solo cuentan CPU y red.
- Un servicio liviano (un bot, un webhook, un servidor de notificaciones) casi no usa CPU ni red: **es inactivo por definición**.
- La documentación **no dice** si avisa antes de reclamar ni cómo.
- Pasar la cuenta a *Pay As You Go* se recomienda en foros, pero la documentación **no** dice que exima del reclamo.
- Una instancia **detenida** tampoco usa CPU: no la dejes apagada días.

### Estrategias

| Estrategia | Aplica a | Cómo | Evaluación |
| :-- | :-- | :-- | :-- |
| **Instancia chica** | A1 | 1 OCPU y 1 GB: el uso normal (~400 MB) supera el 20 % de RAM | Limpia, sin carga artificial. **La mejor** |
| **Keepalive de CPU** | Micro (y A1 si se quiere) | Cron que usa CPU unos segundos cada pocos minutos | Funciona; es carga artificial (zona gris frente a los términos) |
| Tráfico de red | Ambas | Generar tráfico sostenido | Desperdicia ancho de banda; descartada |

### El keepalive (Micro)

```bash
ssh mi-vm "echo \"*/10 * * * * root timeout 75 nice -n 19 sh -c 'cat /dev/urandom | sha256sum >/dev/null' 2>/dev/null || true\" | sudo tee /etc/cron.d/oci-keepalive"
```

Contenido de `/etc/cron.d/oci-keepalive`:

```cron
*/10 * * * * root timeout 75 nice -n 19 sh -c 'cat /dev/urandom | sha256sum >/dev/null' 2>/dev/null || true
```

| Parte | Por qué |
| :-- | :-- |
| `*/10` | Cada 10 minutos |
| `timeout 75` | 75 s de carga ≈ 12,5 % del tiempo, más que el 5 % que necesita el p95; nunca queda corriendo |
| `nice -n 19` | Prioridad mínima: tus servicios siempre tienen la CPU primero |
| `sha256sum` de `/dev/urandom` | Usa CPU sin tocar disco ni red |

### Evidencia

CPU máxima por minuto según Oracle Monitoring (UTC):

```
21:11  50%   21:12  88%   ← keepalive
21:13   0%  …  21:20   0%
21:21  56%   21:22  47%   ← keepalive
```

**Percentil 95 de la última hora: 49,9 %** según Oracle y **49 %** según el registro local de la VM. Muy por encima del 20 %.

### No te confundas con el "0 %"

Ver **CPU 0 %** en un momento dado no significa riesgo: es la foto de un instante sin keepalive. Lo que importa es el **p95 de 7 días**. El [capítulo 09](09-monitoreo.md) lo mide y lo reporta.

### Si la reclaman

- La IP pública cambia al recrear la instancia: actualiza tu DNS.
- Lo que estaba en el disco se pierde: guarda tus scripts de instalación y respaldos fuera ([capítulo 10](10-operacion-y-borrado.md)).
- El reporte de estado deja de llegar: **la ausencia de reporte es la alarma**.

`oracle-cloud` `always-free` `idle-reclamation` `keepalive` `p95`
