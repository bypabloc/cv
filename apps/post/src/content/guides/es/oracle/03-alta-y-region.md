**03**

# Alta de la cuenta y región principal

[← Índice](README.md)

---

### Pasos

1. Entra a **https://signup.cloud.oracle.com/**.
2. País, nombre y correo; verifica el correo.
3. Elige el **nombre de la cuenta** (*cloud account name* o *tenancy*). Lo pedirá cada login.
4. Elige la **región principal** (ver abajo).
5. Tarjeta de verificación: hace un cargo temporal que se reversa. No hay cobro sin *Upgrade*.
6. Espera el aprovisionamiento. La pantalla dice:
   > *Estamos creando su cuenta; este proceso puede tardar hasta 15 minutos.*

   Llegan dos correos: cuenta creada y cuenta lista (*fully provisioned*). Puedes probar a entrar en **https://cloud.oracle.com/** antes del segundo.

### La región principal: la decisión irreversible

- **No se puede cambiar** después del alta.
- Las instancias Always Free **solo** se crean ahí.
- El formulario advierte:
  > *Las cuentas gratuitas no están disponibles en todas las regiones de datos comerciales. La disponibilidad de cada región puede cambiar a lo largo del tiempo. No intente crear varias cuentas para cambiar de región.*
- Oracle **no publica** qué regiones admiten cuentas gratis ni la capacidad A1 de cada una. La fuente real es el selector del formulario.

### Regiones cercanas a Sudamérica

| Región | Identificador |
| :-- | :-- |
| Colombia Central (Bogotá) | `sa-bogota-1` |
| Chile Central (Santiago) | `sa-santiago-1` |
| Chile West (Valparaíso) | `sa-valparaiso-1` |
| Brazil East (São Paulo) | `sa-saopaulo-1` |
| Brazil Southeast (Vinhedo) | `sa-vinhedo-1` |
| Mexico Central (Querétaro) | `mx-queretaro-1` |
| Mexico Northeast (Monterrey) | `mx-monterrey-1` |
| US East (Ashburn) | `us-ashburn-1` |

Fuente: [Regions and Availability Domains](https://docs.oracle.com/en-us/iaas/Content/General/Concepts/regions.htm).

### Cómo elegir

1. Mira cuáles aparecen en el selector: las que no admiten cuenta gratis no aparecen o muestran aviso.
2. Elige la más cercana a tus usuarios.
3. Las regiones grandes (Ashburn, Phoenix, Frankfurt) tienen fama de estar sin capacidad A1. Es anecdótico y no verificable.

### Caso real

- Región asignada: **Chile Central (Santiago)**, con un solo dominio de disponibilidad (`AD-1`).
- Sin capacidad A1 el día del alta (12 intentos). Ver [capítulo 06](06-instancia.md).

`oracle-cloud` `signup` `regiones` `home-region`
