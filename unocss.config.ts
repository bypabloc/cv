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
        display: "inline-block",
        "vertical-align": "middle",
      },
    }),
  ],
});
