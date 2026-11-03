import { describe, expect, it } from 'vitest'

import {
  accessCodeFor,
  BOOKING_STORAGE_KEY,
  clearStoredBooking,
  clearStoredBookingFor,
  readStoredBooking,
  saveStoredBooking,
} from './bookingStorage'

describe('bookingStorage', () => {
  it('lưu, đọc và xóa đơn đang giữ', () => {
    saveStoredBooking({ ma_don: 'DH00100000', ma_truy_cap: 'ma-bi-mat' })

    expect(readStoredBooking()).toEqual({ ma_don: 'DH00100000', ma_truy_cap: 'ma-bi-mat' })
    clearStoredBooking()
    expect(readStoredBooking()).toBeNull()
  })

  it('chỉ xóa đơn đã lưu khi đúng mã đơn', () => {
    saveStoredBooking({ ma_don: 'DH00100000', ma_truy_cap: 'ma-bi-mat' })

    clearStoredBookingFor('DH00100001')
    expect(readStoredBooking()).not.toBeNull()
    clearStoredBookingFor('DH00100000')
    expect(readStoredBooking()).toBeNull()
  })

  it('chỉ trả mã truy cập cho đúng mã đơn', () => {
    saveStoredBooking({ ma_don: 'DH00100000', ma_truy_cap: 'ma-bi-mat' })

    expect(accessCodeFor('DH00100000')).toBe('ma-bi-mat')
    expect(accessCodeFor('DH00100001')).toBeNull()
  })

  it.each(['khong-phai-json', '{"ma_don":"DH1"}', 'null'])('bỏ qua dữ liệu hỏng %s', (raw) => {
    sessionStorage.setItem(BOOKING_STORAGE_KEY, raw)

    expect(readStoredBooking()).toBeNull()
  })
})
