import { definePreset } from "unocss";
import type { Preset } from "unocss";

/**
 * Convierte un valor dado a un número entero.
 * Retorna 0 si el valor no puede ser convertido a un entero válido.
 *
 * @param {string | number} value El valor a convertir.
 * @return {number} El valor entero convertido o 0 si la conversión falla.
 */
function toValidInt(value: string | number): number {
  const valueStr = value.toString();
  const result = parseInt(valueStr, 10);
  return isNaN(result) ? 0 : result;
}

export default definePreset((params?: Preset) => {
  const { options } = params || {};
  const { factor = 4 } = options || {};

  return {
    name: "styles",
    rules: [
      // Regla para margin
      [/^m-(\d+)$/, ([, d]) => ({ margin: `${toValidInt(d) * factor}px` })],
      [
        /^mx-(\d+)$/,
        ([, d]) => ({
          marginLeft: `${toValidInt(d) * factor}px`,
          marginRight: `${toValidInt(d) * factor}px`,
        }),
      ],
      [
        /^my-(\d+)$/,
        ([, d]) => ({
          marginTop: `${toValidInt(d) * factor}px`,
          marginBottom: `${toValidInt(d) * factor}px`,
        }),
      ],

      // Regla para padding
      [/^p-(\d+)$/, ([, d]) => ({ padding: `${toValidInt(d) * factor}px` })],
      [
        /^px-(\d+)$/,
        ([, d]) => ({
          paddingLeft: `${toValidInt(d) * factor}px`,
          paddingRight: `${toValidInt(d) * factor}px`,
        }),
      ],
      [
        /^py-(\d+)$/,
        ([, d]) => ({
          paddingTop: `${toValidInt(d) * factor}px`,
          paddingBottom: `${toValidInt(d) * factor}px`,
        }),
      ],

      // Regla para gap
      [/^gap-(\d+)$/, ([, d]) => ({ gap: `${toValidInt(d) * factor}px` })],
    ],
    variants: [
      /* ... */
    ],
    shortcuts: [
      /* ... */
    ],
  };
});
