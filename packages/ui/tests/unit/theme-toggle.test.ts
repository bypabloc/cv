/**
 * @description Tests para theme-toggle. Cubre AC-4, AC-5.
 *   Usa happy-dom (configurado en vitest.config.ts).
 */
import { beforeEach, describe, expect, it } from 'vitest'
import {
  applyTheme,
  isTheme,
  nextTheme,
  readStoredTheme,
  storeTheme,
} from '../../src/lib/theme-toggle'

class MemoryStorage implements Storage {
  private store = new Map<string, string>()
  get length() {
    return this.store.size
  }
  clear() {
    this.store.clear()
  }
  getItem(key: string) {
    return this.store.get(key) ?? null
  }
  key(index: number) {
    return Array.from(this.store.keys())[index] ?? null
  }
  removeItem(key: string) {
    this.store.delete(key)
  }
  setItem(key: string, value: string) {
    this.store.set(key, value)
  }
}

describe('isTheme', () => {
  it('Given valid value When check Then returns true', () => {
    expect(isTheme('system')).toBe(true)
    expect(isTheme('dark')).toBe(true)
    expect(isTheme('light')).toBe(true)
  })

  it('Given invalid value When check Then returns false', () => {
    expect(isTheme('blue')).toBe(false)
    expect(isTheme(null)).toBe(false)
    expect(isTheme(undefined)).toBe(false)
    expect(isTheme(42)).toBe(false)
  })
})

describe('nextTheme', () => {
  it('Given "system" When next Then returns "dark"', () => {
    expect(nextTheme('system')).toBe('dark')
  })

  it('Given "dark" When next Then returns "light"', () => {
    expect(nextTheme('dark')).toBe('light')
  })

  it('Given "light" When next Then returns "system" (cycle closes)', () => {
    expect(nextTheme('light')).toBe('system')
  })
})

describe('readStoredTheme', () => {
  it('Given empty storage When read Then returns "system"', () => {
    const s = new MemoryStorage()
    expect(readStoredTheme(s)).toBe('system')
  })

  it('Given stored "dark" When read Then returns "dark"', () => {
    const s = new MemoryStorage()
    s.setItem('theme', 'dark')
    expect(readStoredTheme(s)).toBe('dark')
  })

  it('Given stored invalid value When read Then returns "system"', () => {
    const s = new MemoryStorage()
    s.setItem('theme', 'banana')
    expect(readStoredTheme(s)).toBe('system')
  })
})

describe('applyTheme', () => {
  beforeEach(() => {
    document.documentElement.className = ''
    document.documentElement.removeAttribute('data-theme')
  })

  it('Given "dark" When apply Then <html> gets class "dark"', () => {
    applyTheme('dark', document)
    expect(document.documentElement.classList.contains('dark')).toBe(true)
    expect(document.documentElement.classList.contains('light')).toBe(false)
    expect(document.documentElement.dataset.theme).toBe('dark')
  })

  it('Given "light" When apply Then <html> gets class "light"', () => {
    applyTheme('light', document)
    expect(document.documentElement.classList.contains('light')).toBe(true)
    expect(document.documentElement.classList.contains('dark')).toBe(false)
    expect(document.documentElement.dataset.theme).toBe('light')
  })

  it('Given "system" When apply Then no class is set', () => {
    applyTheme('dark', document)
    applyTheme('system', document)
    expect(document.documentElement.classList.contains('dark')).toBe(false)
    expect(document.documentElement.classList.contains('light')).toBe(false)
    expect(document.documentElement.dataset.theme).toBe('system')
  })
})

describe('storeTheme', () => {
  beforeEach(() => {
    document.documentElement.className = ''
  })

  it('Given a theme When store Then persists and applies', () => {
    const s = new MemoryStorage()
    storeTheme('light', s, document)
    expect(s.getItem('theme')).toBe('light')
    expect(document.documentElement.classList.contains('light')).toBe(true)
  })

  it('Given storage that throws on setItem When store Then still applies theme', () => {
    const throwing: Storage = {
      length: 0,
      clear: () => undefined,
      getItem: () => null,
      key: () => null,
      removeItem: () => undefined,
      setItem: () => {
        throw new Error('storage disabled')
      },
    }
    storeTheme('dark', throwing, document)
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })
})

describe('readStoredTheme catch path', () => {
  it('Given storage that throws on getItem When read Then returns "system"', () => {
    const throwing: Storage = {
      length: 0,
      clear: () => undefined,
      getItem: () => {
        throw new Error('storage disabled')
      },
      key: () => null,
      removeItem: () => undefined,
      setItem: () => undefined,
    }
    expect(readStoredTheme(throwing)).toBe('system')
  })
})

describe('applyTheme no-op', () => {
  it('Given no document When apply Then returns silently', () => {
    expect(() =>
      applyTheme('dark', undefined as unknown as Document),
    ).not.toThrow()
  })
})
