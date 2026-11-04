import { describe, expect, it } from 'vitest'

import { collapseSpaces, isPointTooLong, isValidEmail, isValidPhone } from './validation'

describe('isValidPhone', () => {
  it.each(['0905123456', '0123456789', ' 0905123456 '])('chấp nhận %j', (value) => {
    expect(isValidPhone(value)).toBe(true)
  })

  it.each(['', '090512345', '09051234567', '1905123456', '09051234ab', '+84905123456'])(
    'từ chối %j',
    (value) => {
      expect(isValidPhone(value)).toBe(false)
    },
  )
})

describe('isValidEmail', () => {
  it('chấp nhận email thông thường', () => {
    expect(isValidEmail('an@example.com')).toBe(true)
  })

  it.each(['an', 'an@', 'an@example', 'a n@example.com'])('từ chối %j', (value) => {
    expect(isValidEmail(value)).toBe(false)
  })
})

describe('collapseSpaces', () => {
  it('bỏ khoảng trắng hai đầu và gộp khoảng trắng giữa', () => {
    expect(collapseSpaces('  12   Lê  Lợi ')).toBe('12 Lê Lợi')
    expect(collapseSpaces('   ')).toBe('')
  })
})

describe('isPointTooLong', () => {
  it('tính cả phần " – " backend chèn giữa khu vực và địa chỉ', () => {
    // "Đà Nẵng" 7 ký tự + 3 ký tự " – " + 140 = 150
    expect(isPointTooLong('Đà Nẵng', 'x'.repeat(140))).toBe(false)
    expect(isPointTooLong('Đà Nẵng', 'x'.repeat(141))).toBe(true)
  })

  it('không có địa chỉ thì chỉ tính khu vực', () => {
    expect(isPointTooLong('Đà Nẵng', '   ')).toBe(false)
  })
})
