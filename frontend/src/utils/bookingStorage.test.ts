import { describe, expect, it } from 'vitest'

import {
  accessCodeFor,
  BOOKING_STORAGE_KEY,
  clearStoredBooking,
  clearStoredBookingFor,
  CONFIRMED_STORAGE_KEY,
  moveToConfirmed,
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

  it('chuyển đơn vừa xác nhận sang kho riêng, ô đang giữ trống cho đơn mới', () => {
    saveStoredBooking({ ma_don: 'DH00100000', ma_truy_cap: 'ma-1' })
    moveToConfirmed('DH00100000')
    saveStoredBooking({ ma_don: 'DH00100001', ma_truy_cap: 'ma-2' })
    moveToConfirmed('DH00100001')

    expect(readStoredBooking()).toBeNull()
    expect(accessCodeFor('DH00100000')).toBe('ma-1')
    expect(accessCodeFor('DH00100001')).toBe('ma-2')
    expect(accessCodeFor('DH00100002')).toBeNull()
  })

  it('không chuyển khi ô đang giữ là đơn khác', () => {
    saveStoredBooking({ ma_don: 'DH00100000', ma_truy_cap: 'ma-1' })

    moveToConfirmed('DH00100009')

    expect(readStoredBooking()?.ma_don).toBe('DH00100000')
    expect(accessCodeFor('DH00100009')).toBeNull()
  })

  it.each(['khong-phai-json', '[1]', 'null', '{"DH1":5}'])('bỏ qua kho đơn đã xác nhận hỏng %s', (raw) => {
    sessionStorage.setItem(CONFIRMED_STORAGE_KEY, raw)

    expect(accessCodeFor('DH1')).toBeNull()
  })
})
