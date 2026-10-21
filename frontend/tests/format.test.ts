import { formatEur, formatPct } from '@/lib/format'

describe('formato es-ES', () => {
  it('formatea porcentajes y euros', () => {
    expect(formatPct(39.4)).toBe('39,4 %')
    expect(formatEur(24300)).toBe('24.300 €')
  })
})
