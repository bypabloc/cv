---
description: "Reglas de seguridad para este portfolio estatico Astro: credenciales en .env, sin secrets en el bundle publico, headers de seguridad en hosting, sanitizacion de input."
globs: "src/**/*.ts,src/**/*.tsx,src/**/*.astro"
---

# Security Standards - Portfolio

> Reglas de seguridad para el portfolio estatico (Astro 6 + TypeScript).
> El site es publico, sin login, sin DB, sin backend. Las reglas se centran
> en evitar leak de secretos, XSS, configuracion insegura de hosting.

## Credenciales y secretos

- NUNCA hardcodear API keys, tokens, emails o cualquier secreto en el codigo
- SIEMPRE cargar desde `.env` (NO committeado, agregado a `.gitignore`)
- Solo usar `import.meta.env.PUBLIC_*` para valores que **deben** estar en el bundle del browser
- Cualquier valor SIN prefijo `PUBLIC_` se mantiene server-side (build-time)
- NUNCA logear emails personales, contactos, datos privados en `console.log` del bundle publico

### Patron correcto

```typescript
// astro.config.ts o src/lib/config.ts
const PUBLIC_SITE_URL = import.meta.env.PUBLIC_SITE_URL ?? 'https://example.com'
const PRIVATE_ANALYTICS_TOKEN = import.meta.env.ANALYTICS_TOKEN // solo build-time
```

```bash
# .env.local (NO committear)
PUBLIC_SITE_URL=https://my-portfolio.dev
ANALYTICS_TOKEN=sk_xxx     # NO se expone al browser
```

## Validacion de input

El portfolio normalmente no acepta input de usuario, pero si tiene
form de contacto (mailto, formspree, etc.):

- SIEMPRE validar email, nombre, mensaje en cliente y servidor (servidor del provider externo)
- NUNCA confiar en validacion client-only para nada critico
- Sanitizar antes de mostrar input del usuario (si se renderiza en UI)
- NO usar `set:html` en Astro con contenido user-generated
- En Tailwind/CSS, evitar `dangerouslySetInnerHTML` (Biome ya lo enforce con `noDangerouslySetInnerHtml`)

## Headers de seguridad (en hosting)

Configurar en el hosting (`vercel.json`, `netlify.toml`, Cloudflare Pages headers, GitHub Pages no soporta):

- `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY` (o usar CSP `frame-ancestors`)
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- `Content-Security-Policy`: restrictivo, solo `'self'` + dominios necesarios (analytics, fonts si no son self-hosted)

## Content Security Policy

Para un portfolio estatico, CSP estricta es facil de mantener:

```text
default-src 'self';
script-src 'self';
style-src 'self' 'unsafe-inline';   # 'unsafe-inline' solo si se usa CSS inline; preferir 'self' + hashes
img-src 'self' data: https:;
font-src 'self';
connect-src 'self' https://api.<analytics-provider>.com;
object-src 'none';
frame-ancestors 'none';
base-uri 'self';
```

## Dependencias y supply chain

- Revisar `pnpm audit` ANTES de agregar dependencias nuevas
- Pinear versiones en `package.json` (`"astro": "^6.0.0"` esta OK; lockfile fija exacta)
- NUNCA `npm install ...` ni `yarn add ...` — solo pnpm
- Evitar paquetes con < 100 descargas semanales o sin mantener
- Skill `dependency-upgrade` para auditoria periodica

## Datos del CV

El CV es publico por diseno. Aun asi:

- NUNCA committear datos privados (DNI, RUT/RFC, telefono privado, direccion exacta) si no se quieren publicos
- Si hay PDF descargable del CV con datos sensibles, revisar antes de servir
- Email de contacto: considerar obfuscacion JS o usar form provider (formspree, getform) en lugar de mailto plano
- Avatars/fotos personales: revisar metadata EXIF antes de subir (puede contener GPS)

## Anti-patterns prohibidos

- `import.meta.env.SOME_SECRET` referenciado en componentes `.astro` que se renderizan al cliente (lo expone)
- `<script>` inline con datos sensibles (mismo problema)
- `console.log(import.meta.env)` en codigo que se ejecuta en el browser
- Fonts desde Google Fonts CDN (GDPR risk; usar `@fontsource/*`)
- Analytics scripts inline en `<head>` sin CSP que los autorice
- `dangerouslySetInnerHTML` o `set:html` con contenido no sanitizado
