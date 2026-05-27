/**
 * @module build-openapi
 * @description Genera un OpenAPI 3.1 spec estatico que describe los 2
 *   endpoints publicos del backend serverless del portfolio:
 *
 *   - POST /contact: form de contacto + Turnstile token.
 *   - GET  /track:   tracking pixel (sendBeacon-friendly).
 *
 *   El spec se sirve desde el MISMO origen del portfolio (no del API
 *   Gateway, que no expone /openapi.json). El api-catalog (.well-known/)
 *   linkea aqui via service-desc.
 *
 *   Scope minimo deliberado: sin auth schemes, sin error responses 5xx,
 *   sin examples detallados. Suficiente para isitagentready + util como
 *   descripcion para agentes IA. Si en el futuro se exponen mas
 *   endpoints, agregar paths en el builder.
 */

interface OpenApiParams {
  /**
   * URL absoluta del API Gateway del env. Ej:
   * 'https://api.portfolio.the-full-stack.com'.
   */
  apiEndpoint: string
}

/**
 * @function buildOpenApi
 * @description Devuelve el OpenAPI 3.1 spec como JSON listo para
 *   escribirse a `dist/openapi.json`. Termina con newline.
 *
 * @example
 *   buildOpenApi({ apiEndpoint: 'https://api.portfolio.the-full-stack.com' })
 *   // JSON con info, servers, paths (/contact POST, /track GET)
 */
export function buildOpenApi(params: OpenApiParams): string {
  const serverUrl = stripTrailingSlash(params.apiEndpoint)
  const spec = {
    openapi: '3.1.0',
    info: {
      title: 'Pablo Contreras Portfolio API',
      version: '1.0.0',
      description:
        'Backend serverless del portfolio the-full-stack.com. 2 endpoints publicos: form de contacto (POST /contact) y tracking pixel (GET /track). Sin auth de usuario; el contacto valida con Cloudflare Turnstile.',
      contact: {
        name: 'Pablo Contreras',
        url: 'https://the-full-stack.com',
      },
      license: {
        name: 'MIT',
      },
    },
    servers: [{ url: serverUrl, description: 'API Gateway' }],
    paths: {
      '/contact': {
        post: {
          summary: 'Send a contact message',
          description:
            'Validates a Cloudflare Turnstile token and queues an email to the portfolio owner. Returns HTTP 202 when accepted (the email is sent asynchronously).',
          operationId: 'sendContact',
          requestBody: {
            required: true,
            content: {
              'application/json': {
                schema: { $ref: '#/components/schemas/ContactRequest' },
              },
            },
          },
          responses: {
            '202': {
              description: 'Accepted; contact queued for delivery.',
              content: {
                'application/json': {
                  schema: { $ref: '#/components/schemas/ContactAccepted' },
                },
              },
            },
            '400': {
              description: 'Validation error (missing fields, bad email).',
              content: {
                'application/json': {
                  schema: { $ref: '#/components/schemas/Error' },
                },
              },
            },
            '429': {
              description: 'Too many requests (rate-limit per-IP).',
              content: {
                'application/json': {
                  schema: { $ref: '#/components/schemas/Error' },
                },
              },
            },
          },
        },
      },
      '/track': {
        get: {
          summary: 'Record a visitor event',
          description:
            'Records a visitor event (page view, click, etc.) for analytics. Returns a 1x1 transparent GIF so it can be loaded as a tracking pixel or via fetch/sendBeacon. Idempotent on event_id.',
          operationId: 'trackEvent',
          parameters: [
            {
              in: 'query',
              name: 'event_type',
              required: true,
              schema: { type: 'string', enum: ['page_view', 'click', 'cta'] },
              description: 'Type of event being recorded.',
            },
            {
              in: 'query',
              name: 'session_id',
              required: true,
              schema: { type: 'string', format: 'uuid' },
              description: 'Stable visitor session identifier (UUIDv4).',
            },
            {
              in: 'query',
              name: 'event_id',
              required: true,
              schema: { type: 'string', format: 'uuid' },
              description: 'Idempotency key for this specific event.',
            },
            {
              in: 'query',
              name: 'path',
              required: false,
              schema: { type: 'string' },
              description:
                'Optional path of the page where the event happened.',
            },
          ],
          responses: {
            '200': {
              description: '1x1 transparent GIF (event recorded).',
              content: { 'image/gif': {} },
            },
            '400': {
              description: 'Validation error (missing or invalid params).',
              content: {
                'application/json': {
                  schema: { $ref: '#/components/schemas/Error' },
                },
              },
            },
            '429': {
              description: 'Too many requests (rate-limit per-IP).',
              content: {
                'application/json': {
                  schema: { $ref: '#/components/schemas/Error' },
                },
              },
            },
          },
        },
      },
    },
    components: {
      schemas: {
        ContactRequest: {
          type: 'object',
          required: [
            'firstName',
            'lastName',
            'email',
            'message',
            'turnstileToken',
          ],
          properties: {
            firstName: { type: 'string', minLength: 1, maxLength: 80 },
            lastName: { type: 'string', minLength: 1, maxLength: 80 },
            email: { type: 'string', format: 'email' },
            message: { type: 'string', minLength: 1, maxLength: 5000 },
            turnstileToken: {
              type: 'string',
              description: 'Cloudflare Turnstile response token.',
            },
          },
        },
        ContactAccepted: {
          type: 'object',
          required: ['contact_id', 'created_at', 'accepted'],
          properties: {
            contact_id: { type: 'string', format: 'uuid' },
            created_at: { type: 'string', format: 'date-time' },
            accepted: { type: 'boolean', enum: [true] },
          },
        },
        Error: {
          type: 'object',
          required: ['code', 'message'],
          properties: {
            code: {
              type: 'string',
              description: 'Machine-readable error code.',
              example: 'INVALID_REQUEST',
            },
            message: {
              type: 'string',
              description: 'Human-readable error message.',
            },
          },
        },
      },
    },
  }
  return `${JSON.stringify(spec, null, 2)}\n`
}

function stripTrailingSlash(url: string): string {
  return url.endsWith('/') ? url.slice(0, -1) : url
}
