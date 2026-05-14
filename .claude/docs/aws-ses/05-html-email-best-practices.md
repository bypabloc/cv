# HTML Email: best practices, MJML, responsive, cross-client

> Como disenar emails HTML que se vean bien en Gmail, Outlook, Apple Mail.
> MJML framework y responsive design patterns.

## Reto principal: incompatibilidad de clientes

Email es mas fragmentado que web browsers:

| Cliente | Motor de render | Soporte CSS |
|---------|-----------------|------------|
| Gmail | WebKit (custom) | Limitado (sin CSS Grid/Flexbox) |
| Outlook 2016-2021 | Microsoft Word | Muy limitado (casi ninguno) |
| Apple Mail | WebKit | Muy bueno (similar a Safari) |
| Thunderbird | Mozilla (custom) | Bueno |
| Yahoo Mail | WebKit | Bueno |

**Realidad**: Un email que se ve perfecto en Apple Mail puede verse roto en Outlook.

## Patron de diseño: Tables + Divs hibrido

### NO hagas esto (no funciona en Outlook)

```html
<!-- INCORRECTO: CSS Grid -->
<div style="display: grid; grid-template-columns: 1fr 1fr;">
  <div>Column 1</div>
  <div>Column 2</div>
</div>

<!-- INCORRECTO: CSS Flexbox -->
<div style="display: flex;">
  <div>Item 1</div>
  <div>Item 2</div>
</div>

<!-- INCORRECTO: CSS positioning -->
<div style="position: absolute; top: 0; left: 0;">
  Positioned content
</div>
```

Outlook usa Word's rendering engine → NO CSS moderno.

### HAGAS esto (funciona en TODOS los clientes)

```html
<!-- CORRECTO: Tables para estructura -->
<table width="100%" cellpadding="0" cellspacing="0">
  <tr>
    <td width="50%">Column 1</td>
    <td width="50%">Column 2</td>
  </tr>
</table>

<!-- CORRECTO: Inline CSS -->
<p style="font-size: 14px; color: #333; line-height: 1.6;">
  Texto con estilos inline
</p>

<!-- CORRECTO: Media queries para mobile -->
<style>
  @media (max-width: 600px) {
    table { width: 100% !important; }
    td { display: block !important; width: 100% !important; }
  }
</style>
```

## Checklist de emails robustos

### 1. Ancho de email

```html
<table width="600" style="max-width: 600px;" align="center" cellpadding="0" cellspacing="0">
  <!-- Todo el contenido va aqui -->
</table>
```

**600px** es el standard. En mobile (media query) escala al 100%.

### 2. Fonts web-safe

**NO**:
```html
<p style="font-family: 'Custom Font', sans-serif;">...</p>
```

**SI**:
```html
<p style="font-family: -apple-system, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;">
  Fallback chain: iOS system → Windows → General
</p>
```

Fonts web-safe recomendadas:
- Sans-serif: Arial, Helvetica, Verdana, 'Segoe UI', Georgia, Tahoma
- Serif: Georgia, 'Times New Roman'
- Mono: 'Courier New', Courier, monospace

**NUNCA Google Fonts en emails** (muchos clientes no cargan CSS externo).

### 3. CSS inline (no external stylesheets)

```html
<!-- INCORRECTO: external stylesheet -->
<link rel="stylesheet" href="styles.css">

<!-- CORRECTO: style attribute -->
<p style="color: #333; font-size: 16px;">Texto</p>

<!-- CORRECTO: <style> tag (soportado en Apple Mail, Gmail) -->
<style>
  table { width: 100%; }
  p { color: #333; }
</style>
```

**Hybrid approach**: `<style>` tag para reglas comunes + `style=` attribute para overrides.

### 4. Imagenes

```html
<!-- CORRECTO: alt text + absolute URL -->
<img
  src="https://cdn.example.com/logo.png"
  alt="Company logo"
  width="200"
  height="100"
  style="display: block; border: 0;"
/>

<!-- INCORRECTO: relative URL -->
<img src="logo.png" />

<!-- INCORRECTO: sin alt text -->
<img src="https://..." />
```

