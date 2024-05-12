// unocss.config.ts
import { defineConfig } from "unocss";
import { presetIcons } from "unocss";
import Styles from "./src/presets/styles";

export default defineConfig({
  presets: [
    Styles({
      // Options
      name: "cv-styles",
      options: {
        factor: 4,
      },
    }),
    presetIcons({
      scale: 1.2,
      warn: true,
      collections: {
        // https://icon-sets.iconify.design/
        mdi: () =>
          import("@iconify-json/mdi/icons.json").then((i) => i.default),
        "material-symbols": () =>
          import("@iconify-json/material-symbols/icons.json").then(
            (i) => i.default
          ),
        "ant-design": () =>
          import("@iconify-json/ant-design/icons.json").then((i) => i.default),
        clarity: () =>
          import("@iconify-json/clarity/icons.json").then((i) => i.default),
      },
      extraProperties: {
        "font-size": "1.2em",
        display: "inline-block",
        "vertical-align": "middle",
      },
    }),
  ],
  safelist: [
    "i-mdi-whatsapp",
    "dark:i-mdi-whatsapp",
    "i-material-symbols-phone-enabled-outline",
    "dark:i-material-symbols-phone-enabled",
    "i-material-symbols-mail-outline",
    "dark:i-material-symbols-mail",
    "i-ant-design-linkedin-outlined",
    "dark:i-ant-design-linkedin-filled",
    "i-ant-design-github-outlined",
    "dark:i-ant-design-github-filled",
  ],
});
