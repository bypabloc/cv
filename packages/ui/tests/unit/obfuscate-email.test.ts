/**
 * @description Tests para obfuscateEmail / deobfuscateEmail.
 */
import { describe, expect, it } from 'vitest'
import { deobfuscateEmail, obfuscateEmail } from '../../src/lib/obfuscate-email'

describe('obfuscateEmail', () => {
  it('Given a valid email When obfuscate Then returns base64 without padding', () => {
    const result = obfuscateEmail('a@b.com')
    expect(result).toBe('YUBiLmNvbQ')
    expect(result).not.toContain('=')
  })

  it('Given email without @ When obfuscate Then throws', () => {
    expect(() => obfuscateEmail('notanemail')).toThrow(/must contain/u)
  })

  it('Given Pablo email When roundtrip Then returns original', () => {
    const original = 'pacg1991@gmail.com'
    const obf = obfuscateEmail(original)
    const back = deobfuscateEmail(obf)
    expect(back).toBe(original)
  })

  it('Given email with unicode When roundtrip Then preserves it', () => {
    const original = 'pacg1991@example.org'
    expect(deobfuscateEmail(obfuscateEmail(original))).toBe(original)
  })
})
