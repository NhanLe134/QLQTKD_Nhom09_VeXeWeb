import { describe, expect, it } from 'vitest'

import { isValidEmail, isValidPhone } from './validation'

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
