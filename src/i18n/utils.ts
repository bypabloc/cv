import { ui, defaultLang, showDefaultLang } from "./ui";

export function getLangFromUrl(url: URL) {
  const [, lang] = url.pathname.split("/");
  if (lang in ui) return lang as keyof typeof ui;
  return defaultLang;
}

export function useTranslations(lang: string = defaultLang) {
  return function t(key: string) {
    const keys = key.split("."); // Divide la cadena por puntos
    let translation = ui[lang];

    for (const k of keys) {
      if (translation[k] !== undefined) {
        translation = translation[k]; // Navega por los niveles del objeto
      } else {
        translation = undefined;
        break;
      }
    }

    // Si no se encuentra la traducción en el idioma seleccionado, busca en el idioma por defecto
    if (translation === undefined) {
      translation = ui[defaultLang];
      for (const k of keys) {
        if (translation[k] !== undefined) {
          translation = translation[k];
        } else {
          translation = undefined;
          break;
        }
      }
    }

    return translation;
  };
}


export function useTranslatedPath(lang: keyof typeof ui) {
  return function translatePath(path: string, l: string = lang) {
    return !showDefaultLang && l === defaultLang ? path : `/${l}${path}`;
  };
}
