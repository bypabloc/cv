/**
 * @description Tests para createSnapshotProvider — devuelve un provider
 *   read-only que sirve los datos del snapshot estatico.
 */
import { describe, expect, it } from 'vitest'

import { createSnapshotProvider } from '../../src/lib/snapshot-provider'
import { FAKE_SNAPSHOT } from './_fakes'

describe('createSnapshotProvider', () => {
  it('Given snapshot When createSnapshotProvider Then getProfile retorna el profile del snapshot', () => {
    const provider = createSnapshotProvider(FAKE_SNAPSHOT)

    expect(provider.getProfile()).toBe(FAKE_SNAPSHOT.profile)
  })

  it('Given snapshot When createSnapshotProvider Then getExperiences retorna el array del snapshot', () => {
    const provider = createSnapshotProvider(FAKE_SNAPSHOT)

    expect(provider.getExperiences()).toBe(FAKE_SNAPSHOT.experiences)
  })

  it('Given snapshot When createSnapshotProvider Then getProjects retorna el array del snapshot', () => {
    const provider = createSnapshotProvider(FAKE_SNAPSHOT)

    expect(provider.getProjects()).toBe(FAKE_SNAPSHOT.projects)
  })

  it('Given snapshot When createSnapshotProvider Then getSkills retorna el array del snapshot', () => {
    const provider = createSnapshotProvider(FAKE_SNAPSHOT)

    expect(provider.getSkills()).toBe(FAKE_SNAPSHOT.skills)
  })

  it('Given snapshot When createSnapshotProvider Then getEducation retorna el array del snapshot', () => {
    const provider = createSnapshotProvider(FAKE_SNAPSHOT)

    expect(provider.getEducation()).toBe(FAKE_SNAPSHOT.education)
  })
})
