import { ui, defaultLang, showDefaultLang } from "./ui";

export function getLangFromUrl(url: URL) {
  const [, lang] = url.pathname.split("/");
  if (lang in ui) return lang as keyof typeof ui;
  return defaultLang;
}

export function useTranslations(lang: string = defaultLang) {
  return function t(key: string, args: Record<string, any> = {}) {
    const keys = key.split(".");
    let translation: any = ui[lang];

    for (const k of keys) {
      if (translation && typeof translation === "object" && k in translation) {
        translation = translation[k];
      } else {
        translation = undefined;
        break;
      }
    }

    // Si no se encuentra la traducción en el idioma seleccionado, busca en el idioma por defecto
    if (translation === undefined) {
      translation = ui[defaultLang];
      for (const k of keys) {
        if (
          translation &&
          typeof translation === "object" &&
          k in translation
        ) {
          translation = translation[k];
        } else {
          translation = undefined;
          break;
        }
      }
    }

    if (typeof translation === "string") {
      return translation.replace(/\{(\w+)\}/g, (match, key) => {
        return args[key] !== undefined ? args[key] : match;
      });
    }

    return translation;
  };
}

export function useTranslatedPath(lang: keyof typeof ui) {
  return function translatePath(path: string, l: string = lang) {
    return !showDefaultLang && l === defaultLang ? path : `/${l}${path}`;
  };
}