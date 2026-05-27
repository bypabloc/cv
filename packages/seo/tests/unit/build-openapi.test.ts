/**
 * @description Tests para buildOpenApi — OpenAPI 3.1 spec estatico para
 *   los 2 endpoints publicos del backend (POST /contact, GET /track).
 */
import { describe, expect, it } from 'vitest'

import { buildOpenApi } from '../../src/lib/build-openapi'

describe('buildOpenApi', () => {
  it('Given apiEndpoint When build Then es JSON OpenAPI 3.1 valido', () => {
    const out = buildOpenApi({
      apiEndpoint: 'https://api.portfolio.the-full-stack.com',
    })

    const parsed = JSON.parse(out) as {
      openapi: string
      info: { title: string }
    }
    expect(parsed.openapi).toBe('3.1.0')
    expect(parsed.info.title).toBe('Pablo Contreras Portfolio API')
  })

  it('Given apiEndpoint con trailing slash When build Then strippa la slash en servers[0].url', () => {
    const out = buildOpenApi({
      apiEndpoint: 'https://api.portfolio.the-full-stack.com/',
    })

    const parsed = JSON.parse(out) as { servers: { url: string }[] }
    expect(parsed.servers[0]!.url).toBe(
      'https://api.portfolio.the-full-stack.com',
    )
  })

  it('Given se invoca When inspecciono paths Then contiene /contact y /track', () => {
    const out = buildOpenApi({
      apiEndpoint: 'https://api.portfolio.the-full-stack.com',
    })

    const parsed = JSON.parse(out) as { paths: Record<string, unknown> }
    expect(Object.keys(parsed.paths).sort()).toEqual(['/contact', '/track'])
  })

  it('Given se invoca When inspecciono /contact Then tiene POST con request + 202/400/429', () => {
    const out = buildOpenApi({
      apiEndpoint: 'https://api.portfolio.the-full-stack.com',
    })

    const parsed = JSON.parse(out) as {
      paths: {
        '/contact': {
          post: {
            requestBody: { required: boolean }
            responses: Record<string, unknown>
          }
        }
      }
    }
    const contact = parsed.paths['/contact'].post
    expect(contact.requestBody.required).toBe(true)
    expect(Object.keys(contact.responses).sort()).toEqual(['202', '400', '429'])
  })

  it('Given se invoca When inspecciono /track Then tiene GET con 4 query params + 200/400/429', () => {
    const out = buildOpenApi({
      apiEndpoint: 'https://api.portfolio.the-full-stack.com',
    })

    const parsed = JSON.parse(out) as {
      paths: {
        '/track': {
          get: {
            parameters: { in: string; name: string; required: boolean }[]
            responses: Record<string, unknown>
          }
        }
      }
    }
    const track = parsed.paths['/track'].get
    expect(track.parameters.map((p) => p.name).sort()).toEqual([
      'event_id',
      'event_type',
      'path',
      'session_id',
    ])
    expect(Object.keys(track.responses).sort()).toEqual(['200', '400', '429'])
    expect(track.parameters.find((p) => p.name === 'path')!.required).toBe(
      false,
    )
  })

  it('Given se invoca When inspecciono components.schemas Then tiene ContactRequest + ContactAccepted + Error', () => {
    const out = buildOpenApi({
      apiEndpoint: 'https://api.portfolio.the-full-stack.com',
    })

    const parsed = JSON.parse(out) as {
      components: { schemas: Record<string, unknown> }
    }
    expect(Object.keys(parsed.components.schemas).sort()).toEqual([
      'ContactAccepted',
      'ContactRequest',
      'Error',
    ])
  })

  it('Given se invoca When inspecciono Then termina con newline', () => {
    const out = buildOpenApi({ apiEndpoint: 'https://x.com' })

    expect(out.endsWith('\n')).toBe(true)
  })

  it('Given se invoca When inspecciono Then ContactRequest exige los 5 campos', () => {
    const out = buildOpenApi({ apiEndpoint: 'https://x.com' })

    const parsed = JSON.parse(out) as {
      components: {
        schemas: { ContactRequest: { required: string[] } }
      }
    }
    expect(parsed.components.schemas.ContactRequest.required.sort()).toEqual([
      'email',
      'firstName',
      'lastName',
      'message',
      'turnstileToken',
    ])
  })
})
