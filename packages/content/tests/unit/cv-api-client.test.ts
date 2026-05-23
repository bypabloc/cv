/**
 * @description Tests del cliente HTTP del API cv.
 *   Mockean `globalThis.fetch` para verificar la URL construida, los
 *   query params (operation/action/niche/locale), el manejo de errores
 *   HTTP y la resolucion de la base URL desde env vars.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  fetchAwards,
  fetchCertificates,
  fetchCv,
  fetchEducation,
  fetchExperiences,
  fetchLanguages,
  fetchProfile,
  fetchProjects,
  fetchReferences,
  fetchSkillCategories,
} from '../../src/lib/cv-api-client'

const API = 'https://example.test/dev'

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('cv-api-client', () => {
  let fetchMock: ReturnType<typeof vi.fn>
  const origEnv = { ...process.env }

  beforeEach(() => {
    fetchMock = vi.fn().mockResolvedValue(jsonResponse({ name: 'Pablo' }))
    vi.stubGlobal('fetch', fetchMock)
    process.env.PUBLIC_CV_API_URL = API
  })

  afterEach(() => {
    process.env = { ...origEnv }
    vi.restoreAllMocks()
  })

  it('Given default options When fetchCv Then calls /cv?operation=cv&action=get&locale=es', async () => {
    await fetchCv()
    expect(fetchMock).toHaveBeenCalledTimes(1)
    const url = fetchMock.mock.calls[0]?.[0] as string
    expect(url).toBe(`${API}/cv?operation=cv&action=get&locale=es`)
  })

  it('Given niche and locale When fetchExperiences Then includes both query params', async () => {
    await fetchExperiences({ niche: 'fintech', locale: 'en' })
    const url = fetchMock.mock.calls[0]?.[0] as string
    expect(url).toBe(
      `${API}/cv?operation=cv&action=experiences&niche=fintech&locale=en`,
    )
  })

  it('Given apiBase override When fetchProfile Then uses override over env var', async () => {
    await fetchProfile({ apiBase: 'https://override.test/dev/' })
    const url = fetchMock.mock.calls[0]?.[0] as string
    expect(url).toBe(
      'https://override.test/dev/cv?operation=cv&action=profile&locale=es',
    )
  })

  it('Given missing env var and no apiBase Then fetchCv throws', async () => {
    process.env.PUBLIC_CV_API_URL = ''
    process.env.CV_API_URL = ''
    await expect(fetchCv()).rejects.toThrow(/PUBLIC_CV_API_URL/)
  })

  it('Given HTTP 500 When fetching Then throws with status and statusText', async () => {
    fetchMock.mockResolvedValueOnce(
      new Response('boom', { status: 500, statusText: 'Server Error' }),
    )
    await expect(fetchProjects()).rejects.toThrow(/HTTP 500/)
  })

  it.each([
    ['fetchProjects', fetchProjects, 'projects'],
    ['fetchCertificates', fetchCertificates, 'certificates'],
    ['fetchAwards', fetchAwards, 'awards'],
    ['fetchEducation', fetchEducation, 'education'],
    ['fetchLanguages', fetchLanguages, 'languages'],
    ['fetchReferences', fetchReferences, 'references'],
    ['fetchSkillCategories', fetchSkillCategories, 'skills'],
  ])('Given %s When called Then uses action=%s', async (_name, fn, expectedAction) => {
    fetchMock.mockResolvedValueOnce(jsonResponse([]))
    await fn()
    const url = fetchMock.mock.calls[0]?.[0] as string
    expect(url).toContain(`action=${expectedAction}`)
  })

  it('Given JSON response When fetching Then returns parsed body', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse([{ slug: 'a' }]))
    const result = await fetchExperiences()
    expect(result).toEqual([{ slug: 'a' }])
  })
})
