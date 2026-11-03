import { describe, expect, it } from 'vitest'

import { formatCurrency, formatDateTime } from './format'

describe('formatCurrency', () => {
  it.each([
    [200000, '200.000 đ'],
    [150000, '150.000 đ'],
    [1250000, '1.250.000 đ'],
    [0, '0 đ'],
  ])('%d -> %s', (amount, expected) => {
    expect(formatCurrency(amount)).toBe(expected)
  })
})

describe('formatDateTime', () => {
  it('chuyển giờ UTC sang giờ Việt Nam', () => {
    expect(formatDateTime('2026-12-15T01:00:00Z')).toBe('15/12/2026 08:00')
  })

  it('sang ngày mới khi qua nửa đêm giờ Việt Nam', () => {
    expect(formatDateTime('2026-12-14T17:30:00Z')).toBe('15/12/2026 00:30')
  })

  it('nhận chuỗi có múi giờ +07:00 và đối tượng Date', () => {
    expect(formatDateTime('2026-12-15T23:05:00+07:00')).toBe('15/12/2026 23:05')
    expect(formatDateTime(new Date('2026-01-02T03:04:00Z'))).toBe('02/01/2026 10:04')
  })

  it.each(['', 'không phải ngày', '2026-13-45T00:00:00Z'])(
    'trả chuỗi rỗng với giá trị không hợp lệ: %j',
    (value) => {
      expect(formatDateTime(value)).toBe('')
    },
  )

  it('trả chuỗi rỗng với Date không hợp lệ', () => {
    expect(formatDateTime(new Date(Number.NaN))).toBe('')
  })
})
