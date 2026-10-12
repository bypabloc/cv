**02**

# Qué incluye la capa gratuita

[← Índice](README.md)

Fuente: [Always Free Resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm) (consultada en octubre de 2026).

---

### Free Trial vs. Always Free

Al crear la cuenta, la consola muestra:

> *Free Tier account · You are in a Free Trial. When your trial is over, your account is limited to Always Free resources.*

| | Free Trial | Always Free |
| :-- | :-- | :-- |
| Qué es | Crédito de **USD 300** para cualquier servicio | Recursos gratis sin fecha de vencimiento |
| Duración | Normalmente 30 días (la página oficial no lo precisa; revisa tu consola) | Indefinida, mientras la cuenta exista y el recurso no sea reclamado |
| Al terminar | Lo que no sea Always Free se detiene y luego se borra | Sigue funcionando |
| Cobro | Ninguno, salvo que hagas *Upgrade* a Pay As You Go | Ninguno |

**Regla práctica:** crea solo recursos con la etiqueta **Always Free-eligible**. Lo demás desaparece al terminar la prueba.

### Cómputo

| Forma | Cantidad gratis | CPU | RAM | Red |
| :-- | :-- | :-- | :-- | :-- |
| `VM.Standard.E2.1.Micro` (AMD x86) | Hasta **2** instancias | 1/8 OCPU (con ráfagas) | **1 GB** | Hasta 50 Mbps a internet |
| `VM.Standard.A1.Flex` (Ampere ARM) | **1.500 h OCPU + 9.000 h GB al mes** | Equivale a **2 OCPU** | Equivale a **12 GB** | Según la forma |

- A1 se usa como una instancia de 2 OCPU/12 GB o como dos de 1 OCPU.
- Las instancias Always Free **solo se crean en la región principal**.
- Durante la prueba, `oci limits` muestra cupos mucho mayores (por ejemplo 41 OCPU y 277 GB de A1). Son del crédito, no de Always Free.

### Almacenamiento y red

| Recurso | Gratis |
| :-- | :-- |
| Block Volume (boot + datos) | **200 GB** en total, solo región principal |
| Volumen de arranque | Mínimo ~47–50 GB por instancia (la página es inconsistente) |
| Respaldos de volumen | 5 en total |
| Object Storage | 20 GB y 50.000 requests al mes |
| Tráfico de salida | **10 TB al mes** |
| VCN | Hasta 2 |
| Load Balancer | 1 flexible de 10 Mbps + 1 Network Load Balancer |

### Otros servicios

| Servicio | Gratis |
| :-- | :-- |
| Monitoring | 500 millones de puntos ingeridos, 1.000 millones consultados |
| Notifications | 1 millón HTTPS y 1.000 emails al mes |
| Email Delivery | 3.000 emails al mes |
| Autonomous Database | 2 bases de datos de 1 OCPU y 20 GB |
| Vault | 20 versiones de clave HSM, 150 secretos |

### Cuánto dura

- **La cuenta y lo Always Free:** sin vencimiento declarado.
- **Una instancia concreta:** mientras no sea reclamada por inactividad ([capítulo 08](08-reclamo-por-inactividad.md)) ni la borres.
- **El crédito de prueba:** ~30 días.

`oracle-cloud` `always-free` `free-trial` `limites`
