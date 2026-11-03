import { describe, expect, it } from 'vitest'

import {
  formatCountdown,
  formatCurrency,
  formatDate,
  formatDateTime,
  formatTime,
  formatVehicleType,
  todayInVietnam,
} from './format'

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

describe('formatTime', () => {
  it('giờ UTC sang giờ Việt Nam dạng HH:mm', () => {
    expect(formatTime('2026-12-14T23:00:00Z')).toBe('06:00')
    expect(formatTime('2026-12-15T13:05:00Z')).toBe('20:05')
  })

  it('trả chuỗi rỗng với giá trị không hợp lệ', () => {
    expect(formatTime('không phải giờ')).toBe('')
  })
})

describe('formatDate', () => {
  it('giữ nguyên ngày của chuỗi YYYY-MM-DD', () => {
    expect(formatDate('2026-12-16')).toBe('16/12/2026')
  })

  it('đổi thời điểm sang ngày Việt Nam', () => {
    expect(formatDate('2026-12-14T23:00:00Z')).toBe('15/12/2026')
  })

  it('trả chuỗi rỗng với giá trị không hợp lệ', () => {
    expect(formatDate('abc')).toBe('')
  })
})

describe('todayInVietnam', () => {
  it('lấy ngày theo giờ Việt Nam, không theo UTC', () => {
    // 22:00 UTC ngày 14/12 là 05:00 ngày 15/12 giờ Việt Nam
    expect(todayInVietnam(new Date('2026-12-14T22:00:00Z'))).toBe('2026-12-15')
    expect(todayInVietnam(new Date('2026-12-14T16:59:00Z'))).toBe('2026-12-14')
  })
})

describe('formatVehicleType', () => {
  it('dùng tên loại xe từ backend, thiếu tên thì hiện theo số chỗ', () => {
    expect(formatVehicleType('Xe 7 chỗ VIP', 7)).toBe('Xe 7 chỗ VIP')
    expect(formatVehicleType(null, 16)).toBe('Xe 16 chỗ')
  })
})

describe('formatCountdown', () => {
  it.each([
    [300000, '05:00'],
    [120000, '02:00'],
    [119001, '02:00'],
    [61000, '01:01'],
    [1, '00:01'],
    [0, '00:00'],
    [-5000, '00:00'],
  ])('%i ms -> %s', (ms, expected) => {
    expect(formatCountdown(ms)).toBe(expected)
  })
})