**Reglas**:
- URL absoluta (https://)
- Alt text siempre
- Width + height attributes (previene reflow)
- `border: 0` (legacy, pero sigue siendo buena practica)

### 5. Botones (usando tables, no <button>)

```html
<!-- CORRECTO: table para button -->
<table align="center" cellpadding="0" cellspacing="0" style="border-radius: 4px; background-color: #007bff;">
  <tr>
    <td style="padding: 12px 24px;">
      <a href="https://example.com/confirm" style="color: white; text-decoration: none; font-weight: bold; display: block;">
        Confirmar email
      </a>
    </td>
  </tr>
</table>

<!-- INCORRECTO: <button> (no funciona en email) -->
<button onclick="...">Confirmar</button>
```

### 6. Plain text alternative (OBLIGATORIO)

```python
ses.send_email(
    Message={
        'Subject': {'Data': 'Asunto'},
        'Body': {
            'Text': {
                'Data': 'Version plain text del email',
            },
            'Html': {
                'Data': '<html>...</html>',
            },
        },
    },
)
```

Si no incluyes `Text`, algunos clientes no renderizan el email.

## MJML: Framework para emails responsive

MJML compila a HTML cross-client compatible. Ideal para plantillas complejas.

### Instalacion

```bash
npm install -g mjml
```

### Ejemplo basico

```mjml
<mjml>
  <mj-head>
    <mj-title>Nuevo contacto</mj-title>
    <mj-preview>Recibiste un mensaje</mj-preview>
    <mj-style>
      .header { color: #333; }
    </mj-style>
  </mj-head>
  <mj-body background-color="#f4f4f4">
    <mj-section background-color="#ffffff">
      <mj-column>
        <mj-image width="200px" src="https://example.com/logo.png"></mj-image>
        <mj-text font-size="20px" align="center" color="#1f496e">
          Nuevo contacto
        </mj-text>
        <mj-divider border-color="#ddd"></mj-divider>
        <mj-text color="#595959">
          <p><strong>Nombre:</strong> {{name}}</p>
          <p><strong>Email:</strong> {{email}}</p>
        </mj-text>
        <mj-button href="https://example.com/inbox">
          Ver en dashboard
        </mj-button>
      </mj-column>
    </mj-section>
  </mj-body>
</mjml>
```

### Compilar a HTML

```bash
mjml contact-notification.mjml -o contact-notification.html
```

Output: HTML robusto compatible con TODOS los clients.

### Usar en SES (via SendTemplatedEmail)

```python
# 1. Copiar HTML generado por MJML a SES Console
# 2. Crear template con placeholders {{name}}, {{email}}
# 3. SendTemplatedEmail con TemplateData en JSON

response = ses.send_templated_email(
    Source='no-reply@the-full-stack.com',
    Destination={'ToAddresses': ['pacg1991@gmail.com']},
    Template='ContactNotificationMJML',
    TemplateData=json.dumps({
        'name': 'Pablo',
        'email': 'user@example.com',
    }),
)
```

## Dark mode support

Clientes modernos (Apple Mail, Gmail, Outlook 2019+) soportan dark mode:

```html
<style>
  @media (prefers-color-scheme: dark) {
    /* Dark mode overrides */
    table { background-color: #222 !important; }
    p { color: #eee !important; }
    a { color: #66d9ff !important; }
  }
</style>
```

**Nota**: Gmail e Outlook 2019 invierten colores automaticamente en dark mode.
Verifica como se ve.

## Limites importantes

| Limite | Valor | Notas |
|--------|-------|-------|
| Max email size | 40 MB (SES) | Includes attachments |
| Gmail clip size | 102 KB | Emails > 102KB se truncan en Gmail (collapse todo) |
| Outlook max width | 1920px (pero 600px recomendado) | Outlook renderiaza ancho |

**Consejo**: Mantener HTML < 100 KB. Test en [Litmus](https://litmus.com/) o
[Email on Acid](https://www.emailonacid.com/).

## Herramientas de testing

1. **Litmus** (premium): Preivew en 70+ clientes
2. **Email on Acid** (premium): Feedback visual real-time
3. **Can I Email** (free): CSS property browser para email
4. **Premailer** (free): Inline CSS automaticamente

### Premailer Python

```python
from premailer import Premailer

html = """
<style>
  p { color: red; font-size: 14px; }
</style>
<p>Hello</p>
"""

p = Premailer(html)
inlined_html = p.transform()
# Resultado: <p style="color: red; font-size: 14px;">Hello</p>
```

## Template minimalista para portfolio

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Nuevo contacto</title>
  <style>
    body { font-family: -apple-system, 'Segoe UI', Arial, sans-serif; }
    table { border-collapse: collapse; }
    @media (max-width: 600px) {
      table { width: 100% !important; }
      td { display: block !important; width: 100% !important; }
    }
    @media (prefers-color-scheme: dark) {
      body { background-color: #222 !important; }
      table { background-color: #333 !important; color: #eee !important; }
      a { color: #66d9ff !important; }
    }
  </style>
</head>
<body style="margin: 0; padding: 0; background-color: #f9f9f9;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f9f9f9;">
    <tr>
      <td align="center" style="padding: 20px;">
        <table width="600" cellpadding="0" cellspacing="0" style="background-color: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
          <tr>
            <td style="padding: 30px; border-bottom: 1px solid #eee;">
              <h2 style="margin: 0 0 20px 0; color: #333;">Nuevo contacto</h2>
            </td>
          </tr>
          <tr>
            <td style="padding: 30px;">
              <p><strong>Nombre:</strong> {{name}}</p>
              <p><strong>Email:</strong> {{email}}</p>
              <p><strong>Mensaje:</strong></p>
              <p style="color: #666; background-color: #f5f5f5; padding: 10px; border-radius: 4px;">
                {{message}}
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding: 20px; text-align: center; border-top: 1px solid #eee; color: #999; font-size: 12px;">
              <p>Este email fue generado automaticamente. No responder a esta direccion.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
```

## Fuentes

- [MJML: The Responsive Email Framework](https://mjml.io/)
- [HTML Email Best Practices 2026 (Medium)](https://medium.com/@romualdo.bugai/designing-high-performance-email-layouts-in-2026-a-practical-guide-from-the-trenches-a3e7e4535692)
- [Can I Email: Email Client CSS Support](https://www.caniuse.email/)
- [AWS SES HTML email guidelines](https://docs.aws.amazon.com/ses/latest/dg/send-email-html.html)

**Verificado 2026-05-13**
